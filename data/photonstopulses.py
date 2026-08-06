#!/usr/bin/env python3
import logging
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import awkward as ak
import numpy as np
import psutil

from prometheus.utils.dom_response import process_event

logger = logging.getLogger(__name__)

REPO_ROOT = Path.home() / "prometheus"
INPUT_DIR = REPO_ROOT / "output"/ "30jul"
OUTPUT_DIR = REPO_ROOT / "output" / "augpulses"

REQUIRED_COLUMNS = [
    "photons",
    "mc_truth"
]


# Worker Function

def process_single_file(input_file: Path) -> str:
    """Processes a single photons parquet file and saves the generated pulses."""
    output_filename = input_file.name.replace("_photons.parquet", "_pulses.parquet")
    output_file = OUTPUT_DIR / output_filename

    # Skip if file already exists (allows resuming interrupted runs)
    if output_file.exists():
        return f"Skipped (exists)"

    # Generate a unique, deterministic seed per file
    file_seed = (42 + hash(input_file.name)) % (2**32 - 1)
    rng = np.random.default_rng(file_seed)

    events = ak.from_parquet(str(input_file), columns=REQUIRED_COLUMNS)
    n_events = len(events)

    mc = events["mc_truth"]
    vertex_positions = np.column_stack(
        [
            np.asarray(mc["initial_state_x"]),
            np.asarray(mc["initial_state_y"]),
            np.asarray(mc["initial_state_z"]),
        ]
    )

    photons_array = events["photons"]
    pulse_records: list[dict] = []

    for i in range(n_events):
        photons = ak.to_list(photons_array[i])
        record = process_event(photons, vertex_positions[i], rng)
        pulse_records.append(record)

    out = ak.Array(pulse_records)
    ak.to_parquet(out, str(output_file))

    return f"Done!"


# Worker Calculation based on RAM & CPU

def get_safe_worker_count(estimated_ram_per_worker_gb: float = 30) -> int:
    """Calculates the maximum number of worker processes based on available RAM and CPUs."""
    cpu_cores = os.cpu_count() or 4
    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    
    # Reserve 40% RAM for OS/system safety
    usable_ram_gb = total_ram_gb * 0.6
    ram_workers = int(usable_ram_gb // estimated_ram_per_worker_gb)
    
    # Take whichever limit is tighter: CPU count or RAM limit
    workers = max(1, min(cpu_cores, ram_workers))
    print(f"System: {cpu_cores} CPUs | {total_ram_gb:.1f} GB RAM")
    print(f"Allocating {workers} worker processes (~{estimated_ram_per_worker_gb} GB RAM/worker).")
    return workers


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not INPUT_DIR.exists():
        logger.error("Input directory not found: %s", INPUT_DIR)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_files = sorted(INPUT_DIR.rglob("*_photons.parquet"))
    n_files = len(input_files)

    if not input_files:
        logger.warning("No files matching pattern '*_photons.parquet' in %s", INPUT_DIR)
        sys.exit(0)

    num_processes = get_safe_worker_count(estimated_ram_per_worker_gb=10)
    print(f"Found {n_files} file(s) to process. Starting batch...\n")

    # Multiprocessing Pool with imap_unordered for dynamic streaming
    with Pool(processes=num_processes) as pool:
        for i, result in enumerate(pool.imap_unordered(process_single_file, input_files), 1):
            if i % 50 == 0 or i == n_files:
                print(f"[{i}/{n_files}] {result}")

    print("\nBatch processing complete!")


if __name__ == "__main__":
    main()
