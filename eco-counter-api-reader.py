# coding=utf-8
import os
import re
import csv
import time
import json
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request,urlopen
import config as cfg

token = cfg.eco_apiv2_token
outdir = '../radverkehr-zaehlstellen/'
sitefile = outdir + 'site.json'
infofile = outdir + 'SITE_INDEX.md'
startYear = 2026 # angepasst auf die neuen Zählstellen, für die alten nehme man "2019"
startMonth = 6
force = 1

api_url = cfg.eco_apiv2_api_url
wanted_ids = cfg.eco_counter_ids

content = ""

def read_api_url(endpoint):
    """ read data from eco counter api """
    req = Request(api_url + endpoint)
    req.add_header("X-API-KEY", token)
    req.add_header("Accept", "application/json")
    try:
        response_obj = urlopen(req)
        response = response_obj.read().decode('utf-8')
    except URLError as e:
        print(e.reason)
        print(e.code)
        print(e.read())
        print(e)
        exit()

    ratelimit_remaining = int(response_obj.headers.get("X-RateLimit-Remaining"))
    sleep_time = 2
    if ratelimit_remaining < 10:
        sleep_time = 10
    if ratelimit_remaining < 3:
        sleep_time = 30
    print("Sleep {} seconds because RateLimit-Remaining: {}".format(sleep_time, ratelimit_remaining))
    time.sleep(sleep_time)

    return response


def get_mapped_status(status):
    if status == "raw": return 0
    return status


def generate_filename(obj):
    """ we could create fancy file & directory names,
        but as they keep changing (from the api) we don't do it"""
    return str(obj['id'])

    # code to generate fancy directorynames
    name = obj['name'].lower()
    name = name.replace('ä', 'ae')
    name = name.replace('ß', 'ss')
    name = re.sub(r"[^\w\s]", '', name)
    name = re.sub(r"\s+", '-', name)
    return "{}-{}".format(obj['id'], name)

if 0 and os.path.exists(sitefile):

    # load cached site file
    f = open(sitefile, "r")
    content = f.read()

else:

    # read api sites and write cache file
    content = read_api_url('/sites?include=domain,counters,tags,images,flows,segments,attributes')
    with open(sitefile, 'w') as file:
        file.write(content)


sites = []

# parse sites data
sites_json = json.loads(content)


# Write Info-Markdown-File
with open(infofile, 'w') as ifile:
    print("======== Writing info- & site-files ========")
    print(f" ==> Writing infofile: {infofile}")
    ifile.write("# Daten der Fahrradzählstellen in Münster\n\n")
    ifile.write("Dieses Repository enthält die tagesaktuellen Daten der Radverkehr-Zählstellen in Münster. Die Daten werden jede Nacht aktualisiert.\n\n")
    ifile.write("Weitere Informationen zu den Daten in diesem Repository finden Sie auf dem Open-Data-Portal der Stadt Münster (https://opendata.stadt-muenster.de) sowie auf der Homepage des Amt für Mobilität und Tiefbau (https://www.stadt-muenster.de/verkehrsplanung/verkehr-in-zahlen/radverkehrszaehlungen).\n\n")
    ifile.write("Bitte beachten Sie bei der Nutzung dieser Daten, dass es sich um Rohdaten handelt. Diese Daten sind nicht bereinigt und es kann über längere Zeiträume Abweichungen geben (z.B. durch technische Störungen oder Baustellen vor den Zählstellen).\n\n")
    ifile.write("Die Daten stehen stehen unter der Lizenz 'Datenlizenz Deutschland Namensnennung 2.0' (https://www.govdata.de/dl-de/by-2-0).\n\n")
    ifile.write("**Sie finden die Ergebnisse der folgenden Radverkehr-Zählstellen in den entsprechenden Unterverzeichnissen:**\n\n")

    def get_clean_channel_name(cname):
        """ remove unwanted strings from channels names """
        return cname.replace(' (real)', '').replace(' (virtual)', '')

    def getSortKey(elem):
        return elem['name']
    sites_json.sort(key=getSortKey)

    for site_json in sites_json:
        channels = []
        site_id = site_json['id']
        if site_id in wanted_ids:
            clean_channel_name = get_clean_channel_name(site_json['name']);
            # channels.append([site_id, clean_channel_name])
            ifile.write(" * [{0}]({0}) - {1}\n".format(site_json['id'], clean_channel_name))
            if 'flows' in site_json:
                for channel_json in site_json['flows']:
                    channels.append([channel_json['id'], get_clean_channel_name(channel_json['name'])])
                    ifile.write("   * {0} - {1}\n".format(channel_json['id'], get_clean_channel_name(channel_json['name'])))
            sites.append({
                "id": site_json['id'],
                "clean_name": clean_channel_name,
                "name": site_json['name'],
                "directory": generate_filename(site_json),
                "start": startYear,
                "channels": channels
            })


# write sites reduced json file
with open(outdir + 'site_min.json', 'w') as file:
    file.write(json.dumps(sites, indent=4))

# write all data files for all sites and channels into site subdirectories and create dirs if missing
for site in sites:
    currentDate = '{0}-{1:02d}'.format(datetime.now().year,datetime.now().month)
    currentExactDate = '{0}-{1:02d}-{2:02d}'.format(datetime.now().year,datetime.now().month,datetime.now().day)
    sitedir = outdir + site['directory']
    if not os.path.isdir(sitedir):
        os.mkdir(sitedir)

    year = int(site['start'])
    month = startMonth
    processingMonth = '{0}-{1:02d}'.format(year,month)

    dont_process_counter_if_latest_file_is_there = 0
    if (dont_process_counter_if_latest_file_is_there):
        latest_file_filename = "{0}/{1}-{2:02d}.csv".format(sitedir, datetime.now().year, datetime.now().month)
        if os.path.exists(latest_file_filename):
            print(f"   <***> SKIPPING site {site['name']}")
            continue

    while processingMonth < currentDate:

        processingMonth = '{0}-{1:02d}'.format(year,month)
        startdate = '{0}-{1:02d}-01'.format(year,month)
        datafile = "{0}/{1}-{2:02d}.csv".format(sitedir,year,month)

        month+= 1
        if month>12:
            month=1
            year+=1
        enddate = '{0}-{1:02d}-01'.format(year,month)
        if enddate > currentExactDate:
            enddate = currentExactDate

        if (processingMonth == currentDate) or force or (not os.path.exists(datafile)):
            print("======== Reading {} // {} ========".format(processingMonth, site['name']))
            site_data = {}
            site_channels = []

            site_url = '/history/traffic/aggregated?siteId={}&include=status&granularity=PT15M&startDate={}&endDate={}&startTime=00:00&endTime=00:00&gapFilling=false'.format(site['id'], startdate, enddate)
            print(" > Site Data Url: {}".format(site_url))
            site_row_json = read_api_url(site_url)
            site_row_data = json.loads(site_row_json)
            channel_id = site["id"]
            site_channels.append({"id": site["id"], "name": site["clean_name"]})
            for entry in site_row_data[0]["data"]:
                date = entry['timestamp'] # e.g.'2026-06-01T00:00:00+02:00'
                if not date in site_data:
                    site_data[date] = {}
                site_data[date][channel_id] = [int(float(entry['traffic']['counts'])), get_mapped_status(entry['traffic']['status'][0])]
            
            channel_url = '/history/traffic/raw?siteId={}&include=status&startDate={}&endDate={}&startTime=00:00&endTime=00:00&gapFilling=false'.format(site['id'], startdate, enddate)
            print(" > Site Raw Channel Data Url: {}".format(channel_url))
            channel_json = read_api_url(channel_url)
            channel_data = json.loads(channel_json)

            for channel in channel_data:
                channel_id = channel['flowID']
                channel_name = get_clean_channel_name(channel['flowName'])
                print(" > Channel {} {}".format(channel_id, channel_name))
                site_channels.append({"id": channel_id, "name": channel_name})
                if not channel["data"]:
                    print(" => Empty response")

                for entry in channel["data"]:
                    if entry["granularity"] != "PT15M":
                        print(" =>> Skipping entry with granularity {}".format(entry["granularity"]))
                        continue
                    date = entry['timestamp']
                    if not date in site_data:
                        site_data[date] = {}
                    site_data[date][channel_id] = [int(float(entry['counts'])), get_mapped_status(entry['status'][0])]

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
