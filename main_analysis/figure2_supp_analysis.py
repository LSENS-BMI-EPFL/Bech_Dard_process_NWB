import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from cicada_analysis.config.runner import run_from_config

# Get the main directory, sessions and parameters folders
main_dir = Path(__file__).parent.parent
session_path = Path(os.path.join(main_dir, 'configs', 'session_groups'))
parameters_path = Path(os.path.join(main_dir, 'configs', 'analysis_params'))
results_path = Path(os.path.join(main_dir, 'results', 'figure2_supp'))

# Figure2 supp 2ABC
parameters = os.path.join(parameters_path, 'params_figure2_supp2abc.yaml')

for drug in ['muscimol', 'ringer']:
    for target in ['wS1', 'RSC', 'fpS1']:
        results_folder = os.path.join(results_path, '2ABC', drug, target)
        os.makedirs(results_folder, exist_ok=True)

        sessions = os.path.join(session_path, f'sessions_Context_{drug}_{target}.yaml')
        print(f"\nRunning fig. 2 supp 2 {drug} - {target} on:\n{sessions}")
        analysis = run_from_config(
            sessions=sessions,
            params=parameters,
            results_path=results_folder,
                    )
        print(f"Results saved to: {analysis._results_path}")

