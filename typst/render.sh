#!/usr/bin/env bash
# Renders summary.json (from `python -m experiments.run ...`) into a PDF
# report via Typst. Not part of the Python pipeline on purpose - run this
# manually, wherever Typst is installed (experiments/run.py itself doesn't
# need it, e.g. when run on a server).
#
# Usage: typst/render.sh <plot_dir> [<plot_dir> ...]
#
# Each <plot_dir> must contain a summary.json and be inside this repo
# (Typst's --root sandbox can't read files outside the given root, and we
# root at the repo so summary.typ can import its sibling files too).
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <plot_dir> [<plot_dir> ...]" >&2
  exit 1
fi

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

for plot_dir in "$@"; do
  if [[ ! -d "$plot_dir" ]]; then
    echo "error: $plot_dir is not a directory" >&2
    exit 1
  fi
  plot_dir=$(cd "$plot_dir" && pwd)

  case "$plot_dir" in
    "$repo_root"/*) rel=${plot_dir#"$repo_root"/} ;;
    *)
      echo "error: $plot_dir must be inside the repo ($repo_root)" >&2
      exit 1
      ;;
  esac

  summary_json="$plot_dir/summary.json"
  if [[ ! -f "$summary_json" ]]; then
    echo "error: $summary_json not found (run experiments.run first)" >&2
    exit 1
  fi

  out="$plot_dir/summary_report.pdf"
  typst compile --root "$repo_root" --input "summary=/$rel/summary.json" \
    "$repo_root/typst/summary.typ" "$out"
  echo "wrote $out"
done
