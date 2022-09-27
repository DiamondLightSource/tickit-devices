#!/bin/bash

module unload controls_dev
module load python/3.9

if [[ -d "./.venv" ]]
then
    pipenv --rm
fi

mkdir .venv

pipenv --python python
pipenv install --dev

pipenv run pre-commit install

pipenv run tests

