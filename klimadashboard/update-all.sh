#!/bin/bash

set -e

echo "\n########### Updating MARKTSTAMMDATENREGISTER...\n"
pushd ../marktstammdatenregister
./generate_and_copy_files.sh
popd

echo "\n########### Generate PV Anlagen files...\n"
python3 generate_pv_anlagen.py

echo "\n########### Generate Klimadashboard Datafile...\n"
python3 ./split_datafile.py

echo "\n########### DONE\n"

