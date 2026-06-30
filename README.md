# Prometheus-ARCA

This repository offers additional codes for Prometheus, open source neutrino simulations, specifically for ARCA. You can find production and additional scripts.

## ✩ Production Codes

### batches_production.py
produces neutrino simulations in batches in separate cores. Simulated events are saved in the output file inside Prometheus in parquet format. 

The following arguments control:

+ the number of workers (--workers)
+ the total number of events (--total_events) or the number of events per worker (--events_per_worker). Note that if the total number of events isn't a multiple of the amount of workers, there might be slightly fewer simulations than expected.
+ the energy range (--energy)
  + "lower" (1e2-1e6 GeV) 
  + "upper" (1e6-1e9 GeV) 
  + default is "full" (1e2-1e9 GeV)
+ the zenith angle (--zenith) for
  + "upgoing" or
  + "downgoing" events
  + default produces both or "full"
+ the event type (--flavor)
  + "MuMinus" for muon neutrinos by default, which uses ranged injection
  + "NuEbar" for electron antineutrinos, which uses an injection cylinder

### split production
allows to do separately the neutrino injection in full range (100 GeV-1 EeV) and then choose to propagate low or high energy events. For more information click [here](split%20production/README.md).

## ✩ Additional Codes

### coordinate_change.py
overwrites the original arca.geo file with the corrected coordinates for Prometheus. The position of each DOM is determined by the average of its respective PMT coordinates. You may run the script by inputting the location of the real arca coordinate file as an argument. Note that it might be sensitive to how the file content is formatted and thus it's good practice to check in advance whether it works for your input.

### plothist.py
creates simple histograms to check the simulation output stored in the parquet files.
