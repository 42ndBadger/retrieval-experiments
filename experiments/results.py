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
from experiments.naming import config_label, result_base_path


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


def build_summary(specs: list[DatasetSpec], config: ExperimentConfig) -> pd.DataFrame:
    """One row per (dataset spec, algorithm config): distribution params,
    entropy, mean construction/query time, mean size, and relative
    overhead.

    `algorithm` is the raw algorithm name (e.g. "consensus"), shared by
    sibling configs - used to group them as one family in plots/tables.
    `algorithm_label` is the human-readable per-config display label (see
    naming.py::config_label). `algo_spec` carries the exact AlgorithmSpec
    so downstream code (naming.differing_params/config_row_label) can
    identify a row's sibling group precisely, without re-matching on
    label strings.
    """
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
            mean_construction_time_ns = construction.rows["time_ns"].mean()
            mean_query_time_ns = query.rows["query_time_ns"].mean()

            records.append(
                {
                    "distribution": spec.type,
                    **spec.params,
                    "n": spec.n,
                    "entropy_bits": entropy,
                    "algorithm": algo_spec.name,
                    "algo_spec": algo_spec,
                    "algorithm_label": config_label(algo_spec, config.algorithms),
                    "mean_construction_time_ns": mean_construction_time_ns,
                    "mean_query_time_ns": mean_query_time_ns,
                    "mean_size_bytes": mean_size_bytes,
                    "bits_per_key": bits_per_key,
                    "relative_overhead": relative_overhead,
                    # Final per-key metrics, shared verbatim by tables.py
                    # and plotting.py so they can't disagree (construction
                    # is measured as one total per structure-build, hence
                    # the /n here; query_benchmark in benchmark.rs already
                    # divides by the per-iteration key count).
                    "construction_time_per_key_ns": mean_construction_time_ns / spec.n,
                    "query_time_per_key_ns": mean_query_time_ns,
                    "space_overhead_pct": relative_overhead * 100,
                }
            )
    return pd.DataFrame.from_records(records)
