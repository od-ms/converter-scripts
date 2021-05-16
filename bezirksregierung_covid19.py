#!/usr/bin/env python
# coding=utf-8
"""
This script automatically parses COVID19-Data from NRW Website

It needs:
    - a locally checked out repository "resources" with covid19 datafile
"""

import os
import csv
import datetime
import urllib.request
import pprint
import re
import sys

# CONFIG
PATH_TO_OTHER_REPO = '../resources/'
FILENAME_IN_OTHER_REPO = 'coronavirus-fallzahlen-regierungsbezirk-muenster.csv'

# Internal config - Dont change below this line
URL = 'https://www.lzg.nrw.de/covid19/daten/covid19_{}.csv'
DATAFILE = PATH_TO_OTHER_REPO + FILENAME_IN_OTHER_REPO
TEMPFILE = 'temp-covid.csv'

print()
print(' -- COVID PARSER ' + str(datetime.datetime.now()) + '--')
print("Command line arguments:", len(sys.argv), str(sys.argv))
print("Data website url:", URL)


# Read data file
datepattern = r'([0-9]{1,2})[^0-9]+([0-9]{1,2})[^0-9]+([0-9]{4})'
firstline = ''
with open(DATAFILE) as datafile:
    firstline = datafile.readline()
    dateresult = re.findall(datepattern, datafile.readline())
    newest_entry = datetime.datetime(int(dateresult[0][2]), int(dateresult[0][1]), int(dateresult[0][0]))

print("Latest entry in datafile:", newest_entry)

# Kommune 	Datum 	Bestätigte Faelle 	Gesundete 	Todesfaelle
#Stadt Bottrop 	18.12.2020 	2373 	1900 	18
# Kreis Borken 	18.12.2020 	5902 	4900 	100
# Kreis Coesfeld 	18.12.2020 	2556 	2200 	27
# Stadt Gelsenkirchen 	18.12.2020 	6456 	4900 	57
# Stadt Münster 	18.12.2020 	3597 	3100 	38
# Kreis Recklinghausen 	18.12.2020 	13623 	10700 	196
# Kreis Steinfurt 	18.12.2020 	6278 	5300 	133
# Kreis Warendorf

KREISE = {
    "5515": "Stadt Münster",
    "5558": "Kreis Coesfeld",
    "5554": "Kreis Borken",
    "5512": "Stadt Bottrop",
    "5513": "Stadt Gelsenkirchen",
    "5562": "Kreis Recklinghausen",
    "5566": "Kreis Steinfurt",
    "5570": "Kreis Warendorf",
}

# concatenate the separate files (they used to be all in 1 single file..)
complete_file = []
for key in KREISE:
    # Read csv content from website
    current_city = URL.format(key)
    print("Fetching " + current_city)
    response = urllib.request.urlopen(current_city)

    lines = [re.sub(r'[^\x00-\x7F]+','',l.decode('utf-8')) for l in response.readlines()]

    # reverse the whole file but keep the first line (=header row)
    # we need the newest entry first, but they have reversed the date order of the csv file at some point ...
    column_names = lines.pop(0)
    if not complete_file:
        complete_file.append(column_names)
    complete_file += reversed(lines)

pprint.pprint(complete_file)

# create csvreader
csvreader = csv.DictReader(complete_file)
today = None
result = []
for row in csvreader:
    #    pprint.pprint(row)
    if not today:
        dateresult = re.findall(datepattern, row['datum'])
        today = datetime.datetime(int(dateresult[0][2]), int(dateresult[0][1]), int(dateresult[0][0]))
        print("Latest entry on website:", today)
    ags = row['kreis']
    if ags in KREISE:
        row['kommune'] = KREISE[ags]
        result.append(row)


### Write result file
# Write first row
with open(TEMPFILE, mode='w') as csv_file:
    csv_file.write(firstline)

if newest_entry < today:
    # Write todays covid numbers
    print("Adding data:", today)
    with open(TEMPFILE, mode='a') as csv_file:
        mydate = today.strftime('%d.%m.%Y')
        writer = csv.writer(csv_file, dialect='excel')
        for item in result:
            # Kommune 	Datum 	Bestätigte Faelle 	Gesundete 	Todesfaelle
            writer.writerow([
                item['kommune'],
                item['datum'],
                item['anzahlMKumuliert'],
                item['genesenKumuliert'],
                item['verstorbenKumuliert']
                ])


os.system('tail -n +2 ' + DATAFILE + ' >> ' + TEMPFILE)

print("Wrote tempfile:", TEMPFILE)
print("Replacing datafile:", DATAFILE)
print("Result:")

os.system('cp ' + TEMPFILE + ' ' + DATAFILE)
os.system('cd ' + PATH_TO_OTHER_REPO + ';git diff ' + FILENAME_IN_OTHER_REPO)

print("Done.")