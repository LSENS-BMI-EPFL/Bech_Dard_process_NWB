# **Bech & Dard NWB process repository**

## NWB files processing
This repository allows the processing NWBs files to reproduce analysis from Bech & Dard, eLife 2026.  
This README provides instruction to **set up the python environment and run the analysis code to generate intermediate data used to plot**.  

## Figure making
To see how to reproduce the figure panels from the generated intermediate dataset see:  
- [`figure code`](https://github.com/LSENS-BMI-EPFL/Bech_Dard_plot_figures)
- [`intermediate dataset`](link to intermediate dataset for download)

# **Installation**

Create environment 

```
conda create -n bech_dard_nwb_process python=3.11

conda activate bech_dard_nwb_process 

pip install git+https://gitlab.com/cossartlab/cicada_analysis.git

```

# **How to use**

## **Reproduce Figure 1 intermediate data :** 

### Run
```
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/figure1_analysis
```
### Output
In the created result folder

## **Reproduce Figure 3 intermediate data :** 

### Run
```
conda activate bech_dard_nwb_process 
python path/to/repo/main_analysis/figure3_analysis
```
### Output
In the created result folder