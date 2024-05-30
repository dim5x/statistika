#!/bin/bash

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

echo "Executing service in '$BASEDIR'"

cd $BASEDIR

source "$BASEDIR"/ubuntu_env/bin/activate

python "$BASEDIR"/stat.py