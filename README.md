# **Bech & Dard NWB process repository**

## NWB files processing
This repository allows the processing NWBs files to reproduce analysis from Bech & Dard, eLife 2026.  
This README provides instruction to **set up the python environment and run the analysis code to generate intermediate data used to plot**.  
See at the end how to reproduce the figure panels starting from the intermediate dataset. ([`Bech, Dard figures`](https://github.com/LSENS-BMI-EPFL/Bech_Dard_plot_figures))

# **Installation**

### Create environment

```bash
conda create -n bech_dard_nwb_process python=3.11
conda activate bech_dard_nwb_process 
```
### Install git if necessary
```bash
conda install git
```
### Install remaining dependencies
```bash
cd /path/to/Bech_Dard_process_NWB
pip install -e .
```

# **How to use - Reproduce intermediate data**

## Run each file sequentially

```bash
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/figure1_analysis.py
python path/to/repo/main_analysis/figure1_supp_analysis.py
python path/to/repo/main_analysis/figure2_analysis.py
python path/to/repo/main_analysis/figure3_analysis.py
python path/to/repo/main_analysis/figure3_supp_analysis.py
python path/to/repo/main_analysis/figure4_analysis.py
python path/to/repo/main_analysis/process_deeplabcutdata.py
python path/to/repo/main_analysis/process_opto_widefield_examples.py
python path/to/repo/main_analysis/pixel_correlation_analysis.py
python path/to/repo/main_analysis/pixel_correlation_processing.py
```
**Warning** : _pixel_correlation_analysis_ script may run for multiple days (was previously optimized to run on HPC)

## Output
Each script is going to populate a results folder created within the main folder.

# **Reproduction of figures panels**

## **Reorganize results to follow figure panel ordering**

```bash
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/panel_data_format.py
```

This will create a 'published_data' folder within the main result folder.  
This matches publicly available data on [Zenodo](https://zenodo.org/communities/petersen-lab-data)

## Figure making 
To reproduce the figure panels from the downloaded or generated intermediate dataset see:  
- [`Bech, Dard figures`](https://github.com/LSENS-BMI-EPFL/Bech_Dard_plot_figures)
- [`intermediate dataset`](https://zenodo.org/communities/petersen-lab-data)
