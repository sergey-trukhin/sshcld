#!/bin/sh
set -e

echo "*** START UNIT TESTS ***"
cd /app/tests/
pytest -p no:cacheprovider
echo "*** FINISH UNIT TESTS ***"

echo "*** START FLAKE8 TESTS ***"
cd /app/
flake8
echo "*** FINISH FLAKE8 TESTS ***"

echo "*** START PYLINT TESTS ***"
cd /app/
pylint /app/
echo "*** FINISH PYLINT TESTS ***"

exit 0