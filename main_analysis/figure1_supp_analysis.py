import os
import re
import yaml
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_analysis.config.runner import run_from_config
from cicada_nwb.nwb_session import NWBSession

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure1_supp'))

# Figure 1 supp 1A  # maybe very long : ~1400 sessions
figure1_supp1a_sessions = os.path.join(session_path, 'sessions_Context_sessions.yaml')
figure1_supp1a_params = os.path.join(results_path, 'params_figure1b.yaml')
figure1_supp1a_results_path = Path(os.path.join(results_path, '1A'))
os.makedirs(figure1_supp1a_results_path, exist_ok=True)
print(f"\nRunning fig. 1 supp 1A on:\n{figure1_supp1a_sessions}")
analysis = run_from_config(
    sessions=figure1_supp1a_sessions,
    params=figure1_supp1a_params,
    results_path=figure1_supp1a_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

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
