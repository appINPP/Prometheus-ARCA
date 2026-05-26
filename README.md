# Prometheus-ARCA

batches_production.py
-
produces neutrino simulations in batches in separate cores. You may choose the amount of workers (n_workers) and the number of simulated events in total (n_events_total) or per worker (n_events_per_worker). Simulated events are saved in the output file inside Prometheus in parquet format.

You should use the supported arguments to control:

+ the number of workers (--workers)
+ the total number of events (--total_events) or the number of events per worker (--events_per_worker). Note that if you use total number of events and your number isn't a multiple of the amount of workers, you may end up with slightly fewer simulations than expected.
+ the energy range (--energy)
  + "lower" (1e2-1e6 GeV) 
  + "upper" (1e6-1e9 GeV) 
  + default is "full" (1e2-1e9 GeV)
+ the zenith angle (--zenith) for
  + "upgoing" or
  + "downgoing" events
  + default produces both or "full"
+ the particle flavor (--flavor)
  + "MuMinus" for muon neutrinos by default, which uses ranged injection
  + "NuEbar" for electron antineutrinos, which uses an injection cylinder

coordinate_change.py
-
overwrites the original arca.geo file with the corrected coordinates for Prometheus. The position of each DOM is determined by the average of its respective PMT coordinates. You may run the script by inputting the location of the real arca coordinate file as an argument. Note that it might be sensitive to how the file content is formatted and thus it's good practice to check in advance whether it works for your input.
