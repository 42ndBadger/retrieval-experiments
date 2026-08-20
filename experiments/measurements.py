"""Single source of truth for "which results.py::build_summary column is
which output measurement key" - used by json_export.py."""

from __future__ import annotations

import pandas as pd

# summary.py column -> measurement key, present for every algorithm.
BASE_COLUMNS: dict[str, str] = {
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
# output without this file needing to know its name in advance.
_EXTRA_BITS_SUFFIX = "_bits_per_key"


def extra_bit_columns(summary: pd.DataFrame) -> dict[str, str]:
    """summary.py column -> measurement key for whichever
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


def measurement_columns(summary: pd.DataFrame) -> dict[str, str]:
    """The combined summary.py column -> measurement key mapping: the
    fixed base columns plus whichever algorithm-specific extras are
    present in this run."""
    return {**BASE_COLUMNS, **extra_bit_columns(summary)}
