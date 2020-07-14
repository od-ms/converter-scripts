#!/usr/bin/env python
# coding=utf-8
"""
This script automatically parses COVID19-Data from Bezirksregierung Münster Website

It needs:
    - a locally checked out repository "resources" with covid19 datafile
"""

import os
import csv
import datetime
from urllib.request import urlopen
import pprint
import re

# CONFIG
PATH_TO_OTHER_REPO = '../resources/'
FILENAME_IN_OTHER_REPO = 'coronavirus-fallzahlen-regierungsbezirk-muenster.csv'

# Internal config - Dont change below this line
URL = 'https://www.bezreg-muenster.de/de/im_fokus/uebergreifende_themen/coronavirus/coronavirus_allgemein/index.html'
DATAFILE = PATH_TO_OTHER_REPO + FILENAME_IN_OTHER_REPO
TEMPFILE = 'temp-covid.csv'

# Read website
print()
print(' -- COVID PARSER ' + str(datetime.datetime.now()) + '--')
print("Data website url:", URL)
f = urlopen(URL)
htmlPage = f.read().decode('utf-8')

# Read data file
datepattern = r'([0-9]{1,2})\.+([0-9]{1,2})\.+([0-9]{4})'
firstline = ''
with open(DATAFILE) as datafile:
    firstline = datafile.readline()
    dateresult = re.findall(datepattern, datafile.readline())
    newest_entry = datetime.datetime(int(dateresult[0][2]), int(dateresult[0][1]), int(dateresult[0][0]))

print("Latest entry in datafile:", newest_entry)


# --- This is the HTML that we want to parse -- 
# <li><strong>Stadt Bottrop: </strong>Aktuell Infizierte 0 (1),&nbsp;Infizierte 211 (211), Verstorbene 7 (7), Genesene 204 (203)</li>
# <li><strong>Kreis Borken:</strong>&nbsp;Aktuell Infizierte 5 (7), Infizierte 1.111 (1.111), Verstorbene 38 (38), Genesene 1.068 (1.066)</li>
# <li><strong>Kreis Coesfeld:</strong>&nbsp;Aktuell Infizierte 4 (5), Infizierte 871 (871), Verstorbene 24 (24), Genesene 843 (842)</li>


### Parse website
# Find COVID-19 report date
dateresult = re.findall(r'<strong>Stand:[^0-9]*' + datepattern, htmlPage)
today = datetime.datetime(int(dateresult[0][2]), int(dateresult[0][1]), int(dateresult[0][0]))
print("Latest entry on website:", today)

# Parse COVID-19 numbers
numPat = r'[^(]*\((-?[\d.]+)\)'
pattern = r'<li><strong>([SK][^:]+)[^<]*<\/strong>[^<]*[aA]ktuell Infizierte\s*-?([\d.]+)' + numPat+ r'[^<]*Infizierte\s*([\d.]+)'+numPat+r'[^,]*,\s*Verstorbene\s*([\d.]+)'+numPat+r'[^,]*,\s*Genesene\s*([\d.]+)'+numPat
result = re.findall(pattern, htmlPage.replace('&uuml;', 'ü'))
print("Parsed data from website:")
pp = pprint.PrettyPrinter(width=160)
pp.pprint(result)


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
            writer.writerow([item[0], mydate, item[3].replace('.', ''), item[7].replace('.', ''), item[5].replace('.', '')])

yesterday = today - datetime.timedelta(days=1)
if newest_entry < yesterday:
    # Write yesterdays covid numbers
    print("Adding data:", yesterday)
    with open(TEMPFILE, mode='a') as csv_file:
        mydate = yesterday.strftime('%d.%m.%Y')
        writer = csv.writer(csv_file, dialect='excel')
        for item in result:
            writer.writerow([item[0], mydate, item[4].replace('.', ''), item[8].replace('.', ''), item[6].replace('.', '')])

os.system('tail +2 ' + DATAFILE + ' >> ' + TEMPFILE)


print("Wrote tempfile:", TEMPFILE)
print("Replacing datafile:", DATAFILE)
print("Result:")

os.system('cp ' + TEMPFILE + ' ' + DATAFILE)
os.system('cd ' + PATH_TO_OTHER_REPO + ';git diff ' + FILENAME_IN_OTHER_REPO)

print("Done.")