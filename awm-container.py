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
###     https://awm.stadt-muenster.de/abfuhrtermine-und-entsorgungsstandorte
###        a) Choose desired container type
###        b) "Bitte den Stadtteil auswählen: 'alle Stadtteile'"
###        c) Click on any "Standort"
###        d) A map with all positions will show. Check the network requests.
###        e) Save response json to this subdirectory "data/"
###        f) repeat 3 times (all container types: kleider, elektro, glas)
###
### STEP 2: Run this script
###     JSON files will be converted to CSV, CSV-files will be written to "data/" dir
###


path = 'data/'
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

    outfile = path + file + '.csv'
    with open(outfile, mode='w') as csv_file:

        writer = csv.writer(csv_file, dialect='excel')
        writer.writerow(['Nr', 'Containertyp', 'Standort1', 'Standort2', 'Standort3', 'Latitude', 'Longitude', 'Datum'])

        # for some reason items is not an array but a dictionary
        #    print(type(data['poiCategory1']['items']))
        counter = 0
        for item in data:
            counter = counter + 1
            LOGGER.info(" %s / %s", counter, item['inf'][1])
            writer.writerow([
                counter,
                containertype,
                item['inf'][0],
                item['inf'][1],
                item['inf'][2],
                item['lat'],
                item['lng'],
                ("{}".format(TODAY))[0:10]
            ])



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