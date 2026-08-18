"""Thin subprocess wrappers around the Rust CLI's `gen` and `bench`
subcommands (see src/main.rs)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from experiments.config import DatasetSpec

REPO_ROOT = Path(__file__).resolve().parent.parent

# Python (underscore) distribution names -> clap's kebab-case CLI names.
_CLI_DISTRIBUTION_NAME = {
    "uniform": "uniform",
    "bernoulli": "bernoulli",
    "truncated_geometric": "truncated-geometric",
}


class CliError(RuntimeError):
    """A `cargo run` subcommand exited non-zero."""


def _run(args: list[str]) -> None:
    result = subprocess.run(
        ["cargo", "run", "--release", "--", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CliError(
            f"`cargo run --release -- {' '.join(args)}` failed "
            f"(exit {result.returncode}):\n{result.stderr}"
        )


def run_gen(spec: DatasetSpec, out_path: Path) -> None:
    args = ["gen", _CLI_DISTRIBUTION_NAME[spec.type], "-n", str(spec.n)]
    if "p" in spec.params:
        args += ["-p", str(spec.params["p"])]
    if "bound" in spec.params:
        args += ["--bound", str(spec.params["bound"])]
    args += ["-f", str(out_path)]
    _run(args)


def run_bench(
    algorithm: str,
    input_path: Path,
    out_base: Path,
    construction_repetitions: int,
    query_repetitions: int,
    algo_params: dict[str, float | int] | None = None,
) -> None:
    args = [
        "bench",
        "-a",
        algorithm,
        "-i",
        str(input_path),
        "-o",
        str(out_base),
        "-c",
        str(construction_repetitions),
        "-q",
        str(query_repetitions),
    ]
    for k, v in (algo_params or {}).items():
        args += ["--param", f"{k}={v}"]
    _run(args)
