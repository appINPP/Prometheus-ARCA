import h5py
from job_db import init_db, insert_events

import argparse
p = argparse.ArgumentParser(
        description="Preparation for filtering",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
p.add_argument(
    "--flavor",
    choices=["MuMinus", "NuEBar"],
    default="MuMinus",
    help='Primary lepton final state, choose "MuMinus" for muon neutrinos or "NuEbar" for electron antineutrinos'
)
p.add_argument(
    "--file_id",
    type=int,
    help='Number used for file identification'
)
args = p.parse_args()

DB_PATH = "jobs.db"
H5_FILE = f"/prometheusLink/output/{args.flavor}/injection_files/{args.file_id}_LI_output.h5"

ENERGY_THRESHOLD = 1e6  # 1 PeV

def prepare():
    print(f"Reading energies from {H5_FILE}...")
    with h5py.File(H5_FILE, "r") as f:
        energies = f["RangedInjector0"]["properties"]["totalEnergy"][:]
    
    print(f"Found {len(energies)} events. Initializing Database...")
    init_db(DB_PATH)
    
    print("Inserting events into queue...")
    insert_events(DB_PATH, energies, ENERGY_THRESHOLD)
    print("Database ready for production!")

if __name__ == "__main__":
    prepare()
