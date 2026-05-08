import os
import re
import yaml
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.cicada_tools.core.array_utils import find_nearest

# ---------------------------------------------------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------------------------------------------------
def build_standard_behavior_table(nwb_list):
    bhv_data = []
    for nwb_file in nwb_list:
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


def filter_part_by_camview(view):
    if view == 'side':
        return ['jaw_x', 'jaw_y', 'jaw_angle', 'jaw_distance', 'jaw_velocity',
                'nose_angle', 'nose_distance',
                'particle_x', 'particle_y',
                'pupil_area', 'spout_y',
                'tongue_angle', 'tongue_distance', 'tongue_velocity']

    elif view == 'top':
        return ['top_nose_angle', 'top_nose_distance', 'top_nose_velocity',
                'top_particle_x', 'top_particle_y',
                'whisker_angle', 'whisker_velocity']

    else:
        print('Wrong view name')
        return 0


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


def get_dlc_data(nwb_session, trials, timestamps, view, parts='all', start=0, stop=250):
    keys = ['behavior', 'BehavioralTimeSeries']

    if parts == 'all':
        dlc_parts = filter_part_by_camview(view)
    else:
        dlc_parts = [part for part in filter_part_by_camview(view) if part in parts]

    dlc_data = pd.DataFrame(columns=dlc_parts)

    view_timestamps = timestamps[0 if view == 'side' else 1]
    trial_data = []
    if len(view_timestamps) == 0:
        for i, tstamp in enumerate(trials):
            trace = pd.DataFrame(np.ones([abs(start - stop), len(dlc_parts)]) * np.nan, columns=dlc_parts)
            trace['trl_type_idx'] = i
            trace['time'] = np.arange(start / 100, stop / 100, 0.01) - 1
            trial_data += [trace.groupby('trl_type_idx').agg(lambda x: x.tolist())]
        return pd.concat(trial_data)

    for part in dlc_parts:
        dlc_data[part] = get_likelihood_filtered_bodypart(nwb_session, keys, part, threshold=0.5)

    view_timestamps = view_timestamps[:len(dlc_data)]

    for i, tstamp in enumerate(trials):
        frame = find_nearest(view_timestamps, tstamp)

        trace = dlc_data.loc[frame + (start + 1):frame + stop]
        if trace.shape == (len(np.arange(start, stop)), len(dlc_parts)):
            trace = trace.apply(lambda x: x - np.nanmean(x.iloc[0:50]))
        elif trace.shape == (len(np.arange(start, stop)) - 1, len(dlc_parts)):
            print(f"{view} has one frame less than requested")
            trace = dlc_data.loc[frame + (start + 1):frame + stop + 1]
            print(f"New shape {trace.shape[0]}")
        elif trace.shape == (len(np.arange(start, stop)) + 1, len(dlc_parts)):
            print(f"{view} has one frame more than requested")
            trace = trace[:-1, :]
            print(f"New shape {trace.shape[0]}")

        else:
            print(f'{view} has less data for this trial than requested: {trace.__len__()} frames')
            trace = pd.DataFrame(np.ones([abs(start - stop), len(dlc_parts)]) * np.nan, columns=dlc_parts)

        trace['trl_type_idx'] = i
        trace['time'] = np.arange(start / 100, stop / 100, 0.01) - 1
        trial_data += [trace.groupby('trl_type_idx').agg(lambda x: x.tolist())]
    return pd.concat(trial_data)


def get_reduced_im_by_epoch(nwb_session, trials, wf_timestamps, start=0, stop=200):
    frames = []
    rrs_keys = ['ophys', 'brain_grid_fluorescence', 'dff0_grid_traces']
    area_dict = nwb_session.calcium_imaging.get_cell_indices_by_cell_type(roi_serie_keys=rrs_keys)

    for tstamp in trials:
        frame = find_nearest(wf_timestamps, tstamp)
        data = nwb_session.calcium_imaging.get_roi_response_serie_data(keys=rrs_keys)[:, int(frame + start):int(frame + stop)].T
        if data.shape != (len(np.arange(start, stop)), 42):
            data = np.ones([stop-start, 42]) * np.nan
        else:
            data = data - np.nanmean(data[:48], axis=0)

        frames.append([data])

    frames = np.stack(np.array(frames).squeeze(), axis=0)
    wf_data = pd.DataFrame(columns=area_dict.keys())
    for i, loc in enumerate(wf_data.keys()):
        wf_data[loc] = [frames[j,:,area_dict[loc].squeeze()] for j in range(frames.shape[0])]
    wf_data['time'] = [[np.linspace(-1,3.98,250)] for i in range(wf_data.shape[0])]

    return wf_data


def get_dff0_traces_by_epoch(nwb_session, trials, wf_timestamps, start=0, stop=250):
    wf_data = pd.DataFrame(columns=['A1', 'ALM', 'tjM1', 'tjS1', 'RSC', 'wM1', 'wM2', 'wS1', 'wS2'])
    indices = nwb_session.calcium_imaging.get_cell_indices_by_cell_type(['ophys', 'brain_area_fluorescence', 'dff0_traces'])
    for key in indices.keys():
        wf_data[key] = nwb_session.calcium_imaging.get_roi_response_serie_data(['ophys', 'brain_area_fluorescence', 'dff0_traces'])[indices[key][0]]

    data = []
    for tstamp in trials:
        frame = find_nearest(wf_timestamps, tstamp)
        wf = wf_data.loc[frame+start:frame+stop-1].to_numpy()
        if wf.shape != (len(np.arange(start, stop)), wf_data.shape[1]):
            wf = np.ones([len(np.arange(start, stop)), wf_data.shape[1]]) * np.nan
        else:
            wf = wf - np.nanmean(wf[:48], axis=0)
        data += [wf]

    data = np.array(data)
    data = np.stack(data, axis=0)

    wf_data = pd.DataFrame(columns=['A1', 'ALM', 'tjM1', 'tjS1', 'RSC', 'wM1', 'wM2', 'wS1', 'wS2'])
    for i, loc in enumerate(wf_data.keys()):
        wf_data[loc] = [data[j,:,i] for j in range(data.shape[0])]

    return wf_data


def generate_session_wf_opto_data(nwb_files_list, output_path):

    for nwb_file in tqdm(nwb_files_list, desc='Processing sessions'):
        with NWBSession(nwb_file) as session_data:
            session_df = []
            bhv_data = build_standard_behavior_table([nwb_file])
            if bhv_data.trial_id.duplicated().sum()>0:
                bhv_data['trial_id'] = bhv_data.index.values

            bhv_data = bhv_data.loc[(bhv_data.early_lick==0) & (bhv_data.opto_grid_ap!=3.5)]
            bhv_data['opto_stim_coord'] = bhv_data.apply(lambda x: f"({x.opto_grid_ap}, {x.opto_grid_ml})",axis=1)
            wf_timestamps = session_data.widefield.get_widefield_timestamps(['ophys', 'dff0'])
            dlc_timestamps = session_data.petersen.get_dlc_timestamps(['behavior', 'BehavioralTimeSeries'])
            if dlc_timestamps is None:
                dlc_timestamps = [[], []]

            session_id = session_data.session_id
            print(f"\n--------{session_id}-------- ")

            for loc in bhv_data.opto_stim_coord.unique():
                opto_data = bhv_data.loc[bhv_data.opto_stim_coord==loc]

                if loc=='(-5.0, 5.0)':
                    opto_data['opto_stim_loc'] = 'control'
                else:
                    opto_data['opto_stim_loc'] = 'stim'

                trials = opto_data.start_time

                side_dlc = get_dlc_data(session_data, trials, dlc_timestamps, view='side', start=0, stop=250)
                top_dlc = get_dlc_data(session_data, trials, dlc_timestamps, view='top', start=0, stop=250)
                side_dlc['trial_id'] = opto_data.trial_id.values
                top_dlc['trial_id'] = opto_data.trial_id.values

                wf_image = get_reduced_im_by_epoch(session_data, trials, wf_timestamps, start=0, stop=250)
                wf_image['trial_id'] = opto_data.trial_id.values

                opto_data = pd.merge(opto_data.reset_index(drop=True), side_dlc, on='trial_id')
                opto_data = pd.merge(opto_data.reset_index(drop=True), top_dlc, on='trial_id')
                opto_data = pd.merge(opto_data.reset_index(drop=True), wf_image, on='trial_id')

                roi_data = get_dff0_traces_by_epoch(session_data, trials, wf_timestamps, start=0, stop=250)
                roi_data['trial_id'] = opto_data.trial_id.values
                opto_data = pd.merge(opto_data.reset_index(drop=True), roi_data, on='trial_id')
                session_df += [opto_data]

        session_df = pd.concat(session_df, ignore_index=True)
        if not os.path.exists(Path(output_path, session_id)):
            os.makedirs(Path(output_path, session_id))
        session_df.to_parquet(Path(output_path, session_id, 'results.parquet.gzip', compression='gzip'))


def load_wf_opto_data(nwb_path_list, opto_dlc_data_path):
    concat_df = []
    for nwb_file in nwb_path_list:
        with NWBSession(nwb_file) as session_data:
            session_id = session_data.session_id
            df = [pd.read_parquet(Path(opto_dlc_data_path, session_id, 'results.parquet.gzip', compression='gzip'))]
            concat_df += df
    return pd.concat(concat_df, ignore_index=True)

# ---------------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------
# FIGURE 4 - EXTRACT OPTOGENETIC WIDEFIELD RESULT
# ---------------------------------------------------------------------------------------------------------------------
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
session_group = os.path.join(session_path, 'sessions_Context_sessions_wf_opto.yaml')
with open(session_group, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))

save_path = os.path.join(main_dir, 'results', 'optogenetic_widefield_resutls', 'VGAT')
os.makedirs(save_path, exist_ok=True)
print(f'\nGenerate optogenetic widefield results for {len(nwb_files)} sessions (N={len(mice_list)} mice)')
generate_session_wf_opto_data(nwb_files, save_path)

# ---------------------------------------------------------------------------------------------------------------------
# FIGURE 2 - SUPP 3ABC
# ---------------------------------------------------------------------------------------------------------------------
print('\nFigure 2 supp 3ABC')

# Load the data
print('Load table')
total_df = load_wf_opto_data(mice_list, save_path)
total_df['time'] = [np.arange(-1, 1.5, 1/100) for i in range(total_df.shape[0])]
total_df['legend'] = total_df.apply(lambda x: f"{x.opto_stim_coord} - {'lick' if x.lick_flag==1 else 'no lick'}", axis=1)

# Fix the session with no sideview camera
n_times = len(np.arange(-1, 1.5, 1/100))
sideview_bodyparts = ['jaw_angle', 'jaw_y', 'jaw_velocity', 'nose_angle', 'nose_distance', 'particle_x',
                      'particle_y', 'pupil_area', 'spout_y', 'tongue_angle', 'tongue_distance', 'tongue_velocity']
nan_array = np.full(n_times, np.nan)
mask = total_df.session_id == 'PB185_20240902_102747'
for sideview_part in sideview_bodyparts:
    total_df.loc[mask, sideview_part] = pd.Series([nan_array.copy() for _ in range(mask.sum())],
                                                  index=total_df[mask].index)

# Define the grouping functions for dlc data plots
d = {c: lambda x: x.unique()[0] for c in ['opto_stim_loc', 'legend']}
for c in ['jaw_angle', 'jaw_y', 'jaw_velocity', 'nose_angle', 'nose_distance', 'particle_x', 'particle_y',
          'pupil_area', 'spout_y', 'tongue_angle', 'tongue_distance', 'tongue_velocity',
          'top_nose_angle', 'top_nose_distance', 'top_nose_velocity', 'top_particle_x', 'top_particle_y',
          'whisker_angle', 'whisker_velocity']:
    d[f"{c}"] = lambda x: np.nanmean(np.stack(x), axis=0)

# Group with all trials and plot PSTHs + grids
mouse_avg_df = total_df.groupby(['mouse_id', 'context', 'trial_type', 'opto_stim_coord'],
                                as_index=False).agg(d).reset_index()
mouse_full_avg_df = mouse_avg_df.copy()
mouse_full_avg_df = mouse_full_avg_df.drop('mouse_id', axis=1)
mouse_full_avg_df = mouse_full_avg_df.groupby(['context', 'trial_type', 'opto_stim_coord'],
                                              as_index=False).agg(d).reset_index()

# Keep only selected columns:
bodyparts_to_plot = ['jaw_angle', 'jaw_y', 'jaw_velocity',
                     'nose_angle', 'nose_distance', 'top_nose_angle', 'top_nose_distance', 'top_nose_velocity',
                     'tongue_angle', 'tongue_distance', 'tongue_velocity',
                     'whisker_angle', 'whisker_velocity']

# Save intermediary dataset to reproduce panels
kept_cols = bodyparts_to_plot + ['mouse_id', 'context', 'trial_type', 'opto_stim_coord']
mouse_avg_df_saved = mouse_avg_df[kept_cols]
mouse_avg_df_saved.to_csv(os.path.join(main_dir, 'figure2_supp', '3ABC', 'all_trials_bodyparts_psths.csv'))

