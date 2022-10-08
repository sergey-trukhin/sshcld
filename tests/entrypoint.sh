#!/bin/sh
set -e

echo "*** START UNIT TESTS ***"
pytest -p no:cacheprovider
echo "*** FINISH UNIT TESTS ***"

echo "*** START FLAKE8 TESTS ***"
flake8
echo "*** FINISH FLAKE8 TESTS ***"

echo "*** START PYLINT TESTS ***"
pylint .
echo "*** FINISH PYLINT TESTS ***"

exit 0