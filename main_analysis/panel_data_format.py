import os
import glob
import shutil
from pathlib import Path


main_dir = Path(__file__).parent.parent
results_dir = os.path.join(main_dir, 'results')
published_data_folder = os.path.join(results_dir, 'published_data')
os.makedirs(published_data_folder, exist_ok=True)

# #################################################################
# Figure 1
# #################################################################

## 1B
os.makedirs(os.path.join(published_data_folder, 'figure1', '1B'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1B', '*', 'concatenated_bhv_tables.csv'))
dest = os.path.join(published_data_folder, 'figure1', '1B', 'concatenated_bhv_tables.csv')
if matches and not os.path.exists(dest):
    src = matches[0]
    shutil.copy2(src, dest)

## 1CD
os.makedirs(os.path.join(published_data_folder, 'figure1', '1C'),
            exist_ok=True)
os.makedirs(os.path.join(published_data_folder, 'figure1', '1D'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1CDFGH', '*', 'context_days_full_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure1', '1C', 'context_days_full_table.csv')
dest2 = os.path.join(published_data_folder, 'figure1', '1D', 'context_days_full_table.csv')
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copy2(src, dest1)
    if not os.path.exists(dest2):
        shutil.copy2(src, dest2)

## 1E
os.makedirs(os.path.join(published_data_folder, 'figure1', '1E'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1E', '*', 'context_days_full_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure1', '1E', 'context_days_full_table.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 1FG
os.makedirs(os.path.join(published_data_folder, 'figure1', '1FG'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1CDFGH', '*', 'context_transitions_averaged_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure1', '1FG', 'context_transitions_averaged_table.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 1H
os.makedirs(os.path.join(published_data_folder, 'figure1', '1H'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1CDFGH', '*', '1st_whisker_against_time' , 'whisker_transitions_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure1', '1H', 'whisker_transitions_table.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 1IJ
# ---------------------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------------------
def ignore_uncentered(dir, contents):
    return [item for item in contents
            if os.path.isfile(os.path.join(dir, item)) and item.startswith('uncentered')]

def ignore_non_uncentered(dir, contents):
    return [item for item in contents
            if os.path.isfile(os.path.join(dir, item)) and not item.startswith('uncentered')]
# ---------------------------------------------------------------------------------------
matches = glob.glob(os.path.join(results_dir, 'processed_deeplabcut_data'))
dest1 = os.path.join(published_data_folder, 'figure1', '1IJ')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1, ignore=ignore_non_uncentered)

## 1KL
matches = glob.glob(os.path.join(results_dir, 'behaviour_modelling_results', '*'))
dest1 = os.path.join(published_data_folder, 'figure1', '1KL')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)

# #################################################################
# Figure 1 - Supplementary
# #################################################################
## Supp 1A
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1ABC'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1_supp', '1A', 'context_expert_sessions.xlsx'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1ABC', 'context_expert_sessions.xlsx')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## Supp 1B
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1ABC'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1_supp', '1B','context_block_duration.csv'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1ABC', 'context_block_duration.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## Supp 1C
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1ABC'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1_supp', '1C', 'context_block_duration_expert.csv'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1ABC', 'context_block_duration_expert.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## Supp 1E
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1E'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1CDFGH', '*', 'mouse_averaged_reaction_time.csv'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1E', 'mouse_averaged_reaction_time.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## Supp1F
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1F'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1_supp', '1F', '*', 'context_transitions_averaged_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1F', 'context_transitions_averaged_table.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## Supp 2A
matches = glob.glob(os.path.join(results_dir, 'figure1_supp', '2A'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '2A')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)


# #################################################################
# Figure 2
# #################################################################
## 2CDE
matches = glob.glob(os.path.join(results_dir, 'figure2', '2CDE'))
dest1 = os.path.join(published_data_folder, 'figure2', '2CDE')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)

matches = glob.glob(os.path.join(results_dir, 'optogenetic_behavior_resutls', 'VGAT'))
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copytree(src, dest1)
    else:
        # dest1 already exists, copy contents into it
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest1, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d)
            else:
                if not os.path.exists(d):
                    shutil.copy2(s, d)

## 2F
matches = glob.glob(os.path.join(results_dir, 'figure2', '2F'))
dest1 = os.path.join(published_data_folder, 'figure2', '2F')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)

# #################################################################
# Figure 2 - Supplementary
# #################################################################
## Supp 1DE
matches = glob.glob(os.path.join(results_dir, 'figure2_supp', '1DE'))
dest1 = os.path.join(published_data_folder, 'figure2_supp', '1DE')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)

matches = glob.glob(os.path.join(results_dir, 'optogenetic_behavior_resutls', 'controls'))
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copytree(src, dest1)
    else:
        # dest1 already exists, copy contents into it
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dest1, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d)
            else:
                if not os.path.exists(d):
                    shutil.copy2(s, d)

## Supp 2ABC
matches = glob.glob(os.path.join(results_dir, 'figure2_supp', '2ABC'))
dest1 = os.path.join(published_data_folder, 'figure2_supp', '2ABC')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)

## Supp 3ABC
matches = glob.glob(os.path.join(results_dir, 'figure2_supp', '3ABC'))
dest1 = os.path.join(published_data_folder, 'figure2_supp', '3ABC')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)


# #################################################################
# Figure 3
# #################################################################
## 3BC
matches = glob.glob(os.path.join(results_dir, 'processed_deeplabcut_data'))
dest1 = os.path.join(published_data_folder, 'figure3', '3BC')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1, ignore=ignore_uncentered)

## 3D
os.makedirs(os.path.join(published_data_folder, 'figure3', '3D'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure3', 'figure3D', 'GECO_coordinates_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure3', '3D', 'GECO_coordinates_table.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

matches = glob.glob(os.path.join(results_dir, 'figure3', 'figure3D', 'empty_grid.csv'))
dest1 = os.path.join(published_data_folder, 'figure3', '3D', 'empty_grid.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 3E time image courses
os.makedirs(os.path.join(published_data_folder, 'figure3', '3E_images'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure3', 'figure3E', '*', 'general_data_dict.npy'))
dest1 = os.path.join(published_data_folder, 'figure3', '3E_images', 'general_data_dict.npy')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 3E PSTHs
os.makedirs(os.path.join(published_data_folder, 'figure3', '3E_psths'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure3', 'figure3E', '*', 'PSTHs_dataset.csv'))
dest1 = os.path.join(published_data_folder, 'figure3', '3E_psths', 'PSTHs_dataset.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 3F time image courses
os.makedirs(os.path.join(published_data_folder, 'figure3', '3F_images'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure3', 'figure3F', '*', 'general_data_dict.npy'))
dest1 = os.path.join(published_data_folder, 'figure3', '3F_images', 'general_data_dict.npy')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## 3F PSTHs
os.makedirs(os.path.join(published_data_folder, 'figure3', '3F_psths'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure3', 'figure3F', '*', 'PSTHs_dataset.csv'))
dest1 = os.path.join(published_data_folder, 'figure3', '3F_psths', 'PSTHs_dataset.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)


# #################################################################
# Figure 3 - Supplementary
# #################################################################
## Supp 1A&B
for grp in ['1A_tdtomato', '1B_gfp', '1B_gcamp']:
    os.makedirs(os.path.join(published_data_folder, 'figure3_supp', grp), exist_ok=True)
    matches = glob.glob(os.path.join(results_dir, 'figure3_supp', grp, '*', 'general_data_dict.npy'))
    dest1 = os.path.join(published_data_folder, 'figure3_supp', grp, 'general_data_dict.npy')
    if matches and not os.path.exists(dest1):
        src = matches[0]
        shutil.copy2(src, dest1)

## Sup 4AB
matches = glob.glob(os.path.join(results_dir, 'processed_deeplabcut_data'))
dest1 = os.path.join(published_data_folder, 'figure3_supp', '4AB')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1, ignore=ignore_uncentered)

## Sup 5BC
matches = glob.glob(os.path.join(results_dir, 'figure3_supp', '5BC'))
dest1 = os.path.join(published_data_folder, 'figure3_supp', '5BC')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copytree(src, dest1)


# #################################################################
# Figure 4 & supplementary
# #################################################################
# 4AB
matches = glob.glob(os.path.join(results_dir, 'processed_pixel_correlation_data', 'wf_correlation_jrGECO'))
dest1 = os.path.join(published_data_folder, 'figure4', '4AB')
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copytree(src, dest1)

matches = glob.glob(os.path.join(results_dir, 'processed_pixel_correlation_data', 'wf_correlation_jrGECO',
                                 'combined_avg_correlation_results.json'))
dest1 = os.path.join(published_data_folder, 'figure4', '4AB')
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copy2(src, dest1)

# 4C
matches = glob.glob(os.path.join(results_dir, 'optogenetic_widefield_examples', 'opto', 'avg_wf_image_sub.pkl'))
dest1 = os.path.join(published_data_folder, 'figure4', '4C', 'avg_wf_image_sub.pkl')
os.makedirs(os.path.dirname(dest1), exist_ok=True)
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copy2(src, dest1)

## 4DG
matches = glob.glob(os.path.join(results_dir, 'optogenetic_widefield_resutls', 'VGAT'))
dest1 = os.path.join(published_data_folder, 'figure4', '4DG', 'VGAT')
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copytree(src, dest1)

#4 Supp2A
matches = glob.glob(os.path.join(results_dir, 'optogenetic_widefield_examples', 'photoactivation', 'avg_wf_image_sub.pkl'))
dest1 = os.path.join(published_data_folder, 'figure4_supp', '2A', 'avg_wf_image_sub.pkl')
os.makedirs(os.path.dirname(dest1), exist_ok=True)
if matches:
    src = matches[0]
    if not os.path.exists(dest1):
        shutil.copy2(src, dest1)

