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
`environment.py`, `json_export.py`, `run.py`), with example configs
`config/example_config.toml`, `config/small_config.toml`,
`config/paper_config.toml`. Run from the repo root:

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
`cargo` subprocess itself runs. As of the "move configs to config dir"
commit, every config's `data_dir`/`results_dir`/`plot_dir` lives under
gitignored `runs/<name>/` instead of scattered top-level dirs (e.g.
`runs/small/{data,results,plots}`); `config/` holds the TOML configs.

Not done / possible follow-ups:
- `n`, `construction_repetitions`, `query_repetitions`, `algorithms` are
  global-only in the config (not swept/overridable per distribution).
- Consensus's `b` parameter is hardcoded to 20 in the Rust CLI
  (`src/main.rs`) and not exposed for sweeping.
- No automated tests for `experiments/`, only manual smoke-run
  verification.
- Re-verify `typst/render.sh` end-to-end once `comparison_table.typ`/
  `tradeoff_plots.typ`'s summary-json wiring is finished.

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

## Build-flag fairness audit (2026-08-20, after merging `learned` to main)

Checked whether all three algorithms build/run under comparable
conditions. Confirmed fair:
- **Single-threaded, all three.** Caramel's `CMakeLists.txt` strips
  `OpenMP::OpenMP_CXX` from `caramel_lib`'s link line (CaramelDB's own
  CMakeLists links it unconditionally otherwise); LSF's `CMakeLists.txt`
  sets `IPS2RA_DISABLE_PARALLEL ON`; `consensus-retrieval`'s `Cargo.toml`
  has no `rayon`/threading dependency at all. No algorithm can use extra
  cores.
- **Same CPU targeting.** `-march=native` in both `caramel/CMakeLists.txt`
  and `lsf/CMakeLists.txt`; `target-cpu=native` via `.cargo/config.toml`'s
  `rustflags` for the Rust build (covers `consensus-retrieval` too, since
  Cargo applies the *root* package's profile/rustflags across the whole
  build, not the dependency's own).
- **Same CMake build type.** `build.rs` passes `.profile("Release")` for
  both `cmake::Config` calls (caramel, lsf) - both `CMakeLists.txt`s gate
  their extra flags on `CMAKE_BUILD_TYPE STREQUAL "Release"` (or
  `RelWithDebInfo`), so this actually activates them.

Found two real asymmetries, not yet fixed (flagged in README.md's "Build
flags & fairness" section too):
1. **`-ffast-math` only reaches the two C++ algorithms.** Both
   `caramel/CMakeLists.txt` and `lsf/CMakeLists.txt` add it explicitly;
   there's no equivalent stable-Rust flag to give Consensus the same
   treatment (the closest nightly-only options aren't usable from a
   stable toolchain), so this is likely irreducible rather than a bug to
   fix.
2. **Only the Rust build gets LTO/single-codegen-unit.** Top-level
   `Cargo.toml`'s `[profile.release]` sets `lto = true, codegen-units =
   1` - and this is what actually governs the build (Cargo ignores
   `consensus-retrieval`'s *own* `[profile.release]`, e.g. its `lto =
   "thin"`, since profile settings are only read from the root package
   being built - not a fairness issue by itself, just a silent override
   worth knowing about if `consensus-retrieval` is ever built
   standalone). Neither `caramel/CMakeLists.txt` nor `lsf/CMakeLists.txt`
   sets `CMAKE_INTERPROCEDURAL_OPTIMIZATION`, so Caramel/LSF get no
   cross-translation-unit inlining at all. Additionally, Caramel's
   upstream `CARAMEL_COMPILE_OPTIONS` (in `caramel/CaramelDB/CMakeLists.txt`,
   not ours to edit without patching the submodule) adds `-funroll-loops`
   or Release/RelWithDebInfo - LSF's `CMakeLists.txt` and the Rust build
   have no equivalent, so Caramel gets one extra optimization the other
   two don't.

Not fixed pending user direction - enabling CMake IPO for both C++
libraries and/or matching `-funroll-loops` for LSF would close most of
gap 2; gap 1 (`-ffast-math`) has no clean fix on the Rust side.

## Dependency freshness check (2026-08-20)

Checked every direct dependency against its upstream latest:
- **Rust crates** (both this repo's `Cargo.toml` and `consensus-retrieval`'s):
  all already at the latest stable version on crates.io - no `Cargo.toml`
  changes needed. Ran `cargo update` to refresh `Cargo.lock`'s transitive
  deps to their latest semver-compatible versions anyway (20 packages,
  all patch/minor bumps - `clap` 4.6.5→4.6.6, `cc`, `wasm-bindgen`, etc.);
  rebuilt clean afterward.
- **`lsf/LearnedStaticFunction` submodule**: already pinned to upstream's
  current HEAD (`879b3df9`) - nothing to update.
- **`caramel/CaramelDB` submodule**: was 4 months stale (`43589815`,
  2026-04-20) - upstream gained exactly one new commit, `afc44704`
  ("Interleaved bucket-contiguous solution layout (-60% query latency)
  (#86)", 2026-08-17). Checked the diff before updating: touches only
  construction/query internals (`Construct.h`, `BucketedHashStore.h`,
  `CsfQueryCore.h`, the multiset construct files), not `Csf.h`'s public
  `query()`/`getStats()` API our `caramel/caramel.cpp` wrapper calls, and
  not `CMakeLists.txt`. Bumped the submodule pin, rebuilt clean, and
  smoke-tested `bench -a caramel` end-to-end (construct+query+size all
  produced sane output) before keeping the update - since this repo
  exists to measure query/construction time, running 4 months behind a
  commit specifically claiming a 60% query-latency win was worth fixing,
  not just noting.

## `summary.json` now records the execution environment (2026-08-20)

New `experiments/environment.py::collect_environment_info()`, called once
from `json_export.py::write_summary_json` and written as a new top-level
`"environment"` key (hostname, `platform.platform()`, CPU model from
`/proc/cpuinfo`'s `model name` line, logical core count, `rustc
--version`, the C++ compiler `build.rs`/cmake would actually use (`$CXX`
if set, else `c++`) and its `--version`, and `cmake --version`).
Motivated directly by the build-flag-fairness audit above: since the
Rust/C++ builds are pinned to the exact build machine's CPU via
`-march=native`/`target-cpu=native`, a run's numbers aren't meaningfully
comparable to another run without knowing what CPU/compilers produced
them. Best-effort by design - every field is `None` rather than raising
if it can't be determined (e.g. non-Linux, missing binary), since this is
diagnostic metadata a run shouldn't fail over. Collected in Python at
`experiments.run` time rather than baked into the Rust binary at compile
time - simpler, matches the existing "Python owns summary.json" split,
and doesn't need a rebuild to pick up toolchain changes; the tradeoff is
it reflects whatever's on `PATH`/`/proc/cpuinfo` *when the pipeline runs*,
not necessarily what built whichever `target/release` binary happens to
be sitting there if you upgraded a toolchain without rebuilding since.
`experiments/example_summary.json` (the docstring's worked example, and
previously the Typst templates' hardcoded-path fallback) was updated with
a representative `environment` block by hand rather than by a full
regenerated run, to avoid otherwise-unrelated diff noise in that fixture.
Verified 2026-08-20: `collect_environment_info()` standalone, and a full
`config/example_config.toml` run (incl. `lsf`, whose results were
missing for that config until this run) - `summary.json` now carries the
new key correctly.

`typst/summary.typ` (not `comparison_table.typ`/`tradeoff_plots.typ`
themselves, left to the user) renders it as a small gray footer line
below the tradeoff plots - `Execution environment: Host: ... · OS: ... ·
CPU: ... · Logical cores: ... · rustc: ... · C++ compiler: ... · cmake:
...` - built from a `(label, value)` pairs list filtered to drop any
`none`/missing field, so it degrades gracefully for older `summary.json`
files without the key at all, or with individual fields unset. Verified
by rendering `runs/example/plots/summary.json` via `typst/render.sh` and
inspecting the output PDF.

