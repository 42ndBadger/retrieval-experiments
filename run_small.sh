#! /bin/bash
spack env activate pdf
python -m experiments.run experiments/small_config.toml
