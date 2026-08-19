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

from experiments.measurements import measurement_columns
from experiments.naming import instance_groups

# The one CSV-specific column (row identity, not a measurement) - added
# in front of the shared measurement_columns() mapping.
_IDENTITY_COLUMN = {"algorithm_label": "algorithm"}


def write_instance_csvs(summary: pd.DataFrame, plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    columns = {**_IDENTITY_COLUMN, **measurement_columns(summary)}
    for instance, group in instance_groups(summary):
        out = group[list(columns)].rename(columns=columns)
        out.to_csv(plot_dir / f"{instance.stem}.csv", index=False)
