import os
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
import pyarrow.compute as pc
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from dataclasses import dataclass
from typing import Optional, List, Union


# ============================================================
# CONFIGURATION CLASSES
# ============================================================

@dataclass
class VariableConfig:
    column: str                    # Parent Parquet column (e.g., "mc_truth" or "photons")
    field: Optional[str] = None    # Nested struct field (e.g., "initial_state_energy"), if applicable
    kind: str = "value"            # Options: "value", "length", "sum"
    log10: bool = True             # Apply log10 transformation
    range: tuple = (0, 7)          # Axis range
    label: str = "Axis Label"      # Label for the plot axis


@dataclass
class PlotConfig:
    title: str
    outdir: str = "."
    filename: str = "plot.png"
    diagonal_line: bool = False


# ============================================================
# HELPER: DYNAMIC ARROW DATA EXTRACTION
# ============================================================

def extract_variable_data(batch, var_cfg: VariableConfig) -> np.ndarray:
    """Extracts and transforms data array based on VariableConfig specs."""
    arr = batch[var_cfg.column]

    # Handle nested fields (structs)
    if var_cfg.field:
        arr = pc.struct_field(arr, var_cfg.field)

    # Transform based on `kind`
    if var_cfg.kind == "length":
        arr = pc.list_value_length(arr)
    elif var_cfg.kind == "sum":
        # Sum elements along each list in the column
        arr = pc.list_sum(arr)
    elif var_cfg.kind == "value":
        # If it's a list with a single element per row (e.g., final_state_energy[0])
        if pc.types.is_list(arr.type) or pc.types.is_large_list(arr.type):
            arr = pc.list_element(arr, 0)

    # Convert to NumPy array
    data = arr.to_numpy(zero_copy_only=False).astype(np.float64)

    # Apply log10 transformation if requested
    if var_cfg.log10:
        with np.errstate(divide='ignore', invalid='ignore'):
            data = np.log10(data)

    return data


# ============================================================
# 1. FILE DISCOVERY & STREAMING HISTOGRAM BUILDER
# ============================================================

def resolve_file_paths(target_path: Union[str, Path]) -> List[str]:
    path = Path(target_path)
    if path.is_file():
        return [str(path)]
    elif path.is_dir():
        return [str(p) for p in path.rglob("*.parquet")]
    else:
        raise ValueError(f"Path does not exist: {target_path}")


def build_heatmap_from_parquet(
    target_path: Union[str, Path],
    x_cfg: VariableConfig,
    y_cfg: VariableConfig,
    bins: int = 100,
    batch_size: int = 100_000
):
    """
    Streams Parquet file(s) batch-by-batch and accumulates 
    a 2D histogram for any dynamic X and Y configuration.
    """
    file_list = resolve_file_paths(target_path)
    print(f"Found {len(file_list)} Parquet file(s) to process.")

    x_edges = np.linspace(x_cfg.range[0], x_cfg.range[1], bins + 1)
    y_edges = np.linspace(y_cfg.range[0], y_cfg.range[1], bins + 1)
    hist = np.zeros((bins, bins), dtype=np.int64)

    required_cols = list({x_cfg.column, y_cfg.column})

    for idx, file_path in enumerate(file_list, 1):
        print(f"[{idx}/{len(file_list)}] Processing: {file_path}")
        try:
            parquet_file = pq.ParquetFile(file_path)

            for batch in parquet_file.iter_batches(batch_size=batch_size, columns=required_cols):
                x_vals = extract_variable_data(batch, x_cfg)
                y_vals = extract_variable_data(batch, y_cfg)

                # Filter out invalid entries (NaNs, Infs, non-positive values if log10)
                valid = np.isfinite(x_vals) & np.isfinite(y_vals)
                if not np.any(valid):
                    continue

                x = x_vals[valid]
                y = y_vals[valid]

                # Accumulate histogram
                batch_hist, _, _ = np.histogram2d(x, y, bins=[x_edges, y_edges])
                hist += batch_hist.astype(np.int64)

        except Exception as e:
            print(f"Skipping file {file_path} due to error: {e}")

    return hist, x_edges, y_edges


# ============================================================
# 2. HEATMAP PLOTTER
# ============================================================

def plot_2d_heatmap_from_hist(
    hist: np.ndarray,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
    x_cfg: VariableConfig,
    y_cfg: VariableConfig,
    plot_cfg: PlotConfig,
    cmin: int = 1
):
    os.makedirs(plot_cfg.outdir, exist_ok=True)
    plt.figure(figsize=(8, 6))

    hist_masked = np.ma.masked_less(hist, cmin)

    cmap = plt.cm.jet.copy()
    cmap.set_bad(color="white")

    plt.imshow(
        hist_masked.T,
        origin="lower",
        aspect="auto",
        extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
        cmap=cmap,
        norm=mcolors.LogNorm() if np.max(hist) > 1000 else mcolors.Normalize(),
    )

    plt.colorbar(label="Number of events")

    if plot_cfg.diagonal_line:
        common_min = min(x_edges[0], y_edges[0])
        common_max = max(x_edges[-1], y_edges[-1])
        plt.plot(
            [common_min, common_max],
            [common_min, common_max],
            color="red",
            alpha=0.8,
            linewidth=2,
        )

    plt.xlabel(x_cfg.label, fontsize=14)
    plt.ylabel(y_cfg.label, fontsize=14)
    plt.title(plot_cfg.title)
    plt.grid(alpha=0.3)

    output_file = os.path.join(plot_cfg.outdir, plot_cfg.filename)
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to: {output_file}")
    plt.show()
    plt.close()


# ============================================================
# RUN PIPELINE
# ============================================================

if __name__ == "__main__":

    TARGET_PATH = "data_folder/"

    # --- AVAILABLE `kind` OPTIONS: "value", "length", "sum" ---

    var_x = VariableConfig(
        column="mc_truth",
        field="initial_state_energy",
        kind="value",
        log10=True,
        range=(1, 6),
        label="log10(E_initial [GeV])"
    )

    # Example Y Variable using `kind="sum"` to sum values in a list field
    var_y = VariableConfig(
        column="photons",
        field="energy",        # Summing elements in photons.energy
        kind="sum",            # Calculates row-wise sum of list
        log10=True,            # Option to take log10 of the resulting sum
        range=(0, 7),
        label="log10(Total Photon Energy [GeV])"
    )

    plot_config = PlotConfig(
        title="Initial Energy vs Total Deposited Energy",
        outdir=".",
        filename="energy_sum_plot.png",
        diagonal_line=False
    )

    hist, x_edges, y_edges = build_heatmap_from_parquet(
        TARGET_PATH,
        x_cfg=var_x,
        y_cfg=var_y,
        bins=100,
        batch_size=100_000,
    )

    plot_2d_heatmap_from_hist(
        hist,
        x_edges,
        y_edges,
        x_cfg=var_x,
        y_cfg=var_y,
        plot_cfg=plot_config,
        cmin=1
    )
