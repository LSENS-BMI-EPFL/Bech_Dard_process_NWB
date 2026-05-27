"""
muscimol_behaviour_bootstrap.py

Hierarchical bootstrap analysis comparing muscimol vs ringer inactivation
effects on lick behaviour across sessions.

Pipeline:
  1. Load trial tables from NWB files (one YAML per condition)
  2. Assign chronological session numbers per subject × condition
  3. Run hierarchical bootstrap (two-level: subjects → trials)
  4. Save results as .npz and print/plot summary

Usage:
  python muscimol_behaviour_bootstrap.py                  # 10k iterations
  python muscimol_behaviour_bootstrap.py --n_iter 100000  # full paper run
"""

import argparse
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm
from typing import Optional

from cicada_nwb.nwb_session import NWBSession


# ── CONDITIONS ────────────────────────────────────────────────────────────────

CONDITION_PAIRS = [
    ('Context_muscimol_RSC',  'Context_ringer_RSC'),
    ('Context_muscimol_fpS1', 'Context_ringer_fpS1'),
    ('Context_muscimol_wS1',  'Context_ringer_wS1'),
]

ALL_CONDITIONS = [c for pair in CONDITION_PAIRS for c in pair]


# ── 1. DATA LOADING ───────────────────────────────────────────────────────────

def load_behaviour_data(config_dir: Path) -> pd.DataFrame:
    """
    Load and concatenate trial tables for all 6 inactivation conditions.

    For each condition, reads the corresponding YAML file, opens every NWB
    session with NWBSession, extracts the trial table, and adds:
      - inactivation_type : condition name (e.g. 'Context_muscimol_RSC')
      - subject           : mouse ID from session_data.subject_id
      - session_name      : session identifier from session_data.session_id
      - session_number    : chronological rank (1 or 2) per subject × condition

    Early-lick trials are excluded.
    """
    all_dfs = []
    for condition in ALL_CONDITIONS:
        yaml_path = config_dir / f'sessions_{condition}.yaml'
        with open(yaml_path, 'r', encoding='utf8') as f:
            config = yaml.safe_load(f)

        sessions = config['sessions']
        print(f'Loading {condition} ({len(sessions)} sessions)...')

        for session in tqdm(sessions, leave=False):
            try:
                with NWBSession(session['path']) as session_data:
                    df_sess = session_data.behavior.get_trial_table().copy(deep=True)
                    df_sess['session_name'] = session_data.session_id
                    df_sess['subject'] = session_data.subject_id
                    df_sess['inactivation_type'] = condition
                    df_sess = df_sess.loc[df_sess['early_lick'] == 0].reset_index(drop=True)
                    all_dfs.append(df_sess)
            except Exception as e:
                print(f'  Skipping {session["identifier"]}: {e}')

    df = pd.concat(all_dfs, ignore_index=True)

    # Assign chronological session numbers per subject × condition
    df['session_date'] = pd.to_datetime(
        df['session_name'].str.extract(r'(\d{8})')[0], format='%Y%m%d'
    )
    df['session_number'] = (
        df.groupby(['subject', 'inactivation_type'])['session_date']
        .rank(method='dense')
    )
    df = df[df['session_number'] != 3].reset_index(drop=True)  # drop rare 3rd sessions

    return df


# ── 2. HIERARCHICAL BOOTSTRAP ─────────────────────────────────────────────────

def resample_session_data(session_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Two-level hierarchical resample: subjects (with replacement) then trials."""
    subjects = session_df['subject'].unique()
    if len(subjects) < 2:
        raise ValueError('Need at least 2 subjects per session for bootstrapping')

    resampled_subjects = np.random.choice(subjects, size=len(subjects), replace=True)
    chunks = []
    for subj in resampled_subjects:
        subj_data = session_df[session_df['subject'] == subj]
        chunks.append(subj_data.sample(n=len(subj_data), replace=True))
    return pd.concat(chunks)


def hierarchical_bootstrap_comparison(
    data: pd.DataFrame,
    metric: str,
    condition1: str,
    condition2: str,
    context: int,
    n_iterations: int = 10000,
    random_state: Optional[int] = None,
) -> dict:
    """
    Compare the session1→session2 change between two conditions via hierarchical bootstrap.

    The test statistic is the difference-of-differences:
        (cond1: session2 - session1) - (cond2: session2 - session1)

    Returns a plain dict suitable for np.savez() and downstream plotting.
    """
    if random_state is not None:
        np.random.seed(random_state)

    def get_sessions(condition):
        mask = (data['inactivation_type'] == condition) & (data['context'] == context)
        cond = data[mask]
        s1 = cond[cond['session_number'] == 1]
        s2 = cond[cond['session_number'] == 2]
        if len(s1) == 0 or len(s2) == 0:
            raise ValueError(f'No data for {condition}, context={context}')
        return s1, s2

    c1s1, c1s2 = get_sessions(condition1)
    c2s1, c2s2 = get_sessions(condition2)

    # Observed session means and differences
    c1_s1_mean = c1s1[metric].mean()
    c1_s2_mean = c1s2[metric].mean()
    c2_s1_mean = c2s1[metric].mean()
    c2_s2_mean = c2s2[metric].mean()
    observed_diff = (c1_s2_mean - c1_s1_mean) - (c2_s2_mean - c2_s1_mean)

    # Bootstrap iterations
    bs_diffs = np.zeros(n_iterations)
    bs_c1_s1 = np.zeros(n_iterations)
    bs_c1_s2 = np.zeros(n_iterations)
    bs_c2_s1 = np.zeros(n_iterations)
    bs_c2_s2 = np.zeros(n_iterations)

    for i in tqdm(range(n_iterations), leave=False):
        r_c1s1 = resample_session_data(c1s1, metric)
        r_c1s2 = resample_session_data(c1s2, metric)
        r_c2s1 = resample_session_data(c2s1, metric)
        r_c2s2 = resample_session_data(c2s2, metric)

        bs_c1_s1[i] = r_c1s1[metric].mean()
        bs_c1_s2[i] = r_c1s2[metric].mean()
        bs_c2_s1[i] = r_c2s1[metric].mean()
        bs_c2_s2[i] = r_c2s2[metric].mean()
        bs_diffs[i] = (bs_c1_s2[i] - bs_c1_s1[i]) - (bs_c2_s2[i] - bs_c2_s1[i])

    ci_lower, ci_upper = np.percentile(bs_diffs, [2.5, 97.5])
    p_value = 2 * min(
        np.mean(bs_diffs >= 0) if observed_diff < 0 else np.mean(bs_diffs <= 0),
        0.5,
    )

    area = condition1.split('_')[-1]
    return {
        'bootstrap_differences': bs_diffs,
        'bootstrap_c1_s1': bs_c1_s1,
        'bootstrap_c1_s2': bs_c1_s2,
        'bootstrap_c2_s1': bs_c2_s1,
        'bootstrap_c2_s2': bs_c2_s2,
        'condition1_session1_mean': c1_s1_mean,
        'condition1_session2_mean': c1_s2_mean,
        'condition1_difference':    c1_s2_mean - c1_s1_mean,
        'condition2_session1_mean': c2_s1_mean,
        'condition2_session2_mean': c2_s2_mean,
        'condition2_difference':    c2_s2_mean - c2_s1_mean,
        'observed_difference': observed_diff,
        'ci_lower':  ci_lower,
        'ci_upper':  ci_upper,
        'p_value':   p_value,
        'condition1': condition1,
        'condition2': condition2,
        'context':    'R-' if context == 0 else 'R+',
        'area':       area,
    }


# ── 3. PRINT & PLOT ───────────────────────────────────────────────────────────

def print_summary(r: dict, trial_type: str) -> None:
    ctx  = r['context']
    area = r['area']
    print(f"\n{'='*52}")
    print(f"  {trial_type} | {area} | {ctx}")
    print(f"{'='*52}")
    print(f"  Muscimol  S1={r['condition1_session1_mean']:.3f}  "
          f"S2={r['condition1_session2_mean']:.3f}  Δ={r['condition1_difference']:+.3f}")
    print(f"  Ringer    S1={r['condition2_session1_mean']:.3f}  "
          f"S2={r['condition2_session2_mean']:.3f}  Δ={r['condition2_difference']:+.3f}")
    print(f"  Diff of Δ : {r['observed_difference']:+.3f}  "
          f"95% CI [{r['ci_lower']:.3f}, {r['ci_upper']:.3f}]  p={r['p_value']:.3f}")


def plot_results(all_results: list, save_dir: Path) -> None:
    """
    One figure per trial type: 3 areas × 2 contexts.
    Each panel shows session 1 and session 2 lick-rate means for muscimol
    and ringer, connected by lines. The bootstrap p-value is annotated.
    """
    trial_types = sorted({r['trial_type'] for r in all_results})
    areas       = ['RSC', 'fpS1', 'wS1']
    contexts    = ['R-', 'R+']

    colors = {'muscimol': '#d62728', 'ringer': '#1f77b4'}

    for trial_type in trial_types:
        fig, axes = plt.subplots(
            len(areas), len(contexts),
            figsize=(7, 9),
            sharey=True,
            constrained_layout=True,
        )
        fig.suptitle(trial_type, fontsize=13, fontweight='bold')

        for row, area in enumerate(areas):
            for col, ctx in enumerate(contexts):
                ax = axes[row, col]

                match = [
                    r for r in all_results
                    if r['trial_type'] == trial_type
                    and r['area'] == area
                    and r['context'] == ctx
                ]
                if not match:
                    ax.set_visible(False)
                    continue
                r = match[0]

                x = [1, 2]
                ax.plot(x, [r['condition1_session1_mean'], r['condition1_session2_mean']],
                        'o-', color=colors['muscimol'], linewidth=2, label='Muscimol')
                ax.plot(x, [r['condition2_session1_mean'], r['condition2_session2_mean']],
                        's--', color=colors['ringer'], linewidth=2, label='Ringer')

                # Bootstrap distribution behind the lines (light fill)
                bs_c1_diffs = r['bootstrap_c1_s2'] - r['bootstrap_c1_s1']
                bs_c2_diffs = r['bootstrap_c2_s2'] - r['bootstrap_c2_s1']
                _ = bs_c1_diffs, bs_c2_diffs  # available for extended use

                # p-value annotation
                p = float(r['p_value'])
                p_str = f'p={p:.3f}' if p >= 0.001 else 'p<0.001'
                ax.text(0.97, 0.05, p_str,
                        transform=ax.transAxes, ha='right', va='bottom',
                        fontsize=8, color='red' if p < 0.05 else 'grey')

                ax.set_xticks([1, 2])
                ax.set_xticklabels(['S1', 'S2'], fontsize=9)
                ax.set_xlim(0.7, 2.3)
                ax.set_title(f'{area}  {ctx}', fontsize=9)

                if col == 0:
                    ax.set_ylabel('Lick rate', fontsize=8)
                if row == 0 and col == 1:
                    ax.legend(fontsize=7, loc='upper right')

        out_path = save_dir / f'{trial_type}_bootstrap_summary.pdf'
        plt.savefig(out_path, bbox_inches='tight')
        plt.close()
        print(f'  Saved → {out_path}')


# ── 4. MAIN ───────────────────────────────────────────────────────────────────

def main(n_iterations: int = 10000) -> None:
    main_dir   = Path(__file__).parent.parent
    config_dir = main_dir / 'configs' / 'session_groups'
    results_dir = main_dir / 'results' / 'muscimol_bootstrap'
    results_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ──────────────────────────────────────────────────────────
    print('\nLoading behavioural data from NWB files...')
    df = load_behaviour_data(config_dir)
    print(f'\nLoaded {len(df):,} trials | '
          f'{df["session_name"].nunique()} sessions | '
          f'{df["subject"].nunique()} subjects')

    # ── Run bootstrap ──────────────────────────────────────────────────────
    all_results = []

    for trial_type in sorted(df['trial_type'].unique()):
        df_tt = df[df['trial_type'] == trial_type]
        print(f'\n{"#"*56}\n  {trial_type}\n{"#"*56}')

        for cond1, cond2 in CONDITION_PAIRS:
            area = cond1.split('_')[-1]
            for context in [0, 1]:
                ctx_label = 'R-' if context == 0 else 'R+'
                print(f'\n  ▶ {area} | {ctx_label}')
                try:
                    results = hierarchical_bootstrap_comparison(
                        data=df_tt,
                        metric='lick_flag',
                        condition1=cond1,
                        condition2=cond2,
                        context=context,
                        n_iterations=n_iterations,
                        random_state=42,
                    )
                    results['trial_type'] = trial_type
                    print_summary(results, trial_type)

                    # Save NPZ
                    save_dir = results_dir / trial_type / area / f'context_{context}'
                    save_dir.mkdir(parents=True, exist_ok=True)
                    save_path = save_dir / f'{cond1}_vs_{cond2}_context_{context}.npz'
                    np.savez(save_path, **results)

                    all_results.append(results)

                except ValueError as e:
                    print(f'  Skipped: {e}')

    # ── Plot ───────────────────────────────────────────────────────────────
    # if all_results:
    #     print('\nGenerating plots...')
    #     plot_results(all_results, results_dir)

    print('\nDone.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Muscimol inactivation bootstrap analysis')
    parser.add_argument('--n_iter', type=int, default=10000,
                        help='Number of bootstrap iterations (default: 10000)')
    args = parser.parse_args()
    main(n_iterations=args.n_iter)
