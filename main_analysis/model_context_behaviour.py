import os
import yaml
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.cicada_tools.core.array_utils import find_nearest

def build_features_table(nwb_list):
    concatenated_behavior = []
    concatenated_dlc_features = []
    for nwb_file in tqdm(nwb_list, desc='Extract features for model trainng ... '):
        with NWBSession(nwb_file) as session_data:
            bhv_df = session_data.behavior.get_trial_table().copy(deep=True)
            bhv_df['mouse_id'] = session_data.subject_id
            bhv_df['session_id'] = session_data.session_id
            concatenated_behavior.append(bhv_df)

            trial_starts = bhv_df['trial_start'].values[:]
            bodyparts = ['pupil_area', 'whisker_velocity', 'jaw_angle']
            dlc_times = session_data.behavior.get_behavioral_time_series_timestamps(serie_name=bodyparts[0])
            trial_start_frame = [find_nearest(dlc_times, trial_start) for trial_start in trial_starts]
            quiet_window_start = [find_nearest(dlc_times, (trial_start - 2)) for trial_start in trial_starts]
            frames_to_take = [np.arange(quiet_window_start[i], trial_start_frame[i]) for i in range(len(trial_starts))]

            dlc_features = dict({f'{part}' : [] for part in bodyparts})
            for index, key in enumerate(bodyparts):
                data = session_data.behavior.get_behavioral_time_series_data(serie_name=key)
                if 'jaw' in key:
                    dlc_features[key] = [np.mean(np.abs(np.diff(data[frames]))) for frames in frames_to_take]
                else:
                    dlc_features[key] = [np.mean(np.abs(data[frames])) for frames in frames_to_take]
            dlc_features_df = pd.DataFrame(dlc_features)
            concatenated_dlc_features.append(dlc_features_df)

    return pd.concat(concatenated_behavior), pd.concat(concatenated_dlc_features)


def main(nwb_list, output_path):
    bhv_data, dlc_feat = build_features_table(nwb_list)
    # TODO : pass to explain bhv method

if __name__ == '__main__':
    main_dir = Path(__file__).parent.parent
    session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
    group_file = os.path.join(session_path, f'sessions_Context_sessions_expert.yaml')
    with open(group_file, 'r', encoding='utf8') as stream:
        config_dict = yaml.safe_load(stream)
    nwb_paths = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
    mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))
    print(f'\n Start behaviour modelling {len(nwb_paths)} sessions - {len(mice_list)} mice')
    results_path = os.path.join(main_dir, 'results', 'behaviour_modelling_results')
    os.makedirs(results_path, exist_ok=True)
    main(nwb_paths, results_path)


