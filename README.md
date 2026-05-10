# **Bech & Dard NWB process repository**

## NWB files processing
This repository allows the processing NWBs files to reproduce analysis from Bech & Dard, eLife 2026.  
This README provides instruction to **set up the python environment and run the analysis code to generate intermediate data used to plot**.  
See at the end how to reproduce the figure panels starting from the intermediate dataset. ([`figure code`](https://github.com/LSENS-BMI-EPFL/Bech_Dard_plot_figures))

# **Installation**

Create environment 

```
conda create -n bech_dard_nwb_process python=3.11
conda activate bech_dard_nwb_process 
```
Install git if necessary
```
conda install git
```
Install remaining dependencies
```
pip install "git+https://gitlab.com/cossartlab/cicada_analysis.git" "pyarrow>=16"
```

# **How to use**

## **Reproduce Figure 1 intermediate data :** 

### Run
```
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/figure1_analysis.py
```
### Output
In the created results folder

## **Reproduce Figure 3 intermediate data :** 

### Run
```
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/figure3_analysis.py
```
### Output
In the created results folder

# **Reproduction of figures panels**

## **Reorganize results to follow figure panel ordering**
```
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/panel_data_format.py
```

This will create a 'published_data' folder with the main result folder.  
This matches publicly available data at [zenodo release](zenodo)

## Figure making 
To reproduce the figure panels from the downloaded or generated intermediate dataset see:  
- [`figure code`](https://github.com/LSENS-BMI-EPFL/Bech_Dard_plot_figures)
- [`intermediate dataset`](link to intermediate dataset for download)