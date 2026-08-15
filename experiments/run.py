"""Pipeline entry point. Run from the repository root:

    python -m experiments.run experiments/example_config.toml
"""

from __future__ import annotations

import argparse

from experiments.bench import run_benchmarks
from experiments.config import expand_datasets, load_config
from experiments.datagen import ensure_datasets
from experiments.plotting import plot_overhead_vs_time
from experiments.results import build_summary
from experiments.tables import write_tables


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="path to the experiment TOML config")
    parser.add_argument(
        "--skip-gen", action="store_true", help="assume all datasets already exist"
    )
    parser.add_argument(
        "--skip-bench", action="store_true", help="assume all results already exist"
    )
    parser.add_argument(
        "--skip-plot", action="store_true", help="don't produce PDF plots"
    )
    parser.add_argument(
        "--force-bench",
        action="store_true",
        help="re-run benchmarks even if result files already exist",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    specs = expand_datasets(config)
    print(f"{len(specs)} dataset(s) across {len(config.algorithms)} algorithm(s)")

    if not args.skip_gen:
        ensure_datasets(specs, config)
    if not args.skip_bench:
        run_benchmarks(specs, config, force=args.force_bench)
    if not args.skip_plot:
        summary = build_summary(specs, config)
        plot_overhead_vs_time(summary, config.algorithms, config.plot_dir)
        write_tables(summary, config.algorithms, config.plot_dir)
        print(f"plots and tables written to {config.plot_dir}")


if __name__ == "__main__":
    main()
