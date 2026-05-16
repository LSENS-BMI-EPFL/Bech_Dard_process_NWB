import os
import yaml
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from numba import njit, prange
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.cicada_tools.core.array_utils import find_nearest

# --------------------------------------------------------------------------------------------
# UTILS
# --------------------------------------------------------------------------------------------
def get_reduced_im_by_epoch(nwb_session, trials, wf_timestamps, start=0, stop=200, fs=100):
    frames = []
    rrs_keys = ['ophys', 'brain_grid_fluorescence', 'dff0_grid_traces']
    area_dict = nwb_session.calcium_imaging.get_cell_indices_by_cell_type(roi_serie_keys=rrs_keys)
    nframes = abs(start - stop)

    for tstamp in trials:
        frame = find_nearest(wf_timestamps, tstamp)
        data = nwb_session.calcium_imaging.get_roi_response_serie_data(keys=rrs_keys)[:, int(frame + start):int(frame + stop)].T
        if data.shape[0] > np.arange(start, stop).shape[0]:
            data = data[:nframes, :]
        elif data.shape[0] == nframes - 1:
            data = np.pad(data, ((0, 1), (0, 0)), 'edge')
        elif data.shape[0] < nframes - 1:
            data = np.ones([nframes, 42]) * np.nan

        data = (data - np.nanmean(data, axis=0)) / np.nanstd(data, axis=0)

        frames.append([data])

    frames = np.stack(np.array(frames).squeeze(), axis=0)
    wf_data = pd.DataFrame(columns=area_dict.keys())
    for i, loc in enumerate(wf_data.keys()):
        wf_data[loc] = [frames[j, :, area_dict[loc].squeeze()] for j in range(frames.shape[0])]
    wf_data['time'] = [[np.linspace(start / fs, stop / fs, abs(start - stop))] for i in range(wf_data.shape[0])]

    return wf_data


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


@njit()
def correlate(x, y):
    return np.corrcoef(x, y)


@njit(parallel=True)
def compute_corr_numpy(template, target, r):

    for trial in prange(template.shape[0]):
        for px in range(target.shape[0]):
            r[trial, px] = correlate(template[trial, :], target[px, trial, :])[1, 0]

    return r


def trial_based_correlation(mouse_id, session_id, trial_table, dict_roi, data_roi, data_frames, output_path):
    for roi in ['(-0.5, 0.5)', '(-1.5, 0.5)', '(-1.5, 3.5)',
                '(-1.5, 4.5)', '(1.5, 3.5)', '(1.5, 1.5)',
                '(2.5, 2.5)', '(0.5, 4.5)']:

        print(f'\nComputing {roi} correlation')
        template = np.stack(data_roi[roi].to_numpy())
        target = np.rollaxis(data_frames, axis=1)

        # Correlate data
        corr = compute_corr_numpy(template, target, r=np.zeros([template.shape[0], target.shape[0]]))
        trial_table[f'{roi}_r'] = [[corr[im]] for im in range(corr.shape[0])]

        # Shuffle blocks
        block_shuffle = []
        for i in tqdm(range(1000), desc='Shuffle correlations ...'):
            block_id = np.abs(np.diff(trial_table.context.values, prepend=0)).cumsum()
            shuffle = np.hstack([np.where(block_id == block) for block in np.random.permutation(np.unique(block_id))])[
                0]
            block_shuffle += [
                compute_corr_numpy(template[shuffle], target, r=np.zeros([template.shape[0], target.shape[0]]))]

        block_shuffle = np.stack(block_shuffle)
        np.save(Path(output_path, f"{roi}_shuffle.npy"), block_shuffle)

        shuffle_mean = np.nanmean(block_shuffle, axis=0)
        trial_table[f'{roi}_shuffle_mean'] = [[shuffle_mean[im]] for im in range(shuffle_mean.shape[0])]

        shuffle_std = np.nanstd(block_shuffle, axis=0)
        trial_table[f'{roi}_shuffle_std'] = [[shuffle_std[im]] for im in range(shuffle_std.shape[0])]

        percentile = []
        for i, row in trial_table.iterrows():
            percentile += [np.sum(row[f'{roi}_r'][0] >= block_shuffle[:, i, :], axis=0) / block_shuffle.shape[0]]
        trial_table[f"{roi}_percentile"] = percentile

        n_sigmas = (corr - shuffle_mean) / shuffle_std
        trial_table[f"{roi}_nsigmas"] = [[n_sigmas[im]] for im in range(n_sigmas.shape[0])]

    trial_table['mouse_id'] = mouse_id
    trial_table['session_id'] = session_id

    trial_table.to_parquet(path=Path(output_path, "correlation_table.parquet.gzip"), compression='gzip')

    return trial_table
# ---------------------------------------------------------------------------------------------------------------
# This code was run with parallelization on a cluster
def main(groups, output_path):
    for group in groups:
        group_id = os.path.basename(group).split('_')[-1].split('.')[0]
        saving_path = os.path.join(output_path, f'wf_correlation_{group_id}')
        os.makedirs(saving_path, exist_ok=True)

        with open(group, 'r', encoding='utf8') as stream:
            config_dict = yaml.safe_load(stream)
        nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]

        print(f"\nPreprocessing widefield pixel correlation for {group_id} group ({len(nwb_files)} sessions)")

        rrs_keys = ['ophys', 'brain_area_fluorescence', 'dff0_traces']
        for nwb_file in nwb_files:
            with NWBSession(nwb_file) as session_data:
                session_id = session_data.session_id
                mouse_id = session_data.subject_id
                print(f"\nMouse : {mouse_id}, session : {session_id}")

                # Adjust saving path :
                saving_path = os.path.join(saving_path, mouse_id, session_id)
                os.makedirs(saving_path, exist_ok=True)

                # Get trial table
                trial_table = session_data.behavior.get_trial_table()
                correct = []
                for i, x in trial_table.iterrows():
                    if x['trial_type'] == 'auditory_trial' and x['lick_flag'] == 1:
                        correct += [1]
                    elif x['trial_type'] == 'whisker_trial' and x['context'] == 1 and x['lick_flag'] == 1:
                        correct += [1]
                    elif x['trial_type'] == 'whisker_trial' and x['context'] == 0 and x['lick_flag'] == 0:
                        correct += [1]
                    elif x['trial_type'] == 'no_stim_trial' and x['lick_flag'] == 0:
                        correct += [1]
                    else:
                        correct += [0]

                trial_table['correct_trial'] = correct

                wf_timestamps = session_data.calcium_imaging.get_roi_response_serie_timestamps(keys=rrs_keys)

                if 'opto' in group_id:
                    data_roi = get_reduced_im_by_epoch(session_data, trial_table.start_time, wf_timestamps, start=50, stop=100)
                    dict_roi = [roi for roi in data_roi.keys() if roi != 'time']
                    data_frames = get_frames_by_epoch(session_data, trial_table.start_time, wf_timestamps, start=50, stop=100)

                else:
                    data_roi = get_reduced_im_by_epoch(session_data, trial_table.start_time, wf_timestamps, start=-200, stop=0)
                    dict_roi = [roi for roi in data_roi.keys() if roi != 'time']
                    data_frames = get_frames_by_epoch(session_data, trial_table.start_time, wf_timestamps, start=-200, stop=0)

                print('Start trial based correlation')
                results = trial_based_correlation(mouse_id, session_id, trial_table, dict_roi,
                                                  data_roi, data_frames, saving_path)
                print(f'Results saved to {saving_path}')

        return


if __name__ == '__main__':
    main_dir = Path(__file__).parent.parent
    session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
    group_files = [os.path.join(session_path, f'sessions_Context_sessions_expert_WF_jrGECO.yaml')]
    results_path = os.path.join(main_dir, 'results', 'processed_pixel_correlation_data')
    os.makedirs(results_path, exist_ok=True)
    main(group_files, results_path)

