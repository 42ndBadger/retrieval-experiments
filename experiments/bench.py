"""Step 3 of the pipeline: run construction+query benchmarks for every
(dataset, algorithm) pair."""

from __future__ import annotations

from experiments import cli_runner
from experiments.config import DatasetSpec, ExperimentConfig
from experiments.naming import dataset_path, result_base_path


def run_benchmarks(
    specs: list[DatasetSpec], config: ExperimentConfig, force: bool = False
) -> None:
    config.results_dir.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        input_path = dataset_path(spec, config.data_dir)
        for algo_spec in config.algorithms:
            base = result_base_path(spec, algo_spec, config.results_dir)
            construction_out = base.with_name(base.name + ".construction.json")
            query_out = base.with_name(base.name + ".query.json")
            if not force and construction_out.exists() and query_out.exists():
                print(f"[bench] skip (exists): {base.name}")
                continue
            print(f"[bench] running: {base.name}")
            cli_runner.run_bench(
                algo_spec.name,
                input_path,
                base,
                config.construction_repetitions,
                config.query_repetitions,
                algo_params=algo_spec.params,
            )
