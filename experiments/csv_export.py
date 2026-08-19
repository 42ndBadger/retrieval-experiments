"""Step 4 (part 4): per-dataset-instance CSV export of raw timing data.

One CSV per dataset instance (naming.instance_groups - the same
(distribution, swept-parameter-value) grouping plotting.py and tables.py
use), with one row per algorithm config: its display label, mean
construction/query time per key, mean space usage (bits/key, both as an
absolute and as overhead relative to the distribution's entropy), any
algorithm-specific space breakdown (e.g. consensus's
consensus_bits/insertion_bits - NaN for algorithms that don't report
one), and the sample standard deviation of each (over the benchmark
repetitions). Meant as plain data for plotting natively (e.g. directly in
Typst) rather than through matplotlib.
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

# Suffix results.py::_extra_bit_fields uses for its per-key mean columns
# (e.g. "consensus_bits_per_key") - matched dynamically here rather than
# by hardcoded name, so a new algorithm-specific field shows up in the
# CSV without this file needing to know its name in advance.
_EXTRA_BITS_SUFFIX = "_bits_per_key"


def _extra_bit_columns(summary: pd.DataFrame) -> dict[str, str]:
    """summary.py column -> output CSV column for whichever
    algorithm-specific space-breakdown fields are present in `summary`,
    e.g. {"consensus_bits_per_key": "consensus_bits",
    "consensus_bits_per_key_std": "consensus_bits_std"}."""
    columns: dict[str, str] = {}
    for mean_col in sorted(c for c in summary.columns if c.endswith(_EXTRA_BITS_SUFFIX)):
        base = mean_col[: -len("_per_key")]  # e.g. "consensus_bits"
        columns[mean_col] = base
        std_col = f"{mean_col}_std"
        if std_col in summary.columns:
            columns[std_col] = f"{base}_std"
    return columns


def write_instance_csvs(summary: pd.DataFrame, plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    columns = {**_COLUMNS, **_extra_bit_columns(summary)}
    for instance, group in instance_groups(summary):
        out = group[list(columns)].rename(columns=columns)
        out.to_csv(plot_dir / f"{instance.stem}.csv", index=False)
