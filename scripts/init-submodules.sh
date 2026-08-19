#!/usr/bin/env bash
# Initialize this repo's git submodules.
#
# IMPORTANT: do NOT use `git submodule update --init --recursive` for the
# whole repo. lsf/LearnedStaticFunction's own .gitmodules lists
# `lib/tensorflow` (the full TensorFlow source tree - multi-gigabyte,
# hours to build) and `lib/psimd` (only needed to build TensorFlow Lite).
# We don't use either (see lsf/CMakeLists.txt and
# lsf/learned_static_function_no_tf.hpp for why), but plain `--recursive`
# doesn't know that - it will happily clone them. This script initializes
# exactly what's needed and nothing else.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

git submodule update --init --recursive -- caramel/CaramelDB

git submodule update --init -- lsf/LearnedStaticFunction
git -C lsf/LearnedStaticFunction submodule update --init -- lib/burr-vl
git -C lsf/LearnedStaticFunction/lib/burr-vl submodule update --init -- tlx ips2ra pcg-cpp DySECT
git -C lsf/LearnedStaticFunction/lib/burr-vl/DySECT submodule update --init -- module/xxhash utils

echo "Submodules initialized (lsf/LearnedStaticFunction/lib/tensorflow and lib/psimd deliberately left empty)."
