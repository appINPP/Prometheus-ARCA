import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

file_name = "combined_muminus_data.parquet" #example

print(f"Loading {file_name}...")
df = pd.read_parquet(file_name)
print(f"Successfully loaded {len(df):,} events!")

# .・。.・゜✭・.・✫・゜・。.
#      MC TRUTH
# .・。.・゜✭・.・✫・゜・。.

print("Generating MC Truth plots...")
try:
    if isinstance(df["mc_truth"].iloc[0], str):
        mc_df = pd.json_normalize(df["mc_truth"].apply(json.loads))
    else:
        mc_df = pd.json_normalize(df["mc_truth"])
except Exception as e:
    print(
        "  -> Normalizing mc_truth directly failed, falling back to manual line-parsing..."
    )
    mc_rows = []
    for row in df["mc_truth"]:
        if pd.isna(row) or not row:
            continue
        mc_rows.append(json.loads(row) if isinstance(row, str) else row)
    mc_df = pd.json_normalize(mc_rows)

# KEYS TO EXCLUDE
exclude_keys = [
    "interaction",
    "initial_state_type",
    "final_state_type",
    "final_state_parent",
]

columns_initial = []
columns_final = []
columns_others = []

for c in mc_df.columns:
    if c in exclude_keys:
        continue

    if "initial" in c:
        columns_initial.append(c)
    elif "final" in c:
        columns_final.append(c)
    else:
        columns_others.append(c)


def plot_group(column_list, title, filename, default_color):
    if not column_list:
        return

    print(f"-> Plotting {title} ({len(column_list)} columns)...")
    cols = 3
    rows = (len(column_list) + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 4))
    axes = axes.flatten()

    for i, col in enumerate(column_list):
        ax = axes[i]
        raw_series = mc_df[col].dropna()
        data = raw_series.apply(
            lambda x: x[0] if isinstance(x, (list, np.ndarray)) else x
        )

        ax.set_yscale("log")
        ax.set_ylabel("counts (log)")

        # Unique transformation rules
        if "energy" in col:
            bins = np.logspace(
                np.log10(data.min() + 1e-3), np.log10(data.max() + 1), 50
            )
            ax.hist(
                data, bins=bins, histtype="step", linewidth=2, color=default_color
            )
            ax.set_xscale("log")
            ax.set_title(f"{col} (log)")

        elif "zenith" in col:
            cos_data = np.cos(data)
            bins = np.linspace(-1, 1, 50)
            ax.hist(
                cos_data,
                bins=bins,
                histtype="step",
                linewidth=2,
                color=default_color,
            )
            ax.set_title(f"cos({col})")
            ax.set_yscale("linear")
            ax.set_ylabel("counts")
        elif "azimuth" in col:
            ax.hist(
                data, bins=50, histtype="step", linewidth=2, color=default_color
            )
            ax.set_title(col)
            ax.set_yscale("linear")
            ax.set_ylabel("counts")
        else:
            ax.hist(
                data, bins=50, histtype="step", linewidth=2, color=default_color
            )
            ax.set_title(col)

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    fig.suptitle(title, y=1.02, fontsize=18, fontweight="bold")
    plt.savefig(filename, bbox_inches="tight")
    plt.close()
    print(f"Saved: {filename}")

plot_group(
    columns_initial,
    "Initial State Variables",
    "mc_truth_initial.png",
    "darkslateblue",
)
plot_group(
    columns_final, "Final State Variables", "mc_truth_final.png", "mediumvioletred"
)
plot_group(
    columns_others, "Interaction Variables", "mc_truth_interaction.png", "purple"
)

# .・。.・゜✭・.・✫・゜・。.
#       PHOTONS
# .・。.・゜✭・.・✫・゜・。.

print("Processing and flattening photon data...")

photon_data_pools = {}
initialized_keys = False
photon_keys = []

# Loop through every row to parse the strings into actual dictionaries
for idx, row in enumerate(df["photons"]):
    if pd.isna(row) or not row:
        continue

    try:
        if isinstance(row, str):
            event_dict = json.loads(row)
        else:
            event_dict = row  # Already a dict

        if not initialized_keys:
            photon_keys = list(event_dict.keys())
            for key in photon_keys:
                photon_data_pools[key] = []
            initialized_keys = True

        for key in photon_keys:
            if key in event_dict and event_dict[key] is not None:
                arr = np.atleast_1d(event_dict[key])
                if len(arr) > 0:  # Only grab rows that aren't empty []
                    photon_data_pools[key].append(arr)

    except Exception as e:
        continue

print("Generating Photon Detector plots...")

num_keys = len(photon_keys)
if num_keys == 0:
    print("Error: Could not find any valid photon keys. Check file formatting.")
else:
    cols = 3
    rows = (num_keys + cols - 1) // cols

    fig_ph, axes_ph = plt.subplots(rows, cols, figsize=(16, rows * 4))
    axes_ph = axes_ph.flatten()
    
    for i, key in enumerate(photon_keys):
        ax = axes_ph[i]
        ax.set_yscale('log')
        ax.set_ylabel("counts (log)")
        ax.set_title(f"{key}")
        
        # Stitch all the small arrays together for this specific variable
        if len(photon_data_pools[key]) > 0:
            flat_data = np.concatenate(photon_data_pools[key])
            
            if key in ["string_id", "sensor_id", "id_idx"]:
                bins = (
                    np.arange(int(flat_data.min()), int(flat_data.max()) + 2)
                    - 0.5
                )

                ax.hist(
                    flat_data, bins=bins, color="maroon", alpha=0.7, rwidth=0.9
                )
            else:
                ax.hist(flat_data, bins=100, histtype="step", color="maroon", alpha=0.7)
        else:
            ax.text(0.5, 0.5, "No Data Found", ha='center', va='center', color='red')
            
    # Remove extra empty boxes on the plotting layout grid
    for j in range(i + 1, len(axes_ph)):
        fig_ph.delaxes(axes_ph[j])

    plt.tight_layout()
    fig_ph.suptitle("Photon Detector Distributions", y=1.02, fontsize=20, fontweight="bold")
    plt.savefig("photon_detector_plots.png", bbox_inches="tight")
    plt.close()
    print("Saved: photon_detector_plots.png")

print("\n Everything is completely configured! Check your output folder for the new files.")
