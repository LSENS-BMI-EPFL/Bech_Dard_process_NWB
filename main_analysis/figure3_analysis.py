import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_analysis.config.runner import run_from_config

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure3'))

# Figure 3E
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

# Figure 3F
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

