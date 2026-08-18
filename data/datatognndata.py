#!/usr/bin/env python3

import logging
import os
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import awkward as ak
import numpy as np
import psutil

logger = logging.getLogger(__name__)

# ===========================================================================
# Configuration
# ===========================================================================
REPO_ROOT = Path.home() / "prometheus"
FOLDER_A = REPO_ROOT / "output" / "50Kendofinternship"/"30jul"
FOLDER_B = REPO_ROOT / "output" / "50Kendofinternship"/ "augpulses"
OUTPUT_DIR = REPO_ROOT / "output" / "50Kendofinternship"/"bananoippokampos"

# Columns to extract from disk
COLS_FILE_A = ["mc_truth"]
COLS_FILE_B = [
    "sensor_pos_x",
    "sensor_pos_y",
    "sensor_pos_z",
    "pmt_dir_x",
    "pmt_dir_y",
    "pmt_dir_z",
    "tot_ns",
    "fadc_q"
]

# Specify which nested fields from mc_truth you want to include in the output.
# Set to None or [] if you want to include ALL subfields under mc_truth.
MC_TRUTH_FIELDS_TO_KEEP = ["initial_state_energy","final_state_energy"]

# Primary column in File B used to check if a row/event is empty
CHECK_EMPTY_COL_B = "tot_ns"

# Transformations
LOG10_COLUMNS = ["initial_state_energy", "final_state_energy"]  # Evaluated on the un-nested field
RENAME_MAP = {
    "initial_state_energy": "logE_nu",
    "final_state_energy": "logE_mu",
    "sensor_pos_x": "hit_pos_x",
    "sensor_pos_y": "hit_pos_y",
    "sensor_pos_z": "hit_pos_z",
    "pmt_dir_x": "hit_dir_x",
    "pmt_dir_y": "hit_dir_y",
    "pmt_dir_z": "hit_dir_z",
    "tot_ns": "hit_tot",
}


# Helper Functions


def extract_id(filename: str) -> str | None:
    """Extracts a numerical ID from a filename (e.g., 'run_101_a.parquet' -> '101')."""
    match = re.search(r"\d+", filename)
    return match.group(0) if match else None


# Worker Function (Executes in Parallel)


def process_file_pair(task_args: tuple[Path, Path, str]) -> str:
    """Processes a pair of parquet files, dropping rows where File B is empty."""
    file_a, file_b, file_id = task_args
    output_file = OUTPUT_DIR / f"combined_{file_id}.parquet"

    # Skip if output already exists (allows resuming interrupted runs)
    if output_file.exists():
        return f"Skipped (exists): ID {file_id}"

    try:
        # 1. Load requested columns directly into Awkward memory structures
        arr_a = ak.from_parquet(str(file_a), columns=COLS_FILE_A)
        arr_b = ak.from_parquet(str(file_b), columns=COLS_FILE_B)

        n_events_initial = len(arr_a)

        # -------------------------------------------------------------------
        # 2. Identify and Filter Empty Rows from File B
        # -------------------------------------------------------------------
        b_target = arr_b[CHECK_EMPTY_COL_B]

        # Check for missing values or 0-length variable arrays in File B
        if str(b_target.type).startswith("var") or "var *" in str(
            b_target.type
        ):
            # For variable-length arrays: valid if length > 0
            valid_mask = ak.num(b_target) > 0
        else:
            # For standard fields: valid if not None / not null
            valid_mask = ~ak.is_none(b_target)

        # Count dropped rows
        n_valid_events = int(ak.sum(valid_mask))
        n_dropped = n_events_initial - n_valid_events

        # If all rows in File B are empty, skip saving
        if n_valid_events == 0:
            return f"Skipped (all {n_events_initial} rows empty in File B): ID {file_id}"

        # Apply mask to keep only non-empty rows in both arrays
        arr_a = arr_a[valid_mask]
        arr_b = arr_b[valid_mask]

        # -------------------------------------------------------------------
        # 3. Process Fields
        # -------------------------------------------------------------------
        combined_fields = {}

        # Extract specified nested fields from mc_truth
        if "mc_truth" in ak.fields(arr_a):
            mc_struct = arr_a["mc_truth"]
            available_subfields = ak.fields(mc_struct)

            # Determine which subfields to extract
            if MC_TRUTH_FIELDS_TO_KEEP:
                target_subfields = [
                    f for f in MC_TRUTH_FIELDS_TO_KEEP if f in available_subfields
                ]
                missing = set(MC_TRUTH_FIELDS_TO_KEEP) - set(target_subfields)
                if missing:
                    logger.warning(
                        f"ID {file_id}: Specified mc_truth fields not found: {missing}"
                    )
            else:
                target_subfields = available_subfields

            # Extract selected subfields
            for subfield in target_subfields:
                combined_fields[subfield] = mc_struct[subfield]
        else:
            # Fallback if mc_truth was already un-nested in input
            for field in ak.fields(arr_a):
                if not MC_TRUTH_FIELDS_TO_KEEP or field in MC_TRUTH_FIELDS_TO_KEEP:
                    combined_fields[field] = arr_a[field]
        
        if "final_state_energy" in combined_fields:
           combined_fields["final_state_energy"] = (
            combined_fields["final_state_energy"][:, 0]
            )

        # Extract fields from Folder B
        for field in ak.fields(arr_b):
            combined_fields[field] = arr_b[field]

        # Generate evt_id for remaining valid events (0, 1, 2, ..., N-1)
        combined_fields["evt_id"] = np.arange(n_valid_events)
        
        combined_fields["pseudo_runid"] = [file_id] * n_valid_events

        for column in LOG10_COLUMNS:
            if column in combined_fields:
                data = combined_fields[column]
                safe_data = ak.where(data > 0, data, np.nan)
                combined_fields[column] = np.log10(safe_data)

        # Apply field renames
        final_fields = {}
        for old_name, field_array in combined_fields.items():
            new_name = RENAME_MAP.get(old_name, old_name)
            final_fields[new_name] = field_array


        # -------------------------------------------------------------------
        # Flatten inner hit_tot lists while repeating corresponding hit fields
        # -------------------------------------------------------------------

        # Index of each outer hit within each event:
        hit_indices = ak.local_index(final_fields["hit_tot"], axis=1)

        hit_indices = ak.flatten(
            ak.broadcast_arrays(
                hit_indices,
                final_fields["hit_tot"]
            )[0],
            axis=2
        )

        # Repeat the outer hit-level fields according to hit_tot's inner lists
        REPEAT_FIELDS = [
            "hit_pos_x",
            "hit_pos_y",
            "hit_pos_z",
            "hit_dir_x",
            "hit_dir_y",
            "hit_dir_z",
        ]

        for field in REPEAT_FIELDS:
            final_fields[field] = final_fields[field][hit_indices]

        # Flatten hit_tot itself
        final_fields["hit_tot"] = ak.flatten(
            final_fields["hit_tot"],
            axis=2
        )

        # fadc_q: if it has the same [[...], [...]] structure as hit_tot
        if "fadc_q" in final_fields:
            final_fields["fadc_q"] = ak.flatten(
                final_fields["fadc_q"],
                axis=2
            )


        # Save output Parquet file
        out_array = ak.Array(final_fields)
        ak.to_parquet(out_array, str(output_file))

        # Build informative status message for stdout
        status_msg = f"Done: ID {file_id} ({n_valid_events} events written"
        if n_dropped > 0:
            status_msg += f", {n_dropped} empty rows from File B dropped)"
        else:
            status_msg += ")"

        return status_msg

    except Exception as e:
        return f"Error processing ID {file_id}: {e}"


# Dynamic Worker Count Calculation


def get_safe_worker_count(estimated_ram_per_worker_gb: float = 2.0) -> int:
    """Calculates maximum parallel worker processes based on system resources."""
    cpu_cores = os.cpu_count() or 4
    total_ram_gb = psutil.virtual_memory().total / (1024**3)

    usable_ram_gb = total_ram_gb * 0.6
    ram_workers = int(usable_ram_gb // estimated_ram_per_worker_gb)

    workers = max(1, min(cpu_cores, ram_workers))
    print(f"System: {cpu_cores} CPUs | {total_ram_gb:.1f} GB RAM")
    print(
        f"Allocating {workers} worker processes (~{estimated_ram_per_worker_gb} GB RAM/worker).\n"
    )
    return workers


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )

    if not FOLDER_A.exists() or not FOLDER_B.exists():
        logger.error("One or both input directories do not exist.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Index files in Folder B recursively across all subdirectories
    files_b_map = {}
    for file_b in FOLDER_B.rglob("*.parquet"):
        b_id = extract_id(file_b.name)
        if b_id:
            files_b_map[b_id] = file_b

    # Step 2: Match files in Folder A recursively across all subdirectories
    tasks = []
    for file_a in FOLDER_A.rglob("*.parquet"):
        a_id = extract_id(file_a.name)
        if a_id and a_id in files_b_map:
            tasks.append((file_a, files_b_map[a_id], a_id))
        else:
            logger.warning(
                "No matching file in Folder B for %s (ID: %s)",
                file_a.name,
                a_id,
            )

    n_tasks = len(tasks)
    if n_tasks == 0:
        logger.warning("No matching Parquet file pairs found to process.")
        sys.exit(0)

    # Step 3: Run multiprocessing pool
    num_processes = get_safe_worker_count(estimated_ram_per_worker_gb=8.0)
    print(f"Found {n_tasks} file pair(s) to process. Starting batch...\n")

    with Pool(processes=num_processes) as pool:
        for i, result in enumerate(
            pool.imap_unordered(process_file_pair, tasks), 1
        ):
            print(f"[{i}/{n_tasks}] {result}")

    print("\nBatch processing complete.")


if __name__ == "__main__":
    main()
