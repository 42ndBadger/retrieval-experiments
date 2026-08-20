"""Step 4: the pipeline's sole output beyond raw data/results - one
consolidated JSON file with everything the TOML config specifies (n,
repetitions, algorithms + their params, distribution families + their
swept variants and entropy) plus all the aggregated measurements/std-devs
- nested so a hand-written Typst script (see typst/) can walk it directly
instead of re-joining rows.

Schema:

    {
      "n": int, "construction-reps": int, "query-reps": int,
      "distrs": [{"name": str, "sub": [
        {"params": {...}, "analytical_entropy": float, "empirical_entropy": float}
      ]}],
      "algs": [{
        "name": str,            # per-config display label
        "params": {...},        # algorithm config params
        "measurement_keys": [str],  # keys actually present below
        "distrs": [{"name": str, "variants": [
          {"params": {...}, "measurements": {key: float | null}}
        ]}]
      }]
    }

See experiments/example_summary.json for a worked example.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.config import DatasetSpec, ExperimentConfig
from experiments.entropy import empirical_entropy_bits, entropy_bits
from experiments.measurements import measurement_columns
from experiments.naming import config_label, dataset_path, param_label_and_key, variant_params


def _json_safe(value):
    """NaN (missing/undefined, e.g. std with <2 repetitions) -> JSON
    `null` rather than Python's `json` module's non-standard bare `NaN`
    token; numpy scalars (from pandas) -> native Python types."""
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def _top_level_distrs(specs: list[DatasetSpec], config: ExperimentConfig) -> list[dict]:
    by_type: dict[str, list[DatasetSpec]] = {}
    for spec in specs:
        by_type.setdefault(spec.type, []).append(spec)

    result = []
    for dist, family_specs in by_type.items():
        ordered = sorted(family_specs, key=lambda s: param_label_and_key(dist, s.params)[1])
        sub = [
            {
                "params": spec.params,
                "analytical_entropy": entropy_bits(spec),
                "empirical_entropy": empirical_entropy_bits(dataset_path(spec, config.data_dir)),
            }
            for spec in ordered
        ]
        result.append({"name": dist, "sub": sub})
    return result


def _algorithm_entry(algo_spec, config: ExperimentConfig, summary: pd.DataFrame) -> dict:
    subset = summary[summary["algo_spec"].apply(lambda s: s is algo_spec)]
    # A measurement key belongs to this algorithm only if at least one of
    # its variants has a real (non-NaN) value for it - e.g. Caramel never
    # gets "consensus_bits" at all, rather than carrying it as always-null
    # (contrast a *_std that's null only because reps==1 for one variant -
    # that key is still "applicable", just undefined for that variant).
    columns = {col: key for col, key in measurement_columns(summary).items() if subset[col].notna().any()}

    distrs: dict[str, list[dict]] = {}
    for _, row in subset.iterrows():
        variant = {
            "params": {k: _json_safe(v) for k, v in variant_params(row["distribution"], row).items()},
            "measurements": {key: _json_safe(row[col]) for col, key in columns.items()},
        }
        distrs.setdefault(row["distribution"], []).append((row, variant))

    distrs_out = [
        {
            "name": dist,
            "variants": [v for _, v in sorted(entries, key=lambda e: param_label_and_key(dist, e[0])[1])],
        }
        for dist, entries in distrs.items()
    ]

    return {
        "name": config_label(algo_spec, config.algorithms),
        "params": algo_spec.params,
        "measurement_keys": sorted(columns.values()),
        "distrs": distrs_out,
    }


def write_summary_json(
    specs: list[DatasetSpec], summary: pd.DataFrame, config: ExperimentConfig, plot_dir: Path
) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "n": config.n,
        "construction-reps": config.construction_repetitions,
        "query-reps": config.query_repetitions,
        "distrs": _top_level_distrs(specs, config),
        "algs": [_algorithm_entry(algo_spec, config, summary) for algo_spec in config.algorithms],
    }
    with (plot_dir / "summary.json").open("w") as f:
        json.dump(data, f, indent=2)
