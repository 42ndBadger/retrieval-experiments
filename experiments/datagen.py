"""Step 2 of the pipeline: generate any datasets that don't exist yet."""

from __future__ import annotations

from experiments import cli_runner
from experiments.config import DatasetSpec, ExperimentConfig
from experiments.naming import dataset_path


def ensure_datasets(specs: list[DatasetSpec], config: ExperimentConfig) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        path = dataset_path(spec, config.data_dir)
        if path.exists():
            print(f"[gen] skip (exists): {path.name}")
            continue
        print(f"[gen] generating: {path.name}")
        cli_runner.run_gen(spec, path)
