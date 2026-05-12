import os
import yaml
import numpy as np
import pandas as pd
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


def get_frames_by_epoch(nwb_session, trials, wf_timestamps, start=-200, stop=200):
    frames = []
    nframes = abs(start - stop)
    for tstamp in trials:
        frame = find_nearest(wf_timestamps, tstamp)
        data = nwb_session.widefield.get_widefield_dff0(['ophys', 'dff0'], frame + start, frame + stop)
        if data.shape[0] > nframes:
            data = data[:nframes, :]
        elif data.shape[0] == nframes - 1:
            data = np.pad(data, ((0, 1), (0, 0), (0, 0)), 'edge')
        elif data.shape[0] < nframes - 1:
            data = np.ones([nframes, 125, 160]) * np.nan

        data_filt = (data.reshape(nframes, -1) - np.nanmean(data.reshape(nframes, -1), axis=0)) / np.nanstd(
            data.reshape(nframes, -1), axis=0)

        data_filt = data_filt.T
        frames.append(data_filt)

    data_frames = np.array(frames)

    return data_frames


def plot_example_stim_images(nwb_file_path, result_path):
    df = []
    for nwb_file in nwb_file_path:
        with NWBSession(nwb_file) as session_data:
            bhv_data =build_standard_behavior_table([nwb_file])
            if bhv_data.trial_id.duplicated().sum()>0:
                bhv_data['trial_id'] = bhv_data.index.values

            bhv_data = bhv_data.loc[(bhv_data.early_lick==0) & (bhv_data.opto_grid_ap!=3.5)]
            bhv_data['opto_stim_coord'] = bhv_data.apply(lambda x: f"({x.opto_grid_ap}, {x.opto_grid_ml})",axis=1)
            wf_timestamps = session_data.widefield.get_widefield_timestamps(['ophys', 'dff0'])
            session_id = session_data.session_id
            mouse_id = session_data.subject_id
            print(f"--------- {session_id} ---------")

            for loc in bhv_data.opto_stim_coord.unique():
                if loc not in ["(-1.5, 3.5)", "(1.5, 1.5)", "(-1.5, 0.5)", "(-5.0, 5.0)"]:
                    continue

                opto_data = bhv_data.loc[bhv_data.opto_stim_coord==loc]
                opto_data['mouse_id'] = mouse_id
                opto_data['session_id'] = session_id
                trials = opto_data.start_time
                wf_image = get_frames_by_epoch(session_data, trials, wf_timestamps, start=40, stop=60)
                opto_data['wf_image'] = [wf_image[i] for i in range(wf_image.shape[0])]
                df += [opto_data]

        df = pd.concat(df)
        df['wf_image_sub'] = df.apply(lambda x: x['wf_image'] - np.nanmean(x['wf_image'][:10], axis=0),axis=1)
        mouse_avg = df.groupby(by=['mouse_id', 'context', 'trial_type', 'opto_stim_coord']).agg({'wf_image_sub': lambda x: np.nanmean(np.stack(x), axis=0)}).reset_index()
        avg = mouse_avg.groupby(by=['context', 'trial_type', 'opto_stim_coord']).agg({'wf_image_sub': lambda x: np.nanmean(np.stack(x), axis=0)}).reset_index()

        avg.to_csv(os.path.join(result_path, f"avg_wf_image_sub.csv"))
# ---------------------------------------------------------------------------------------------------------------------
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))

## Example images (Figure 4C)
print('\nExtracting data for optogenetic widefield examples Fig 4C')
group_file = os.path.join(session_path, 'sessions_Context_sessions_wf_opto.yaml')
results_path = os.path.join(main_dir, 'results', 'optogenetic_widefield_examples', 'opto')
os.makedirs(results_path, exist_ok=True)
with open(group_file, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
plot_example_stim_images(nwb_files, results_path)

## Photoactivation example images (Figure 4 - supp)
print('\nExtracting data for optogenetic widefield photoactivation effect')
group_file = os.path.join(session_path, 'sessions_Context_sessions_wf_opto_photoactivation.yaml')
results_path = os.path.join(main_dir, 'results', 'optogenetic_widefield_examples', 'photoactivation')
os.makedirs(results_path, exist_ok=True)
with open(group_file, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
plot_example_stim_images(nwb_files, results_path)

