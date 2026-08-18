"""Single source of truth for dataset/result file naming, shared by
datagen, bench, and results so they always agree on paths. Also owns the
human-readable "swept parameter" label used by plotting and tables, so both
stay consistent with each other."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from experiments.config import AlgorithmSpec, DatasetSpec


def param_label_and_key(distribution: str, row: pd.Series) -> tuple[str, tuple]:
    """Human-readable label for a summary row's swept parameter(s), plus a
    sort key so callers can order low-to-high rather than alphabetically."""
    if distribution == "uniform":
        return f"bound={row['bound']:g}", (row["bound"],)
    if distribution == "bernoulli":
        return f"p={row['p']:g}", (row["p"],)
    if distribution == "truncated_geometric":
        return f"p={row['p']:g}, bound={row['bound']:g}", (row["p"], row["bound"])
    raise ValueError(f"unknown distribution type {distribution!r}")


def _algo_suffix(spec: AlgorithmSpec) -> str:
    """Filename-safe suffix encoding the algorithm name and its params."""
    if not spec.params:
        return spec.name
    parts = [f"{k}={v}" for k, v in sorted(spec.params.items())]
    return f"{spec.name}_{'_'.join(parts)}"


def _params_suffix(spec: DatasetSpec) -> str:
    parts = []
    if "p" in spec.params:
        parts.append(f"p{spec.params['p']}")
    if "bound" in spec.params:
        parts.append(f"bound{spec.params['bound']}")
    return "".join(f"_{part}" for part in parts)


def dataset_stem(spec: DatasetSpec) -> str:
    return f"{spec.type}_n{spec.n}{_params_suffix(spec)}"


def dataset_path(spec: DatasetSpec, data_dir: Path) -> Path:
    return data_dir / f"{dataset_stem(spec)}.kv"


def result_base_path(spec: DatasetSpec, algo_spec: AlgorithmSpec, results_dir: Path) -> Path:
    return results_dir / f"{_algo_suffix(algo_spec)}_{dataset_stem(spec)}"
