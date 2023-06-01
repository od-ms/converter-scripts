
# -*- coding: UTF-8 -*-

import re
import json
import random
import logging
import requests
import os.path
import pprint
import time
import csv
import os
from pyfiglet import Figlet
from datetime import datetime, timezone



# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
fonts = (
    'puffy slant smslant speed standard thick basic bell c_ascii_ charact1 charact2 charact6 chunky clr6x8 colossal '
    'contessa cosmic crawford demo_1__ drpepper fender graceful gothic'
)
HEADLINE_FONT = random.choice(fonts.split())
logging.debug("(headline font = '%s')", HEADLINE_FONT)


BASE_URL = 'https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetVerkleinerteOeffentlicheEinheitStromerzeugung?'

# Ok, das ist zwei mal die gleiche URL, nur mit Sortierung einmal von vorn und einmal von hinten
# Weil Limit von denen ist bei 5000 Ergebnisse. Derzeit gibt es ca. 6000 Anlagen.
# Wenn wir einmal von vorn und einmal von hinten abfragen, bekommen wir alle Anlagen.
#
# !!Sollten das mehr als 10.000 werden, dann gibts aber Problem, dann stimmen die Zahlen nicht mehr
# und das muss umprogrammiert werden!!
# Idee für Workaround: Anlagen > 10 kW, Anlagen < 10 kW und Anlagen == 10 kW
#
#
SOURCE_URLS = [
    BASE_URL + 'sort=EinheitMeldeDatum-asc&page=1&pageSize=10000&group=&filter=Energietr%C3%A4ger~eq~%272495%2C2497%27~and~Betriebs-Status~eq~%2735%2C37%27~and~Gemeindeschl%C3%BCssel~eq~%2705515000%27~and~Ort~eq~%27M%C3%BCnster%27',
    BASE_URL + 'sort=EinheitMeldeDatum-desc&page=1&pageSize=10000&group=&filter=Energietr%C3%A4ger~eq~%272495%2C2497%27~and~Betriebs-Status~eq~%2735%2C37%27~and~Gemeindeschl%C3%BCssel~eq~%2705515000%27~and~Ort~eq~%27M%C3%BCnster%27'
]

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
    value = value if value else 0
    if name in my_dict:
        my_dict[name] = my_dict[name] + value
    else:
        my_dict[name] = value


def collect_data_from_url(mstr_url, id_list, start_values, EnergietraegerName):
    anlagenJson = readUrlWithCache(mstr_url)
    anlagen = anlagenJson.get('Data')

    query_results_count = int(anlagenJson.get('Total'))
    json_results_count = len(anlagen)
    logging.info("Anlagen gesamt: %s", query_results_count)
    logging.info("Anlagen in result: %s", json_results_count)
    if (query_results_count / 2) > json_results_count:
        logging.error("TOO MANY ANLAGEN IN QUERY RESULT! ")
        raise ValueError("Please update program code, we need more than 2 requests")

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
        "Bruttoleistung": 0,
        "AnzahlSolarModule": 0
    }
    if (start_values):
        wanted_collections = start_values["Werte"]
        wanted_sums = start_values["Summen"]

    doppelt_count = 0
    # Add all anlagen values
    for anlage in anlagen:
        if anlage["EnergietraegerName"] != EnergietraegerName:
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


def save(URLS, TYPE):
    custom_fig = Figlet(font=HEADLINE_FONT, width=120)
    logging.info("\n" + custom_fig.renderText(TYPE))

    logging.info("# \\.")
    logging.info("####>>> Processing %s Anlagen <<<", TYPE)
    logging.info("# /°")

    EXCLUDE_IDs = {}
    RESULT_DATA = None
    for URL in URLS:
        RESULT_DATA = collect_data_from_url(URL, EXCLUDE_IDs, RESULT_DATA, TYPE)
    write_json_file(RESULT_DATA, "anlagen_{}.json".format(TYPE.lower().replace(" ", "_")))
    logging.info(pprint.pformat(RESULT_DATA))


save(SOURCE_URLS, "Wind")
save(SOURCE_URLS, "Solare Strahlungsenergie")
