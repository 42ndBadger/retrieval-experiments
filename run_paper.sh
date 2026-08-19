#! /bin/bash
spack env activate pdf
python -m experiments.run experiments/paper_config.toml
