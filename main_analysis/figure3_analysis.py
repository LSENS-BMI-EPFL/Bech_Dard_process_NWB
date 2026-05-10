import os
import yaml
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from scipy.ndimage import center_of_mass
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession
from cicada_analysis.config.runner import run_from_config

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure3'))

# Figure 3D
figure3d_sessions = os.path.join(session_path, 'sessions_Context_sessions_expert_WF_jrGECO.yaml')
group_id = os.path.basename(figure3d_sessions).split('_')[-1].split('.')[0]
saving_path = os.path.join(results_path, 'figure3D')
os.makedirs(saving_path, exist_ok=True)

with open(figure3d_sessions, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]

print('\nGenerate data for Fig. 3D')
print(f"Processing data for {group_id} group ({len(nwb_files)} sessions)")

# Keys & Params
rrs_keys = ['ophys', 'brain_area_fluorescence', 'dff0_traces']
segmentation_list = ['ophys', 'brain_areas', 'brain_area_segmentation']
scale = 1
x = [62 * scale, 167 * scale]
y = [162 * scale, 152 * scale]
c = np.round(np.sqrt((x[1] - x[0]) ** 2 + (y[0] - y[1]) ** 2) / 6)
bregma = (88, 120)

# Extract data
coordinates_df = []
for nwb_path in tqdm(nwb_files):
    with NWBSession(nwb_path) as session:
        session_id = session.session_id
        mouse_id = session.subject_id
        print(f"\nMouse: {mouse_id}, Session: {session_id}")

        area_dict = session.calcium_imaging.get_cell_indices_by_cell_type(roi_serie_keys=rrs_keys)
        masks_list = session.calcium_imaging.get_image_mask(segmentation_info=segmentation_list)
        sensory_areas = ['wS1', 'wS2', 'A1']
        coor_df = pd.DataFrame()
        ap_list = []
        ml_list = []
        area_list = []
        origin_x = []
        origin_y = []
        for sensory_area in sensory_areas:
            print(f"Area: {sensory_area}")
            area_list.append(sensory_area)
            mask = masks_list[int(area_dict.get(sensory_area)[0])]
            mass_center = center_of_mass(mask)
            origin_x.append(mass_center[1])
            origin_y.append(mass_center[0])
            corrected_mass_center = np.array([mass_center[1] - bregma[0], bregma[1] - mass_center[0]])
            mass_center_coordinates = corrected_mass_center / c
            ap_list.append(mass_center_coordinates[0])
            ml_list.append(mass_center_coordinates[1])
            print(f"AP: {mass_center_coordinates[0]}, ML: {mass_center_coordinates[1]}")
        coor_df['AP'] = ap_list
        coor_df['ML'] = ml_list
        coor_df['Area'] = area_list
        coor_df['Mouse'] = mouse_id
        coor_df['Session'] = session_id
        coordinates_df.append(coor_df)
coordinates_df = pd.concat(coordinates_df)
coordinates_df.to_csv(os.path.join(saving_path, 'GECO_coordinates_table.csv'))
print(f'\nResults saved to {saving_path}')

# Empty grid template
x_vals = np.arange(5.5, -0.5, -1.0)
y_vals = np.arange(2.5, -4.5, -1.0)
rows = [(x, y) for x in x_vals for y in y_vals]
df = pd.DataFrame(rows, columns=["x", "y"])
df["dff0"] = 0
df["frame"] = 0
df.to_csv(os.path.join(saving_path, "empty_grid.csv"))

# Figure 3E (Auditory trials responses)
figure3e_sessions = os.path.join(session_path, 'sessions_Context_sessions_expert_WF_jrGECO.yaml')
figure3e_img_params = os.path.join(parameters_path, 'params_figure3e_img.yaml')
figure3e_psth_params = os.path.join(parameters_path, 'params_figure3e_psth.yaml')
figure3e_results_path = Path(os.path.join(results_path, 'figure3E'))
os.makedirs(figure3e_results_path, exist_ok=True)

# 3E image series
print(f"\nRunning fig. 3E image series on:\n{figure3e_sessions}")
analysis = run_from_config(
    sessions=figure3e_sessions,
    params=figure3e_img_params,
    results_path=figure3e_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

# 3E psths
print(f"\nRunning fig. 3E psths on:\n{figure3e_sessions}")
analysis = run_from_config(
    sessions=figure3e_sessions,
    params=figure3e_psth_params,
    results_path=figure3e_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

# Figure 3F (Whisker trial responses)
figure3f_sessions = os.path.join(session_path, 'sessions_Context_sessions_expert_WF_jrGECO.yaml')
figure3f_img_params = os.path.join(parameters_path, 'params_figure3f_img.yaml')
figure3f_psth_params = os.path.join(parameters_path, 'params_figure3f_psth.yaml')
figure3f_results_path = Path(os.path.join(results_path, 'figure3F'))
os.makedirs(figure3f_results_path, exist_ok=True)

# 3F image series
print(f"\nRunning fig. 3F image series on:\n{figure3f_sessions}")
analysis = run_from_config(
    sessions=figure3f_sessions,
    params=figure3f_img_params,
    results_path=figure3f_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

# 3F psths
print(f"\nRunning fig. 3F psths on:\n{figure3f_sessions}")
analysis = run_from_config(
    sessions=figure3f_sessions,
    params=figure3f_psth_params,
    results_path=figure3f_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

