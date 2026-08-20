#!/usr/bin/env bash
# Runs the experiment pipeline inside the "retrieval-experiments" spack
# environment. See README.md for how to create that environment.
#
# Usage: ./run_with_spack.sh <config> [extra experiments.run args...]
#
#   <config> is either a name under config/ (e.g. "small" resolves to
#   config/small_config.toml) or a path to any .toml config file.
#
# Examples:
#   ./run_with_spack.sh small
#   ./run_with_spack.sh paper --skip-gen
#   ./run_with_spack.sh config/example_config.toml --force-bench
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <config> [extra experiments.run args...]" >&2
  exit 1
fi

name="$1"; shift
config="$name"
if [[ ! -f "$config" ]]; then
  config="config/${name}_config.toml"
fi
if [[ ! -f "$config" ]]; then
  echo "error: no such config: '$name' (looked for it as a path and as config/${name}_config.toml)" >&2
  exit 1
fi

spack env activate retrieval-experiments
python -m experiments.run "$config" "$@"
