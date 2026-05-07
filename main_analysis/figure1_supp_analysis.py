import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_analysis.config.runner import run_from_config

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure1_supp'))


# Figure 1F
figure1_supp1f_sessions = os.path.join(session_path, 'sessions_Context_sound_off_only.yaml')
figure1_supp1f_params = os.path.join(parameters_path, 'params_figure1_supp1f.yaml')
figure1_supp1f_results_path = Path(os.path.join(results_path, '1F'))
os.makedirs(figure1_supp1f_results_path, exist_ok=True)
print(f"\nRunning on: {figure1_supp1f_sessions}")
analysis = run_from_config(
    sessions=figure1_supp1f_sessions,
    params=figure1_supp1f_params,
    results_path=figure1_supp1f_results_path,
            )
print(f"Results saved to: {analysis._results_path}")
