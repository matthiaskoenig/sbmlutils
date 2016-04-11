#!/bin/bash
############################################################
# Run all the unittests and create coverage report.
#
# Usage: 
#	./run_tests.sh 2>&1 | tee ./run_tests.log
#
############################################################

nosetests

# coverage report
# nosetests --with-coverage --cover-erase --cover-inclusive --cover-package=sbmlutils --cover-html
# firefox cover/index.html
