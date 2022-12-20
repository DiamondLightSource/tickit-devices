#!/bin/bash

# controls_dev sets pip up to look at a local pypi server, which is incomplete
module unload controls_dev 

module load python/3.9

if [ -d "./.venv" ]
then
rm -rf .venv
fi
mkdir .venv

python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
source .venv/bin/activate
pip install -e .[dev]

python -m pytest
