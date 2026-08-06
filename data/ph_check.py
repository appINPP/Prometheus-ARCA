import polars as pl
import numpy as np

FILE_PATH = "3august.parquet"  # Update to your target file path

# 1. Lazy scan of the Parquet file
lazy_df = pl.scan_parquet(FILE_PATH)

# Compute energy statistics lazily
energy_exprs = lazy_df.select([
    pl.len().alias("total_rows"),
    pl.col("mc_truth").struct.field("initial_state_energy").min().alias("min_E"),
    pl.col("mc_truth").struct.field("initial_state_energy").max().alias("max_E")
]).collect()

total_rows = energy_exprs["total_rows"][0]
min_e = energy_exprs["min_E"][0]
max_e = energy_exprs["max_E"][0]

print(f"Total Amount of Events: {total_rows}\n")
print(f"Min Energy: {min_e:.2e} GeV  (log10 = {np.log10(min_e):.2f})")
print(f"Max Energy: {max_e:.2e} GeV  (log10 = {np.log10(max_e):.2f})")

# 2. Add calculated columns lazily (avoiding expensive Python loops)
analysis_df = lazy_df.with_columns([
    # Calculate hit count per event (returns 0 if null or missing sensor_id)
    pl.col("photons").struct.field("sensor_id").list.len().fill_null(0).alias("n_hits"),
    
    # Flags for missing fields
    pl.col("photons").is_null().alias("is_photons_null"),
    (
        pl.col("mc_truth").is_null() | 
        pl.col("mc_truth").struct.field("initial_state_energy").is_null() | 
        pl.col("mc_truth").struct.field("final_state_energy").is_null()
    ).alias("is_truth_missing")
])

# 3. Aggregate checks in a single query
stats = analysis_df.select([
    # Empty/Zero-hit photons (either photons struct is null or n_hits == 0)
    (pl.col("is_photons_null") | (pl.col("n_hits") == 0)).sum().alias("empty_photons"),
    
    # Missing MC truth energy
    pl.col("is_truth_missing").sum().alias("empty_truth"),
    
    # Low hits count (0 <= n_hits <= 10)
    (pl.col("n_hits") <= 10).sum().alias("low_hits")
]).collect()

empty_photons_count = stats["empty_photons"][0]
empty_truth_count = stats["empty_truth"][0]
count_low = stats["low_hits"][0]

# Calculate percentages
pct_empty_photons = (empty_photons_count / total_rows) * 100
pct_empty_truth = (empty_truth_count / total_rows) * 100
percentage_low = (count_low / total_rows) * 100

# 4. Print Results
print("\n--- CHECK RESULTS ---")
print(f"Empty/Zero-hit Photons: {empty_photons_count} out of {total_rows} ({pct_empty_photons:.2f}%)")
print(f"Missing MC Truth Energy: {empty_truth_count} out of {total_rows} ({pct_empty_truth:.2f}%)")

print("\n--- LOW HIT STATISTICS ---")
print(f"Events with 0 to 10 hits: {count_low} out of {total_rows} ({percentage_low:.2f}%)")
