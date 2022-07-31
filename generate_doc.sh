#!/bin/bash
rm -R docs/html/*
sphinx-apidoc -f -o docs/ shaclapi --separate
sphinx-build docs/ docs/html/
