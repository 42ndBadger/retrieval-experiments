"""Step 4 (part 1): parse benchmark result files and build a tidy summary
table with the derived relative-overhead metric."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from experiments.config import DatasetSpec, ExperimentConfig
from experiments.entropy import entropy_bits
from experiments.naming import result_base_path


@dataclass
class Measurement:
    header: dict
    rows: pd.DataFrame


def load_result(path: Path) -> Measurement:
    """Parse a single `<base>.construction.json` / `<base>.query.json` file:
    a JSON header line followed by a CSV body (see measurement_writer.rs)."""
    text = path.read_text()
    header_line, _, csv_body = text.partition("\n")
    header = json.loads(header_line)
    rows = pd.read_csv(io.StringIO(csv_body))
    return Measurement(header=header, rows=rows)


def algo_label(algo_spec) -> str:
    """Human-readable algorithm label including params for display in plots/tables."""
    if not algo_spec.params:
        return algo_spec.name
    parts = [f"{k}={v}" for k, v in sorted(algo_spec.params.items())]
    return f"{algo_spec.name} [{', '.join(parts)}]"


def build_summary(specs: list[DatasetSpec], config: ExperimentConfig) -> pd.DataFrame:
    """One row per (dataset spec, algorithm): distribution params, entropy,
    mean construction/query time, mean size, and relative overhead."""
    records = []
    for spec in specs:
        entropy = entropy_bits(spec)
        for algo_spec in config.algorithms:
            base = result_base_path(spec, algo_spec, config.results_dir)
            construction = load_result(base.with_name(base.name + ".construction.json"))
            query = load_result(base.with_name(base.name + ".query.json"))

            mean_size_bytes = construction.rows["size"].mean()
            bits_per_key = mean_size_bytes * 8 / spec.n
            relative_overhead = (bits_per_key - entropy) / entropy

            records.append(
                {
                    "distribution": spec.type,
                    **spec.params,
                    "n": spec.n,
                    "entropy_bits": entropy,
                    "algorithm": algo_spec.name,
                    "algo_params": algo_spec.params,
                    "algorithm_label": algo_label(algo_spec),
                    "mean_construction_time_ns": construction.rows["time_ns"].mean(),
                    "mean_query_time_ns": query.rows["query_time_ns"].mean(),
                    "mean_size_bytes": mean_size_bytes,
                    "bits_per_key": bits_per_key,
                    "relative_overhead": relative_overhead,
                }
            )
    return pd.DataFrame.from_records(records)
