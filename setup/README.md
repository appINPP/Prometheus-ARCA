#Setup

This folder contains all the information to get started on Prometheus, as well as useful codes to customise the framework to ARCA.

##Installation

The following method is intended for Linux. If you encounter any issues or use a different OS, additional information should be found on my Drive or in the Prometheus repository itsel. 
Considering the preinstalled requirements of: 
+ python version of at least 3.11
+ bash or zsh
+ curl

we can install Prometheus using the following commands:
```bash
git clone https://github.com/Harvard-Neutrino/prometheus.git && cd prometheus
bash install.sh
source scripts/activate.sh .prometheus_env
```
The last command activates the environment and is used each time we wish to run Prometheus.

##Detector Coordinates

Production codes use the arca.geo file located in resources/geofiles to load the detector geometry and medium. This file contains the cartesian coordinates of the centres of the DOMs with reference point above the sea level, as well as ID numbers of the string and module.

`coordinate_change.py` performs the coordinate conversion required by Prometheus, by reading the .detx files of the real ARCA and overwriting the original arca.geo file. Before running the script make sure to inspect the .detx file to validate it works right for yout input (i.e. that the lines skipped are correct). To run it:
```bash
python coordinate_change.py path/to/file.detx
```

##Configuration parameters

There are parameters such as number of PMTs, quantum efficiency, TTS, ToT and others that should be adjusted to ARCA. These can be found in prometheus/config_types.py in the class DOMResponseConfig.

##PMT Coordinates

To place the PMTs accurately on the DOM after setting the number of PMTs to 31 in the configuration, we use the code snippet inside `pmts.py` instead of the fibonacci_sphere function inside prometheus/utils/pmt_response.py

##Future Work
+ Validation of PMT placing following the string axis, as the comment in the Prometheus code suggests. This could be useful for non-static ARCA but should be checked out.
+ Addition of MOD_prometheus.py in the setup if split_production becomes the default production method.
 
