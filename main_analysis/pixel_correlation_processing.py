import os
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------------------------------------------------
def preprocess_corr_results(file):
    df = pd.read_parquet(file.replace("\\", "/"), use_threads=False)

    df['block_id'] = np.abs(np.diff(df.context.values, prepend=0)).cumsum()
    df['trial_count'] = np.empty(len(df), dtype=int)
    df.loc[df.trial_type == 'whisker_trial', 'trial_count'] = df.loc[df.trial_type == 'whisker_trial'].groupby(
        'block_id').cumcount()
    df.loc[df.trial_type == 'auditory_trial', 'trial_count'] = df.loc[
        df.trial_type == 'auditory_trial'].groupby(
        'block_id').cumcount()
    df.loc[df.trial_type == 'no_stim_trial', 'trial_count'] = df.loc[df.trial_type == 'no_stim_trial'].groupby(
        'block_id').cumcount()

    df = df.melt(id_vars=['mouse_id', 'session_id', 'context', 'context_background', 'block_id', 'correct_trial'],
                 value_vars=['(-1.5, 0.5)_r', '(-1.5, 0.5)_shuffle_mean', '(-1.5, 0.5)_shuffle_std',
                             '(-1.5, 0.5)_percentile', '(-1.5, 0.5)_nsigmas',
                             '(-1.5, 3.5)_r', '(-1.5, 3.5)_shuffle_mean', '(-1.5, 3.5)_shuffle_std',
                             '(-1.5, 3.5)_percentile', '(-1.5, 3.5)_nsigmas',
                             '(-1.5, 4.5)_r', '(-1.5, 4.5)_shuffle_mean', '(-1.5, 4.5)_shuffle_std',
                             '(-1.5, 4.5)_percentile', '(-1.5, 4.5)_nsigmas',
                             '(1.5, 3.5)_r', '(1.5, 3.5)_shuffle_mean', '(1.5, 3.5)_shuffle_std',
                             '(1.5, 3.5)_percentile', '(1.5, 3.5)_nsigmas',
                             '(0.5, 4.5)_r', '(0.5, 4.5)_shuffle_mean', '(0.5, 4.5)_shuffle_std',
                             '(0.5, 4.5)_percentile', '(0.5, 4.5)_nsigmas',
                             '(1.5, 1.5)_r', '(1.5, 1.5)_shuffle_mean', '(1.5, 1.5)_shuffle_std',
                             '(1.5, 1.5)_percentile', '(1.5, 1.5)_nsigmas',
                             '(2.5, 2.5)_r', '(2.5, 2.5)_shuffle_mean', '(2.5, 2.5)_shuffle_std',
                             '(2.5, 2.5)_percentile', '(2.5, 2.5)_nsigmas'])

    avg_df = df.groupby(by=['mouse_id', 'session_id', 'context', 'correct_trial', 'variable'])[
        'value'].apply(lambda x: np.array(x.tolist()).mean(axis=0)).reset_index()

    return avg_df
# ---------------------------------------------------------------------------------------------------------------------

def main(input_folder):
    all_files = glob.glob(os.path.join(input_folder, "**", "*", "correlation_table.parquet.gzip"))
    data = []
    for file in tqdm(all_files):
        session_data = preprocess_corr_results(file)
        data.append(session_data)
    data = pd.concat(data, axis=0, ignore_index=True)
    data.to_json(os.path.join(input_folder, "combined_avg_correlation_results.json"))


# Figure 4AB correlation averaging

if __name__ == '__main__':
    main_dir = Path(__file__).parent.parent
    source_folder = os.path.join(main_dir, 'results', 'processed_pixel_correlation_data', 'wf_correlation_jrGECO')
    main(source_folder)



