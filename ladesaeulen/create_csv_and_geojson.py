""" Lese Daten von Bundesnetzagentur und speichere als GeoJSON und CSV """

# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long

import os
import os.path
import time
import csv
import re
import json
import random
import logging
from datetime import datetime
import requests
from pyfiglet import Figlet
from io import StringIO



# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, f"\033[1;31m{logging.getLevelName(logging.WARNING)}\033[1;0m" )
logging.addLevelName(logging.ERROR, f"\033[1;41m{logging.getLevelName(logging.ERROR)}\033[1;0m")
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
FONTS = (
    'puffy slant smslant speed standard thick basic bell c_ascii_ charact1 charact2 charact6 chunky clr6x8 colossal '
    'contessa cosmic crawford demo_1__ drpepper fender graceful gothic'
)
# Pick a random font for fancier logging
HEADLINE_FONT = random.choice(FONTS.split())
logging.debug("(headline font = '%s')", HEADLINE_FONT)

# Use cosmic font, it rocks
# HEADLINE_FONT = "cosmic"

SOURCE_URL = 'https://data.bundesnetzagentur.de/Bundesnetzagentur/SharedDocs/Downloads/DE/Sachgebiete/Energie/Unternehmen_Institutionen/E_Mobilitaet/Ladesaeulenregister.csv'


def read_url_with_cache(url):
    """ Read URLs only once, and cache them to files """
    filename = f'cache/{format(re.sub("[^0-9a-zA-Z]+", "_", os.path.basename(url)))[0:250]}'

    current_ts = time.time()
    cache_max_age = 60 * 60 * 24 * 30 # days
    generate_cache_file = True
    filecontent = ""
    if os.path.isfile(filename):
        file_mod_time = os.path.getmtime(filename)
        time_diff = current_ts - file_mod_time
        if time_diff > cache_max_age:
            logging.debug("# CACHE file age %s too old: %s", time_diff, filename)
        else:
            generate_cache_file = False
            logging.debug("(using cached file instead of url get)")
            with open(filename, encoding='utf-8') as myfile:
                filecontent = "".join(line for line in myfile)

    if generate_cache_file:
        logging.debug("# URL HTTP GET %s ", filename)
        req = requests.get(url, timeout=10)
        if req.status_code > 399:
            logging.warning('  - Request result: HTTP %s - %s', req.status_code, url)

        open(filename, 'wb').write(req.content)
        filecontent = req.text
        # lets wat a bit, dont kill a public server
        time.sleep(1)

    return filecontent

#               0           1       2               3           4               5   6           7                           8                   9               10                        11                            12
FIRST_ROW = '"Betreiber";"Straße";"Hausnummer";"Adresszusatz";"Postleitzahl";"Ort";"Bundesland";"Kreis/kreisfreie Stadt";"Breitengrad";"Längengrad";"Inbetriebnahmedatum";"Nennleistung Ladeeinrichtung [kW]";"Art der Ladeeinrichung";"Anzahl Ladepunkte";"Steckertypen1";"P1 [kW]";"Public Key1";"Steckertypen2";"P2 [kW]";"Public Key2";"Steckertypen3";"P3 [kW]";"Public Key3";"Steckertypen4";"P4 [kW]";"Public Key4"'

def compare_first_row(row):
    f = StringIO(FIRST_ROW)
    csvreader = csv.reader(f, delimiter=';')
    firstrow = next(csvreader, None)
    if row != firstrow:
        logging.warning("%s", row)
        logging.warning("%s", firstrow)
        raise ValueError("Unexpected header row in CSV")


def wget_stationen(source_url):
    """ Stationen auslesen """
    filecontent = read_url_with_cache(source_url)
    f = StringIO(filecontent)
    csvreader = csv.reader(f, delimiter=';')

    # first 10 rows are file description text
    for count in range ( 0, 10 ):
        logging.debug("%s", next(csvreader, None))

    # check if file format is still the same
    firstrow = next(csvreader, None)
    compare_first_row(firstrow)


    big_debug_text("Start reading CSV...")

    stationen_geojson_list = []

    with open("ladesaeulen-muenster.csv", 'w', newline='', encoding='utf-8') as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        outwriter.writerow(list(firstrow))


        for row in csvreader:
            if row[7] != 'Kreisfreie Stadt Münster':
                continue

            logging.debug("Found a row %s", row[0:9])
            outwriter.writerow(row)
            lat = float(row[9].replace(',','.'))
            lon = float(row[8].replace(',','.'))
            if (lat < 7) or (lon < 51):
                logging.warning("SKIP out of range lat %s, lon %s: %s", lat, lon, row)
                continue

            stationen_geojson_list.append([
                [lat, lon],
                {
                    'Typ': row[10],
                    'Betreiber': row[0],
                    'Inbetriebnahme': row[10],
                    'Nennleistung[kW]': row[11],
                    'Ladeeinrichung': row[12],
                    'Anzahl Ladepunkte': row[13],
                    'Steckertypen': row[14],
                    'Ladeleistung[kW]': row[15]
                }
            ])

    return stationen_geojson_list



def write_json_file(data, outfile_name):
    """ Create and write output format: GeoJSON """

    big_debug_text("Writing GeoJSON...")

    features = []
    for entry in data:
        features.append(
          {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": entry[0]
            },
            "properties": entry[1]
          }
        )

    logging.info('Got %s Stationen', len(features))

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    logging.info( "Writing file '%s'", outfile_name)
    with open(outfile_name, "w", encoding="utf-8") as outfile:
        json.dump(geojson, outfile, ensure_ascii=True, indent=2)


def big_debug_text(text):
    """ Write some fancy big text into log-output """
    custom_fig = Figlet(font=HEADLINE_FONT, width=120)
    logging.info("\n\n%s", custom_fig.renderText(text))


def main_process(source_url):
    """ ▂▃▅▇█▓▒░۩۞۩ MAIN ۩۞۩░▒▓█▇▅▃▂ """

    big_debug_text("Reading Stationen Data")
    stationen_data = wget_stationen(source_url)

    write_json_file(stationen_data, "ladesaeulen-muenster.json")



main_process(SOURCE_URL)

big_debug_text("DONE!")
