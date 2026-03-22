#!/bin/bash
set -x
rm -f dist/* && \
  python -m build && \
  twine upload dist/*
