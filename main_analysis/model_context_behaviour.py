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


# ----------------------------------------------------------------------------------------------------------------------
# UTILS
# ----------------------------------------------------------------------------------------------------------------------
def unc_to_mac_path(path_name, base_dir='/Volumes'):
    """Convert a UNC-style path (//server/share/...) to a macOS /Volumes/... path."""
    parts = [p for p in path_name.split('/') if p]
    # parts[0] is server name, parts[1] is share name, rest is the subpath
    mac_path = Path(base_dir, *parts[1:])
    return mac_path

def build_features_table(nwb_list):
    concatenated_behavior = []
    concatenated_dlc_features = []
    for nwb_file in tqdm(nwb_list, desc='Extract features for model training ... '):
        with NWBSession(nwb_file) as session_data:
            bhv_df = session_data.behavior.get_trial_table().copy(deep=True)
            bhv_df['mouse_id'] = session_data.subject_id
            bhv_df['session_id'] = session_data.session_id
            bhv_df = bhv_df.loc[bhv_df.early_lick == 0].reset_index(drop=True)
            concatenated_behavior.append(bhv_df)

            trial_starts = bhv_df['start_time'].values[:]
            bodyparts = ['pupil_area', 'whisker_velocity', 'jaw_angle']
            dlc_times = session_data.behavior.get_behavioral_time_series_timestamps(serie_name=bodyparts[0])
            if dlc_times is None:
                continue
            trial_start_frame = [find_nearest(dlc_times, trial_start) for trial_start in trial_starts]
            quiet_window_start = [find_nearest(dlc_times, (trial_start - 2)) for trial_start in trial_starts]
            frames_to_take = [np.arange(quiet_window_start[i], trial_start_frame[i]) for i in range(len(trial_starts))]

            dlc_nwb_keys = ['behavior', 'BehavioralTimeSeries']
            thresholds = {
                'jaw_angle': 0.6,
                'pupil_area': 0.6,
                'whisker_velocity':0.8,
            }
            dlc_features = dict({f'{part}' : [] for part in bodyparts})
            for index, key in enumerate(bodyparts):
                # Get dlc data
                data = session_data.behavior.get_behavioral_time_series_data(serie_name=key)
                # Filter with likelihood
                kinematic = key.split("_")[-1]
                root = re.sub(kinematic, '', key)
                suffix = 'base_likelihood' if 'whisker' in key or 'top_nose' in key else 'likelihood'
                likelihood = session_data.petersen.get_dlc_data(dlc_nwb_keys, root + suffix)
                data = np.where(likelihood >= thresholds[key], data, 0 if 'tongue' in key else np.nan)
                # Center
                data = data - np.nanmean(data[175:200])
                if 'jaw' in key:
                    dlc_features[key] = [np.nanmean(np.abs(np.diff(data[frames]))) for frames in frames_to_take]
                else:
                    dlc_features[key] = [np.nanmean(np.abs(data[frames])) for frames in frames_to_take]
            dlc_features_df = pd.DataFrame(dlc_features)
            concatenated_dlc_features.append(dlc_features_df)

    return pd.concat(concatenated_behavior), pd.concat(concatenated_dlc_features)

def run_behaviour_model(df, config, results_dir):
    df_use = prepare_behavior_features(df, config)

    if config['mode'] == 'classification':
        df_use = df_use.loc[df_use.trial_type == 'whisker_trial']
    elif config['mode'] == 'regression':
        df_use = df_use.dropna(subset=['reaction_time'])
        df_use = df_use.loc[df_use.trial_type.isin(['whisker_trial', 'auditory_trial'])]
        df_use = df_use.loc[df_use.trial_outcome == 'Hit']

    # DLC features: placeholder for when the DLC loading script is added
    # if 'dlc_features' in config:
    #     config['whisker_features'] = config['whisker_features'] + config['dlc_features']
    #     config['feature_labels'] = config['feature_labels'] + config['dlc_features_labels']

    df_test = None
    if config['leave_out_one_session']:
        test_session = rng.choice(df_use['session'].unique())
        df_test = df_use[df_use['session'] == test_session]
        df_use = df_use[df_use['session'] != test_session]

    df_use = df_use[config['whisker_features']]
    df_use = df_use.rename(columns=dict(zip(df_use.columns, config['feature_labels'])))

    run_name = f"run_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    save_dir = results_dir / run_name
    save_dir.mkdir(parents=True, exist_ok=True)

    analyzer = BehavioralAnalysisGBM(save_path=save_dir, mode=config['mode'])
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

def combine_bhv_and_dlc(
        df_bhv,
        df_dlc,
    ):
    df_bhv['trial_id'] = df_bhv.groupby('session_name').cumcount()
    
    df_merged = pd.merge(
        df_bhv,
        df_dlc,
        left_on=['session_name', 'trial_id'],
        right_on=['session_id', 'trial_id'],
        how='inner',
        suffixes=('', '_y')  # Keep original column names for left df, add _y suffix for right df
    )

    # Drop the session_id column since we already have session_name
    if 'session_id' in df_merged.columns:
        df_merged = df_merged.drop(columns=['session_id'])

    return df_merged

def main(nwb_list, analysis_config, output_path):
    bhv_data, dlc_feat = build_features_table(nwb_list)
    df = combine_bhv_and_dlc(bhv_data, dlc_feat)
    # TODO : pass to explain bhv method
    results = run_behaviour_model(df, analysis_config, output_path)
    if analysis_config['mode'] == 'classification':
        print(f"\nBalanced Accuracy: {results['metrics']['balanced_accuracy']:.3f}")
        print(f"F1 Score: {results['metrics']['f1_score']:.3f}")
        print("\nTop Features by Importance:")
        print(results['feature_importance'].head())


if __name__ == '__main__':
    main_dir = Path(__file__).parent.parent
    session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
    group_file = os.path.join(session_path, f'sessions_Context_sessions_expert.yaml')
    with open(group_file, 'r', encoding='utf8') as stream:
        config_dict = yaml.safe_load(stream)
    analysis_config_path = main_dir / 'configs' / 'analysis_params' / 'whisker_classification_dlc.yaml'
    with open(analysis_config_path, 'r', encoding='utf8') as stream:
        analysis_config = yaml.safe_load(stream)
    nwb_paths = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
    nwb_paths = [unc_to_mac_path(p) for p in nwb_paths]
    mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))
    print(f'\n Start behaviour modelling {len(nwb_paths)} sessions - {len(mice_list)} mice')
    results_path = os.path.join(main_dir, 'results', 'behaviour_modelling_results')
    os.makedirs(results_path, exist_ok=True)
    main(nwb_paths, analysis_config, results_path)


