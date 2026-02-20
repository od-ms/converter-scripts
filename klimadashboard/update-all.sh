#!/bin/bash

set -e

headline() {
  RED='\033[1;93m\033[5m\033[45m'
  NC='\033[0m' 
  echo -e "\n${RED}########### $1 ###########${NC}\n"
}

headline "Updating MARKTSTAMMDATENREGISTER..."
pushd ../marktstammdatenregister
./generate_and_copy_files.sh
popd

headline "Generate PV Anlagen files..."
python3 generate_pv_anlagen.py

headline "Generate Klimadashboard Datafile..."
python3 ./split_datafile.py

headline "DONE"

