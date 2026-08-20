"""Step 4 (part 1): parse benchmark result files and build a tidy summary
table with the derived relative-overhead metric (`relative_overhead`,
against **empirical** entropy - see CLAUDE.md's "Design decisions" note;
the analytical value is computed separately, only in json_export.py's
`distrs[].sub[]`, not used here)."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from experiments.config import DatasetSpec, ExperimentConfig
from experiments.entropy import empirical_entropy_bits
from experiments.naming import config_label, dataset_path, result_base_path


@dataclass
class Measurement:
    header: dict
    rows: pd.DataFrame


def _std(series: pd.Series) -> float:
    """Sample standard deviation over benchmark repetitions (Bessel's
    correction, ddof=1). NaN with fewer than 2 repetitions."""
    if len(series) < 2:
        return float("nan")
    return series.std(ddof=1)


def _extra_bit_fields(rows: pd.DataFrame, n: int) -> dict[str, float]:
    """Reduce the per-repetition JSON `extra_json` column to per-key mean
    and std for every bit-count field it carries (e.g. consensus's
    `consensus_bits`/`insertion_bits` breakdown of its total size, from
    ConsensusExtra in src/instances.rs - `null`/absent for algorithms with
    no extra data). Field names are discovered dynamically (only those
    ending in `_bits`) so this doesn't need updating if the set of
    algorithms reporting extra data changes; result keys are named
    `<field>_per_key`/`<field>_per_key_std`, the same per-key + mean/std
    pairing as the top-level bits_per_key.

    Older result files predating this field lack the `extra_json` column
    entirely - returns no fields in that case rather than erroring, so
    stale results can still be summarized (just without the breakdown)."""
    if "extra_json" not in rows.columns:
        return {}
    # pandas' read_csv parses the bare `null` token (algorithms with no
    # extra data serialize to JSON `null`) as a missing value - i.e. NaN,
    # not the string "null" - so json.loads only sees an actual string
    # for rows that have real extra data.
    parsed = [json.loads(v) if isinstance(v, str) else None for v in rows["extra_json"]]
    keys = {k for p in parsed if isinstance(p, dict) for k in p if k.endswith("_bits")}
    fields: dict[str, float] = {}
    for key in keys:
        values = pd.Series([p.get(key, float("nan")) if isinstance(p, dict) else float("nan") for p in parsed])
        fields[f"{key}_per_key"] = values.mean() / n
        fields[f"{key}_per_key_std"] = _std(values) / n
    return fields


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
    sibling configs - used to group them as one family in json_export.py.
    `algorithm_label` is the human-readable per-config display label (see
    naming.py::config_label). `algo_spec` carries the exact AlgorithmSpec
    so downstream code (json_export.py::_algorithm_entry) can identify a
    row's sibling group precisely, without re-matching on label strings.
    """
    records = []
    for spec in specs:
        # Empirical, not analytical - see CLAUDE.md's "Design decisions"
        # note. Read once per spec (not per algorithm config below), same
        # as the old analytical call this replaced.
        entropy = empirical_entropy_bits(dataset_path(spec, config.data_dir))
        for algo_spec in config.algorithms:
            base = result_base_path(spec, algo_spec, config.results_dir)
            construction = load_result(base.with_name(base.name + ".construction.json"))
            query = load_result(base.with_name(base.name + ".query.json"))

            mean_size_bytes = construction.rows["size"].mean()
            bits_per_key = mean_size_bytes * 8 / spec.n
            relative_overhead = (bits_per_key - entropy) / entropy
            mean_construction_time_ns = construction.rows["time_ns"].mean()
            mean_query_time_ns = query.rows["query_time_ns"].mean()
            # Std scales linearly with the same /n or verbatim-copy
            # treatment as its mean above (see the per-key comment below),
            # so it's derived the same way here.
            construction_time_std_ns = _std(construction.rows["time_ns"])
            query_time_std_ns = _std(query.rows["query_time_ns"])
            # bits_per_key is a linear rescaling of size (*8/n) and
            # relative_overhead a further linear rescaling of bits_per_key
            # (-entropy, /entropy, both constants for this spec), so their
            # standard deviations propagate through the same two factors.
            bits_per_key_std = _std(construction.rows["size"]) * 8 / spec.n
            relative_overhead_std = bits_per_key_std / entropy

            record = {
                "distribution": spec.type,
                **spec.params,
                "n": spec.n,
                "empirical_entropy_bits": entropy,
                "algorithm": algo_spec.name,
                "algo_spec": algo_spec,
                "algorithm_label": config_label(algo_spec, config.algorithms),
                "mean_construction_time_ns": mean_construction_time_ns,
                "mean_query_time_ns": mean_query_time_ns,
                "mean_size_bytes": mean_size_bytes,
                "bits_per_key": bits_per_key,
                "relative_overhead": relative_overhead,
                "bits_per_key_std": bits_per_key_std,
                "relative_overhead_std": relative_overhead_std,
                # Final per-key metrics, shared verbatim by json_export.py
                # (construction is measured as one total per
                # structure-build, hence the /n here; query_benchmark in
                # benchmark.rs already divides by the per-iteration key
                # count).
                "construction_time_per_key_ns": mean_construction_time_ns / spec.n,
                "query_time_per_key_ns": mean_query_time_ns,
                "construction_time_per_key_std_ns": construction_time_std_ns / spec.n,
                "query_time_per_key_std_ns": query_time_std_ns,
                "space_overhead_pct": relative_overhead * 100,
            }
            # Algorithm-specific space breakdown (e.g. consensus's
            # consensus_bits/insertion_bits) - present only for algorithms
            # that report it; missing keys become NaN across the rest of
            # the DataFrame once all records are assembled.
            record.update(_extra_bit_fields(construction.rows, spec.n))
            records.append(record)
    return pd.DataFrame.from_records(records)
