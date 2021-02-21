#!/bin/bash
###############################################################
# Create the rst directly from the ipynb files
#  ./make_notebooks_rst.sh 2>&1 | tee ./make_notebooks_rst.log
###############################################################
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

date
echo "--------------------------------------"
echo "convert notebooks to rst"
echo "--------------------------------------"
NBDIR=$DIR/notebooks

# convert the notebooks to rst after running headlessly
# if errors should abort, remove the --allow-errors option
# jupyter nbconvert --to=rst --allow-errors --execute $NBDIR/*.ipynb
# In the process the notebooks are completely executed
jupyter nbconvert --ExecutePreprocessor.timeout=600 --to=rst --execute $NBDIR/*.ipynb
echo "DONE"

