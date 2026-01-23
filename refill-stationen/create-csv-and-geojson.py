""" Lese Daten von Refill Stationen und speichere als GeoJSON und CSV """

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
import pyfiglet



# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, f"\033[1;31m{logging.getLevelName(logging.WARNING)}\033[1;0m" )
logging.addLevelName(logging.ERROR, f"\033[1;41m{logging.getLevelName(logging.ERROR)}\033[1;0m")
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
HEADLINE_FONT = random.choice(pyfiglet.FigletFont.getFonts())
logging.debug("(headline font = '%s')", HEADLINE_FONT)

# Use cosmic font, it rocks
# HEADLINE_FONT = "cosmic"

# Links zur API von https://refill-deutschland.de/ :
# Die Daten stehen anscheinend unter der Lizenz CC0-V1
SOURCE_URL = 'https://api.ofdb.io/v0/search?bbox=51.88730730025642%2C7.520301570620901%2C52.027579043215226%2C7.731788387027151&text=refill%2C%20refill%20station%2C%20leitungswasser%2C%20trinkwasser%2C%20refill-sticker&categories=2cd00bebec0c48ba9db761da48678134%2C77b3c33a92554bcf8e8c2c86cedd6f6f'
            #'https://api.ofdb.io/v0/search?bbox=51.927648559470114%2C7.52391815185547%2C51.98900306873843%2C7.678413391113282&text=refill%20refill-station%20refill-trinkbrunnen%20refill-sticker%20trinkwasser%20leitungswasser&categories=2cd00bebec0c48ba9db761da48678134%2C77b3c33a92554bcf8e8c2c86cedd6f6f'
BASE_URL = 'https://api.ofdb.io/v0/' # dieser string wird für die cachedateinamen entfernt


def read_url_with_cache(url):
    """ Read URLs only once, and cache them to files """
    filename = f'cache/{format(re.sub("[^0-9a-zA-Z]+", "_", url.replace(BASE_URL, "")))[0:250]}'

    current_ts = time.time()
    cache_max_age = 60 * 60 * 24 * 30  # days
    generate_cache_file = True
    filecontent = "{}"
    if os.path.isfile(filename):
        file_mod_time = os.path.getmtime(filename)
        time_diff = current_ts - file_mod_time
        if time_diff > cache_max_age:
            logging.debug("# CACHE file age %s too old: %s", time_diff, filename)
        else:
            generate_cache_file = False
            logging.debug("(using cached file instead of url get)")
            with open(filename, encoding='utf-8') as myfile:
                filecontent = "".join(line.rstrip() for line in myfile)

    if generate_cache_file:
        logging.debug("# URL HTTP GET %s ", filename)
        req = requests.get(url, timeout=10)
        if req.status_code > 399:
            logging.warning('  - Request result: HTTP %s - %s', req.status_code, url)

        open(filename, 'wb').write(req.content)
        filecontent = req.text
        # lets wat a bit, dont kill a public server
        time.sleep(1)

    jsn = json.loads(filecontent)
    if isinstance(jsn, list):
        return jsn
    if jsn.get('status') == 404:
        logging.warning('  - missing url: %s', url)
        return json.loads("{}")
    return jsn


def wget_stationen(geojson_url):
    """ Refill Stationen auslesen """
    anlagen_json = read_url_with_cache(geojson_url)
    anlagen = anlagen_json.get('visible')

    json_results_count = len(anlagen)
    logging.info("Anlagen in result: %s", json_results_count)

    stationen_list = []

    for anlage in anlagen:
        station_id = anlage['id']
        station_name = anlage['title']
        logging.info("Reading: %s", station_name)

        station_data = read_url_with_cache(f'https://api.ofdb.io/v0/entries/{station_id}')

        tempdate = station_data[0]['created']
        station_data[0]['created'] = datetime.fromtimestamp(int(tempdate)).strftime('%Y-%m-%d')

        # Achtung: station_data response is an array with only 1 entry..
        stationen_list.append(station_data[0])

    return stationen_list


HEAD_ROW        = ['id', 'title', 'lat',     'lng',       'street', 'zip', 'city', 'opening_hours', 'homepage', 'description', 'created', 'license']
HEAD_ROW_TITLES = ['ID', 'Name','Latitude', 'Longitude', 'Straße', 'PLZ', 'Ort', 'Öffnungszeiten', 'Homepage', 'Beschreibung', 'Erstellungsdatum', 'Lizenz']

JSON_ROW        = ['id', 'title', 'street', 'zip', 'opening_hours', 'homepage', 'description']
JSON_ROW_TITLES = ['ID', 'Name',  'Straße', 'PLZ', 'Öffnungszeiten', 'Homepage', 'Beschreibung']


def write_json_file(data, outfile_name):
    """ Create and write output format: GeoJSON """

    big_debug_text("Writing GeoJSON...")

    features = []
    for entry in data:
        # Werte mit  list comprehension  rausziehen
        properties = {}
        for key, val in enumerate(JSON_ROW):
            if entry[val]:
                properties[JSON_ROW_TITLES[key]] = entry[val]
            else:
                logging.debug("'%s' - skipping empty %s", entry['title'], val)
        # geojson features array aufbauen
        features.append(
          {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [entry['lng'], entry['lat']]
            },
            "properties": properties
          }
        )

    logging.info('Got %s Stationen', len(features))

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    logging.info( "Writing file '%s'", outfile_name)
    with open(outfile_name, "w", encoding="utf-8") as outfile:
        json.dump(geojson, outfile, ensure_ascii=True, indent=2, sort_keys=True)


def write_csv_file(data, outfile_name):
    """ Create and write output format: CSV """

    big_debug_text("Writing CSV...")

    with open(outfile_name, 'w', newline='', encoding='utf-8') as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        outwriter.writerow(HEAD_ROW_TITLES)
        for datarow in data:
            logging.debug("####>>> Processing row: %s", datarow['title'])
            csv_row = []
            for col in HEAD_ROW:
                csv_row.append(datarow.get(col))
            outwriter.writerow(csv_row)
    logging.info( "Number of entries: %s", len(data))
    logging.info( "Wrote file '%s'", outfile_name)


def big_debug_text(text):
    """ Write some fancy big text into log-output """
    custom_fig = pyfiglet.Figlet(font=HEADLINE_FONT, width=120)
    logging.info("\n\n%s", custom_fig.renderText(text))


def main_process(URL):
    """ ▂▃▅▇█▓▒░۩۞۩ MAIN ۩۞۩░▒▓█▇▅▃▂ """

    big_debug_text("Reading\n Refill Stationen")
    stationen_data = wget_stationen(URL)

    write_json_file(stationen_data, "refill-stationen-muenster.json")
    write_csv_file(stationen_data, "refill-stationen-muenster.csv")


main_process(SOURCE_URL)

big_debug_text("DONE!")
