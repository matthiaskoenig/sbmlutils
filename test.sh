#!/bin/bash
############################################################
# Run all the unittests and create coverage report.
#
# Usage: 
#	./test.sh 2>&1 | tee ./run_tests.log
#
############################################################

# only run tests
nosetests
# to run the tests in the virtual environment use
#  /home/mkoenig/.virtualenvs/sbmlutils/bin/nosetests

# coverage report
# issue with import directories
# nosetests --with-coverage --cover-erase --cover-inclusive --cover-package=sbmlutils --cover-html
# firefox cover/index.html
