import os
import re
import yaml
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
warnings.filterwarnings("ignore")

from cicada_analysis.config.runner import run_from_config
from cicada_nwb.nwb_session import NWBSession

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure1_supp'))

# Figure 1 supp 1A  # maybe very long : ~1400 sessions
figure1_supp1a_sessions = os.path.join(results_path, 'sessions_Context_sessions.yaml')
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


# Figure 1 supp 1E
figure1_supp1e_sessions = os.path.join(session_path, 'sessions_Context_sound_off_only.yaml')
figure1_supp1e_params = os.path.join(parameters_path, 'params_figure1_supp1e.yaml')
figure1_supp1e_results_path = Path(os.path.join(results_path, '1E'))
os.makedirs(figure1_supp1e_results_path, exist_ok=True)
print(f"\nRunning fig. 1 supp 1E on:\n{figure1_supp1e_sessions}")
analysis = run_from_config(
    sessions=figure1_supp1e_sessions,
    params=figure1_supp1e_params,
    results_path=figure1_supp1e_results_path,
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
