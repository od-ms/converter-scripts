#!/bin/bash

python3 load_detailed_data_from_mstr.py

cat alle-anlagen-muenster-details.csv | grep -P "AnlagenbetreiberId|,Speicher," >stromspeicher-muenster.csv

cp *.csv ../../solar-und-windkraft-muenster/

echo .
echo "now check and commit all files in ../../solar-und-windkraft-muenster/"
echo .
