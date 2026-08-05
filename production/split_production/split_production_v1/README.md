# Split Production 
is built to handle large productions by doing separately the injection stage in full energy range (100 GeV-1 EeV) and then an energy-based filtered propagation. This pipeline is split for flexibility and a bash script is available for automation.   

## ✩ Setup
Before running Split Production, replace prometheus.py with MOD_prometheus.py, keeping the original filename. This should execute properly as well as with any code other than the following pipeline.  

## ✩ Pipeline
This pipeline uses a job distributor based on the energy threshold of 1 PeV, for volume injection specifically for ARCA-21.

### injection.py
is responsible for the injection stage and handles the same arguments as [batches_production.py](../README.md###batches_production.py). 

Injection files are stored in prometheus/output/flavor/injection_files.

### init_propagation.py
initialises the event database and prepares the propagation stage by filtering injected events into upper and lower energy bins. It reads the corresponding injection file based on the:
+ event type (--flavor), to open the relevant folder where the data is stored
+ injection file's identification number (--id)

All events are then stored in a local job database as unpropagated (PENDING), where they remain queued until picked up by the propagation workers in the next stage.

### propagation.py
implements the final stage of the pipeline by having multiple workers propagate filtered batches of injected events until all the upper or lower energy range events are processed.

The following arguments handle the:
+ event type (--flavor), which opens the relevant folder where the injection data is stored
+ injection file's identification number (--id)
+ amount of workers (--workers)
+ number of events per worker (--events_per_worker)
+ energy (--energy), "lower" or "upper" to choose to propagate events corresponding to less or more than 1 PeV respectively

The resulting simulation data is written in parquet format under prometheus/output/flavor/simulation_files.

## ✩ Automation

split_production.sh handles the above pipeline automatically. Once again, arguments control the:
+ amount of workers (--workers)
+ total number of events (--total_events)
+ event type (--flavor)
+ propagation energy range (--energy), "upper", "lower" (default) or "full". 

Each worker handles up to 1K events for the injection, 500 for the lower energy propagation and 120 for the upper.

You may run the script in the background and keep the screen output in split.log as the example down below:

```bash
nohup ./split_production.sh --total_events 50000 --workers 40 --flavor MuMinus --energy lower > split.log 2>&1 &
```

## ✩ Additional Code
In addition to the codes above, concatenate.py handles the simulation parquet files by concatenating them in one. The code will then ask whether to delete the original files.

