# Example for python multithreading

import os

# Disable internal BLAS/OpenMP oversubscription
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Safer JAX/XLA memory behavior
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["XLA_PYTHON_CLIENT_ALLOCATOR"] = "platform"
# imports
import time
from multiprocessing import Process, Pool
from pathlib import Path
from prometheus import Prometheus, config
import gc

# Prefer CPU JAX when available
try:
    from jax.config import config as jconfig
    jconfig.update("jax_enable_x64", True)
    jconfig.update("jax_platform_name", "cpu")
except Exception:
    pass

#Paths
REPO_ROOT = Path("/prometheusLink")
output_base = REPO_ROOT / "output"
output_base.mkdir(exist_ok=True)

#Detector Setup
geofile= str(REPO_ROOT / "resources" / "geofiles" / "arca.geo")
config.detector.geo_file = geofile

def simulate_batch(settings):
    id, n_events = settings
    
    # Output Location
    run_dir = output_base / f"core_{id}of{n_workers}-events_{n_events_total}"
    run_dir.mkdir(exist_ok=True)
        
    config.run.storage_prefix = str(run_dir)
    
    # Configuration
    config.run.run_number = 10+id
    #config.run.random_state_seed = 832796
    config.run.nevents = n_events
    config.run.summary_mode='debug'
    #config.run.verbosity='DEBUG'
    
    """
    # Splits the detector to use less memory, default is 10000
    config.photon_propagator.name="olympus"
    config.photon_propagator.olympus.simulation.splitter=1000000000000
    """
    
    # Injection
    injector= "LeptonInjector"
    config.injection.name = injector
    injection_config = config["injection"][injector]
    
    # 0 degrees for upgoing, 180 for downgoing
    injection_config.simulation.min_zenith= 0 #degrees
    injection_config.simulation.max_zenith= 90 #degrees
    
    injection_config.simulation.minimal_energy = 1e6
    injection_config.simulation.maximal_energy = 1e9
    injection_config.simulation.gamma = 1.4
    
    #injection_config.simulation.is_ranged = False
    #injection_config.simulation.cylinder_radius = 800 
    #injection_config.simulation.cylinder_height = 3500 
    
    # final_state_1 either MuMinus or NuEBar
    injection_config.simulation.final_state_1= "MuMinus"
    injection_config.simulation.final_state_2= "Hadrons"
    
    print(f"[Worker {id}] starting simulation")
    
    prometheus = Prometheus()
    prometheus.sim()
    
    del prometheus
    gc.collect()
    return (id,n_events)

if __name__ == "__main__":
    start_time = time.time()
    
    n_workers = 5                 #No of workers used
    n_events_total = 20           #No of TOTAL events (will split into respective workers)
    
    events_per_worker = int(n_events_total / n_workers)
    pool_inputs = [(i, events_per_worker) for i in range(n_workers)]
    
    print(f"Spawning pool with {n_workers} workers...")
    
    with Pool(processes=n_workers, maxtasksperchild=1) as pool:
        results = pool.map(simulate_batch, pool_inputs)
        
    instances_total = sum(events for worker_id, events in results)
    
    print("Finished processes: %d" % len(results))
    time_diff = (time.time() - start_time) / 60
    print(
        "simulated %s events in %s minutes using %s cores. \n Time pr. event pr. core is: %s"
        % (instances_total, time_diff, n_workers, (instances_total / n_workers) / time_diff)
    )
    
