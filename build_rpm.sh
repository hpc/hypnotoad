#!/bin/bash

if [ ! -f setup.py ];
then
    echo "setup.py not found. Are you running this script from the top level distribution directory?"
    exit
fi

PYTHON=/usr/bin/python
$PYTHON setup.py bdist --format=rpm

# EOF
