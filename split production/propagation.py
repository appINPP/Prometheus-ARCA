import os
import sys
import time
import multiprocessing
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prometheus import Prometheus, config
from job_db import claim_events
import gc
from prometheus.config import config

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
#os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "0.20" 

import argparse
p = argparse.ArgumentParser(
        description="Simulation production in batches using pre-existing injection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
p.add_argument(
    "--flavor",
    choices=["MuMinus", "NuEBar"],
    default="MuMinus",
    help='Primary lepton final state, choose "MuMinus" for muon neutrinos or "NuEbar" for electron antineutrinos'
)
p.add_argument(
    "--id",
    type=int,
    help='ID of the injection file'
)
p.add_argument(
    "--workers",
    type=int,
    help="Amount of workers"
    )
p.add_argument(
    "--events_per_worker",
    type=int,
    help="Events per worker"
    )
p.add_argument(
    "--energy",
    choices=["upper", "lower"],
    default="lower",
    help='Whether to propagate for higher or lower than 1 PeV'
)
args = p.parse_args()

REPO_ROOT = Path.home()/"prometheus"
DB_PATH = "jobs.db"
H5_FILE = f"{REPO_ROOT}/output/{args.flavor}/injection_files/{args.id}_LI_output.h5"

def simulate_batch(worker_id):
    bin_name = args.energy 
    batch_size = args.events_per_worker
    
    # Initializing Prometheus
    settings = {
        "injection": {
            "name": "LeptonInjector",
            "LeptonInjector": {
                "inject": False,
                "paths": {"injection_file": H5_FILE}
            }
        }
    }
    
    # Detector Setup
    config.detector.geo_file = str(REPO_ROOT / "resources" / "geofiles" / "arca.geo")
    config.run.db_path = DB_PATH
    config.run.nevents = args.events_per_worker
    
    p = Prometheus(settings)
    
    p.inject()

    total_processed = 0
    
    while True:
        # Claim work from the DB
        event_ids = claim_events(DB_PATH, bin_name, limit=batch_size)
        
        if not event_ids:
            print(f"Core {worker_id}: No more events. Shutting down.")
            break
            
        # Unique output name per batch and per core 
        parq_dir=REPO_ROOT / "output" / f"{args.flavor}"/ "simulation_files"
        parq_dir.mkdir(parents=True, exist_ok=True)
        out_name = str(parq_dir/f"{args.id}-en_{bin_name}-core{worker_id}-batch{event_ids[0]}-{event_ids[-1]}.parquet")
        
        config.run.outfile = str(out_name)
       
        p.propagate(event_ids=event_ids)
        
        #print("DEBUG propagate event_ids:", event_ids)
        #print("DEBUG internal _last_event_ids:", getattr(p, "_last_event_ids", None))
        
        p.construct_output()
        
        total_processed += len(event_ids)
        gc.collect() 

    return total_processed

def init_worker():
    process = multiprocessing.current_process()
    worker_idx = process._identity[0] - 1

    allowed = sorted(os.sched_getaffinity(0))
    cpu = allowed[worker_idx % len(allowed)]

    os.sched_setaffinity(0, {cpu})
    print(f"Worker {worker_idx} pinned to CPU {cpu}")

if __name__ == "__main__":
    n_workers = args.workers 
    start_time = time.time()
    
    print(f"Spawning pool with {n_workers} workers...")
    
    with Pool(processes=n_workers, initializer=init_worker, maxtasksperchild=1) as pool:
        results = pool.map(simulate_batch, range(n_workers))
    
    total_events = sum(results)
    duration = (time.time() - start_time) / 60
    
    print("-" * 30)
    print(f"Production Complete!")
    print(f"Total events: {total_events}")
    print(f"Total time: {duration:.2f} minutes")
    print(f"Speed: {total_events/duration:.2f} events/min")
