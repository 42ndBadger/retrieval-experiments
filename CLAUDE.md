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
  (`rel_space_overhead`/`relative_overhead`) is the **analytical** Shannon
  entropy computed from the distribution's closed-form parameters (p,
  bound), not the empirical entropy of the generated data - this part of
  the original decision still holds, so that metric doesn't move based on
  which random keys happened to get generated. Superseded update (during
  the json-refactor branch): the **empirical** entropy is now also
  computed (`entropy.py::empirical_entropy_bits`, from the actual
  generated `.kv` file) and exposed alongside the analytical one in the
  JSON export, for comparison/sanity-checking - it's just no longer
  excluded outright the way this bullet originally said.
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
table/plots"): the full pipeline lives in `experiments/` (`config.py`,
`entropy.py`, `naming.py`, `cli_runner.py`, `datagen.py`, `bench.py`,
`results.py`, `plotting.py`, `tables.py`, `run.py`), with example configs
`experiments/example_config.toml`, `experiments/small_config.toml`,
`experiments/paper_config.toml`. Run from the repo root:

    cargo build --release   # once, so `cargo run --release --` is fast
    python -m experiments.run experiments/example_config.toml

Current output (post-restructure - this superseded the original
per-distribution-family design mentioned above):
- **Plots**: one PDF per *dataset instance* - a (distribution, single
  swept-parameter-value) pair, e.g. `overhead_vs_construction_bernoulli_p0.1.pdf`,
  `overhead_vs_construction_bernoulli_p0.2.pdf`, ... - not one plot per
  whole distribution family with a curve across the entropy sweep.
  `naming.py::dataset_instances` enumerates these instances (shared by
  plotting.py and tables.py). Within one instance's plot, each *algorithm*
  gets one fixed color+marker, and sibling configs of the same algorithm
  (e.g. differently-tuned Consensus runs) are drawn as separate points
  connected by a line, sorted by relative overhead - so the line traces
  that algorithm's own config tradeoff on that one dataset, not an
  entropy sweep.
- **Table**: `write_tables` (tables.py) only emits `summary_table.csv` and
  a Typst source file `summary_table.typ` - it no longer writes a PDF
  directly. Compiling to PDF is a manual separate step
  (`typst compile summary_table.typ`). Rows are grouped by algorithm
  *config* (one group per `[[algorithm]]` entry, 4 metric sub-rows each),
  columns by dataset instance, shaded by distribution family.

`naming.py::param_label_and_key` remains the shared source of truth both
plotting.py and tables.py use for the human-readable swept parameter
label and its sort key, so labels/ordering stay consistent between plots
and tables. `naming.py::config_label`/`config_row_label` handle the new
per-config display names (`display_name` in the TOML, required when
multiple configs share an algorithm name).

Verified end-to-end 2026-08-15 (before the restructure) with a small
smoke config; not re-verified end-to-end since. `data_dir`/`results_dir`/
`plot_dir` resolve relative to the cwd at invocation (assumed to be the
repo root), independent of where the Rust `cargo` subprocess itself runs.
Untracked `example/`, `small/`, `old-small/` dirs at the repo root are
generated data/results/plots output from the example/small configs, not
checked in.

Not done / possible follow-ups:
- `n`, `construction_repetitions`, `query_repetitions`, `algorithms` are
  global-only in the config (not swept/overridable per distribution).
- Consensus's `b` parameter is hardcoded to 20 in the Rust CLI
  (`src/main.rs`) and not exposed for sweeping.
- No automated tests for `experiments/`, only manual smoke-run verification
  (and that was against the pre-restructure plot/table layout).
- Re-verify end-to-end against the current per-instance plots + csv/typ
  table output.

