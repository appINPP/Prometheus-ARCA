import polars as pl
from pathlib import Path
import argparse
import glob
import os

p=argparse.ArgumentParser(
        description="Concatenation of simulated files",
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
    "--energy",
    choices=["upper", "lower", "full"],
    default="full",
    help='Whether the simulated files are for higher or lower than 1 PeV'
)
args = p.parse_args()

REPO_ROOT=Path.home()/"prometheus"

energy_paths = {
    "lower": f"{REPO_ROOT}/{args.flavor}/simulation_files/{args.id}-en_lower-*.parquet",
    "upper": f"{REPO_ROOT}/{args.flavor}/simulation_files/{args.id}-en_upper-*.parquet",
    "full": f"{REPO_ROOT}/{args.flavor}/simulation_files/{args.id}-*.parquet"
}

selected_path = energy_paths.get(args.energy)
output_file = (
    f"{REPO_ROOT}/{args.flavor}/simulation_files/{args.id}_{args.energy}_combined.parquet"
)

pl.scan_parquet(selected_path).sink_parquet(output_file)

print(f"Successfully concatenated data for ID:{args.id}")

source_files = glob.glob(selected_path)

if source_files:
    response = input(f"Do you want to delete the {len(source_files)} source files? (y/n): ").strip().lower()
    
    if response == 'y':
        for file_path in source_files:
            if os.path.abspath(file_path) != os.path.abspath(output_file):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        print("Source files deleted.")
    else:
        print("Skipped deletion. Source files kept.")

    
