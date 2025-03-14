#!/bin/bash

# Set PYTHONPATH and run tests with coverage
export PYTHONPATH=$PWD
python -m pytest src/tests/ --cov=src "$@"
