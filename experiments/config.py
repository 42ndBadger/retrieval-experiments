"""TOML config loading and dataset-sweep expansion.

Run everything from the repository root: `data_dir`/`results_dir`/
`plot_dir` in the config are resolved relative to the current working
directory (matching the existing `data/`, `results/` layout), not relative
to the config file's location.
"""

from __future__ import annotations

import itertools
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Distribution families, matching (in spirit) the Rust CLI's
# DistributionSelection enum. Keys here are the TOML `type` values; sweeping
# is done over whichever of `p` / `bound` the family accepts.
SWEEP_PARAMS = {
    "uniform": ("bound",),
    "bernoulli": ("p",),
    "truncated_geometric": ("p", "bound"),
}


@dataclass
class DistributionSweep:
    type: str
    params: dict[str, list[float | int]]

    def __post_init__(self) -> None:
        if self.type not in SWEEP_PARAMS:
            raise ValueError(
                f"unknown distribution type {self.type!r}, expected one of "
                f"{sorted(SWEEP_PARAMS)}"
            )
        expected = set(SWEEP_PARAMS[self.type])
        got = set(self.params)
        if got != expected:
            raise ValueError(
                f"distribution {self.type!r} expects sweep params "
                f"{sorted(expected)}, got {sorted(got)}"
            )


@dataclass
class DatasetSpec:
    type: str
    params: dict[str, float | int]
    n: int


@dataclass
class AlgorithmSpec:
    name: str
    params: dict[str, float | int] = field(default_factory=dict)


@dataclass
class ExperimentConfig:
    n: int
    construction_repetitions: int
    query_repetitions: int
    algorithms: list[AlgorithmSpec]
    data_dir: Path
    results_dir: Path
    plot_dir: Path
    distributions: list[DistributionSweep] = field(default_factory=list)


def load_config(path: str | Path) -> ExperimentConfig:
    path = Path(path)
    with path.open("rb") as f:
        raw = tomllib.load(f)

    experiment = raw["experiment"]
    distributions = [
        DistributionSweep(
            type=block["type"],
            params={k: v for k, v in block.items() if k != "type"},
        )
        for block in raw.get("distribution", [])
    ]

    algorithms = []
    for block in raw.get("algorithm", []):
        name = block["name"]
        params = dict(block.get("params", {}))
        algorithms.append(AlgorithmSpec(name=name, params=params))

    return ExperimentConfig(
        n=experiment["n"],
        construction_repetitions=experiment["construction_repetitions"],
        query_repetitions=experiment["query_repetitions"],
        algorithms=algorithms,
        # Resolved to absolute paths (relative to the current working
        # directory) so they stay correct even though `cli_runner` runs
        # `cargo` with cwd set to the repo root.
        data_dir=Path(experiment["data_dir"]).resolve(),
        results_dir=Path(experiment["results_dir"]).resolve(),
        plot_dir=Path(experiment["plot_dir"]).resolve(),
        distributions=distributions,
    )


def expand_datasets(config: ExperimentConfig) -> list[DatasetSpec]:
    """Cartesian-product each distribution block's sweep lists into
    individual DatasetSpecs, sharing the global `n`."""
    specs: list[DatasetSpec] = []
    for sweep in config.distributions:
        keys = sorted(sweep.params)  # deterministic order: bound, p
        value_lists = [sweep.params[k] for k in keys]
        for combo in itertools.product(*value_lists):
            params = dict(zip(keys, combo))
            specs.append(DatasetSpec(type=sweep.type, params=params, n=config.n))
    return specs
