# coding=utf-8
import json
import csv
from urllib.request import urlopen
import config as cfg

url = cfg.fahrradverleihe_url
outfile = 'data/fahrradverleihe.csv'
print("Data url:", url)

f = urlopen(url)
myfile = f.read()
#print(myfile)

data = json.loads(myfile)

    #cityName	"Billerbeck"
    #email	"..."
    #hasDelivery	false
    #hasEbikes	false
    #id	34
    #latitude	51.978301
    #longitude	7.295661
    #name	"..."
    #phone	"..."
    #street	"Holthauser Strasse 3"
    #website	"..."
    #zip	"48727"

with open(outfile, mode='w') as csv_file:
    fieldnames = ['name', 'street', 'zip', 'latitude', 'longitude', 'hasEbikes', 'hasDelivery']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for verleih in data['data']:
        if verleih['cityName'] == "Münster":
            del verleih["email"]
            del verleih["cityName"]
            del verleih["additionalInfo"]
            del verleih["phone"]
            del verleih["website"]
            del verleih["id"]
            print('Name: ' + verleih['name'])
            writer.writerow(verleih)
