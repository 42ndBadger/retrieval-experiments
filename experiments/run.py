"""Pipeline entry point. Run from the repository root:

    python -m experiments.run config/example_config.toml

Produces data/results/summary.json only - no PDFs. Rendering summary.json
into PDFs (a table + tradeoff plots) is a separate, manual step that needs
Typst installed; see typst/render.sh.
"""

from __future__ import annotations

import argparse

from experiments.bench import run_benchmarks
from experiments.config import expand_datasets, load_config
from experiments.datagen import ensure_datasets
from experiments.json_export import write_summary_json
from experiments.results import build_summary


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
        "--skip-summary", action="store_true", help="don't (re)write summary.json"
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
    if not args.skip_summary:
        summary = build_summary(specs, config)
        write_summary_json(specs, summary, config, config.plot_dir)
        print(f"summary.json written to {config.plot_dir}")


if __name__ == "__main__":
    main()
