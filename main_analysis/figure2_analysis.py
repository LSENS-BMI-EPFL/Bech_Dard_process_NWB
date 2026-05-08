import os
import glob
import yaml
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings("ignore")

from cicada_nwb.nwb_session import NWBSession

# ---------------------------------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------------------------------
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


def generate_mouse_opto_data(data, result_path):
    for mouse, mouse_data in data.groupby('mouse_id'):
        print(f'\nMouse: {mouse}')
        saving_path = os.path.join(result_path, mouse)
        if not os.path.exists(saving_path):
            os.makedirs(saving_path)

        mouse_shuffle_grid_agg = []
        for name, group in mouse_data.groupby(by=['context_background', 'trial_type']):
            trial_type_grid = []
            if 'whisker_trial' in name:
                outcome = 'outcome_w'
            elif 'auditory_trial' in name:
                outcome = 'outcome_a'
            else:
                outcome = 'outcome_n'

            control = group.loc[group.opto_stim == 0].drop_duplicates()
            stim = group.loc[group.opto_stim == 1].drop_duplicates()

            stim['opto_grid_no_global'] = stim.groupby(by=['session_id', 'opto_grid_no']).ngroup()

            trial_grid = stim.groupby(by=['opto_grid_ml', 'opto_grid_ap'])[outcome].apply(np.nanmean).reset_index()
            nostim_grid = control.groupby(by=['opto_grid_ml', 'opto_grid_ap'])[outcome].apply(np.nanmean).reset_index()
            trial_grid[f"{outcome}_sub"] = trial_grid[outcome] - nostim_grid[outcome].values[0]

            for i in tqdm(range(10000)):
                shuffle_group = group.copy().reset_index()
                shuffle_group[outcome] = shuffle_group.groupby('session_id')[outcome].apply(
                    lambda x: np.random.permutation(x.values)).reset_index().explode(outcome, ignore_index=True)[
                    outcome]
                control = shuffle_group.loc[shuffle_group.opto_stim == 0]
                stim = shuffle_group.loc[shuffle_group.opto_stim == 1]
                shuffle_grid = stim.groupby(by=['opto_grid_ml', 'opto_grid_ap'])[outcome].apply(
                    np.nanmean).reset_index()
                nostim_grid = control.groupby(by=['opto_grid_ml', 'opto_grid_ap'])[outcome].apply(
                    np.nanmean).reset_index()
                shuffle_grid[f"{outcome}_sub"] = shuffle_grid[outcome] - nostim_grid[outcome].values[0]
                trial_type_grid += [shuffle_grid]

            trial_type_grid = pd.concat(trial_type_grid)
            trial_type_grid_agg = trial_type_grid.groupby(by=['opto_grid_ml', 'opto_grid_ap']).agg(
                shuffle_mean=(outcome, 'mean'), shuffle_std=(outcome, 'std'),
                shuffle_mean_sub=(f'{outcome}_sub', 'mean'), shuffle_std_sub=(f'{outcome}_sub', 'std'))
            trial_type_grid_agg['shuffle_std'] = trial_type_grid_agg.shuffle_std.mask(
                trial_type_grid_agg.shuffle_std == 0).fillna(0.000001)
            trial_type_grid_agg['shuffle_std_sub'] = trial_type_grid_agg.shuffle_std.mask(
                trial_type_grid_agg.shuffle_std_sub == 0).fillna(0.000001)

            trial_type_grid_agg['shuffle_dist'] = trial_type_grid.reset_index(drop=True).pivot_table(outcome,
                                                                                                     ['opto_grid_ml',
                                                                                                      'opto_grid_ap'],
                                                                                                     aggfunc=list)
            trial_type_grid_agg['shuffle_dist_sub'] = trial_type_grid.reset_index(drop=True).pivot_table(
                f"{outcome}_sub", ['opto_grid_ml', 'opto_grid_ap'], aggfunc=list)
            trial_type_grid_agg['data_mean'] = trial_grid.pivot_table(outcome, ['opto_grid_ml', 'opto_grid_ap'])[
                outcome]
            trial_type_grid_agg['data_mean_sub'] = \
            trial_grid.pivot_table(f'{outcome}_sub', ['opto_grid_ml', 'opto_grid_ap'])[f'{outcome}_sub']
            trial_type_grid_agg['percentile'] = trial_type_grid_agg.apply(
                lambda x: np.sum(x['data_mean'] >= np.asarray(x.shuffle_dist)) / len(x.shuffle_dist), axis=1)
            trial_type_grid_agg['percentile_sub'] = trial_type_grid_agg.apply(
                lambda x: np.sum(x['data_mean_sub'] >= np.asarray(x.shuffle_dist_sub)) / len(x.shuffle_dist_sub),
                axis=1)
            trial_type_grid_agg['n_sigma'] = trial_type_grid_agg.apply(
                lambda x: (x['data_mean'] - x['shuffle_mean']) / x['shuffle_std'], axis=1)
            trial_type_grid_agg['n_sigma_sub'] = trial_type_grid_agg.apply(
                lambda x: (x['data_mean_sub'] - x['shuffle_mean_sub']) / x['shuffle_std_sub'], axis=1)
            trial_type_grid_agg['p'] = trial_type_grid_agg.apply(lambda x: 2 * (1 - norm.cdf(abs(x.n_sigma))), axis=1)
            reject, adj_pvals, _, __ = multipletests(trial_type_grid_agg['p'].values, alpha=0.05, method='fdr_bh',
                                                     is_sorted=False, returnsorted=False)
            trial_type_grid_agg['p_corr'] = adj_pvals
            trial_type_grid_agg['p_sub'] = trial_type_grid_agg.apply(lambda x: 2 * (1 - norm.cdf(abs(x.n_sigma_sub))),
                                                                     axis=1)
            reject, adj_pvals, _, __ = multipletests(trial_type_grid_agg['p_sub'].values, alpha=0.05, method='fdr_bh',
                                                     is_sorted=False, returnsorted=False)
            trial_type_grid_agg['p_corr_sub'] = adj_pvals
            trial_type_grid_agg['context'] = ['rewarded' if group.context.unique()[0] == 1 else 'non-rewarded' for i in
                                              range(trial_type_grid_agg.shape[0])]
            trial_type_grid_agg['context_background'] = [name[0] for i in range(trial_type_grid_agg.shape[0])]
            trial_type_grid_agg['trial_type'] = [name[1] for i in range(trial_type_grid_agg.shape[0])]

            trial_type_grid_agg = trial_type_grid_agg.reset_index()
            mouse_shuffle_grid_agg += [trial_type_grid_agg]

        mouse_shuffle_grid_agg = pd.concat(mouse_shuffle_grid_agg).reset_index()
        mouse_shuffle_grid_agg.to_json(os.path.join(saving_path, 'opto_data.json'))


def load_opto_data(mice, opto_data_path):
    single_mouse_result_files = glob.glob(os.path.join(opto_data_path, "*", "opto_data.json"))
    opto_df = []
    for file in single_mouse_result_files:
        d = pd.read_json(file)
        d['mouse_id'] = [os.path.basename(os.path.dirname(file)) for i in range(d.shape[0])]
        opto_df += [d]
    opto_df = pd.concat(opto_df)
    opto_df = opto_df.loc[opto_df.opto_grid_ap!=3.5]
    df_to_save = opto_df.copy()
    df_to_save['shuffle_dist_sub'] = df_to_save['shuffle_dist_sub'].apply(json.dumps)

    return df_to_save.loc[df_to_save.mouse_id.isin(mice)]

# ---------------------------------------------------------------------------------------------------------------------
# FIGURE 2
# ---------------------------------------------------------------------------------------------------------------------
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
session_group = os.path.join(session_path, 'sessions_Context_sessions_opto.yaml')
with open(session_group, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))
print(f'\nFig. 2CDE')
print(f'Aggregate {len(nwb_files)} sessions by mouse ({mice_list} - N = {len(mice_list)})')

# # Figure 2CDE
save_path = os.path.join(main_dir, 'results', 'optogenetic_behavior_resutls', 'VGAT')
os.makedirs(save_path, exist_ok=True)
print('\nAggregate behavior tables')
joint_behavior_table = build_standard_behavior_table(nwb_list=nwb_files)
print('Extract optogenetic effect')
generate_mouse_opto_data(data=joint_behavior_table, result_path=save_path)
print('\nConvert to table')
df_for_plot = load_opto_data(mice_list, save_path)

df_save_path = os.path.join(main_dir, 'results', 'figure2', '2CDE')
os.makedirs(df_save_path, exist_ok=True)
joint_behavior_table.to_csv(os.path.join(df_save_path, 'trial_data_table_VGAT.csv'))
df_for_plot.to_csv(os.path.join(df_save_path, 'optogrid_data_table_VGAT.csv'))

# Figure 2F
print(f'\nFig. 2F')
trial_tables = []
for nwb_file in nwb_files:
    bhv_data = build_standard_behavior_table([nwb_file])
    if bhv_data.trial_id.duplicated().sum() > 0:
        bhv_data['trial_id'] = bhv_data.index.values

    bhv_data = bhv_data.loc[(bhv_data.early_lick == 0) & (bhv_data.opto_grid_ap != 3.5)]
    bhv_data['opto_stim_coord'] = bhv_data.apply(lambda x: f"({x.opto_grid_ap}, {x.opto_grid_ml})", axis=1)

    trial_tables.append(bhv_data)

trial_tables = pd.concat(trial_tables, ignore_index=True)

# Get a sub-table for piezo lick times
piezo_lick_cols = ['mouse_id', 'stim_onset', 'lick_time', 'context', 'trial_type', 'opto_stim_coord']
piezo_lick_df = trial_tables.loc[trial_tables.lick_flag == 1, piezo_lick_cols]
piezo_lick_df['rt'] = piezo_lick_df['lick_time'] - piezo_lick_df['stim_onset']

# Save this dataframe for plot
df_save_path = os.path.join(main_dir, 'results', 'figure2', '2F')
os.makedirs(df_save_path, exist_ok=True)
piezo_lick_df.to_csv(os.path.join(df_save_path, 'piezo_reaction_time.csv'))


# ---------------------------------------------------------------------------------------------------------------------
# FIGURE 2 - SUPP 1DE
# ---------------------------------------------------------------------------------------------------------------------
session_group = os.path.join(session_path, 'sessions_Context_sessions_opto_control.yaml')
with open(session_group, 'r', encoding='utf8') as stream:
    config_dict = yaml.safe_load(stream)
nwb_files = [config_dict['sessions'][i]['path'] for i in range(len(config_dict['sessions']))]
mice_list = list(set([config_dict['sessions'][i]['identifier'][0:5] for i in range(len(config_dict['sessions']))]))
print(f'\nFig. 2 sup1 DE')
print(f'Aggregate {len(nwb_files)} sessions by mouse ({mice_list} - N = {len(mice_list)})')

save_path_ctrls = os.path.join(main_dir, 'results', 'optogenetic_behavior_resutls', 'controls')
os.makedirs(save_path_ctrls, exist_ok=True)
print('\nAggregate behavior tables')
joint_behavior_table = build_standard_behavior_table(nwb_list=nwb_files)
print('Extract optogenetic effect')
generate_mouse_opto_data(data=joint_behavior_table, result_path=save_path_ctrls)
print('\nConvert to table')
df_for_plot = load_opto_data(mice_list, save_path_ctrls)

df_save_path = os.path.join(main_dir, 'results', 'figure2_supp', '1DE')
os.makedirs(df_save_path, exist_ok=True)
df_for_plot.to_csv(os.path.join(df_save_path, 'optogrid_data_table_controls.csv'))

