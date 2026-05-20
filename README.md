# Prometheus-ARCA

batches_production.py
-
produces neutrino simulations in batches. You may choose the amount of workers (n_workers) and the number of simulated events  in total (n_events_total) or per worker (n_events_per_worker). Note that if the total number of events isn't a multiple of the number of workers, you may end up with fewer simulations than expected. You may also select the flavour by choosing the final_state_1 to be "MuMinus" for muon neutrinos or "NuEbar" for electron antineutrinos. The initial zenith angle can be adjusted, with 0 degrees corresponding to upgoing events and 180 degrees to downgoing. Simulated events are saved in the output file inside Prometheus in parquet format.

You should use the currently supported arguments to control the above:

+the number of workers (--workers)
+the total number of events (--total_events) or the number of events per worker (--events_per_worker) 
+the energy range (--energy)
+the zenith angle (--zenith)
+the particle flavor (--flavor)

coordinate_change.py
-
overwrites the original arca.geo file with the corrected coordinates for Prometheus. The position of each DOM is determined by the average of its respective PMT coordinates. You may run the script by inputting the location of the real arca coordinate file as an argument. Note that it might be sensitive to how the file content is formatted and thus it's good practice to check in advance whether it works for your input.
