""" Lese Daten von  Stadtwerke Netzplan  und speichere als GeoJSON und CSV """

# -*- coding: UTF-8 -*-
# pylint: disable=line-too-long

import csv
import json
import random
import logging
from datetime import datetime
from pyfiglet import Figlet

#
# Zunächst müssen die folgenden Dateien im aktuellen Verzeichnis abgelegt werden:
#
# - haltestellen_barrierefrei.json
#     Quelle: https://www.netzplan-muenster.de/#poiLayers=swmuenster_pois_Berrierfreie_HST
#
# -
#
# Die Dateien finden sich im Entwickler Tab in den Requests ("html", nicht "xhr").
#

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

SOURCE_FILE = 'haltestellen_barrierefrei.json'
OUTPUT_FILENAME = 'data/haltestellen_barrierefrei'


def main():
    """Hauptmethode, hier passieren die wichtigen Dinge"""

    # Opening JSON file
    f = open(SOURCE_FILE)

    # returns JSON object as a dictionary
    data_input = json.load(f)

    # Iterating through the json
    json_output = []
    csv_output = []
    for feature in data_input['features']:

        # Build JSON data
        props =  feature["properties"]
        props_output = {
            "title": props['title'],
            'id': props['idint'],
        }
        if props['info']:
             props_output['info'] = props['info']

        json_output.append([
            feature["geometry"]["coordinates"],
            props_output
        ])

        # Build CSV data
        csv_output.append(
            [
                props['idint'],
                props['title'],
                feature["geometry"]["coordinates"][1],
                feature["geometry"]["coordinates"][0],
                props['info'],
            ]
        )

    f.close()

    write_json_file(
        json_output,
        OUTPUT_FILENAME + '.geojson'
    )

    write_csv_file(
        ['ID', 'Title', 'Latitude', 'Longitude', 'Info'],
        csv_output,
        OUTPUT_FILENAME + '.csv'
    )



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


def write_csv_file(csv_header, data, outfile_name):
    """ Create and write output format: CSV """

    big_debug_text("Writing CSV...")

    with open(outfile_name, 'w', newline='', encoding='utf-8') as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        outwriter.writerow(csv_header)
        for datarow in data:
            outwriter.writerow(datarow)

    logging.info( "Number of entries: %s", len(data))
    logging.info( "Wrote file '%s'", outfile_name)

def big_debug_text(text):
    """ Write some fancy big text into log-output """
    custom_fig = Figlet(font=HEADLINE_FONT, width=120)
    logging.info("\n\n%s", custom_fig.renderText(text))



big_debug_text("START..")

main()

big_debug_text("DONE!")
