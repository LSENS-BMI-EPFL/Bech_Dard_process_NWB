import os
import re
import yaml
import scipy
import itertools
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm
from pathlib import Path
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.config.runner import run_from_config


# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure1_supp'))

# ---------------------------------------------------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------------------------------------------------
def build_standard_behavior_table(nwb_list):
    bhv_data = []
    for nwb_file in tqdm(nwb_list):
        with NWBSession(nwb_file) as session_data:
            data_frame = session_data.behavior.get_trial_table()
            mouse_id = session_data.subject_id
            behavior_type, day = session_data.petersen.get_bhv_type_and_training_day_index()
            session_id = session_data.session_id
            data_frame['mouse_id'] = [mouse_id for trial in range(len(data_frame.index))]
            data_frame['session_id'] = [session_id for trial in range(len(data_frame.index))]
            data_frame['behavior'] = [behavior_type for trial in range(len(data_frame.index))]
            data_frame['day'] = [day for trial in range(len(data_frame.index))]
            bhv_data.append(data_frame)

    bhv_data = pd.concat(bhv_data, ignore_index=True)

    # Add performance outcome column for each stimulus.
    bhv_data['outcome_w'] = bhv_data.loc[(bhv_data.trial_type == 'whisker_trial')]['lick_flag']
    bhv_data['outcome_a'] = bhv_data.loc[(bhv_data.trial_type == 'auditory_trial')]['lick_flag']
    bhv_data['outcome_n'] = bhv_data.loc[(bhv_data.trial_type == 'no_stim_trial')]['lick_flag']
    bhv_data['correct_choice'] = bhv_data.reward_available == bhv_data.lick_flag

    return bhv_data


def get_standard_single_session_table(combine_bhv_data, session, block_size=20, verbose=True):
    """
    Get a single session trial table from the combined behavior table.
    :param combine_bhv_data:
    :param session:
    :param block_size:
    :param verbose:
    :return:
    """
    session_table = combine_bhv_data.loc[(combine_bhv_data['session_id'] == session)]
    session_table = session_table.loc[session_table.early_lick == 0]
    session_table = session_table.reset_index(drop=True)
    if verbose:
        print(f" ")
        print(f"Session : {session}, mouse : {session_table['mouse_id'].values[0]}, "
              f"behavior : {session_table['behavior'].values[0]}, "
              f"day : {session_table['day'].values[0]}")

    # Find the block length if context
    if session_table['behavior'].values[0] == ["context", "whisker_context"]:
        switches = np.where(np.diff(session_table.context.values[:]))[0]
        if len(switches) <= 1:
            block_length = switches[0] + 1
        else:
            block_length = min(np.diff(switches))
    else:
        switches = None
        block_length = block_size

    # Add the block info :
    session_table['trial'] = session_table.index
    session_table['block'] = session_table.loc[session_table.early_lick == 0, 'trial'].transform(
        lambda x: x // block_length)

    # Compute hit rates. Use transform to propagate hit rate to all entries.
    session_table['hr_w'] = session_table.groupby(['block', 'opto_stim'], as_index=False, dropna=False)[
        'outcome_w'].transform(np.nanmean)
    session_table['hr_a'] = session_table.groupby(['block', 'opto_stim'], as_index=False, dropna=False)[
        'outcome_a'].transform(np.nanmean)
    session_table['hr_n'] = session_table.groupby(['block', 'opto_stim'], as_index=False, dropna=False)[
        'outcome_n'].transform(np.nanmean)
    session_table['correct'] = session_table.groupby(['block', 'opto_stim'], as_index=False, dropna=False)[
        'correct_choice'].transform(np.nanmean)

    return session_table, switches, block_length

def plot_single_session(combine_bhv_data, color_palette, saving_path):
    sessions_list = np.unique(combine_bhv_data['session_id'].values[:])
    n_sessions = len(sessions_list)
    expert_sessions_table = []
    print(f"N sessions : {n_sessions}")
    for session_id in sessions_list:
        session_table, switches, block_size = get_standard_single_session_table(combine_bhv_data, session=session_id)
        if session_table['behavior'].values[0] == 'free_licking':
            print(f"No plot for {session_table['behavior'].values[0]} sessions")
            continue

        # Set plot parameters.
        raster_marker = 2
        marker_width = 2
        figsize = (15, 8)

        d = session_table.loc[session_table.early_lick == 0][int(block_size / 2)::block_size]
        marker = itertools.cycle(['o', 's'])
        markers = [next(marker) for i in d["opto_stim"].unique()]

        if session_table['behavior'].values[0] in ['context', 'whisker_context']:
            figure, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize,
                                                   gridspec_kw={'height_ratios': [2, 3]},
                                                   sharex=True)

            # Plot the contrast perf
            hr_w_contrast = [(np.abs(d.hr_w.values[i] - d.hr_w.values[i - 1]) +
                              np.abs(d.hr_w.values[i] - d.hr_w.values[i + 1])) / 2 for
                             i in np.arange(1, d.hr_w.size - 1)]
            hr_w_contrast.insert(0, np.nan)
            hr_w_contrast.insert(len(hr_w_contrast), np.nan)
            d['contrast_w'] = hr_w_contrast

            hr_a_contrast = [(np.abs(d.hr_a.values[i] - d.hr_a.values[i - 1]) +
                              np.abs(d.hr_a.values[i] - d.hr_a.values[i + 1])) / 2 for
                             i in np.arange(1, d.hr_a.size - 1)]
            hr_a_contrast.insert(0, np.nan)
            hr_a_contrast.insert(len(hr_a_contrast), np.nan)
            d['contrast_a'] = hr_a_contrast

            hr_n_contrast = [(np.abs(d.hr_n.values[i] - d.hr_n.values[i - 1]) +
                              np.abs(d.hr_n.values[i] - d.hr_n.values[i + 1])) / 2 for
                             i in np.arange(1, d.hr_n.size - 1)]
            hr_n_contrast.insert(0, np.nan)
            hr_n_contrast.insert(len(hr_n_contrast), np.nan)
            d['contrast_n'] = hr_n_contrast

            sns.lineplot(data=d, x='trial', y='contrast_n',
                         color=color_palette[4], ax=ax1, markers=markers)
            if 'contrast_w' in list(d.columns) and (not np.isnan(d.contrast_w.values[:]).all()):
                sns.lineplot(data=d, x='trial', y='contrast_w',
                             color=color_palette[2], ax=ax1, markers=markers)
            if 'contrast_a' in list(d.columns) and (not np.isnan(d.contrast_a.values[:]).all()):
                sns.lineplot(data=d, x='trial', y='contrast_a',
                             color=color_palette[0], ax=ax1, markers=markers)
            ax1.set_ylim([-0.05, 1.05])
            ax1.set_ylabel('Contrast Lick Probability')
            ax1.axhline(y=0.375, xmin=0, xmax=1, color='g', linewidth=2, linestyle='--')
            if d.contrast_w.count() > 2:
                bootstrap_res = scipy.stats.bootstrap(data=(d.contrast_w,), statistic=np.nanmean, n_resamples=10000)
                y_err = np.zeros((2, 1))
                y_err[0, 0] = np.nanmean(d.contrast_w) - bootstrap_res.confidence_interval.low
                y_err[1, 0] = bootstrap_res.confidence_interval.high - np.nanmean(d.contrast_w)
                ci_low = bootstrap_res.confidence_interval.low
                ci_high = bootstrap_res.confidence_interval.high
            else:
                y_err = np.zeros((2, 1))
                y_err[0, 0] = 0
                y_err[1, 0] = 0
                ci_low = np.nanmean(d.contrast_w)
                ci_high = np.nanmean(d.contrast_w)
            ax1.errorbar(max(d.trial) + 10, np.nanmean(d.contrast_w),
                         yerr=y_err,
                         xerr=None, fmt='o', color=color_palette[2], ecolor=color_palette[2], elinewidth=2)
            rwd_hr_w = d.loc[d.context == 1].hr_w
            non_rwd_hr_w = d.loc[d.context == 0].hr_w
            d_prime = (np.nanmean(rwd_hr_w) - np.nanmean(non_rwd_hr_w)) / np.sqrt(0.5 * (np.var(rwd_hr_w) + np.var(non_rwd_hr_w)))
            d_prime_lsens = scipy.stats.norm.ppf(min(np.nanmean(rwd_hr_w), 0.999)) - scipy.stats.norm.ppf(max(np.nanmean(non_rwd_hr_w), 0.001))
            perf_dict = {'mouse_id': [session_id[0:5]],
                         'session_id': [session_id],
                         'w_contrast_thresh': [0.375],
                         'w_contrast_mean': [np.nanmean(d.contrast_w)],
                         'w_contrast_ci_low': [ci_low],
                         'w_contrast_ci_high': [ci_high],
                         'w_context_expert': [ci_low > 0.375],
                         'd_prime': [d_prime],
                         'lsens_d_prime': [d_prime_lsens]}
            expert_sessions_table.append(pd.DataFrame.from_dict(perf_dict))
            if ci_low > 0.375:
                ax1.plot(max(d.trial) + 10, 0.9, marker='*', color=color_palette[2])
        else:
            figure, ax2 = plt.subplots(1, 1, figsize=figsize)

        # Plot the lines
        sns.lineplot(data=d, x='trial', y='hr_n', color='k', ax=ax2,
                     markers=markers)

        if 'hr_w' in list(d.columns) and (not np.isnan(d.hr_w.values[:]).all()):
            sns.lineplot(data=d, x='trial', y='hr_w', color=color_palette[2], ax=ax2, markers=markers)
        if 'hr_a' in list(d.columns) and (not np.isnan(d.hr_a.values[:]).all()):
            sns.lineplot(data=d, x='trial', y='hr_a', color=color_palette[0], ax=ax2, markers=markers)

        if session_table['behavior'].values[0] in ['context', 'whisker_context']:
            rewarded_bloc_bool = list(d.context.values[:])
            bloc_limites = np.arange(start=0, stop=len(session_table.index), step=block_size)
            bloc_area_color = ['green' if i == 1 else 'firebrick' for i in rewarded_bloc_bool]
            if bloc_limites[-1] < len(session_table.index):
                bloc_area = [(bloc_limites[i], bloc_limites[i + 1]) for i in range(len(bloc_limites) - 1)]
                bloc_area.append((bloc_limites[-1], len(session_table.index)))
                if len(bloc_area) > len(bloc_area_color):
                    bloc_area = bloc_area[0: len(bloc_area_color)]
                for index, coords in enumerate(bloc_area):
                    color = bloc_area_color[index]
                    ax2.axvspan(coords[0], coords[1], alpha=0.25, facecolor=color, zorder=1)

        # Plot the trials :
        ax2.scatter(x=session_table.loc[session_table.lick_flag == 0]['trial'],
                    y=session_table.loc[session_table.lick_flag == 0]['outcome_n'] - 0.1,
                    color=color_palette[4], marker=raster_marker, linewidths=marker_width)
        ax2.scatter(x=session_table.loc[session_table.lick_flag == 1]['trial'],
                    y=session_table.loc[session_table.lick_flag == 1]['outcome_n'] - 1.1,
                    color='k', marker=raster_marker, linewidths=marker_width)

        if 'hr_a' in list(d.columns) and (not np.isnan(d.hr_w.values[:]).all()):
            ax2.scatter(x=session_table.loc[session_table.lick_flag == 0]['trial'],
                        y=session_table.loc[session_table.lick_flag == 0]['outcome_a'] - 0.15,
                        color=color_palette[1], marker=raster_marker, linewidths=marker_width)
            ax2.scatter(x=session_table.loc[session_table.lick_flag == 1]['trial'],
                        y=session_table.loc[session_table.lick_flag == 1]['outcome_a'] - 1.15,
                        color=color_palette[0], marker=raster_marker, linewidths=marker_width)

        if 'hr_w' in list(d.columns) and (not np.isnan(d.hr_w.values[:]).all()):
            ax2.scatter(x=session_table.loc[session_table.lick_flag == 0]['trial'],
                        y=session_table.loc[session_table.lick_flag == 0]['outcome_w'] - 0.2,
                        color=color_palette[3], marker=raster_marker, linewidths=marker_width)
            ax2.scatter(x=session_table.loc[session_table.lick_flag == 1]['trial'],
                        y=session_table.loc[session_table.lick_flag == 1]['outcome_w'] - 1.2,
                        color=color_palette[2], marker=raster_marker, linewidths=marker_width)

        ax2.set_ylim([-0.2, 1.05])
        ax2.set_xlabel('Trial number')
        ax2.set_ylabel('Lick probability')
        figure_title = f"{session_table.mouse_id.values[0]}, {session_id[0:14]}, {session_table.behavior.values[0]} " \
                       f"{session_table.day.values[0]}"
        plt.suptitle(figure_title)
        sns.despine()

        save_formats = ['pdf', 'png', 'svg']
        figure_name = f"{session_table.mouse_id.values[0]}_{session_table.behavior.values[0]}_" \
                      f"{session_table.day.values[0]}"
        session_saving_path = os.path.join(saving_path, f"{session_table.mouse_id.values[0]}",
                                           f'{session_table.session_id.values[0]}_{session_table.behavior.values[0]}_{session_table.day.values[0]}')
        if not os.path.exists(session_saving_path):
            os.makedirs(session_saving_path)
        for save_format in save_formats:
            figure.savefig(os.path.join(f'{session_saving_path}', f'{figure_name}.{save_format}'),
                           format=f"{save_format}")

        plt.close('all')

    if expert_sessions_table:
        expert_sessions_table = pd.concat(expert_sessions_table)
        session_index = []
        for mouse in expert_sessions_table['mouse_id'].unique():
            session_index.extend(np.arange(0, len(expert_sessions_table.loc[expert_sessions_table.mouse_id == mouse])))
        expert_sessions_table['session_index'] = session_index
        expert_sessions_table.to_excel(os.path.join(saving_path, 'context_expert_sessions.xlsx'))
        fig = sns.relplot(
            data=expert_sessions_table, x='session_index', y="w_contrast_mean", col="mouse_id", hue='w_context_expert',
            height=1.5, aspect=1, col_wrap=4, legend=True)
        fig.set_ylabels('Whisker contrast')
        fig.set(ylim=(-0.05, 1.05))
        fig.fig.suptitle('Global whisker context performance')
        fig.tight_layout()
        for save_format in save_formats:
            fig.savefig(os.path.join(f'{saving_path}', f'whisker_context_perf.{save_format}'), format=f"{save_format}")
# -----------------------------------------------------------------------------------------------------------------------
# Figure 1 supp 1A  # maybe very long : ~1400 sessions
figure1_supp1a_sessions = os.path.join(session_path, 'sessions_Context_sessions.yaml')
figure1_supp1a_params = os.path.join(parameters_path, 'params_figure1b.yaml')
figure1_supp1a_results_path = Path(os.path.join(results_path, '1A'))
os.makedirs(figure1_supp1a_results_path, exist_ok=True)
print(f"\nRunning fig. 1 supp 1A on:\n{figure1_supp1a_sessions}")
with open(figure1_supp1a_sessions, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))
print(f'Extract behavior table for {len(nwb_files)} sessions - N = {len(mice_list)} mice')
joint_behavior_table = build_standard_behavior_table(nwb_list=nwb_files)
colors = ['#225ea8', '#00FFFF', '#238443', '#d51a1c', '#cccccc']
print(f'Plot single sessions, extract contrast value and d-prime')
plot_single_session(combine_bhv_data=joint_behavior_table, color_palette=colors, saving_path=figure1_supp1a_results_path)
print(f"Results saved to: {figure1_supp1a_results_path}")

# Figure 1 sup 1B # maybe very long : ~1400 sessions
figure1_supp1b_sessions = os.path.join(session_path, 'sessions_Context_sessions.yaml')
figure1_supp1b_results_path = Path(os.path.join(results_path, '1B'))
os.makedirs(figure1_supp1b_results_path, exist_ok=True)

with open(figure1_supp1b_sessions, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_paths = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
print('\nFig. 1 supp 1B')
print(f'Extract duration and number of context epochs per session for {len(nwb_paths)} sessions')

save_table = []
for nwb_path in tqdm(nwb_paths):
    with NWBSession(nwb_path) as session_data:
        mouse_id = session_data.subject_id
        session_id = session_data.session_id
        epoch_names = session_data.behavior.get_behavioral_epochs_names()
        dfs = []
        for epoch_name in epoch_names:
            epoch_times = session_data.behavior.get_behavioral_epochs_times(epoch_name=epoch_name)
            epoch_length = [epoch_times[1, i] - epoch_times[0, i] for i in range(epoch_times.shape[1])]
            df = pd.DataFrame.from_dict({'mouse_id': mouse_id, 'session_id':session_id,
                                         'epoch': epoch_name, 'epoch length': epoch_length})
            dfs.append(df)
    if not dfs:
        continue
    dfs = pd.concat(dfs, ignore_index=True)
    save_table.append(dfs)
save_table = pd.concat(save_table, ignore_index=True)
save_table.to_csv(os.path.join(figure1_supp1b_results_path, 'context_block_duration.csv'))

# Figure 1 supp 1C
figure1_supp1c_sessions = os.path.join(session_path, 'sessions_Context_sessions_expert.yaml')
figure1_supp1c_results_path = Path(os.path.join(results_path, '1C'))
os.makedirs(figure1_supp1c_results_path, exist_ok=True)

with open(figure1_supp1c_sessions, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_paths = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
print('\nFig. 1 supp 1C')
print(f'Extract duration and number of context epochs per session for {len(nwb_paths)} sessions')

save_table = []
for nwb_path in tqdm(nwb_paths):
    with NWBSession(nwb_path) as session_data:
        mouse_id = session_data.subject_id
        session_id = session_data.session_id
        epoch_names = session_data.behavior.get_behavioral_epochs_names()
        dfs = []
        for epoch_name in epoch_names:
            epoch_times = session_data.behavior.get_behavioral_epochs_times(epoch_name=epoch_name)
            epoch_length = [epoch_times[1, i] - epoch_times[0, i] for i in range(epoch_times.shape[1])]
            df = pd.DataFrame.from_dict({'mouse_id': mouse_id, 'session_id':session_id,
                                         'epoch': epoch_name, 'epoch length': epoch_length})
            dfs.append(df)
    dfs = pd.concat(dfs, ignore_index=True)
    save_table.append(dfs)
save_table = pd.concat(save_table, ignore_index=True)
save_table.to_csv(os.path.join(figure1_supp1c_results_path, 'context_block_duration_expert.csv'))

# Figure 1 supp 1F
figure1_supp1f_sessions = os.path.join(session_path, 'sessions_Context_sound_off_only.yaml')
figure1_supp1f_params = os.path.join(parameters_path, 'params_figure1_supp1f.yaml')
figure1_supp1f_results_path = Path(os.path.join(results_path, '1F'))
os.makedirs(figure1_supp1f_results_path, exist_ok=True)
print(f"\nRunning fig. 1 supp 1F on:\n{figure1_supp1f_sessions}")
analysis = run_from_config(
    sessions=figure1_supp1f_sessions,
    params=figure1_supp1f_params,
    results_path=figure1_supp1f_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

# Figure 1 supp 2A
# Utils ----------------------------------------------------------------------------
def get_likelihood_filtered_bodypart(nwb_session, keys, part, threshold=0.8):
    kinematic = part.split("_")[-1]
    root = re.sub(kinematic, '', part)
    suffix = 'base_likelihood' if 'whisker' in part or 'top_nose' in part else 'likelihood'
    data = nwb_session.petersen.get_dlc_data(keys, part)
    likelihood = nwb_session.petersen.get_dlc_data(keys, root+suffix)

    if ((likelihood >=threshold).sum()/ likelihood.shape[0])*100 < 70 and 'tongue' not in part and 'pupil' not in part:
        data = np.zeros_like(data)*np.nan
        print(f"{nwb_session.session_id} {part} has more than 30% of NaN values, discard")

    return np.where(likelihood >= threshold, data, 0 if 'tongue' in part else np.nan)
# -----------------------------------------------------------------------------------------

results_path_supp2a = os.path.join(results_path, '2A')
os.makedirs(results_path_supp2a, exist_ok=True)
example_session = os.path.join(session_path, 'sessions_Context_expert_DLC_example.yaml')
with open(example_session, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_path = config_dict['sessions'][0]['path']
print('Extract example DLC data for Fig. 1 sup 2A')
with NWBSession(nwb_path) as session:
    timestamps = session.petersen.get_dlc_timestamps(keys=['behavior', 'BehavioralTimeSeries'])

    trial_table = session.behavior.get_trial_table()
    trial_table['context'] = trial_table['context'].map({0: 'non-rewarded', 1: 'rewarded'})
    trial_table.to_csv(os.path.join(results_path_supp2a, 'example_trial_table.csv'))

    dlc_data = pd.DataFrame(columns=['whisker_angle', 'jaw_y', 'pupil_area'])
    for part in ['whisker_angle', 'jaw_y', 'pupil_area']:
        dlc_data[part] = get_likelihood_filtered_bodypart(session, ['behavior', 'BehavioralTimeSeries'],
                                                          part, threshold=0.5)
    dlc_data['time'] = timestamps[0]
    dlc_data.to_csv(os.path.join(results_path_supp2a, 'example_dlc_data.csv'))

    print(f'Results saved to : {results_path_supp2a}')
