import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_analysis.config.runner import run_from_config

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure1'))

# Figure 1B
figure1b_sessions = os.path.join(session_path, 'sessions_Context_sessions_expert.yaml')
figure1b_params = os.path.join(parameters_path, 'params_figure1b.yaml')
figure1b_results_path = Path(os.path.join(results_path, 'figure1B'))
os.makedirs(figure1b_results_path, exist_ok=True)
print(f"\nRunning on: {figure1b_sessions}")
analysis = run_from_config(
    sessions=figure1b_sessions,
    params=figure1b_params,
    results_path=figure1b_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

# Figure 1C-D-F-G
figure1c_sessions = os.path.join(session_path, 'sessions_Context_sessions_expert.yaml')
figure1c_params = os.path.join(parameters_path, 'params_figure1cdfgh.yaml')
figure1c_results_path = Path(os.path.join(results_path, 'figure1CDFGH'))
os.makedirs(figure1c_results_path, exist_ok=True)
print(f"\nRunning on: {figure1c_sessions}")
analysis = run_from_config(
    sessions=figure1c_sessions,
    params=figure1c_params,
    results_path=figure1c_results_path,
            )
print(f"Results saved to: {analysis._results_path}")

# Figure 1E
figure1e_sessions = os.path.join(session_path, 'sessions_Context_sound_off.yaml')
figure1e_params = os.path.join(parameters_path, 'params_figure1e.yaml')
figure1e_results_path = Path(os.path.join(results_path, 'figure1E'))
os.makedirs(figure1e_results_path, exist_ok=True)
print(f"\nRunning on: {figure1e_sessions}")
analysis = run_from_config(
    sessions=figure1e_sessions,
    params=figure1e_params,
    results_path=figure1e_results_path,
            )
print(f"Results saved to: {analysis._results_path}")