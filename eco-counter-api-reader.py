# coding=utf-8
import json
import csv
from urllib.request import Request,urlopen
import config as cfg
import logging
import os
import re
from datetime import datetime
import time


token = cfg.eco_counter_token
outdir = '../radverkehr-zaehlstellen/'
sitefile = outdir + 'site.json'
infofile = outdir + 'SITE_INDEX.md'
startYear = 2019

api_url = cfg.eco_counter_api_url
wanted_ids = cfg.eco_counter_ids

content = ""

def read_api_url(endpoint):
    # read site data from api
    req = Request(api_url + endpoint)
    req.add_header("Authorization", "Bearer {}".format(token))
    req.add_header("Accept", "application/json")
    return urlopen(req).read().decode('utf-8')

def generate_filename(obj):
    return str(obj['id'])

    # no fancy names, just IDs
    name = obj['name'].lower()
    name = name.replace('ä', 'ae')
    name = name.replace('ß', 'ss')
    name = re.sub(r"[^\w\s]", '', name)
    name = re.sub(r"\s+", '-', name)
    return "{}-{}".format(obj['id'], name)

if os.path.exists(sitefile):

    # load cached site file
    f = open(sitefile, "r")
    content = f.read()

else:

    # read api sites and write cache file
    content = read_api_url('/site')
    with open(sitefile, 'w') as file:
        file.write(content)


sites = []

# parse sites data
sites_json = json.loads(content)


# Write Info-Markdown-File
with open(infofile, 'w') as ifile:
    print("======== Writing info- & site-files ========")
    print(" ==> Writing infofile: {}".format(infofile))
    ifile.write("# Daten der Fahrradzählstellen in Münster\n\n")
    ifile.write("Dieses Repository enthält die tagesaktuellen Daten der Radverkehr-Zählstellen in Münster. Die Daten werden jede Nacht aktualisiert.\n\n")
    ifile.write("Weitere Informationen zu den Daten in diesem Repository finden Sie auf dem Open-Data-Portal der Stadt Münster (https://opendata.stadt-muenster.de) sowie auf der Homepage des Amt für Mobilität und Tiefbau (https://www.stadt-muenster.de/verkehrsplanung/verkehr-in-zahlen/radverkehrszaehlungen).\n\n")
    ifile.write("Bitte beachten Sie bei der Nutzung dieser Daten, dass es sich um Rohdaten handelt. Diese Daten sind nicht bereinigt und es kann über längere Zeiträume Abweichungen geben (z.B. durch technische Störungen oder Baustellen vor den Zählstellen).\n\n")
    ifile.write("Die Daten stehen stehen unter der Lizenz 'Datenlizenz Deutschland Namensnennung 2.0' (https://www.govdata.de/dl-de/by-2-0).\n\n")
    ifile.write("**Sie finden die Ergebnisse der folgenden Radverkehr-Zählstellen in den entsprechenden Unterverzeichnissen:**\n\n")

    def getName(elem):
        return elem['name']
    sites_json.sort(key=getName)

    for site_json in sites_json:
        channels = []
        site_id = site_json['id']
        if site_id in wanted_ids:
            channels.append([site_id, site_json['name']])
            ifile.write(" * [{0}]({0}) - {1}\n".format(site_json['id'], site_json['name']))
            if 'channels' in site_json:
                for channel_json in site_json['channels']:
                    channels.append([channel_json['id'], channel_json['name']])
                    ifile.write("   * {0} - {1}\n".format(channel_json['id'], channel_json['name']))
            sites.append({
                "name": site_json['name'],
                "directory": generate_filename(site_json),
                "start": startYear if site_id != 100031300 else 2020, # date correction hack
                "channels": channels
            })


# write sites reduced json file
with open(outdir + 'site_min.json', 'w') as file:
    file.write(json.dumps(sites, indent=4))

# write all data files for all sites and channels into site subdirectories and create dirs if missing
for site in sites:
    currentDate = '{0}-{1:02d}'.format(datetime.now().year,datetime.now().month)
    sitedir = outdir + site['directory']
    if not os.path.isdir(sitedir):
        os.mkdir(sitedir)

    year = int(site['start'])
    month = 1
    processingMonth = '{0}-{1:02d}'.format(year,month)

    while processingMonth < currentDate:

        processingMonth = '{0}-{1:02d}'.format(year,month)
        startdate = '{0}-{1:02d}-01T00:00:00'.format(year,month)
        datafile = "{0}/{1}-{2:02d}.csv".format(sitedir,year,month)

        month+= 1
        if month>12:
            month=1
            year+=1
        enddate = '{0}-{1:02d}-01T00:00:00'.format(year,month)

        if (processingMonth == currentDate) or (not os.path.exists(datafile)):
            print("======== Reading {} // {} ========".format(processingMonth, site['name']))
            site_data = {}
            site_channels = []

            for channel in site['channels']:
                channel_id = channel[0]
                channel_name = channel[1]
                print(" > Channel {} {}".format(channel_id, channel_name))
                site_channels.append({"id": channel_id, "name": channel_name})
                channel_url = '/data/site/{}?begin={}&end={}&step=15m&complete=false'.format(channel_id, startdate, enddate)
                print(" > Url: {}".format(channel_url))
                channel_json = read_api_url(channel_url)
                channel_data = json.loads(channel_json)
                if not channel_data:
                    print(" => Empty response")
                #else:
                #    time.sleep(1)

                for entry in channel_data:
                    date = entry['date']
                    if not date in site_data:
                        site_data[date] = {}
                    site_data[date][channel_id] = [entry['counts'], entry['status']]

            if not site_data:
                print(" =>> Empty Site! Skipping file.")
            else:
                print(" ==> Writing: {}".format(datafile))
                with open(datafile, 'w') as csvfile:
                    csvfile = csv.writer(csvfile)

                    # Headline row: Time, channel-ids, and channel-ids + "-status"
                    channel_titles = ['Datetime']
                    for chan in site_channels:
                        channel_titles.append("{} ({})".format(chan['id'], chan['name']))
                    for chan in site_channels:
                        channel_titles.append("{}-status".format(chan['id']))
                    csvfile.writerow(channel_titles)

                    # Now write all channels into one csv file
                    for ctime, cdata in site_data.items():
                        row_data = [ctime[0:16].replace('T',' ')]
                        row_status = []
                        for chan in site_channels:
                            row_channel_id = chan['id']
                            if row_channel_id in cdata:
                                row_data.append(cdata[row_channel_id][0])
                                row_status.append(cdata[row_channel_id][1])
                            else:
                                row_data.append('')
                                row_status.append('')
                        csvfile.writerow([*row_data,*row_status])
