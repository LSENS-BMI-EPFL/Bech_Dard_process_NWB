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

# #################################################################
# Figure 1 - Supplementary
# #################################################################
## Supp1D
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1D'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1', 'figure1CDFGH', '*', 'mouse_averaged_reaction_time.csv'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1D', 'mouse_averaged_reaction_time.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

## Supp1F
os.makedirs(os.path.join(published_data_folder, 'figure1_supp', '1E'),
            exist_ok=True)
matches = glob.glob(os.path.join(results_dir, 'figure1_supp', '1E', '*', 'context_transitions_averaged_table.csv'))
dest1 = os.path.join(published_data_folder, 'figure1_supp', '1E', 'context_transitions_averaged_table.csv')
if matches and not os.path.exists(dest1):
    src = matches[0]
    shutil.copy2(src, dest1)

# #################################################################
# Figure 2 - Supplementary
# #################################################################
## Supp 2ABC
matches = glob.glob(os.path.join(results_dir, 'figure2_supp', '2ABC'))
dest1 = os.path.join(published_data_folder, 'figure2_supp', '2ABC')
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