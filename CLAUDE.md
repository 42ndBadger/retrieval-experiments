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

## Third algorithm: `lsf` (Learned Static Function, added 2026-08-19)
Integrated gvinciguerra/LearnedStaticFunction (github.com/gvinciguerra/
LearnedStaticFunction) as a third `--algorithm` alongside `consensus` and
`caramel`, following the same "vendor a thin C ABI shim over a git
submodule, link a static lib from build.rs" pattern as `caramel/`
(CaramelDB) - see `caramel/caramel.h`/`caramel.cpp` for the precedent.
New/changed files: `lsf/` (submodule `LearnedStaticFunction` +
`CMakeLists.txt` + `lsf_shim.h`/`.cpp` + vendored
`learned_static_function_no_tf.hpp`), `src/lsf.rs`, `src/lib.rs`,
`src/instances.rs` (`impl BenchmarkInstance for LsfU32`), `src/main.rs`
(`Algorithm::Lsf`), `build.rs`, `experiments/example_config.toml` (added
`[[algorithm]] name = "lsf"` - no other `experiments/` changes needed,
the Python pipeline is fully generic over algorithm name).

**No TensorFlow.** Upstream LSF's "real" model (`ModelWrapper`) runs a
TFLite neural net, which means building the full TensorFlow source tree
(`lib/tensorflow` submodule - multi-gigabyte, hours to build) - this is
the "expensive part" the user asked to exclude. We use `lsf::ModelFreq`
instead: a plain per-value frequency table with no ML backend, which
predicts the same global value distribution for every key regardless of
features. Since our keys carry no signal about their value (data_gen
assigns values i.i.d., independent of the key string), a real ML model
couldn't do better than the marginal frequency anyway - `ModelFreq` isn't
a compromise here, it's the entropy-optimal choice for exactly this data.
`lib/tensorflow` and `lib/psimd` (TFLite's SIMD polyfill) are left as
uninitialized submodules; `lsf/learned_static_function_no_tf.hpp` is our
vendored copy of upstream's `include/lsf/learned_static_function.hpp`
with the `model_wrapper.hpp`/TFLite include dropped (see that file's
top-of-file comment for this and two other small deviations from
upstream: keys are hashed explicitly via `Dataset::get_key(i)` rather
than upstream's assumption that the key *is* the dataset row index, and
the upstream per-construction `std::cout` debug prints are removed so
they don't skew `src/benchmark.rs`'s construction timing or spam stdout
across a sweep). `lsf/CMakeLists.txt` explains the rest of what's
excluded and why (upstream's own top-level CMakeLists.txt can't be
`add_subdirectory`'d - it hard-requires TensorFlow Lite as a link
dependency - so we replicate only the BuRR-VLR ribbon retrieval structure
(`lib/burr-vl`, a fork of lorenzhs/BuRR) and its `tlx`/`ips2ra`
submodules).

**Submodule init is NOT plain `--recursive`** - LSF's own `.gitmodules`
lists `lib/tensorflow`/`lib/psimd`, so a blind `git submodule update
--init --recursive` at the repo root would defeat the whole point. Use
`scripts/init-submodules.sh`, which does the equivalent selective,
level-by-level init (documented inline in that script).

**Value domain constraint**: LSF's model/coder store value "labels" as
`uint16_t`, so `classes_count` (= `max(values) + 1`, computed in
`LsfU32::new`) must be ≤ 65535. Fine for this repo's distributions
(uniform/bernoulli/truncated-geometric bounds are all small), but would
need revisiting for a value domain with many distinct values.

Verified 2026-08-19: standalone C++ smoke test (`lsf_u32_build`/`query`/
`size`) round-trips correctly; `cargo build --release` links cleanly;
`cargo test` (incl. 3 new `src/lsf.rs` unit tests) passes; a full
`experiments.run` smoke sweep (n=2000, 3 algorithms incl. `lsf`, all 3
distribution families) produced correct plots/tables with `lsf` as a
third series - on `uniform bound=17` LSF hit ~4.96 bits/key (entropy
4.09, so ~21% relative overhead) vs Caramel's ~25% and Consensus's ~48%,
confirming the integration is not just functional but competitive. At
n=100000, `uniform bound=17` overhead drops to ~1.8%, i.e. LSF's per-item
overhead dominates at small n more than Caramel's.

