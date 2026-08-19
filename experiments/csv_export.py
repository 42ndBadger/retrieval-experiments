"""Step 4 (part 4): per-dataset-instance CSV export of raw timing data.

One CSV per dataset instance (naming.instance_groups - the same
(distribution, swept-parameter-value) grouping plotting.py and tables.py
use), with one row per algorithm config: its display label, mean
construction/query time per key, mean space usage (bits/key, both as an
absolute and as overhead relative to the distribution's entropy), and the
sample standard deviation of each (over the benchmark repetitions). Meant
as plain data for plotting natively (e.g. directly in Typst) rather than
through matplotlib.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from experiments.naming import instance_groups

# summary.py column -> output CSV column, in output column order.
_COLUMNS = {
    "algorithm_label": "algorithm",
    "construction_time_per_key_ns": "constr_time",
    "construction_time_per_key_std_ns": "constr_std",
    "query_time_per_key_ns": "query_time",
    "query_time_per_key_std_ns": "query_std",
    "bits_per_key": "space_bits",
    "bits_per_key_std": "space_bits_std",
    "relative_overhead": "rel_space_overhead",
    "relative_overhead_std": "rel_space_overhead_std",
}


def write_instance_csvs(summary: pd.DataFrame, plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    for instance, group in instance_groups(summary):
        out = group[list(_COLUMNS)].rename(columns=_COLUMNS)
        out.to_csv(plot_dir / f"{instance.stem}.csv", index=False)
