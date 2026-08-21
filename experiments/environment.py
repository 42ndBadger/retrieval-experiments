"""Captures the machine/toolchain an experiment ran on, for
json_export.py's `environment` key - CPU model and compiler versions
especially, since the Rust/C++ builds are pinned to this exact CPU via
-march=native/target-cpu=native (see CLAUDE.md's build-flag-fairness
audit), so results aren't meaningfully comparable across machines without
knowing what machine/compilers actually produced them.

Best-effort only: every field is `None` if it couldn't be determined
(missing binary, non-Linux /proc/cpuinfo, ...) rather than raising - this
is diagnostic metadata, a run shouldn't fail over it."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess


def _run_first_line(cmd: list[str]) -> str | None:
    """First line of `cmd`'s stdout, or None if the binary isn't on PATH,
    fails to run, or exits non-zero."""
    if shutil.which(cmd[0]) is None:
        return None
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout:
        return None
    return result.stdout.splitlines()[0].strip()


def _cpu_model() -> str | None:
    """Linux: the `model name` field from /proc/cpuinfo - what
    -march=native actually targets. Falls back to platform.processor()
    (often empty on Linux, but may work elsewhere)."""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or None


def _cxx_compiler() -> tuple[str, str | None]:
    """(compiler command, first line of --version) for whichever C++
    compiler cmake would pick to build caramel/lsf - build.rs never sets
    CMAKE_CXX_COMPILER, so that's $CXX if set, else the same `c++` default
    cmake/make fall back to."""
    cxx = os.environ.get("CXX", "c++")
    return cxx, _run_first_line([cxx, "--version"])


def collect_environment_info() -> dict:
    """One-shot snapshot for json_export.py: hostname/OS, CPU, logical
    core count, and rustc/C++/cmake versions."""
    cxx, cxx_version = _cxx_compiler()
    return {
        "hostname": platform.node() or None,
        "os": platform.platform(),
        "cpu": _cpu_model(),
        "logical_cpus": os.cpu_count(),
        "rustc_version": _run_first_line(["rustc", "--version"]),
        "cxx_compiler": cxx,
        "cxx_compiler_version": cxx_version,
        "cmake_version": _run_first_line(["cmake", "--version"]),
    }
