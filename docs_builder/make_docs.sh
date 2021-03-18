#!/bin/bash
###############################################################
# Build script for tellurium documentation from rst files and
# python docstrings in the tellurium package
#
# execute this script in the docs folder i.e., after
# 	cd tellurium/docs
#
# Usage:
#	./make_docs.sh 2>&1 | tee ./make_docs.log
#
# The documentation is written in docs/_build
###############################################################

date
echo "--------------------------------------"
echo "remove old documentation"
echo "--------------------------------------"
rm -rf _apidoc
rm -rf _built
rm -rf _notebooks
rm -rf _static
echo "DONE"

# create rst files from the notebooks
# ./make_notebooks_rst.sh 2>&1 | tee ./make_notebooks_rst.log

# create html documentation
echo "--------------------------------------"
echo "create html docs"
echo "--------------------------------------"
# make html
sphinx-build -b html . _build/html
echo "DONE"

# the new documentation is now in docs/_built
firefox _build/html/index.html

