# Compressed Static Function Data Structure Experiments

This repository contains code for benchmarking and comparing static function data structures:
- [CONSENSUS-CSF](https://github.com/42ndBadger/consensus-retrieval)
- [Caramel](https://github.com/detorresramos/CaramelDB)
- [BuRR-VLR](https://github.com/gvinciguerra/LearnedStaticFunction)

LLMs were used to create Rust bindings and python scripts—performance sensitive measurement loops are hand-written.

---


Benchmarking harness comparing static-function/retrieval-data-structure
implementations - Consensus, Caramel, and LSF (Learned Static Function) -
across swept synthetic data distributions. A Rust CLI generates data and
runs the benchmarks; a Python pipeline drives it from a TOML config and
produces a JSON summary; Typst templates render that summary into PDF
plots/tables. See `CLAUDE.md` for the full design rationale and status
notes.

## Repository layout

- `src/` - the Rust CLI (`gen`/`bench` subcommands, see `src/main.rs`).
  Links against two vendored C++ libraries, each a git submodule built
  from `build.rs`/cmake - `caramel/CaramelDB` and
  `lsf/LearnedStaticFunction` (only its non-TensorFlow pieces, see
  `lsf/CMakeLists.txt`) - plus the sibling `consensus-retrieval` crate.
- `experiments/` - the Python pipeline (`python -m experiments.run
  <config>`): reads a TOML config, generates data, runs benchmarks, writes
  `summary.json`. No plotting/table code lives here (see below).
- `config/` - the TOML configs consumed by `experiments.run`
  (`example_config.toml`, `small_config.toml`, `paper_config.toml`).
- `typst/` - Typst templates that render a `summary.json` into a PDF
  report (`typst/render.sh <plot_dir>`); a separate, manual step from the
  Python pipeline so the latter doesn't need Typst installed.
- `runs/` - gitignored; each config's `data_dir`/`results_dir`/`plot_dir`
  lives under here (e.g. `runs/small/{data,results,plots}`).

## Dependencies

- **A sibling checkout of `consensus-retrieval`**. `Cargo.toml` depends on
  it via `path = "../consensus-retrieval"`, so it must be cloned next to
  this repo (`../consensus-retrieval` relative to this repo's root), not
  fetched automatically.
- **Rust** (edition 2024, needs rustc 1.85+). Install via
  [rustup](https://rustup.rs) - don't rely on a package manager's `rust`,
  including spack's (see "Setting up via spack" below): distro/spack
  packages routinely lag behind the stable release needed for edition
  2024.
- **A C++23-capable toolchain** (`g++` - LSF's shim needs C++23, Caramel
  only C++17) plus **CMake** + **GNU Make** - `build.rs` builds both
  vendored C++ libraries via `cmake::Config`. OpenMP/TBB are *not*
  required - both are explicitly disabled in the vendored builds so every
  algorithm stays single-threaded (see the "Build flags & fairness"
  section below).
- **Git** with submodule support - `caramel/CaramelDB` and
  `lsf/LearnedStaticFunction` are git submodules, but **don't** run a
  blind `git submodule update --init --recursive` at the repo root: LSF's
  own `.gitmodules` pulls in a multi-gigabyte TensorFlow checkout we never
  use. Run `./scripts/init-submodules.sh` instead, which initializes
  exactly the submodules actually needed (documented inline).
- **Python 3.11+** (needs stdlib `tomllib`) with **pandas**.
- **Typst** - only for `typst/render.sh`'s manual rendering step; not
  needed to generate data/run benchmarks/produce `summary.json`.

### Setting up via spack

The repo's `spack.yaml` defines a spack environment named
`retrieval-experiments` with the CMake/Make/Git/Python/pandas
dependencies above (everything except Rust, the C++ compiler itself, and
Typst - see below). Create and install it once:

```sh
spack env create retrieval-experiments spack.yaml
spack env activate retrieval-experiments
spack install
```

Rust is deliberately **not** part of this environment - install it via
[rustup](https://rustup.rs) instead (see "Dependencies" above) and leave
it on `PATH`; `cargo`/`rustc` resolve there regardless of whether the
spack env is active.

You need a C++23-capable compiler (e.g. GCC 12+) available to this
environment. If your system already has one (e.g. `build-essential` on a
recent Debian/Ubuntu), just make sure spack can see it:

```sh
spack compiler find
```

Otherwise, build one through spack and register it (this compiles a full
GCC from source, so expect it to take a while):

```sh
spack install gcc
spack compiler add "$(spack location -i gcc)"
```

Once installed, activate the environment before working in the repo:

```sh
spack env activate retrieval-experiments
```

or use `./run_with_spack.sh` (below), which activates it for you.

Typst isn't part of the spack env (it's only needed for the separate
rendering step, possibly on a different machine) - install it however you
like, e.g. `cargo install --locked typst-cli` or a prebuilt binary from
<https://github.com/typst/typst/releases>.

### Setting up via nix

`shell.nix`/`.envrc` set up an equivalent devshell (`nix-shell`, or
automatically via `direnv allow` since `.envrc` says `use nix`) with the
same non-Typst dependencies, aside from the sibling `consensus-retrieval`
checkout and git submodule, which are unaffected by either environment
manager.

## Running

Initialize submodules, then build the CLI once (subsequent
`cargo run --release --` calls made by the Python pipeline reuse this
build):

```sh
./scripts/init-submodules.sh
cargo build --release
```

Run a config, e.g. via spack:

```sh
./run_with_spack.sh small            # config/small_config.toml
./run_with_spack.sh paper --skip-gen # config/paper_config.toml, skip data-gen
./run_with_spack.sh config/example_config.toml
```

or directly, with dependencies already on `PATH` (e.g. inside `nix-shell`,
or an activated spack env):

```sh
python -m experiments.run config/small_config.toml
```

This writes `runs/<name>/data`, `runs/<name>/results`, and
`runs/<name>/plots/summary.json`. Useful flags (see `experiments/run.py`):
`--skip-gen`, `--skip-bench`, `--skip-summary`, `--force-bench`.

Render that summary into PDFs (needs Typst, run separately/manually):

```sh
typst/render.sh runs/small/plots
```

## Build flags & fairness

All three algorithms build Release, single-threaded, and pinned to the
build machine's CPU (`-march=native` for the two C++ libraries via their
`CMakeLists.txt`, `target-cpu=native` for Rust via `.cargo/config.toml`) -
see the comments in `caramel/CMakeLists.txt` and `lsf/CMakeLists.txt` for
the reasoning (OpenMP is stripped from Caramel's link line, ips2ra's
parallel mode is disabled for LSF, and `consensus-retrieval` pulls in no
threading dependency at all, so no algorithm benefits from extra cores).

Two known asymmetries remain - see the note at the end of `CLAUDE.md`'s
Status section for the full audit:

- `-ffast-math` only applies to the two C++ algorithms (Caramel, LSF) -
  there's no stable-Rust equivalent for Consensus.
- Only the Rust build enables LTO (`Cargo.toml`'s `[profile.release]`);
  neither `caramel/CMakeLists.txt` nor `lsf/CMakeLists.txt` turns on
  `CMAKE_INTERPROCEDURAL_OPTIMIZATION`. Caramel's upstream
  `CARAMEL_COMPILE_OPTIONS` also adds `-funroll-loops`, which neither LSF
  nor the Rust build get an equivalent of.
