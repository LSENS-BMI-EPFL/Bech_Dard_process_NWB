import os
import re
import yaml
import itertools
import numpy as np
import pandas as pd
from pathlib import Path

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.cicada_tools.core.period_utils import filter_events_based_on_epochs, find_nearest


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


def get_traces_by_epoch(nwb_session, trials, timestamps, view, center=True, parts='all', start=-2, stop=2):
    parts = ['jaw_angle', 'jaw_distance', 'jaw_x', 'jaw_y', 'pupil_area',
             'tongue_angle', 'tongue_distance', 'whisker_angle',
             'whisker_velocity', 'top_particle_x', 'top_particle_y']

    thresholds = {
        'jaw_angle': 0.6,
        'jaw_distance': 0.6,
        'jaw_x': 0.6,
        'jaw_y': 0.6,
        'pupil_area': 0.6,
        'tongue_angle': 0.5,
        'tongue_distance': 0.5,
        'whisker_angle': 0.8,
        'whisker_velocity': 0.8,
        'top_particle_x': 0.8,
        'top_particle_y': 0.8
    }
    fr = 1 / np.round(np.median(np.diff(timestamps[0 if view == 'side' else 1])), 3)
    keys = ['behavior', 'BehavioralTimeSeries']

    nframes = int(abs(start * fr - stop * fr))

    if parts == 'all':
        dlc_parts = filter_part_by_camview(view)
    else:
        dlc_parts = [part for part in filter_part_by_camview(view) if part in parts]

    dlc_data = pd.DataFrame(columns=dlc_parts)

    for part in dlc_parts:

        dlc_data[part] = get_likelihood_filtered_bodypart(nwb_session, keys, part, threshold=thresholds[part])
        if part in ['jaw_x', 'jaw_y'] and len(dlc_data[part].dropna()) != 0:
            ref = np.percentile(dlc_data[part].dropna(), 5)
            dlc_data[part] = dlc_data[part] - ref

    view_timestamps = timestamps[0 if view == 'side' else 1][:len(dlc_data)]
    if len(view_timestamps) == 0:
        trial_data = np.ones([len(trials), len(dlc_parts)]) * np.nan
        return pd.DataFrame(trial_data, columns=dlc_parts)

    trial_data = []
    for tstamp in trials:
        frame = find_nearest(view_timestamps, tstamp)

        trace = dlc_data.loc[frame + (start * fr) + 1:frame + (stop * fr)]

        if trace.shape[0] == (nframes - 1, len(dlc_parts)):
            trace = dlc_data.loc[frame + (start * fr) + 1:frame + stop * fr + 1]
        elif trace.shape[0] > nframes:
            trace = trace.iloc[:nframes, :]
        elif trace.shape[0] < nframes - 1:
            trace = pd.DataFrame(np.ones([nframes, len(dlc_parts)]) * np.nan, columns=trace.keys())

        if center:
            trace = trace.apply(lambda x: x - np.nanmean(x.iloc[175:200]))

        trace['time'] = np.round(np.arange(start, stop, 1 / fr), 2)
        trial_data += [trace]
    return pd.concat(trial_data)


def compute_combined_data(nwb_files, parts, center=True):
    combined_side_data, combined_top_data = [], []

    for nwb_index, nwb_path in enumerate(nwb_files):

        with NWBSession(nwb_path) as session:
            mouse_id = session.mouse_id
            session_id = session.session_id

            print(" ")
            print(f"Analyzing session {session_id}")

            trial_table = session.behavior.get_trial_table()
            trial_table['correct_choice'] = trial_table.reward_available == trial_table.lick_flag
            trial_table['context'] = trial_table['context'].map({0: 'non-rewarded', 1: 'rewarded'})

            epochs = session.behavior.get_behavioral_epochs_names()
            epochs = [epoch for epoch in epochs if epoch in ['rewarded', 'non-rewarded']]

            mouse_trial_avg_data = dict.fromkeys(epochs)
            mouse_trial_avg_data['mouse_id'] = mouse_id
            mouse_trial_avg_data['session_id'] = session_id

            trial_types = session.behavior.get_behavioral_events_names()
            trial_types = [trial_type for trial_type in trial_types if trial_type.split("_")[0] not in ['jaw', 'tongue']]

            timestamps = session.petersen.get_dlc_timestamps(keys=['behavior', 'BehavioralTimeSeries'])

            if len(epochs) > 0:
                epoch_trial_permutations = list(itertools.product(epochs, trial_types))

                for epoch_trial in epoch_trial_permutations:
                    # print(f"Epoch : {epoch_trial[0]}, Trials : {epoch_trial[1]}")
                    if nwb_index == 0:
                        mouse_trial_avg_data[f'{epoch_trial[0]}_{epoch_trial[1]}'] = []

                    epoch_times = session.behavior.get_behavioral_epochs_times(epoch_trial[0])
                    trials = session.behavior.get_behavioral_events_times(epoch_trial[1])[0]
                    trials_kept = filter_events_based_on_epochs(events_ts=trials, epochs=epoch_times)
                    if len(trials_kept) == 0:
                        continue

                    side_data = get_traces_by_epoch(session, trials_kept, timestamps,
                                                    'side', center=center, parts=parts,
                                                    start=-2, stop=2)
                    side_data['mouse_id'] = mouse_id
                    side_data['session_id'] = session_id
                    side_data['context'] = epoch_trial[0]
                    side_data['trial_type'] = epoch_trial[1]
                    side_data['context_background'] = \
                    trial_table.groupby('context').get_group(epoch_trial[0])['context_background'].unique()[0]
                    side_data['correct_choice'] = side_data['trial_type'].map(
                        {'auditory_hit_trial': 1, 'auditory_miss_trial': 0, 'correct_rejection_trial': 1,
                         'false_alarm_trial': 0})
                    side_data.loc[(side_data['context'] == "rewarded") & (
                            side_data['trial_type'] == 'whisker_hit_trial'), 'correct_choice'] = 1
                    side_data.loc[(side_data['context'] == "rewarded") & (
                            side_data['trial_type'] == 'whisker_miss_trial'), 'correct_choice'] = 0
                    side_data.loc[(side_data['context'] == "non-rewarded") & (
                            side_data['trial_type'] == 'whisker_miss_trial'), 'correct_choice'] = 1
                    side_data.loc[(side_data['context'] == "non-rewarded") & (
                            side_data['trial_type'] == 'whisker_hit_trial'), 'correct_choice'] = 0
                    combined_side_data += [side_data]

                    top_data = get_traces_by_epoch(session, trials_kept, timestamps, 'top',
                                                   center=center, parts=parts,
                                                   start=-2, stop=2)
                    top_data['mouse_id'] = mouse_id
                    top_data['session_id'] = session_id
                    top_data['context'] = epoch_trial[0]
                    top_data['trial_type'] = epoch_trial[1]
                    top_data['context_background'] = \
                    trial_table.groupby('context').get_group(epoch_trial[0])['context_background'].unique()[0]
                    top_data['correct_choice'] = top_data['trial_type'].map(
                        {'auditory_hit_trial': 1, 'auditory_miss_trial': 0, 'correct_rejection_trial': 1,
                         'false_alarm_trial': 0})
                    top_data.loc[(top_data['context'] == "rewarded") & (
                            top_data['trial_type'] == 'whisker_hit_trial'), 'correct_choice'] = 1
                    top_data.loc[(top_data['context'] == "rewarded") & (
                            top_data['trial_type'] == 'whisker_miss_trial'), 'correct_choice'] = 0
                    top_data.loc[(top_data['context'] == "non-rewarded") & (
                            top_data['trial_type'] == 'whisker_miss_trial'), 'correct_choice'] = 1
                    top_data.loc[(top_data['context'] == "non-rewarded") & (
                            top_data['trial_type'] == 'whisker_hit_trial'), 'correct_choice'] = 0
                    combined_top_data += [top_data]

                for context in ['rewarded', 'non-rewarded']:
                    epoch_times = session.behavior.get_behavioral_epochs_times(context)
                    side_data = get_traces_by_epoch(session, epoch_times[0], timestamps, 'side',
                                                    center=center, parts=parts, start=-2, stop=2)
                    side_data['mouse_id'] = mouse_id
                    side_data['session_id'] = session_id
                    side_data['context'] = context
                    side_data['trial_type'] = "to_rewarded" if context == 'rewarded' else 'to_non_rewarded'
                    side_data['context_background'] = \
                    trial_table.groupby('context').get_group(epoch_trial[0])['context_background'].unique()[0]
                    side_data['correct_choice'] = np.nan
                    combined_side_data += [side_data]

                    top_data = get_traces_by_epoch(session, epoch_times[0], timestamps, 'top',
                                                   center=center, parts=parts, start=-2, stop=2)
                    top_data['mouse_id'] = mouse_id
                    top_data['session_id'] = session_id
                    top_data['context'] = context
                    top_data['trial_type'] = "to_rewarded" if context == 'rewarded' else 'to_non_rewarded'
                    top_data['context_background'] = \
                    trial_table.groupby('context').get_group(epoch_trial[0])['context_background'].unique()[0]
                    top_data['correct_choice'] = np.nan
                    combined_top_data += [top_data]

    return pd.concat(combined_side_data), pd.concat(combined_top_data)



def compute_dlc_data(nwb_files, output_path):

    parts = ['jaw_angle', 'jaw_distance', 'jaw_x', 'jaw_y',
             'nose_angle', 'nose_distance', 'particle_x',
             'particle_y', 'pupil_area', 'spout_y',
             'tongue_angle', 'tongue_distance', 'top_nose_angle',
             'top_nose_distance', 'whisker_angle', 'whisker_velocity',
             'top_particle_x', 'top_particle_y']

    print('Computing DLC centered data ...')
    combined_side_data, combined_top_data = compute_combined_data(nwb_files, parts)
    combined_side_data.to_csv(os.path.join(output_path, 'side_dlc_results.csv'))
    combined_top_data.to_csv(os.path.join(output_path, 'top_dlc_results.csv'))

    print(f'Computing DLC uncentered data ...')
    uncentered_combined_side_data, uncentered_combined_top_data = compute_combined_data(nwb_files, parts, center=False)
    uncentered_combined_side_data.to_csv(os.path.join(output_path, 'uncentered_side_dlc_results.csv'))
    uncentered_combined_top_data.to_csv(os.path.join(output_path, 'uncentered_top_dlc_results.csv'))


def main(groups, output_path):
    for group in groups:
        group_id = os.path.basename(group).split('_')[-1].split('.')[0]
        os.makedirs(os.path.join(output_path, group_id), exist_ok=True)

        with open(group, 'r', encoding='utf8') as stream:
            config_dict = yaml.safe_load(stream)
        nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]

        print(f"Preprocessing DeepLabCut data for {group_id} group ({len(nwb_files)} sessions)")
        compute_dlc_data(nwb_files, output_path)

        print(f'{group_id} group CSV tables written in {output_path}')


if __name__ == '__main__':
    main_dir = Path(__file__).parent.parent
    session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
    group_ids = ['gcamp', 'GFP', 'jrGECO', 'tomato']
    group_files = [os.path.join(session_path, f'sessions_Context_sessions_expert_WF_{group_id}.yaml')
              for group_id in group_ids]
    results_path = os.path.join(main_dir, 'results', 'processed_deeplabcut_data')
    os.makedirs(results_path, exist_ok=True)
    main(group_files, results_path)
