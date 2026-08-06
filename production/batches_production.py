# Example for python multithreading

import os

# Disable internal BLAS/OpenMP oversubscription
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

"""
# Safer JAX/XLA memory behavior
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["XLA_PYTHON_CLIENT_ALLOCATOR"] = "platform"
"""

# imports
import time
from multiprocessing import Process, Pool
from pathlib import Path
from prometheus import Prometheus, config
import argparse
import gc
import jax 

# Prefer CPU JAX when available
try:
    from jax.config import config as jconfig
    jconfig.update("jax_enable_x64", True)
    jconfig.update("jax_platform_name", "cpu")
except Exception:
    pass

# Paths
REPO_ROOT = Path("/prometheus")
output_base = REPO_ROOT / "output"
output_base.mkdir(exist_ok=True)

p = argparse.ArgumentParser(
        description="Production in Batches",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
p.add_argument(
    "--energy",
    choices=["lower", "full", "upper"],
    default="full",
    help='Choose "lower" (1e2-1e6 GeV) or "upper" (1e6-1e9 GeV) energy range. Default is full range (1e2-1e6 GeV)'
)
p.add_argument(
    "--zenith",
    choices=["upgoing", "full", "downgoing"],
    default="full",
    help='Choose "upgoing" or "downgoing" events. Default produces both.'
    )
p.add_argument(
    "--workers",
    type=int,
    help="Choose amount of workers"
    )
p.add_argument(
    "--flavor",
    choices=["MuMinus", "NuEBar"],
    default="MuMinus",
    help='Primary lepton final state, choose "MuMinus" for muon neutrinos or "NuEbar" for electron antineutrinos'
)

group = p.add_mutually_exclusive_group(required=True)

group.add_argument(
    "--total_events",
    type=int,
    help="Total number of events to simulate (split across workers). Note that if the total number of events isn't a multiple of the number of workers, you may end up with fewer simulations than expected."
)

group.add_argument(
    "--events_per_worker",
    type=int,
    help="Events per worker"
)

EN_RANGES = {
    "lower": (1e2, 1e6),
    "full":  (1e2, 1e9),
    "upper":  (1e6, 1e9),
}
ZE_RANGES = {
    "upgoing": (0, 90),
    "full":   (0, 180),
    "downgoing":  (90, 180),
}
args = p.parse_args()

# Parameters
emin, emax = EN_RANGES[args.energy]
zenmin, zenmax = ZE_RANGES[args.zenith]

n_workers = args.workers
if args.total_events is not None:
    events_per_worker = int(int(args.total_events) / n_workers)
else:
    events_per_worker = int(args.events_per_worker)
def simulate_batch(settings):
    id, n_events = settings
    
    from prometheus import Prometheus, config
    # detector setup
    geofile= str((REPO_ROOT / "resources" / "geofiles" / "arca.geo").resolve())
    config.detector.geo_file = geofile
    # Output Location
    run_dir = output_base / f"f_{args.flavor}-{id}-en_{args.energy}"
    run_dir.mkdir(exist_ok=True)
        
    config.run.storage_prefix = str(run_dir)
    
    # Configuration
    config.run.run_number = id                  #by default is used as seed
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
    injection_config.simulation.min_zenith= zenmin
    injection_config.simulation.max_zenith= zenmax
    
    injection_config.simulation.minimal_energy = emin
    injection_config.simulation.maximal_energy = emax
    injection_config.simulation.power_law = 1.4
    
    injection_config.simulation.is_ranged = False
    injection_config.cylinder_radius = 805 
    injection_config.cylinder_height = 3500 

    # final_state_1 either MuMinus or NuEBar
    injection_config.simulation.final_state_1= args.flavor
    injection_config.simulation.final_state_2= "Hadrons"
    
    print(f"[Worker {id}] starting simulation")
    prometheus = Prometheus()
    prometheus.sim()
    print(f"[Simulation saved in {str(run_dir)}]")
    del prometheus
    gc.collect()
    jax.clear_caches() #jax cleanup
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)               #C cleanup
    except Exception:
        pass
    return (id,n_events)

import multiprocessing

def init_worker():
    process = multiprocessing.current_process()
    worker_idx = process._identity[0] - 1

    allowed = sorted(os.sched_getaffinity(0))
    cpu = allowed[worker_idx % len(allowed)]

    os.sched_setaffinity(0, {cpu})
    print(f"Worker {worker_idx} pinned to CPU {cpu}")


if __name__ == "__main__":
    start_time = time.time()
    
    # Checks if this combination of no of workers/events has been done before and changes the seed
    check=1002160
    run_dir = output_base / f"f_{args.flavor}-{check}-en_{args.energy}"
    while run_dir.exists():
        check+=n_workers
        run_dir = output_base / f"f_{args.flavor}-{check}-en_{args.energy}"

    pool_inputs = [(check+i, events_per_worker) for i in range(n_workers)]
    
    print(f"Spawning pool with {n_workers} workers...")
    
    with Pool(processes=n_workers, initializer=init_worker) as pool:
        results = pool.map(simulate_batch, pool_inputs)
        
    instances_total = sum(events for worker_id, events in results)
    
    print("Finished processes: %d" % len(results))
    time_diff = (time.time() - start_time) / 60
    print(
        "simulated %s events in %s minutes using %s workers. \n Time per event per core is: %s sec"
        % (instances_total, time_diff, n_workers, (instances_total / n_workers) / time_diff)
    )

