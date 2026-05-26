import os
import re
import yaml
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from explain_behaviour.models.behavioural_analysis_GBM import BehavioralAnalysisGBM
from explain_behaviour.preprocessing.trial_features import prepare_behavior_features

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.cicada_tools.core.array_utils import find_nearest

rng = np.random.default_rng(20)

# ----------------------------------------------------------------------------------------------------------------------
# UTILS
# ----------------------------------------------------------------------------------------------------------------------
def build_features_table(nwb_list):
    """Extract behavior trial tables and compute DLC features from NWB files.

    DLC computation replicates dlc_analysis.get_traces_by_epoch(center=True)
    from the original nwb_analysis pipeline.
    """
    concatenated_behavior = []
    for nwb_file in tqdm(nwb_list, desc='Extract features for model training ... '):
        with NWBSession(nwb_file) as session_data:
            bhv_df = session_data.behavior.get_trial_table().copy(deep=True)
            bhv_df['subject'] = session_data.subject_id
            bhv_df['session_name'] = session_data.session_id
            bhv_df = bhv_df.loc[bhv_df.early_lick == 0].reset_index(drop=True)

            dlc_times = session_data.behavior.get_behavioral_time_series_timestamps(
                serie_name='pupil_area'
            )
            if dlc_times is None:
                continue  # skip sessions without DLC (matches original inner-join exclusion)

            fr = 1 / np.median(np.diff(dlc_times))
            nframes_window = int(round(2 * fr))  # ~400 at 200 Hz

            trial_starts = bhv_df['start_time'].values
            trial_start_idx = np.array([find_nearest(dlc_times, t) for t in trial_starts])
            window_start_idx = np.array([find_nearest(dlc_times, t - 2) for t in trial_starts])

            dlc_nwb_keys = ['behavior', 'BehavioralTimeSeries']
            thresholds = {'pupil_area': 0.6, 'whisker_velocity': 0.8, 'jaw_y': 0.6, 'whisker_angle': 0.8}

            dlc_results = {
                'pupil_area_nanmean': [],
                'whisker_velocity_mean_abs': [],
                'jaw_y_nanmean': [],
                'jaw_y_mean_abs_diff': [],
                'whisker_angle_mean': [],
            }

            # Session-level NaN filter replicates get_likelihood_filtered_bodypart:
            # skip session if any non-pupil, non-tongue part has >30% low-likelihood frames.
            # jaw_angle is checked here (not used as feature); whisker_angle is checked in
            # the main feature loop below.
            session_skip = False
            extra_filter_keys = {
                'jaw_angle': ('jaw_', 'likelihood', 0.6),
            }
            for fkey, (froot, fsuffix, fthresh) in extra_filter_keys.items():
            #     try:
                fraw = session_data.behavior.get_behavioral_time_series_data(serie_name=fkey)
                flike = session_data.petersen.get_dlc_data(dlc_nwb_keys, froot + fsuffix)
                fdata = np.where(flike >= fthresh, fraw, np.nan).astype(float)
                if np.isnan(fdata).mean() > 0.3:
                    session_skip = True
                    break
                # except Exception:
                #     pass  # part absent in this NWB — don't skip on missing data

            if session_skip:
                continue

            part_data = {}
            for key in ['pupil_area', 'whisker_velocity', 'jaw_y', 'whisker_angle']:
                raw_data = session_data.behavior.get_behavioral_time_series_data(serie_name=key)
                kinematic = key.split('_')[-1]
                root = re.sub(kinematic, '', key)
                suffix = 'base_likelihood' if 'whisker' in key else 'likelihood'
                likelihood = session_data.petersen.get_dlc_data(dlc_nwb_keys, root + suffix)
                data = np.where(likelihood >= thresholds[key], raw_data, np.nan).astype(float)

                # pupil_area exempt from session skip (matches 'pupil' not in part in original)
                if key != 'pupil_area' and np.isnan(data).mean() > 0.3:
                    session_skip = True
                    break

                part_data[key] = data

            if session_skip:
                continue

            for key, data in part_data.items():
                # jaw_y: subtract 5th-percentile of valid session values (global baseline)
                if key == 'jaw_y':
                    valid = data[~np.isnan(data)]
                    if len(valid) > 0:
                        data = data - np.percentile(valid, 5)

                n_total = len(data)
                for ws, we in zip(window_start_idx, trial_start_idx):
                    frames = np.arange(ws, min(we, n_total))
                    if len(frames) == 0:
                        window = np.array([np.nan])
                    else:
                        window = data[frames].copy()

                    # per-trial centering: subtract mean of baseline frames 175:200
                    if len(window) >= 200:
                        center_val = np.nanmean(window[175:200])
                    elif len(window) > 0:
                        center_val = np.nanmean(window)
                    else:
                        center_val = np.nan
                    window = window - center_val

                    if key == 'pupil_area':
                        dlc_results['pupil_area_nanmean'].append(np.nanmean(window))
                    elif key == 'whisker_velocity':
                        # diff per trial (center cancels: diff(x-c)=diff(x)), matching original
                        wv_diff = np.full(len(window), np.nan)
                        if len(window) > 1:
                            wv_diff[1:] = np.diff(window) * nframes_window
                        dlc_results['whisker_velocity_mean_abs'].append(np.nanmean(np.abs(wv_diff)))
                    elif key == 'jaw_y':
                        dlc_results['jaw_y_nanmean'].append(np.nanmean(window))
                        dlc_results['jaw_y_mean_abs_diff'].append(
                            np.nanmean(np.abs(np.diff(window))) if len(window) > 1 else np.nan
                        )
                    elif key == 'whisker_angle':
                        dlc_results['whisker_angle_mean'].append(np.nanmean(window))

            dlc_df = pd.DataFrame(dlc_results)
            bhv_df = pd.concat([bhv_df.reset_index(drop=True), dlc_df], axis=1)
            concatenated_behavior.append(bhv_df)

    return pd.concat(concatenated_behavior)

def run_behaviour_model(df, config, results_dir):
    df_use = prepare_behavior_features(df, config)

    if config['mode'] == 'classification':
        df_use = df_use.loc[df_use.trial_type == 'whisker_trial']
    elif config['mode'] == 'regression':
        df_use = df_use.dropna(subset=['reaction_time'])
        df_use = df_use.loc[df_use.trial_type.isin(['whisker_trial', 'auditory_trial'])]
        df_use = df_use.loc[df_use.trial_outcome == 'Hit']

    if 'dlc_features' in config:
        already = set(config['whisker_features'])
        new_feats = [f for f in config['dlc_features'] if f not in already]
        new_labels = [config['dlc_features_labels'][i]
                      for i, f in enumerate(config['dlc_features']) if f not in already]
        config['whisker_features'] = config['whisker_features'] + new_feats
        config['feature_labels'] = config['feature_labels'] + new_labels

    # Save checkpoint before test-session split so comparison is not confounded
    # by which random session gets held out.
    df_pre_split = df_use[config['whisker_features']].rename(
        columns=dict(zip(df_use[config['whisker_features']].columns, config['feature_labels']))
    )

    df_test = None
    if config['leave_out_one_session']:
        test_session = rng.choice(df_use['session'].unique())
        df_test = df_use[df_use['session'] == test_session]
        df_use = df_use[df_use['session'] != test_session]

    df_use = df_use[config['whisker_features']]
    df_use = df_use.rename(columns=dict(zip(df_use.columns, config['feature_labels'])))

    # return None
    run_name = f"run_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    save_dir = results_dir / run_name
    save_dir.mkdir(parents=True, exist_ok=True)

    analyzer = BehavioralAnalysisGBM(save_path=save_dir, mode=config['mode'], random_state=config['random_state'])
    results = analyzer.run_analysis(
        df=df_use,
        outcome_col=config['outcome_column'],
        categorical_cols=config['categorical_columns'],
        interaction_features=config['interaction_features_discrete'],
        **config['analysis_params'],
    )
    analyzer.plot_results()

    if df_test is not None:
        df_test.to_csv(save_dir / 'df_test.csv', index=False)
    analyzer.save_results(save_dir)
    with open(save_dir / 'config.yaml', 'w') as f:
        yaml.dump(config, f)

    print(f"\nSaved results to {save_dir}")
    return results

def main(nwb_list, analysis_config, output_path):
    bhv_data = build_features_table(nwb_list)
    results = run_behaviour_model(bhv_data, analysis_config, output_path)
    if analysis_config['mode'] == 'classification':
        print(f"\nBalanced Accuracy: {results['metrics']['balanced_accuracy']:.3f}")
        print(f"F1 Score: {results['metrics']['f1_score']:.3f}")
        print("\nTop Features by Importance:")
        print(results['feature_importance'].head())


if __name__ == '__main__':
    main_dir = Path(__file__).parent.parent
    session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
    group_file = os.path.join(session_path, f'session_context_expert_behaviour_model.yaml')
    with open(group_file, 'r', encoding='utf8') as stream:
        config_dict = yaml.safe_load(stream)
    analysis_config_path = main_dir / 'configs' / 'analysis_params' / 'whisker_classification.yaml'
    with open(analysis_config_path, 'r', encoding='utf8') as stream:
        analysis_config = yaml.safe_load(stream)
    nwb_paths = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]

    mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))
    print(f'\n Start behaviour modelling {len(nwb_paths)} sessions - {len(mice_list)} mice')
    results_path = Path(main_dir, 'results', 'behaviour_modelling_results')
    results_path.mkdir(parents=True, exist_ok=True)
    main(nwb_paths, analysis_config, results_path)
