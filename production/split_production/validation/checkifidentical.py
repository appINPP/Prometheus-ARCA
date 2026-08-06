import os
import glob
import re

# 1. Mute the Awkward Array warning
os.environ["POLARS_UNKNOWN_EXTENSION_TYPE_BEHAVIOR"] = "load_as_storage"

import polars as pl

# 2. Get and sort files by batch integer
file_paths = glob.glob("0-en_lower-*.parquet")

def get_batch_start(file_path):
    match = re.search(r"batch(\d+)", file_path)
    return int(match.group(1)) if match else -1

sorted_files = sorted(file_paths, key=get_batch_start)

# 3. Read and unnest directly
df = pl.read_parquet(sorted_files)

flat_df = df.unnest("mc_truth").unnest("photons")

print(flat_df)


df0=pl.read_parquet("0_photons.parquet")

flat_df0=df0.unnest("mc_truth").unnest("photons")

df0_filtered = flat_df0.filter(pl.col("initial_state_energy")<1e6)

"""
are_equal = flat_df.equals(df0_filtered)
print(are_equal)

"""
from polars.testing import assert_frame_equal
"""
# This will print the precise mismatch details!
assert_frame_equal(flat_df, df0_filtered)

"""

# Returns True if there is AT LEAST one duplicate row
has_duplicates = flat_df.is_duplicated().any()
print("Has duplicates?:", has_duplicates)

# Count how many total duplicate rows exist
duplicate_count = flat_df.is_duplicated().sum()
print("Total duplicate rows:", duplicate_count)




print("Top 5 highest energies in 0_photons.parquet:")
print(flat_df0.select("initial_state_energy").sort("initial_state_energy", descending=True).head(5))
print(flat_df.select("initial_state_energy").sort("initial_state_energy", descending=True).head(5))


print(f"Batch files row count: {len(flat_df)}")             # Should be 98
print(f"Filtered 100-file row count: {len(df0_filtered)}")  # Should now be 98

# 5. Check if they are exactly equal!
are_equal = flat_df.equals(df0_filtered)
print("Are they exactly equal?:", are_equal)

# If they aren't exact, this will highlight the exact column or floating point mismatch
assert_frame_equal(flat_df, df0_filtered)

print("Top 5 highest energies in 0_photons.parquet:")
print(flat_df0.select("initial_state_energy").sort("initial_state_energy", descending=True).head(5))


