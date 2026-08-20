# retrieval-experiments

Benchmarking harness comparing static-function/retrieval-data-structure
implementations (currently Consensus and Caramel) across swept synthetic
data distributions. A Rust CLI generates data and runs the benchmarks; a
Python pipeline drives it from a TOML config and produces a JSON summary;
Typst templates render that summary into PDF plots/tables. See
`CLAUDE.md` for the full design rationale and status notes.

## Repository layout

- `src/` - the Rust CLI (`gen`/`bench` subcommands, see `src/main.rs`).
  Links against a vendored `caramel/CaramelDB` (C++, via a git submodule +
  `build.rs`/cmake) and the sibling `consensus-retrieval` crate.
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
- **Rust** (edition 2024 - a recent stable toolchain).
- **A C++17 toolchain with OpenMP** (`g++`, linked as `stdc++`/`gomp`) and
  **CMake** + **GNU Make** - `build.rs` builds the vendored
  `caramel/CaramelDB` via `cmake::Config`.
- **Git** with submodule support - `caramel/CaramelDB` is a git submodule;
  after cloning, run `git submodule update --init --recursive`.
- **Python 3.11+** (needs stdlib `tomllib`) with **pandas**.
- **Typst** - only for `typst/render.sh`'s manual rendering step; not
  needed to generate data/run benchmarks/produce `summary.json`.

### Setting up via spack

The repo's `spack.yaml` defines a spack environment named
`retrieval-experiments` with the Rust/CMake/Make/Git/Python/pandas
dependencies above (everything except the C++ compiler itself and Typst -
see below). Create and install it once:

```sh
spack env create retrieval-experiments spack.yaml
spack env activate retrieval-experiments
spack install
```

You need a C++ compiler with OpenMP available to this environment. If
your system already has one (e.g. `build-essential` on Debian/Ubuntu),
just make sure spack can see it:

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

Build the CLI once (subsequent `cargo run --release --` calls made by the
Python pipeline reuse this build):

```sh
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
