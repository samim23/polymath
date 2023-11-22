#!/bin/bash


mkdir -p processed separated library input
sudo docker run -v "$(pwd)"/processed:/polymath/processed -v "$(pwd)"/separated:/polymath/separated -v"$(pwd)"/library:/polymath/library -v "$(pwd)"/input:/polymath/input polymath python /polymath/polymath.py "$@"