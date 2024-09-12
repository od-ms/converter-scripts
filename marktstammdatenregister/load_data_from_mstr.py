
# -*- coding: UTF-8 -*-

import re
import json
import random
import logging
import os
import os.path
import pprint
import time
import csv
import requests
from pyfiglet import Figlet
from datetime import datetime, timezone



# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, f"\033[1;31m{logging.getLevelName(logging.WARNING)}\033[1;0m")
logging.addLevelName(logging.ERROR, f"\033[1;41m{logging.getLevelName(logging.ERROR)}\033[1;0m")
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
FONTS = (
    'puffy slant smslant speed standard thick basic bell c_ascii_ charact1 charact2 charact6 chunky clr6x8 colossal '
    'contessa cosmic crawford demo_1__ drpepper fender graceful gothic'
)
HEADLINE_FONT = random.choice(FONTS.split())
logging.debug("(headline font = '%s')", HEADLINE_FONT)

# Link zum Frontend, mit gesetztem Filter:
# http://www.marktstammdatenregister.de/MaStR/Einheit/Einheiten/OeffentlicheEinheitenuebersicht?filter=Ort~eq~%27M%C3%BCnster%27~and~Betriebs-Status~eq~%2735%2C37%27~and~Energietr%C3%A4ger~eq~%272495%2C2497%27~and~Gemeindeschl%C3%BCssel~eq~%2705515000%27

BASE_URL = 'https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetVerkleinerteOeffentlicheEinheitStromerzeugung?'

SOURCE_URL = (
    BASE_URL + 'sort=EinheitMeldeDatum-desc'
    '&pageSize=5000'
    '&group=&filter=Ort~eq~%27M%C3%BCnster%27~and~'
    'Betriebs-Status~eq~%2735%2C37%27~and~'
    'Energietr%C3%A4ger~eq~%272495%2C2497%27~and~'
    'Gemeindeschl%C3%BCssel~eq~%2705515000%27'
)

# https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetVerkleinerteOeffentlicheEinheitStromerzeugung?sort=EinheitMeldeDatum-desc&page=1&pageSize=10&group=&filter=Ort~eq~%27M%C3%BCnster%27~and~Betriebs-Status~eq~%2735%2C37%27~and~Energietr%C3%A4ger~eq~%272495%2C2497%27~and~Gemeindeschl%C3%BCssel~eq~%2705515000%27

# https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetVerkleinerteOeffentlicheEinheitStromerzeugung?sort=EinheitMeldeDatum-desc&page=1&pageSize=10&group=&filter=Betriebs-Status~eq~%2735%2C37%27~and~Energietr%C3%A4ger~eq~%272495%2C2497%27~and~Gemeindeschl%C3%BCssel~eq~%2705515000%27

# SOURCE_URL = 'https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetVerkleinerteOeffentlicheEinheitStromerzeugung?sort=&page=1&pageSize=5896&group=&filter=Energietr%C3%A4ger~eq~%272495%27~and~Betriebs-Status~eq~%2735%2C37%27~and~Gemeindeschl%C3%BCssel~eq~%2705515000%27'



def readUrlWithCache(url):

    filename = 'cache/{}'.format(re.sub("[^0-9a-zA-Z]+", "_", url.replace(BASE_URL, "")))

    currentTS = time.time()
    cacheMaxAge = 60 * 60 * 24 * 30
    generateCacheFile = True
    filecontent = "{}"
    if os.path.isfile(filename):
        fileModTime = os.path.getmtime(filename)
        timeDiff = currentTS - fileModTime
        if (timeDiff > cacheMaxAge):
            logging.debug("# CACHE file age %s too old: %s", timeDiff, filename)
        else:
            generateCacheFile = False
            logging.debug("(using cached file instead of url get)")
            with open(filename) as myfile:
                filecontent = "".join(line.rstrip() for line in myfile)

    if generateCacheFile:
        logging.debug("# URL HTTP GET %s ", filename)
        req = requests.get(url)
        if req.status_code > 399:
            logging.warning('  - Request result: HTTP %s - %s', req.status_code, url)

        open(filename, 'wb').write(req.content)
        filecontent = req.text
        # lets wat a bit, dont kill a public server
        time.sleep(1)

    jsn = json.loads(filecontent)
    if jsn.get('status') == 404:
        logging.warning('  - missing url: %s', url)
        return json.loads("{}")
    return jsn


def addToDict(my_dict, name, value):
    name = str(name)
    value = str(value)
    if name in my_dict:
        if value in my_dict[name]:
            my_dict[name][value] = my_dict[name][value] + 1
        else:
            my_dict[name][value] = 1
    else:
        my_dict[name] = {value: 1}


def addSum(my_dict, name, value):
    value = int(value) if value else 0
    if name in my_dict:
        my_dict[name] = my_dict[name] + value
    else:
        my_dict[name] = value


def collect_data_from_url(mstr_url, id_list, start_values, energietraeger_name):
    """ return Energieträger Type Anlagen, added to id_list """
    anlagen_json = readUrlWithCache(mstr_url)
    anlagen = anlagen_json.get('Data')

    query_results_count = int(anlagen_json.get('Total'))
    json_results_count = len(anlagen)
    if json_results_count < 1:
        return 0
    logging.info("Anlagen gesamt: %s", query_results_count)
    logging.info("Anlagen in result: %s", json_results_count)

    # Initialize values
    wanted_collections = {
        "Plz": {},
        "BetriebsStatusName": {},
        "EnergietraegerName": {},
        "PersonenArtId": {},
        "IsPilotwindanlage": {},
        "IsAnonymisiert": {}
    }
    wanted_sums = {
        "Nettonennleistung": 0,
        "Bruttoleistung": 0,
        "AnzahlSolarModule": 0
    }
    if (start_values):
        wanted_collections = start_values["Werte"]
        wanted_sums = start_values["Summen"]

    doppelt_count = 0
    # Add all anlagen values
    for anlage in anlagen:
        if anlage["EnergietraegerName"] != energietraeger_name:
            continue

        # Skip anlagen that we already have
        anlagen_id = anlage['MaStRNummer']
        if anlagen_id in id_list:
            doppelt_count = doppelt_count + 1
            continue
        id_list[anlagen_id] = 1

        wanted_sums["AnzahlAnlagen"] = (wanted_sums["AnzahlAnlagen"] + 1) if ("AnzahlAnlagen" in wanted_sums) else 1
        for wert in wanted_collections.keys():
            if wert in anlage:
                addToDict(wanted_collections, wert, anlage[wert])
        for wert in wanted_sums.keys():
            if wert in anlage:
                addSum(wanted_sums, wert, anlage[wert])

    logging.debug("Doppelte: %s", doppelt_count)

    return {"Summen": wanted_sums, "Werte": wanted_collections}


def write_json_file(data, outfile_name):
    with open(outfile_name, "w") as outfile:
        json.dump(data, outfile, ensure_ascii=True, indent=2, sort_keys=True)


def write_csv_file(data, HEAD_ROW, outfile_name):
    with open(outfile_name, 'w', newline='', encoding='utf-8') as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        outwriter.writerow(["DATEINAME"] + HEAD_ROW)
        for file_name, rows in data.items():
            for row in rows:
                outwriter.writerow([file_name] + row)


def save(URL, TYPE):
    """ Parse all result pages and write json File """
    custom_fig = Figlet(font=HEADLINE_FONT, width=120)
    logging.info("\n%s", custom_fig.renderText(TYPE[0:10]))

    exclude_ids = {}
    accumulated_results = None
    pagenr = 1
    while True:
        logging.info("# \\.")
        logging.info("####>>> Processing %s Anlagen - Page %s <<<", TYPE, pagenr)
        logging.info("# /°")
        page_url = URL + '&page=' + str(pagenr)
        response = collect_data_from_url(page_url, exclude_ids, accumulated_results, TYPE)
        if not response:
            logging.info("EMPTY PAGE - %s is done.", TYPE)
            break
        accumulated_results = response
        pagenr = pagenr + 1
    write_json_file(accumulated_results, f"anlagen_{TYPE.lower().replace(' ', '_')}.json")
    logging.info(pprint.pformat(accumulated_results))


save(SOURCE_URL, "Wind")
save(SOURCE_URL, "Solare Strahlungsenergie")
