# -*- coding: UTF-8 -*-

import re
import json
import logging
import requests
import os.path
import time
import csv
import os

from datetime import datetime, timezone

FILE = 'data/220307_HHB_Auswertung_Ergebnisse-vereinfacht_formatiert.csv'

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())


spalten = ['Zeile', 'Stadtteil', 'Pers./Haush.',	'Pkw/100 EW',	'Pkw/Haush.',	'Rad/100 EW',	'Rad/Haush.',	'Durchschnittsalter (Jahre)',	'Anteil Azubi',	'Anteil Schüler',	'Anteil Studenten',	'Anteil in Ausbildung',	'Anteil Vollzeit',	'Anteil Teilzeit',	'Anteil Erwerbst.', 'Fuß', 'Rad', 'MIV', 'ÖPNV', 'Sonstige', 'Wege/P*T', 'Wege/mP*T', 'min/mP', 'min/Weg', 'Fuß', 'Rad', 'E-Bike', 'MIV-F', 'Krad', 'MIV-MF', 'Bahn', 'Bus', 'Sonstige','Fuß', 'Rad', 'MIV', 'ÖPNV', 'Sonstige',  'Fuß', 'Rad', 'E-Bike', 'MIV-F', 'Krad', 'MIV-MF', 'Bahn', 'Bus', 'Sonstige', 'Gesamt']


logging.debug("anzahl Spalten %s", len(spalten))
logging.info("Reading %s", FILE)


line = 0
with open('data/mobilitaetsdaten.csv', 'w', newline='') as outfile:
  outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  outwriter.writerow(spalten)

  with open(FILE, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
    for row in spamreader:
      if row[0]:
        converted_row = row
      else:
        converted_row = converted_row[0:(len(converted_row)-1)] + row[14:19] + row[23:]
        # logging.debug('ROW %s', converted_row)
        if line < 1:
          logging.debug("anzahl Spalten %s", len(converted_row))
        line = line + 1
        outwriter.writerow([line] + converted_row)



