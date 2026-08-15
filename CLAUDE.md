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
- Entropy in the "relative overhead over entropy" plots is the **analytical**
  Shannon entropy computed from the distribution's closed-form parameters
  (p, bound), not the empirical entropy of the generated data.
- Each distribution family (uniform, bernoulli, truncated-geometric) is
  **swept** over a list of p/bound values in the TOML config, so a single
  tradeoff plot shows a curve/trend across multiple entropy values, not just
  one point per family.
- "Relative overhead over entropy" is read as one derived metric,
  `(bits_per_key - entropy) / entropy`, plotted against time (not entropy
  as its own axis) — this was the agent's interpretation of an ambiguous
  phrase, not explicitly confirmed by the user. Revisit if it turns out to
  be wrong.

## Status
Implemented (2026-08-13, extended 2026-08-15): the full pipeline lives in
`experiments/` (`config.py`, `entropy.py`, `naming.py`, `cli_runner.py`,
`datagen.py`, `bench.py`, `results.py`, `plotting.py`, `tables.py`,
`run.py`), driven by `experiments/example_config.toml`. Run from the repo
root:

    cargo build --release   # once, so `cargo run --release --` is fast
    python -m experiments.run experiments/example_config.toml

Produces, per distribution family, `plots/overhead_vs_construction_<dist>.pdf`
and `plots/overhead_vs_query_<dist>.pdf` (plotting.py splits by distribution
so each plot's marker legend stays readable), plus a combined
`plots/summary_table.{csv,pdf}` (tables.py) with one row per
(distribution, swept parameters) and (algorithm, metric) columns - space
overhead %, bits/key, construction/query time per key - shaded by
distribution family. `naming.py::param_label_and_key` is the shared source
of truth both plotting.py and tables.py use for the human-readable swept
parameter label and its sort key, so labels/ordering stay consistent
between plots and tables.

Verified end-to-end 2026-08-15 with a small smoke config (n=2000, 2
algorithms, all 3 distribution families) after a session interruption: gen
→ bench → 6 per-distribution plot PDFs + summary table (csv+pdf) all
produced correctly; rendered PDFs to PNG (`pdftoppm`) and visually
confirmed legends, shading, and values look right. `data_dir`/
`results_dir`/`plot_dir` resolve relative to the cwd at invocation
(assumed to be the repo root), independent of where the Rust `cargo`
subprocess itself runs.

Not done / possible follow-ups:
- `n`, `construction_repetitions`, `query_repetitions`, `algorithms` are
  global-only in the config (not swept/overridable per distribution).
- Consensus's `b` parameter is hardcoded to 20 in the Rust CLI
  (`src/main.rs`) and not exposed for sweeping.
- No automated tests for `experiments/`, only manual smoke-run verification.

