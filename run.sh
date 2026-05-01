#!/bin/bash

echo "Python usado:"
which python

echo "Python del venv:"
venv/bin/python --version

venv/bin/python run.py
