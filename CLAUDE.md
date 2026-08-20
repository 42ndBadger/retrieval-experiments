# Instructions

I want python scripts that handle the whole experiments. On a high level that includes
1. reading a toml config specifing a list of distributions for test data, the
   algorithms, number of repetitions of construction and query
2. generates data of the required distributions into a data folder (if they
   weren't allready generated) using the `gen` command of the rust cli
3. runing the benchmarks and saving the result to a results folder using `bench`
4. Generating pdf plots into a plot folder

## Plots
- Tradeoff plots for relative overhead over entropy vs {construction, query} time

## Framework
- Split into multiple python files
- Use python's matplot lib

# AI Agent context

Here you may save some context where you left off and explain the structure of
the project and other noteworthy learnings and observations.  You can also list
tasks done and to be done here.

## Design decisions (confirmed with user)
- Entropy in the "relative overhead over entropy" metric
  (`rel_space_overhead`/`relative_overhead`, computed in
  `results.py::build_summary`) is now the **empirical** Shannon entropy
  - measured from the actual generated `.kv` file's value distribution
  (`entropy.py::empirical_entropy_bits`) - as of a second revision on the
  json-refactor branch. This reverses the immediately-preceding decision
  below (which itself only reversed the *original* decision to compute
  analytical only). Analytical entropy (`entropy.py::entropy_bits`,
  closed-form from p/bound) is still computed and exposed separately in
  the JSON export (`distrs[].sub[].analytical_entropy`) for comparison,
  it's just no longer what the overhead metric is measured against.
- Each distribution family (uniform, bernoulli, truncated-geometric) is
  **swept** over a list of p/bound values in the TOML config. Originally
  this meant a single tradeoff plot per family with a curve across entropy
  values; as of the "Named algorithm configs" restructure (commit
  `e25582c`) that's no longer how the plots are organized - see Status
  below for the current per-instance layout.
- "Relative overhead over entropy" is read as one derived metric,
  `(bits_per_key - entropy) / entropy`, plotted against time (not entropy
  as its own axis) — this was the agent's interpretation of an ambiguous
  phrase, not explicitly confirmed by the user. Revisit if it turns out to
  be wrong.

## Status
Implemented (2026-08-13, extended 2026-08-15, restructured 2026-08-1x in
commit `e25582c` "Named algorithm configs + restructured summary
table/plots", **split Python/Typst 2026-08-20**): the Python pipeline
lives in `experiments/` (`config.py`, `entropy.py`, `naming.py`,
`cli_runner.py`, `datagen.py`, `bench.py`, `results.py`, `measurements.py`,
`json_export.py`, `run.py`), with example configs
`experiments/example_config.toml`, `experiments/small_config.toml`,
`experiments/paper_config.toml`. Run from the repo root:

    cargo build --release   # once, so `cargo run --release --` is fast
    python -m experiments.run experiments/example_config.toml

**As of 2026-08-20, `run.py` only writes `<plot_dir>/summary.json`** - no
PDFs, no CSVs, no matplotlib dependency. This is so the data-gen/benchmark
step can run on a server with no Typst installed. `plotting.py`,
`tables.py`, and `csv_export.py` (and the `naming.py` helpers that only
existed for them - `dataset_instances`/`instance_groups`/
`config_row_label`/`differing_params`/`DatasetInstance`) were deleted;
`--skip-plot` became `--skip-summary`.

Rendering `summary.json` into PDFs is now a **separate, manual step** in
`typst/` (not invoked by `run.py`):
- `typst/style.typ`: minimal shared prelude - just re-exports `strfmt`
  (from `@preview/oxifmt`) and a `colors` dict (`lightgray`/`yellow`),
  the only two things `comparison_table.typ` actually used from the old
  `../style.typ` import, which was never committed to this repo and had
  to be reconstructed from usage.
- `typst/comparison_table.typ` (`comp-table(data)`) and
  `typst/tradeoff_plots.typ` (`tradeoff-plots(summary, ..)`) are the two
  content generators, each taking the parsed `summary.json` as a
  parameter (fixed by the user from an earlier WIP state where
  `comp-table` ignored its parameter and hardcoded reading
  `example_summary.json` instead).
- `typst/summary.typ` is the actual compile entry point: loads
  `json(sys.inputs.at("summary"))` and calls both generators into one
  report (table, then a page break, then the tradeoff plots).
- `typst/render.sh <plot_dir> [<plot_dir> ...]`: thin bash wrapper - for
  each `plot_dir` (must be inside the repo, containing a `summary.json`),
  runs `typst compile --root <repo> --input summary=/<rel>/summary.json
  typst/summary.typ <plot_dir>/summary_report.pdf`. Requires `typst` on
  PATH; run it locally/wherever Typst is installed.

`naming.py::param_label_and_key` remains the shared source of truth for
the human-readable swept-parameter label (used by `json_export.py` and,
via `variant_params`, per-variant JSON keys). `naming.py::config_label`
handles per-config display names (`display_name` in the TOML, required
when multiple configs share an algorithm name).

Verified end-to-end 2026-08-15 (before the restructure) with a small
smoke config. The `run.py` → `summary.json`-only path was smoke-tested
2026-08-20 against the `example` config. The Typst render path
(`render.sh`/`summary.typ`) has *not* been verified end-to-end - it
depends on the user's own in-progress fix to `comp-table`/
`tradeoff-plots`'s summary-json plumbing, done concurrently with this
split. `data_dir`/`results_dir`/`plot_dir` resolve relative to the cwd at
invocation (assumed to be the repo root), independent of where the Rust
`cargo` subprocess itself runs. Untracked `example/`, `small/`, `1_small/`,
`2_small/`, `small3/`, `lsf/` dirs at the repo root are generated
data/results/summary.json output from various configs, not checked in.

Not done / possible follow-ups:
- `n`, `construction_repetitions`, `query_repetitions`, `algorithms` are
  global-only in the config (not swept/overridable per distribution).
- Consensus's `b` parameter is hardcoded to 20 in the Rust CLI
  (`src/main.rs`) and not exposed for sweeping.
- No automated tests for `experiments/`, only manual smoke-run
  verification.
- Re-verify `typst/render.sh` end-to-end once `comparison_table.typ`/
  `tradeoff_plots.typ`'s summary-json wiring is finished.

