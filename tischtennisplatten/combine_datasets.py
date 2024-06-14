
# -*- coding: UTF-8 -*-

import re
import json
import logging
import csv
from decimal import Decimal
from datetime import datetime, timezone
from pyproj import Transformer

# file -bi Spielplaetze_Stadt_MS_06_22.csv
#       Antwort z.B.: text/plain; charset=iso-8859-1
# iconv -f ISO-8859-1 -t UTF-8//TRANSLIT Spielplaetze_Stadt_MS_06_22.csv -o Spielplaetze_2022.csv

FILE_SPIELPLAETZE = 'Spielplaetze_2022.csv'
FILE_SCHULEN = 'Schulen.csv'
FILE_SONSTIGE = 'Manuelle_Eintraege.csv'
FILE_TISCHTENNISPLATTEN = 'Tischtennisplatten2024.csv'

TRANSFORMER = Transformer.from_crs("EPSG:32632", "EPSG:4326")
TRANSFORMER2 = Transformer.from_crs("EPSG:31467", "EPSG:4326")

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())



def centroid(vertices):
    """calculate the center of a polygon"""
    x, y = 0, 0
    n = len(vertices)
    signed_area = 0
    for i in range(len(vertices)):
        x0, y0 = vertices[i]
        x1, y1 = vertices[(i + 1) % n]
        x0 = Decimal(x0)
        x1 = Decimal(x1)
        y0 = Decimal(y0)
        y1 = Decimal(y1)
        # shoelace formula
        area = (x0 * y1) - (x1 * y0)
        signed_area += area
        x += (x0 + x1) * area
        y += (y0 + y1) * area
    signed_area *= Decimal(0.5)
    x /= 6 * signed_area
    y /= 6 * signed_area
    return x, y


def inmap(f, x):
    """modify all elemenets of a LIST in place"""
    for i, v in enumerate(x):
            x[i] = f(v)


def load_spielplaetze():
    """Read all spielplätze, and calculate their coordinates"""
    DATA_SPIELPLAETZE = {}
    # 0 ObjektNr;1 statBz;2 Rev; 3 RevierBezeichnung; 4 Objekt_Bezeichnung; 5 Anzahl SpielG; 6 Nutzungsform; 7 Fläche in m2; 8 Koordinaten_X_Y; 9 gis_komplex_UTM

    logging.info("Reading %s", FILE_SPIELPLAETZE)
    with open(FILE_SPIELPLAETZE, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        discard_headers = next(csvreader, None)
        for row in csvreader:
            spielplatzname = row[4]
            spielplatz_geo_raw = row[9]
            geomatch = re.search(r"\(([\d\.,\s]+)\)", spielplatz_geo_raw)
            if geomatch:
                spielplatz_polygon = geomatch.group(1);
                sp_vertices = re.split(",\s", spielplatz_polygon)
                inmap(lambda x:re.split("\s", x), sp_vertices)
                geocenter = centroid(sp_vertices)
                lat_lon = TRANSFORMER.transform(*geocenter)

                logging.info("Spielplatz '%s': %s ", spielplatzname, lat_lon)
                DATA_SPIELPLAETZE[spielplatzname] = ['Spielplatz', *lat_lon, row[6], row[0]]
            else:
                logging.error("Spielplatz '%s' no Geo %s", spielplatzname, spielplatz_geo_raw)

    return DATA_SPIELPLAETZE


def load_schulen():
    """Read all schulen, and calculate their coordinates"""
    DATA_SCHULEN = {}
    # 0 X; 1 Y; 2 LFDNR; 3 NAME; 4 URL; 5 SchoolType
    logging.info("Reading %s", FILE_SCHULEN)
    with open(FILE_SCHULEN, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        discard_headers = next(csvreader, None)
        for row in csvreader:
            schulname = row[3]
            lat_lon = TRANSFORMER2.transform(row[1], row[0])
            logging.info("Schule '%s': %s ", schulname, lat_lon)
            DATA_SCHULEN[schulname]= ['Schule', *lat_lon, row[5], row[2]]

    return DATA_SCHULEN


def load_sonstige():
    """Read all sonstige"""
    DATA = {}
    # 0 NAME; 1 Geo
    logging.info("Reading %s", FILE_SONSTIGE)
    with open(FILE_SONSTIGE, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in csvreader:
            name = row[0]
            lat_lon = re.split(', ', row[1])
            logging.info("Sonstige '%s': %s ", name, lat_lon)
            DATA[name]= [row[2], *lat_lon, '', '']

    return DATA



ALL_DATA = load_spielplaetze()
ALL_DATA.update( load_schulen() )
ALL_DATA.update( load_sonstige() )


print(json.dumps(ALL_DATA, sort_keys=True, indent=2))

spalten = ['LfdNr', 'Objektname','Objekttyp','Lat', 'Lon','Objekttyp2','ObjektID', 'BezirkID', 'ObjektID2', 'PlatteBezeichnung','PlatteBaujahr','PlatteMaterial']

line = 0
with open('tischtennisplatten_merge.csv', 'w', newline='') as outfile:
    outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    outwriter.writerow(spalten)
    with open(FILE_TISCHTENNISPLATTEN, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        discard_headers = next(csvreader, None)
        for row in csvreader:
            rawname = row[0]
            tischname = rawname[9:]
            stringmatch = re.match(r'(.+?)[,;]', tischname)
            if stringmatch:
                tischname = stringmatch.group(1);
                logging.info("Tischtennisplatte '%s': %s ", tischname, rawname)

            line = line + 1
            found = 0
            for key in ALL_DATA:
                contains_string = re.search(re.sub(r"[\+\(\)\-\.]", ".?", tischname), key, re.IGNORECASE)
                if contains_string:
                    logging.info("%s Found %s .. %s", line, tischname, key)
                    found = 1
                    outwriter.writerow([line, tischname] + ALL_DATA[key] + row[2:])
                    break

            if not found:
                logging.warning("%s NOT Found %s", line, tischname)
                outwriter.writerow([line, tischname, "not found"])



