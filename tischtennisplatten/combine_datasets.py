
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
    # pylint: disable=consider-using-enumerate
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


def load_spielplaetze_geo():
    """Read all spielplätze, and calculate their coordinates"""
    logging.info("Reading %s", FILE_SPIELPLAETZE)
    spielplaetze_geodata = {}

    # Inputdata - CSV row format:
    # 0 ObjektNr;1 statBz;2 Rev; 3 RevierBezeichnung; 4 Objekt_Bezeichnung;
    # 5 Anzahl SpielG; 6 Nutzungsform; 7 Fläche in m2; 8 Koordinaten_X_Y; 9 gis_komplex_UTM
    with open(FILE_SPIELPLAETZE, 'r', newline='', encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        next(csvreader, None)
        for row in csvreader:
            spielplatzname = row[4]
            spielplatz_geo_raw = row[9]
            geomatch = re.search(r"\(([\d\.,\s]+)\)", spielplatz_geo_raw)
            if geomatch:
                spielplatz_polygon = geomatch.group(1)
                sp_vertices = re.split(",\s", spielplatz_polygon)
                inmap(lambda x:re.split("\s", x), sp_vertices)
                geocenter = centroid(sp_vertices)
                lat_lon = TRANSFORMER.transform(*geocenter)

                logging.info("Spielplatz '%s': %s ", spielplatzname, lat_lon)
                spielplaetze_geodata[spielplatzname] = ['Spielplatz', *lat_lon, row[6], row[0]]
            else:
                logging.error("Spielplatz '%s' no Geo %s", spielplatzname, spielplatz_geo_raw)

    return spielplaetze_geodata


def load_schulen_geo():
    """Read all schulen, and calculate their coordinates"""
    logging.info("Reading %s", FILE_SCHULEN)
    schulen_geodata = {}
    # Inputdata - CSV row format:
    # 0 X; 1 Y; 2 LFDNR; 3 NAME; 4 URL; 5 SchoolType
    with open(FILE_SCHULEN, 'r', encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        next(csvreader, None)
        for row in csvreader:
            schulname = row[3]
            lat_lon = TRANSFORMER2.transform(row[1], row[0])
            logging.info("Schule '%s': %s ", schulname, lat_lon)
            schulen_geodata[schulname]= ['Schule', *lat_lon, row[5], row[2]]

    return schulen_geodata


def load_sonstige_geo():
    """Read all sonstige"""
    logging.info("Reading %s", FILE_SONSTIGE)
    diverse_geodata = {}
    # Inputdata - CSV row format:
    # 0 Lookup name	; 1 Geokoordinaten ; 2 Typ ; 3 Genauer Standort? ; 4 Bemerkung
    with open(FILE_SONSTIGE, 'r', encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        next(csvreader, None)
        for row in csvreader:
            name = row[0]
            lat_lon = re.split(', ', row[1])
            logging.info("Sonstige '%s': %s ", name, lat_lon)
            diverse_geodata[name]= [row[2], float(lat_lon[0]), float(lat_lon[1]), '', '']

    return diverse_geodata


def write_json_file(data, outfile_name):
    """ Create and write output format: GeoJSON """

    logging.info("Writing GeoJSON...")

    features = []
    for key, val in enumerate(data):
        features.append(
          {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": val[0]
            },
            "properties": val[1]
          }
        )
    logging.info('FeatureCollection size: %s', len(features))
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    logging.info( "Writing file '%s'", outfile_name)
    with open(outfile_name, "w", encoding="utf-8") as outfile:
        json.dump(geojson, outfile, ensure_ascii=True, indent=2)


ALL_GEODATA = load_spielplaetze_geo()
ALL_GEODATA.update( load_schulen_geo() )
ALL_GEODATA.update( load_sonstige_geo() )


# print(json.dumps(ALL_GEODATA, sort_keys=True, indent=2))

spalten = ['LfdNr', 'Objektname','Objekttyp','Lat', 'Lon','Objekttyp2','ObjektID', 'BezirkID', 'ObjektID2', 'PlatteBezeichnung','PlatteBaujahr', 'PlatteMaterial', 'PlatteID']



def write_csv_and_collect_geojson_data():
    """ Enumerate all our data, write the CSV file, assemble the geojson point and property objects """
    logging.info('   -------- write_csv_and_collect_geojson_data --------    ')
    line = 0
    filtered_elements = []
    tischtennis_with_geodata = []
    with open('tischtennisplatten_muenster.csv', 'w', newline='', encoding="utf-8") as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        outwriter.writerow(spalten)
        with open(FILE_TISCHTENNISPLATTEN, newline='', encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
            next(csvreader, None) # discard headline row in csv
            for row in csvreader:
                # row = "0 ObjektID (Zusammengesetzter Monsterstring)";1"statistischerBezirk";2"Bezirk";3"ObjNr";4"Bezeichnung";5"Baujahr";6"Material"
                line = line + 1

                # First prepare the name of the Object for string matching
                rawname = row[0]
                tischname = rawname[9:]
                stringmatch = re.match(r'(.+?)[,;]', tischname)
                if stringmatch:
                    tischname = stringmatch.group(1)
                    logging.debug("%s ..Removing Adress String from '%s'", line, rawname)

                found = 0
                filtered = 0
                for key, place_infos in ALL_GEODATA.items():
                    contains_string = re.search(re.sub(r"[\+\(\)\-\.]", ".?", tischname), key, re.IGNORECASE)
                    if contains_string:
                        logging.info("%s Found %s .. %s", line, tischname, key)

                        # Check if it's really a Tischtennisplatte
                        is_tischtennisplatte = re.search('tischtennis', row[4], re.IGNORECASE)
                        if not is_tischtennisplatte:
                            logging.warning('%s filtering .. IS NOT A Tischtennisplatte: "%s"', line, row[4])
                            filtered_elements.append(row[4])
                            filtered = 1
                            continue

                        found = 1

                        # Write CSV
                        outwriter.writerow([line, tischname] + place_infos + row[2:]+ [rawname])

                        # Assemble data for GEOJSON
                        prettyname = key
                        platten_ort = place_infos[0]
                        if platten_ort != 'Schule':
                            prettyname = prettyname.title()
                        props = {
                            #   place_infos = 0 "Schule", 1 51.9601389602283, 2 7.64515656956438, 3 Details, 4 ID
                            'name': prettyname,
                            'ort': platten_ort,
                            'ortId': row[3],
                        }
                        if row[6]:
                            props['material'] = row[6]
                        if row[4]:
                            props['typ'] = row[4]
                        if row[5]:
                            props['baujahr'] = row[5]

                        tischtennis_with_geodata.append([
                            [place_infos[2], place_infos[1]],
                            props
                        ])
                        break

                if (not found) and not filtered:
                    logging.warning("%s NOT Found %s", line, tischname)
                    outwriter.writerow([line, tischname, "not found"])

    logging.warning('Filtered %s Datasets because not Tischtennisplatte: %s', len(filtered_elements), filtered_elements)

    return tischtennis_with_geodata

GEOJSON_DATA = write_csv_and_collect_geojson_data()

logging.info('GEOJSON_DATA: Got %s Datasets', len(GEOJSON_DATA))
write_json_file(GEOJSON_DATA, 'tischtennisplatten_muenster.geojson')
