



# -*- coding: UTF-8 -*-

import re
import csv
import time
import random
import logging
import os
from datetime import datetime, timezone, timedelta
import requests
import pyfiglet
import zipfile


# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
HEADLINE_FONT = random.choice(pyfiglet.FigletFont.getFonts())
HEADLINE_FINT = "future"
logging.debug("(headline font = '%s')", HEADLINE_FONT)


# Base config
CACHEDIR = 'cache/'
BASE_URL = 'https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/'
BASEFILE = 'Unfallorte{}_EPSG25832_CSV.zip'
FILES = [
    'Unfallorte2016_LinRef.txt', 'Unfallorte2017_LinRef.txt',  #'Unfallorte2021_EPSG25832_CSV.csv' ,
    'Unfallorte2018_LinRef.txt', 'Unfallorte2019_LinRef.txt', 'Unfallorte2020_LinRef.csv',
    'Unfallorte2021_LinRef.csv', 'Unfallorte2022_LinRef.csv', 'Unfallorte2023_LinRef.csv'
]
OUTPUT_FILE = 'unfaelle-muenster.csv'


# the following is currently unused, still maybe interesting
fileformats = {
    2016: 'FID;OBJECTID;ULAND;UREGBEZ;UKREIS;UGEMEINDE;UJAHR;UMONAT;USTUNDE;UWOCHENTAG;UKATEGORIE;UART;UTYP1;ULICHTVERH;IstStrasse;IstRad;IstPKW;IstFuss;IstKrad;IstGkfz;IstSonstig;LINREFX;LINREFY;XGCSWGS84;YGCSWGS84',
    # 0;1;01;0;53;120;2016;01;09;5;2;8;1;0;2;0;1;0;0;0;0;606982,393999999970000;5954659,924999999800000;10,621659329000000;53,729614888000000
    2017: 'OBJECTID;UIDENTSTLA;ULAND;UREGBEZ;UKREIS;UGEMEINDE;UJAHR;UMONAT;USTUNDE;UWOCHENTAG;UKATEGORIE;UART;UTYP1;IstRad;IstPKW;IstFuss;IstKrad;IstSonstig;LICHT;STRZUSTAND;LINREFX;LINREFY;XGCSWGS84;YGCSWGS84',
    # 1;01170113152013852017;01;0;55;012;2017;01;05;6;2;9;1;0;1;0;0;0;2;2;605079,422900000010000;6001757,554700000200000;10,609031240000036;54,153150062000066
    2018: 'OBJECTID_1;ULAND;UREGBEZ;UKREIS;UGEMEINDE;UJAHR;UMONAT;USTUNDE;UWOCHENTAG;UKATEGORIE;UART;UTYP1;ULICHTVERH;IstRad;IstPKW;IstFuss;IstKrad;IstGkfz;IstSonstig;STRZUSTAND;LINREFX;LINREFY;XGCSWGS84;YGCSWGS84'
    # 1;01;0;03;000;2018;01;08;5;2;0;7;0;1;0;0;0;0;0;0;612054,341999999950000;5969634,006000000100000;10,703950299000041;53,863081147000059

}


# Daten 2021
# Schlüssel-nummer	Regionale Bezeichnung			    Fläche     Bevölkerung
#		Kreis / Landkreis	                NUTS3	    km2        insgesamt	männlich	weiblich	je km2
#055	Reg.-Bez. Münster
#05512	Kreisfreie Stadt	Bottrop, Stadt	DEA31	    100,62	   117 311	   57 069	   60 242	   1 166
#05513	Kreisfreie Stadt	Gelsenkirchen, 	DEA32	    104,94	   260 126	   129 271	   130 855	   2 479
#05515	Kreisfreie Stadt	Münster, Stadt	DEA33	    303,28	   317 713	   152 515	   165 198	   1 048
#05554	Kreis	            Borken	        DEA34	   1 420,98	   373 582	   186 654	   186 928	    263
#05558	Kreis	            Coesfeld	    DEA35	   1 112,04	   221 352	   109 210	   112 142	    199
#05562	Kreis	            Recklinghausen	DEA36	    761,48	   612 801	   298 416	   314 385	    805
#05566	Kreis	            Steinfurt	    DEA37	   1 795,75	   450 176	   223 922	   226 254	    251
#05570	Kreis	            Warendorf	    DEA38	   1 319,42	   278 176	   137 425	   140 751	    211
#    ^ numbers used in the result file

def big_debug_text(text):
    """ Write some fancy big text into log-output """
    custom_fig = pyfiglet.Figlet(font=HEADLINE_FONT, width=120)
    logging.info("\n\n%s", custom_fig.renderText(text))


def downloadFileToCache(url):
    """ repeated runs of this script will use the same cache file for 1 month """

    filename = CACHEDIR + '{}'.format(re.sub("[^0-9a-zA-Z._]+", "_", url.replace(BASE_URL, "")))

    currentTS = time.time()
    cacheMaxAge = 60 * 60 * 24 * 365
    generateCacheFile = True
    filecontent = "{}"
    if os.path.isfile(filename):
        fileModTime = os.path.getmtime(filename)
        timeDiff = currentTS - fileModTime
        if timeDiff > cacheMaxAge:
            logging.debug("# CACHE file age %s too old: %s", timeDiff, filename)
        else:
            generateCacheFile = False
            filename = ""
            logging.debug("(using cached file instead of url get)")

    if generateCacheFile:
        logging.debug("# URL HTTP GET %s ", filename)
        req = requests.get(url, timeout=120)
        if req.status_code > 399:
            logging.warning('  - Request result: HTTP %s - %s', req.status_code, url)

        open(filename, 'wb').write(req.content)
        time.sleep(1)

    return filename


def download_and_unzip_data():
    for year in range(2016, 2024):
        big_debug_text(f"Load {year}")

        fileurl = BASE_URL + BASEFILE.format(year)
        filename = downloadFileToCache(fileurl)
        if filename:
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(CACHEDIR)


def combine_csv_files():

    csv.register_dialect('semikolon', delimiter=';')
    csv.register_dialect('komma', delimiter=',')
    WANTED_FIELDS_STR = 'ULAND;UREGBEZ;UKREIS;UGEMEINDE;UJAHR;UMONAT;USTUNDE;UWOCHENTAG;UKATEGORIE;UART;UTYP1;ULICHTVERH;IstRad;IstPKW;IstFuss;IstKrad;IstGkfz;IstSonstige;LINREFX;LINREFY;XGCSWGS84;YGCSWGS84;STRZUSTAND;UIDENTSTLAE'
    WANTED_FIELDS = WANTED_FIELDS_STR.split(";")

    alle_unfaelle = []

    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    outfile = OUTPUT_FILE
    with open(outfile, mode='w') as csv_file:

        writer = csv.writer(csv_file, dialect='excel')
        writer.writerow(WANTED_FIELDS)

        for file in FILES:
            filenr = 0
            with open(CACHEDIR + 'csv/' + file, 'r', newline='', encoding="utf-8") as csvfile:
                filenr = filenr + 1
                big_debug_text(f"{filenr}. {file}")
                logging.info("==========> processing file %s: %s", filenr, file)

                csvreader = csv.DictReader(csvfile, dialect='semikolon')
                rownr = 0
                for row in csvreader:
                    if rownr == 0:
                        logging.debug("keys: %s", list(row.keys()))
                        logging.debug("vals: %s", list(row.values()))
                    rownr = rownr + 1
                    if (int(row['ULAND']) == 5) and (int(row['UREGBEZ']) == 5):
                        resultrow = {}
                        for field in WANTED_FIELDS:
                            if field in row:
                                resultrow[field] = row[field]
                            else:
                                resultrow[field] = ''
                                if rownr % 1000 == 0:
                                    logging.debug("%s/%s '%s' not found", filenr, rownr, field)

                        # Fix some field names that changed over time
                        if "IstSonstig" in row:
                            resultrow['IstSonstige'] = row['IstSonstig']
                        if "IstStrassenzustand" in row:
                            if rownr % 1000 == 0:
                                logging.debug("%s/%s IstStrassenzustand found", filenr, rownr)
                            resultrow['STRZUSTAND'] = row['IstStrassenzustand']
                        if "USTRZUSTAND" in row:
                            if rownr % 1000 == 0:
                                logging.debug("%s/%s USTRZUSTAND found", filenr, rownr)
                            resultrow['STRZUSTAND'] = row['USTRZUSTAND']

                        # Convert german comma to decimal dot
                        for field in ['LINREFX','LINREFY','XGCSWGS84','YGCSWGS84']:
                            resultrow[field] = resultrow[field].replace(',','.')

                        # Finally write row
                        finalrow = []
                        for field in WANTED_FIELDS:
                            finalrow.append(resultrow[field])
                        writer.writerow(finalrow)


download_and_unzip_data()

combine_csv_files()



