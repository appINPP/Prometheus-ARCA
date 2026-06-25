# Prometheus-ARCA

batches_production.py
-
produces neutrino simulations in batches in separate cores. Simulated events are saved in the output file inside Prometheus in parquet format. You should use the supported arguments to control:

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

split production
-
allows to do the neutrino injection separately and choose later on to produce filtered high energy or low energy events (over/under 1 PeV). To run the code one should run the MOD_prometheus.py code to run simulations instead of the normal prometheus.py provided by the initial code. To set the event distributor to use later on, run the code job_db.py once.

You can create the injection files with injection.py with the same arguments used in batches_production.py. This also creates a folder named by the event type and a subfolder named "injection files" to store them in.

To run the simulations you should first initialize the event distributor through init_propagation.py for your spcecific file found by the arguments of event type (--flavor) and (--id), the identification number used for the injection file. Once that's set you can run the propagation.py code to create simulations while using arguments such as --flavor, --file_id, --workers, --events_per_worker and --energy with inputs high or low depending on what energy events you want to propagate. Parquet files will be saved inside the event type folder inside the subfolder named "simulation_files". Good luck!

