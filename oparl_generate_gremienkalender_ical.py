# -*- coding: UTF-8 -*-

import re
import json
import logging
import requests
import os.path
import time
import csv
import os

from datetime import datetime, timezone

from icalendar import Calendar, Event, vCalAddress, vText
import pytz

# Config
OPARL_BASE_URL = 'https://oparl.stadt-muenster.de/'
OPARL_MEETING_URL = 'https://www.stadt-muenster.de/sessionnet/sessionnetbi/si0057.php?__ksinr={}'
OUTPUT_FILE_ICS = 'ratsinformation_termine.ics'
OUTPUT_FILE_CSV = 'ratsinformation_termine.csv'

SKIP_EMPTY_ORGANIZATION_NAMES = True
CONFIG_EXPORT_YEAR = "2024"


# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())


def writeIcal(calendarItems):
    """
    Write ICAL and CSV files
    """

    cal = Calendar()
    cal.add('prodid', '-//Gremien Kalender//opendata.stadt-muenster.de//')
    cal.add('version', '2.0')

    with open(OUTPUT_FILE_CSV, 'w', newline='') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['MeetingID', 'Start', 'Ende', 'Gremium', 'Veranstaltung', 'Ort', 'Weitere Information'])

        for key, session in sorted(calendarItems.items()):

            # Prepare event title (and convert datestrings to datetime objects with timezone)
            meetingId = session[5]
            sessionName = session[2]
            committee = session[3]
            location = session[4]
            start = datetime.strptime(session[0], "%Y-%m-%dT%H:%M:%S%z")
            end = datetime.strptime(session[1], "%Y-%m-%dT%H:%M:%S%z")
            meetingUrl = OPARL_MEETING_URL.format(meetingId)
            logging.info("Adding ical: %s %s %s", start, committee, sessionName)

            # Create ical event (and convert datetimes to UTC)
            event = Event()
            event.add('summary', '{} - {}'.format(committee, sessionName))
            event.add('dtstart', start.astimezone(pytz.utc))
            event.add('dtend', end.astimezone(pytz.utc))
            event.add('dtstamp', datetime.now())
            event.add('description', meetingUrl)
            event.add('uid', '20220215T101010/{}@ms'.format(meetingId))

            organizer = vCalAddress('MAILTO:opendata@citeq.de')
            organizer.params['cn'] = vText('Stadt Münster')
            organizer.params['role'] = vText('Ratsinformationssytem')
            event['organizer'] = organizer
            event['location'] = vText(location)

            # Add event to calendar
            cal.add_component(event)

            # Add event to CSV
            csvWriter.writerow([meetingId, str(start), str(end), committee, sessionName, location, meetingUrl])


    # Write ical file
    f = open(OUTPUT_FILE_ICS, 'wb')
    f.write(cal.to_ical())
    f.close()



def getDictValueFailsafe(target_dict, keys):
    node_value = ''
    try:
        if len(keys) == 4:
            node_value = target_dict[keys[0]][keys[1]][keys[2]][keys[3]]
        elif len(keys) == 3:
            node_value = target_dict[keys[0]][keys[1]][keys[2]]
        elif len(keys) == 2:
            node_value = target_dict[keys[0]][keys[1]]
        elif len(keys) == 1:
            node_value = target_dict[keys[0]]
        else:
            raise Exception("get_nested_json_value() not implemented for {} keys in: {}".format(len(keys), keys))

    except (TypeError, KeyError, IndexError):
        logging.debug("Did not find key %s", keys)

    return node_value


def readUrlWithCache(url):

    filename = 'cache/{}'.format(re.sub("[^0-9a-zA-Z]+", "_", url.replace(OPARL_BASE_URL, "")))

    currentTS = time.time()
    cacheMaxAge = 60*60*24*30
    generateCacheFile = True
    filecontent = "{}"
    if os.path.isfile(filename):
        fileModTime = os.path.getmtime(filename)
        timeDiff = currentTS - fileModTime
        if (timeDiff > cacheMaxAge):
            logging.debug("cache file age %s too old: %s", timeDiff, filename)
        else:
            generateCacheFile = False
            logging.debug("%s - using cache", filename)
            with open(filename) as myfile:
                filecontent ="".join(line.rstrip() for line in myfile)

    if generateCacheFile:
        logging.debug("%s - HTTP GET", filename)
        req = requests.get(url)
        if req.status_code > 399:
            logging.warning('Request result: HTTP %s - %s', req.status_code, url)

        open(filename, 'wb').write(req.content)
        filecontent = req.text
        # lets wat a bit, dont kill a public server
        time.sleep(1)

    jsn = json.loads(filecontent)
    if jsn.get('status') == 404:
        logging.warning('missing url: %s', url)
        return json.loads("{}")
    return jsn


def getOrganizations():

    orgUrlTemplate = OPARL_BASE_URL + 'bodies/0001/organizations?page={}'
    logging.debug("Organziation URL: %s", orgUrlTemplate)

    orgList = {}

    for pageNr in range(0, 300):
        logging.info("====================> Processing page %s", pageNr)
        organizations  = readUrlWithCache(orgUrlTemplate.format(pageNr)).get('data')

        if not organizations:
            logging.info("** DONE **")
            break

        for org in organizations:
            id = org['id']
            name = org['name']
            shortName = org['shortName']
            logging.info("%s %s %s", id, name, shortName)

            orgList[id] = [name, shortName]

    return orgList


def getGremienList():

    # Read meeting list
    meetingUrlTemplate = OPARL_BASE_URL + 'bodies/0001/meetings?page={}'
    logging.debug("Meeting URL: %s", meetingUrlTemplate)

    # Because opar from SOMACOS Session is so broken,
    # we try to use the list of the "organziations" endpoint as a fallback.
    # .. maybe the missing organization is in there..?
    # Update: Nope, this doesn't help .. Some organizatinos are not returned via oparl api at all
    orgList = getOrganizations()

    calendar = {}

    for pageNr in range(0, 300):
        logging.info("====================> Processing page %s", pageNr)
        meetingUrl = meetingUrlTemplate.format(pageNr)
        meetingsJson = readUrlWithCache(meetingUrl)
        meetings = meetingsJson.get('data')

        if not meetings:
            logging.info("** DONE **")
            break

        for meeting in meetings:
            name = meeting['name']
            start = meeting['start']
            end = meeting['end']
            room = getDictValueFailsafe(meeting, ['location', 'room'])
            orgUrl = getDictValueFailsafe(meeting, ['organization', 0])
            # Parse numeric meeting ID from meeting url (url is in field "id")
            meetingId = re.search("/(\d+)$", meeting['id']).group(1)
            orgName = ""

            if not start.startswith(CONFIG_EXPORT_YEAR):
                logging.debug("wrong year %s", start)
                continue

            elif not orgUrl:
                logging.warning("empty 'organisation' field")

            elif not orgUrl.startswith(OPARL_BASE_URL):
                logging.warning("invalid 'organisation' url %s", orgUrl)

            else:
                org = readUrlWithCache(orgUrl)
                if not org:
                    # This should not happen at all and is validation of oparl specification
                    # But sadly, this happens a lot with
                    logging.warning("organisation url failed - %s", start)
                    if orgUrl in orgList:
                        orgName = orgList[orgUrl][0]
                    elif not SKIP_EMPTY_ORGANIZATION_NAMES:
                        logging.warning("organization not in org list")
                        orgName = 'Gremium "{}"'.format(orgUrl.replace(OPARL_BASE_URL, ''))

                else:
                    organisation = org.get('name')
                    orgShortName = org.get('shortName')
                    #members = len(org.get('membership'))
                    #startDate = org.get('startDate')
                    orgName = organisation if organisation else orgShortName

            if orgName:
                logging.info('%s - %s | %s - %s',start, orgName, name, room)
                calendar[start + str(meetingId)] = [start, end, name, orgName, room, meetingId]
            else:
                logging.warning("%s - skipping event, empty organziation name", start)

    for key, value in sorted(calendar.items()):
        logging.info("%s %s", key, value)

    return calendar


def main():

    calendarItems = getGremienList()

    writeIcal(calendarItems)



main()