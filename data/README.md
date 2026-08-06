# Data
This folder contains scripts for handling the simulation output until it reaches the GNN training. There are also codes for validation plots and checks.
## Output to GNN
To prepare the raw simulation files (photons) for the training we use two scrips subsequently: photonstopulses.py and datatognn.py. Both scripts handle multiple parquet files inside directories and their subdirectories, using multiprocessing. Before running, check out the parameters of the function `get_workers` to make sure it aligns with your RAM use expectations.

**photonstopulses.py**, creates new parquet files containing the information on hit positions, directions, dom/pmt ids and electronics. **datatognn.py** takes the photons and pulses parquets and creates a new unified parquet file with the features of our choice. Those unified parquets are then ready to be condensed and transferred for further analysis.

## Validation
To validate the simulation output we may use:
+ **scatterplot.py**, to create scatterplots with data from multiple files. This is based on Melina's plotting codes (thanks so much!)
+ **ph_checks.py**, to print out information on the amount of events in a single photons file, the amount of undetected events, the minimum/maximum energy and the number of events with low hit counts.
+ **ph_histograms.py**, creates histograms on the data from a single photons file.

## Limitations/Future Work
+ datatognn.py doesn't work because of an wkward extension. This either requires a workaround or a change in how photons files are written (i.e. disabling the extension while writing the files). Otherwise we may keep mc_truth and features separately and move them like that to the GNN. This requires further work.
