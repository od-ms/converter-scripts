# coding=utf-8
import json
import csv
from datetime import datetime
import logging

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')

LOGGER = logging.getLogger(__name__)
TODAY = datetime.now()

LOGGER.info("=====> START %s <=====", TODAY)


###
### STEP 1: Download data files from AWM website:
###     https://awm.stadt-muenster.de/verwertung-entsorgung/sammlung-services/altglascontainer
###     bzw. einfach unter:
###     https://www.muellmax.de/abfallkalender/awm/res/AwmStart.php
###     Then:
###        a) Choose desired container type
###        b) "Bitte den Stadtteil auswählen: 'alle Stadtteile'"
###        c) Click on any "Standort" (click the map pin icon on the right)
###        d) A map with all positions will show. Check the network tab for xhr request "AwmStart".
###        e) Save response json to the subdirectory "data/" als files with ending ".json"
###        f) repeat 3 times (all container types: kleider, elektro, glas)
###
### STEP 2: Run this script
###     in directory "../data/": "awm-$xyz.json" files will be parsed and written to ".csv" and ".geojson"
###


path = '../data/'
files = [
    ['awm-glascontainer', 'Glascontainer'],
    ['awm-altkleider', 'Altkleidercontainer'],
    ['awm-elektrokleingeraete', 'Elektrokleingeräte-Container']
]



for config in files:
    file = config[0]
    containertype = config[1]
    LOGGER.info("Starting %s / %s", file, containertype)

    f = open(path + file + '.json', "r")
    myfile = f.read()
    data = json.loads(myfile)

    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    outfile = path + file + '.csv'
    with open(outfile, mode='w') as csv_file:

        writer = csv.writer(csv_file, dialect='excel')
        writer.writerow(['Containertyp', 'Standort1', 'Standort2', 'Standort3', 'Latitude', 'Longitude'])

        # for some reason items is not an array but a dictionary
        #    print(type(data['poiCategory1']['items']))
        counter = 0
        for item in data:
            counter = counter + 1
            if "inf" in item:
                LOGGER.info(" %s / %s", counter, item)
                writer.writerow([
                    containertype,
                    item['inf'][0],
                    item['inf'][1],
                    item['inf'][2],
                    item['lat'],
                    item['lng']
                ])

                feature = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(item['lng']), float(item['lat'])]},
                    "properties": {
                        "Typ": containertype,
                        "Stadtteil": item['inf'][0],
                        "Standort": item['inf'][1]
                    }
                }
                geojson["features"].append(feature)
        writer.writerow(['Erstellungsdatum:', "{}".format(TODAY)[0:10], "", "", "", "", ""])

    outfile = path + file + '.geojson'
    LOGGER.info("Writing Geojson file '%s' ", outfile)
    with open(outfile, mode='w') as json_file:
        json.dump(geojson, json_file, indent=2)





# JSON FORMAT
# {
#  "inf": [
#    "48151 M\u00fcnster - Aaseestadt",
#    "Lange Ossenbeck, vor Nr. 9",
#    ""],
#  "lat": "51.937202",
#  "lng": "7.597586"
# }


print("Done")
