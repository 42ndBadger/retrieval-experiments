"""Single source of truth for dataset/result file naming, shared by
datagen, bench, and results so they always agree on paths. Also owns the
human-readable "swept parameter" label used by plotting and tables, so both
stay consistent with each other."""

from __future__ import annotations

from dataclasses import dataclass
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
    used for the one-legend-entry-per-algorithm in plots, and as
    config_label's fallback for a name's sole config."""
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


def differing_params(spec: AlgorithmSpec, siblings: list[AlgorithmSpec]) -> dict:
    """Params whose value differs across the sibling configs sharing
    `spec.name` (comparing every key present in any sibling's params).
    Empty if `spec.name` has no siblings."""
    family = [s for s in siblings if s.name == spec.name]
    if len(family) <= 1:
        return {}
    all_keys = {k for s in family for k in s.params}
    return {
        k: spec.params.get(k)
        for k in all_keys
        if len({s.params.get(k) for s in family}) > 1
    }


def config_row_label(spec: AlgorithmSpec, siblings: list[AlgorithmSpec]) -> str:
    """`config_label` plus a parenthetical of whichever param(s) actually
    differ between sibling configs, e.g.
    "Consensus A (max_difficulty_of_task=8)" - used for table row labels.
    Plot point annotations use plain `config_label` instead (see
    plotting.py)."""
    label = config_label(spec, siblings)
    diff = differing_params(spec, siblings)
    if not diff:
        return label
    parts = ", ".join(f"{k}={v}" for k, v in sorted(diff.items()))
    return f"{label} ({parts})"


@dataclass
class DatasetInstance:
    """One (distribution, swept-parameter-value) dataset instance - the
    unit both the summary table's columns and the per-instance tradeoff
    plots are built around."""

    distribution: str
    parameters: str  # human-readable label, e.g. "bound=3"
    sort_key: tuple
    stem: str  # filename-safe, e.g. "uniform_bound3"


def variant_params(distribution: str, row: pd.Series) -> dict:
    """The raw swept parameter value(s) for a summary row (e.g.
    `{"p": 0.1}`), as opposed to `param_label_and_key`'s formatted
    `"p=0.1"` string - used where a caller wants the values themselves
    rather than a display label (e.g. json_export.py's per-variant
    `params`)."""
    return {k: row[k] for k in ("p", "bound") if k in row.index and pd.notna(row[k])}


def _instance_stem(distribution: str, row: pd.Series) -> str:
    params = variant_params(distribution, row)
    # Reuses _params_suffix's param-name knowledge via a throwaway
    # DatasetSpec; `n` is irrelevant here, _params_suffix doesn't use it.
    return f"{distribution}{_params_suffix(DatasetSpec(type=distribution, params=params, n=0))}"


def dataset_instances(summary: pd.DataFrame) -> list[DatasetInstance]:
    """Enumerate the distinct dataset instances present in `summary`, in
    the order tables/plots should show them: distributions in first-seen
    order, then low-to-high by swept value within each. Single source of
    truth so the table and the per-instance plots agree on both ordering
    and labeling (factored out of what was inline in
    tables.py::build_table)."""
    labels_and_keys = summary.apply(lambda r: param_label_and_key(r["distribution"], r), axis=1)
    df = summary.copy()
    df["_parameters"] = [lk[0] for lk in labels_and_keys]
    df["_sort_key"] = [lk[1] for lk in labels_and_keys]

    dist_order = list(dict.fromkeys(summary["distribution"]))
    unique = (
        df.drop_duplicates(subset=["distribution", "_parameters"])
        .sort_values(by="_sort_key", kind="stable")
        .sort_values(by="distribution", key=lambda col: col.map(dist_order.index), kind="stable")
    )

    return [
        DatasetInstance(
            distribution=row["distribution"],
            parameters=row["_parameters"],
            sort_key=row["_sort_key"],
            stem=_instance_stem(row["distribution"], row),
        )
        for _, row in unique.iterrows()
    ]


def instance_groups(summary: pd.DataFrame) -> list[tuple[DatasetInstance, pd.DataFrame]]:
    """Pair each `dataset_instances()` entry with the subset of `summary`
    rows belonging to it - the per-instance filter shared by plotting.py
    and csv_export.py so they don't each reimplement it."""
    labels_and_keys = summary.apply(lambda r: param_label_and_key(r["distribution"], r), axis=1)
    df = summary.copy()
    df["_parameters"] = [lk[0] for lk in labels_and_keys]
    return [
        (instance, df[(df["distribution"] == instance.distribution) & (df["_parameters"] == instance.parameters)])
        for instance in dataset_instances(summary)
    ]


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
