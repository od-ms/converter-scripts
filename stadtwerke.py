# coding=utf-8
import json
import csv
from urllib.request import urlopen
import config as cfg
from pprint import pprint

url = cfg.stadtwerke_url
print("Data url:", url)
f = urlopen(url)
myfile = f.read()
data = json.loads(myfile)
path = 'data/'

def writeEntries(csv_file, category, headlines):
    print("Processing " + category)
    writer = csv.writer(csv_file, dialect='excel')
    writer.writerow(headlines)

    # for some reason items is not an array but a dictionary
    #    print(type(data['poiCategory1']['items']))
    for key, item in data[category]['items'].items():
        # pprint(item)
        writer.writerow([
            item['id'],
            item['name'],
            item['center'][0] if 'center' in item else '',
            item['center'][1] if 'center' in item else ''
        ])


outfile = path + 'haltestellen_barrierefrei.csv'
with open(outfile, mode='w') as csv_file:
    writeEntries(csv_file, 'poiCategory1', ['Haltestellen-Id', 'Name der barrierefreien Haltestelle', 'Latitude', 'Longitude'])

outfile = path + 'stadtwerke_bike_and_ride_stationen.csv'
with open(outfile, mode='w') as csv_file:
    writeEntries(csv_file, 'poiCategory2', ['Stations-Id', 'Name der Bike-And-Ride-Station', 'Latitude', 'Longitude'])

outfile = path + 'stadtwerke_park_and_ride_stationen.csv'
with open(outfile, mode='w') as csv_file:
    writeEntries(csv_file, 'poiCategory3', ['Stations-Id', 'Name der Park-and-Ride-Station', 'Latitude', 'Longitude'])

outfile = path + 'stadtwerke_elektrotankstellen.csv'
with open(outfile, mode='w') as csv_file:
    writeEntries(csv_file, 'poiCategory6', ['Id', 'Name der Elektrotankstelle', 'Latitude', 'Longitude'])


print("Done")