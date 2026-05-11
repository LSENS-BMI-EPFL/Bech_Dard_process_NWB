import os
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.config.runner import run_from_config
from cicada_analysis.cicada_tools.core.array_utils import find_nearest


main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
param_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))

# Figure 3 - supp 1AB
group_ids = ['gcamp', 'GFP', 'tomato']
group_files = [os.path.join(session_path, f'sessions_Context_sessions_expert_WF_{group_id}.yaml')
          for group_id in group_ids]
results_path = os.path.join(main_dir, 'results', 'figure3_supp')
os.makedirs(results_path, exist_ok=True)

for group in group_files:
    group_id = os.path.basename(group).split('_')[-1].split('.')[0]
    if 'tomato' in group_id:
        saving_path = os.path.join(results_path, f'1A_td{group_id.lower()}')
        os.makedirs(saving_path, exist_ok=True)
    else:
        saving_path = os.path.join(results_path, f'1B_{group_id.lower()}')
        os.makedirs(saving_path, exist_ok=True)

    print(f"\nExtracting image series data of Fig.3 supp 1A&B for {group_id} group")

    param_file = os.path.join(param_path, f'params_figure3_supp1_{group_id.lower()}_img.yaml')

    analysis = run_from_config(
        sessions=group,
        params=param_file,
        results_path=saving_path,
    )
    print(f"Results saved to: {analysis._results_path}")

# Figure 3 - supp 5BC
session_file = os.path.join(session_path, 'sessions_Context_sessions_expert_WF_jrGECO.yaml')
saving_path = os.path.join(results_path, '5BC')
os.makedirs(saving_path, exist_ok=True)
with open(session_file, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]

# PARAMS
rrs_keys = ['ophys', 'brain_grid_fluorescence', 'dff0_grid_traces']
pre_stim = 5
post_stim = 18

# EXTRACT
print(f'\nExtract data for Fig. 3 - supp5BC ({len(nwb_files)} sessions)')
tables = []
for nwb_file in nwb_files:
    with NWBSession(nwb_file) as session_data:
        mouse = session_data.subject_id
        session = session_data.session_id
        print(f"\nMouse: {mouse}, Session: {session}")

        # Extract session neural data
        traces = session_data.calcium_imaging.get_roi_response_serie_data(keys=rrs_keys)
        rrs_ts = session_data.calcium_imaging.get_roi_response_serie_timestamps(keys=rrs_keys)
        if len(rrs_ts) > traces.shape[1]:
            rrs_ts = rrs_ts[0: traces.shape[1]]

        # Extract area names
        area_dict = session_data.calcium_imaging.get_cell_indices_by_cell_type(roi_serie_keys=rrs_keys)
        sorted_areas = sorted(area_dict, key=area_dict.get)
        print(f"Grid spots: {sorted_areas}")

        # Get trial table
        trial_table = session_data.behavior.get_trial_table()
        trial_table['correct_trials'] = trial_table.lick_flag == trial_table.reward_available

        # Filter trial table
        selected_columns = ['trial_id', 'start_time', 'trial_type', 'correct_trials', 'context']
        selected_table = trial_table.copy(deep=True)
        selected_table = selected_table[selected_columns]
        selected_table['mouse_id'] = mouse
        selected_table['session_id'] = session
        selected_table['activity_array'] = [None] * len(selected_table)
        selected_table = selected_table.loc[selected_table.trial_type == 'whisker_trial']
        selected_table = selected_table.reset_index(drop=True)

        # Add whisker index
        whisker_index = np.tile(np.arange(0, 8), 50)
        whisker_index = whisker_index[0: len(selected_table)]
        selected_table['whisker_index'] = whisker_index

        # Loop on each trial to get imaging data
        nf = pre_stim + post_stim
        for trial in range(len(selected_table)):
            stim_time = selected_table.iloc[trial].start_time
            stim_frame = find_nearest(rrs_ts, stim_time)
            start_frame = stim_frame - pre_stim
            end_frame = stim_frame + post_stim
            if (start_frame < 0) or (end_frame > traces.shape[1]):
                selected_table.at[trial, 'activity_array'] = np.zeros((len(sorted_areas), nf)) * np.nan
            else:
                selected_table.at[trial, 'activity_array'] = traces[:, np.arange(start_frame, end_frame)]
        tables.append(selected_table)
tables = pd.concat(tables, ignore_index=True)
tables = tables.drop(['trial_id', 'start_time', 'trial_type', 'correct_trials'], axis=1)
tables.to_pickle(os.path.join(saving_path, f'psth_over_blocks.pkl'))
np.save(os.path.join(saving_path, f'sorted_areas.npy'), sorted_areas)
print(f'\nData saved to {saving_path}')