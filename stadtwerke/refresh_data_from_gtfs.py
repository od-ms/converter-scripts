#!/usr/bin/env python
# coding=utf-8
"""
This script loads Data files from Stadtwerke-Netzplan
And saves them as geojson and csv
"""

import os
import csv
import json
import random
import wget
import logging
from datetime import datetime
import pyfiglet
import zipfile


# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())

# Nicer log files with random fonts
HEADLINE_FONT = random.choice(pyfiglet.FigletFont.getFonts())
FONT2 = random.choice(pyfiglet.FigletFont.getFonts())
logging.debug("(headline font = '%s', font2 = '%s')", HEADLINE_FONT, FONT2)


def main(): 
  """Hauptmethode, hier passieren die wichtigen Dinge"""
  
  gtfs_url = "https://api.busradar.conterra.de/data/stadtwerke_feed.zip" # redirected from https://www.stadtwerke-muenster.de/Externe%20Links/GTFS%20Open%20Data"
  
  os.chdir("cache/")
  zip_filename = "gtfs.zip"
  output_file = "../data/haltestellen.geojson"

  if not os.path.isfile(zip_filename):
      logging.info("Downloading GTFS data")
      wget.download(gtfs_url, out=zip_filename)

  logging.info("Extracting GTFS data from %s", zip_filename)
  zipfile.ZipFile(zip_filename).extractall()
  
  logging.info("Converting stops.txt to GeoJSON")
  stops_geojson = {"type": "FeatureCollection", "features": []}
  
  with open("stops.txt", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
      feature = {
        "type": "Feature",
        "properties": {name: value for name, value in row.items() if value and (name not in ["stop_lat", "stop_lon"])},
        "geometry": {
          "type": "Point",
          "coordinates": [float(row["stop_lon"]), float(row["stop_lat"])]
        }
      }
      stops_geojson["features"].append(feature)
    
  with open(output_file, "w", encoding="utf-8") as f:
    json.dump(stops_geojson, f, indent=2)
  
  logging.info("Saved %d stops to %s", len(stops_geojson["features"]), output_file)


def big_debug_text(text, font=HEADLINE_FONT):
  """ Write some fancy big text into log-output """
  custom_fig = pyfiglet.Figlet(font=font, width=120)
  logging.info("\n\n%s", custom_fig.renderText(text))


big_debug_text("START..")

main()

big_debug_text("DONE!")
