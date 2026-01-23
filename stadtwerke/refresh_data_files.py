#!/usr/bin/env python
# coding=utf-8
"""
This script loads Data files from Stadtwerke-Netzplan
And saves them as geojson and csv
"""

import os
import re
import time
import csv
import json
import random
import logging
from datetime import datetime
import pyfiglet
import requests

START_URL = 'https://www.netzplan-muenster.de'

URLS = {

    'haltestellen_barrierefrei': 'https://www.netzplan-muenster.de/api/wfs-layers/14/features?format=GeoJSON&locale=de-de&props=info,info2,foto,strasse,hausnr,Zusatz,plz,stadt,webseite,telefon,email,geometry,idint,f_type,centerx,centery,title,svg,svg_hover,extern_url,ttip_img&srs=EPSG:4326',

    'park_and_ride_stationen': 'https://www.netzplan-muenster.de/api/wfs-layers/60/features?format=GeoJSON&locale=de-de&props=info,info2,foto,strasse,hausnr,Zusatz,plz,stadt,webseite,telefon,email,geometry,idint,f_type,centerx,centery,title,svg,svg_hover,extern_url,ttip_img&srs=EPSG:4326',

    'ticketautomaten': 'https://www.netzplan-muenster.de/api/wfs-layers/24/features?format=GeoJSON&locale=de-de&props=info,info2,foto,strasse,hausnr,Zusatz,plz,stadt,webseite,telefon,email,geometry,idint,f_type,centerx,centery,title,svg,svg_hover,extern_url,ttip_img&srs=EPSG:4326',

    'vorverkaufsstellen': 'https://www.netzplan-muenster.de/api/wfs-layers/26/features?format=GeoJSON&locale=de-de&props=info,info2,foto,strasse,hausnr,Zusatz,plz,stadt,webseite,telefon,email,geometry,idint,f_type,centerx,centery,title,svg,svg_hover,extern_url,ttip_img&srs=EPSG:4326',

    'bike_and_ride_stationen': 'https://www.netzplan-muenster.de/api/wfs-layers/13/features?format=GeoJSON&locale=de-de&props=info,info2,foto,strasse,hausnr,Zusatz,plz,stadt,webseite,telefon,email,geometry,idint,f_type,centerx,centery,title,svg,svg_hover,extern_url,ttip_img&srs=EPSG:4326'

}

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
HEADLINE_FONT = random.choice(pyfiglet.FigletFont.getFonts())
FONT2 = random.choice(pyfiglet.FigletFont.getFonts())
logging.debug("(headline font = '%s', font2 = '%s')", HEADLINE_FONT, FONT2)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0"
}

SESSION = requests.Session()
SESSION_IS_INITIALIZED = False
CSRF_TOKEN = ""


def readUrlWithCache(cachefile_name, url):
    global SESSION_IS_INITIALIZED
    global CSRF_TOKEN
    filename = f'{cachefile_name}.json'

    currentTS = time.time()
    cache_max_age = 60 * 60 * 24 * 30
    generate_cache_file = True
    filecontent = "{}"
    if os.path.isfile(filename):
        fileModTime = os.path.getmtime(filename)
        timeDiff = currentTS - fileModTime
        if (timeDiff > cache_max_age):
            logging.debug("# CACHE file age %s too old: %s", timeDiff, filename)
        else:
            generate_cache_file = False
            logging.debug("(using cached file instead of url get)")
            with open(filename) as myfile:
                filecontent = "".join(line.rstrip() for line in myfile)

    if generate_cache_file:
        if not SESSION_IS_INITIALIZED:
            logging.debug("Fetching START_URL: %s", START_URL)
            response = SESSION.get(START_URL, headers=HEADERS)
            logging.debug("Status: %s", response.status_code)
            matchobj = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)">', str(response.content))
            if matchobj:
                CSRF_TOKEN = matchobj.group(1)
                logging.debug("Got CSRF_TOKEN %s", CSRF_TOKEN)
            else:
                logging.warning("Did not find CSRF_TOKEN")

            SESSION_IS_INITIALIZED = True
            logging.debug("--------- COOKIE ----------")
            print(SESSION.cookies.get_dict())

        logging.debug("# URL HTTP GET %s ", filename)
        HEADERS2 = {
            "Referer": "https://www.netzplan-muenster.de/",
            "X-CSRF-TOKEN": CSRF_TOKEN,
            'Accept':'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'X-Requested-With': 'XMLHttpRequest',
        }
        HEADERS2.update(HEADERS)
        req = SESSION.get(url, headers=HEADERS2)
        if req.status_code > 399:
            logging.error('  - Request result: HTTP %s - %s', req.status_code, req)
            raise FileNotFoundError

        open(filename, 'wb').write(req.content)
        filecontent = req.text
        time.sleep(1)

    jsn = json.loads(filecontent)
    if jsn.get('status') == 404:
        logging.warning('  - missing url: %s', url)
        return json.loads("{}")
    return jsn


def main():
    """Hauptmethode, hier passieren die wichtigen Dinge"""
    for name, url in URLS.items():
        big_debug_text(name)
        logging.debug(".---------------------------------------------------------->>>>>>>>>>>>> . . ")
        logging.debug("| Fetching %s: %s", name, url)
        response = readUrlWithCache(name, url)
        logging.debug("RESPONSE %s bytes", len(str(response)))
        stationen = response.get('features')
        logging.debug("ANZAHL STATIONEN %s", len(stationen))

        write_csv_and_json_files(f'{name}.json', f'data/{name}')


def write_csv_and_json_files(SOURCE_FILE, OUTPUT_FILENAME):
    """Konvertiere die Quell-JSON Datei in CSV und in GeoJSON"""

    # Opening JSON file
    f = open(SOURCE_FILE)

    # returns JSON object as a dictionary
    data_input = json.load(f)

    # Iterating through the json
    json_output = []
    csv_output = []
    for feature in data_input['features']:

        # Build JSON data
        props = feature["properties"]
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

    big_debug_text("...GeoJSON...", FONT2)

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

    logging.info("Writing file '%s'", outfile_name)
    with open(outfile_name, "w", encoding="utf-8") as outfile:
        json.dump(geojson, outfile, ensure_ascii=True, indent=2)


def write_csv_file(csv_header, data, outfile_name):
    """ Create and write output format: CSV """

    big_debug_text("...CSV...", FONT2)

    with open(outfile_name, 'w', newline='', encoding='utf-8') as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        outwriter.writerow(csv_header)
        for datarow in data:
            outwriter.writerow(datarow)

    logging.info("Number of entries: %s", len(data))
    logging.info("Wrote file '%s'", outfile_name)


def big_debug_text(text, font=HEADLINE_FONT):
    """ Write some fancy big text into log-output """
    custom_fig = pyfiglet.Figlet(font=font, width=120)
    logging.info("\n\n%s", custom_fig.renderText(text))


big_debug_text("START..")

main()

big_debug_text("DONE!")
