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

# `spack env activate` requires the `spack` *shell function* (from
# spack's setup-env.sh), not just the `spack` binary on PATH. Interactive
# login shells often get the function for free (many clusters source
# setup-env.sh from a system-wide profile script), but non-interactive
# shells - notably `sbatch`/`srun --pty=false` batch jobs, which don't go
# through a login shell - don't, and silently fail with "spack: command
# not found", leaving PATH without the env's compiler/cmake/etc. Source
# setup-env.sh explicitly so this script behaves the same interactively
# and under Slurm.
if ! declare -F spack >/dev/null 2>&1; then
  for setup_env in \
    "${SPACK_ROOT:-}/share/spack/setup-env.sh" \
    /nfs/software/spack-installs/user/share/spack/setup-env.sh \
  ; do
    if [[ -n "$setup_env" && -f "$setup_env" ]]; then
      # shellcheck disable=SC1090
      source "$setup_env"
      break
    fi
  done
fi
if ! declare -F spack >/dev/null 2>&1; then
  echo "error: spack shell function not found - source spack's setup-env.sh before running this script (or set SPACK_ROOT)" >&2
  exit 1
fi

spack env activate retrieval-experiments
python -m experiments.run "$config" "$@"
