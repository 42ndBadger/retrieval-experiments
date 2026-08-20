"""Single source of truth for dataset/result file naming, shared by
datagen, bench, and results so they always agree on paths. Also owns the
human-readable "swept parameter" label and per-config display label used
by results.py/json_export.py, so the summary.json output stays consistent
with itself."""

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


# Friendly default label for an algorithm's *sole* config (no explicit
# display_name needed in that case - see config_label). Falls back to the
# raw algorithm name for anything not listed here.
_DEFAULT_ALGO_DISPLAY_NAMES = {
    "lsf": "Ribbon VLR",
    "caramel": "Caramel",
    "consensus": "Consensus",
}


def algorithm_family_label(name: str) -> str:
    """Friendly label for an algorithm *family* as a whole (e.g. "Ribbon
    VLR" for "lsf"), independent of any particular config's display_name -
    used as config_label's fallback for a name's sole config."""
    return _DEFAULT_ALGO_DISPLAY_NAMES.get(name, name)


def config_label(spec: AlgorithmSpec, siblings: list[AlgorithmSpec]) -> str:
    """Human-readable label for one algorithm config: its explicit
    `display_name` if set, else a friendly per-algorithm default. Only
    valid when `spec` is the sole config using `spec.name` among
    `siblings` if `display_name` is unset - config.py's
    `_validate_display_names` guarantees any ambiguous group (>1 config
    sharing a name) all have `display_name` set, so this never has to
    guess between siblings."""
    if spec.display_name:
        return spec.display_name
    return algorithm_family_label(spec.name)


def variant_params(distribution: str, row: pd.Series) -> dict:
    """The raw swept parameter value(s) for a summary row (e.g.
    `{"p": 0.1}`), as opposed to `param_label_and_key`'s formatted
    `"p=0.1"` string - used where a caller wants the values themselves
    rather than a display label (e.g. json_export.py's per-variant
    `params`)."""
    return {k: row[k] for k in ("p", "bound") if k in row.index and pd.notna(row[k])}


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
