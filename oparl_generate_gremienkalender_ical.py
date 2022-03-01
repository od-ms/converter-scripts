# -*- coding: UTF-8 -*-

import re
import json
import logging
import requests
import os.path
import time
import os

from datetime import datetime

from icalendar import Calendar, Event, vCalAddress, vText
import pytz

# Config
OPARL_BASE_URL = 'https://oparl.stadt-muenster.de/'
OPARL_MEETING_URL = 'https://www.stadt-muenster.de/sessionnet/sessionnetbi/si0057.php?__ksinr={}'
OUTPUT_FILE_ICS = 'ratsinformation_termine.ics'
OUTPUT_FILE_CSV = 'ratsinformation_termine.csv'


# Basic logger configuration
logging.basicConfig(level=logging.INFO, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())


def writeIcal(calendarItems):
    """
    Write ical file

    """
    cal = Calendar()
    # cal.add('attendee', 'MAILTO:opendata@citeq.de')
    cal.add('prodid', '-//Gremien Kalender//opendata.stadt-muenster.de//')
    cal.add('version', '2.0')

    for key, session in sorted(calendarItems.items()):


        p = re.match("^(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)", session[0])

        # Prepare event data
        meetingId = session[5]
        title = '{} - {}'.format(session[3], session[2])
        p = re.match("^(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)", session[0])
        start = datetime(int(p.group(1)), int(p.group(2)), int(p.group(3)), int(p.group(4)), int(p.group(5)), int(p.group(6)), tzinfo=pytz.utc)
        p = re.match("^(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)", session[1])
        end = datetime(int(p.group(1)), int(p.group(2)), int(p.group(3)), int(p.group(4)), int(p.group(5)), int(p.group(6)), tzinfo=pytz.utc)
        logging.info("Adding ical: %s %s %s", start, end, title)

        # Create ical event
        event = Event()
        event.add('summary', title)
        event.add('dtstart', start)
        event.add('dtend', end)
        event.add('dtstamp', datetime.now())
        event.add('description', OPARL_MEETING_URL.format(meetingId))
        event.add('uid', '20220215T101010/{}@ms'.format(meetingId))

        organizer = vCalAddress('MAILTO:opendata@citeq.de')
        organizer.params['cn'] = vText('Stadt Münster')
        organizer.params['role'] = vText('Ratsinformationssytem')
        event['organizer'] = organizer
        event['location'] = vText(session[4])

        # Add event to calendar
        cal.add_component(event)

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

    if os.path.isfile(filename):
        logging.debug("%s - using cache", filename)
        with open(filename) as myfile:
            filecontent ="".join(line.rstrip() for line in myfile)

    else:
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



orgList = {}

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


def getGremienList():

    # Read meeting list
    meetingUrlTemplate = OPARL_BASE_URL + 'bodies/0001/meetings?page={}'
    logging.debug("Meeting URL: %s", meetingUrlTemplate)

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
            meetingId = re.search("/(\d+)$", meeting['id']).group(1)
            orgName = ""

            if not start.startswith("2022"):
                logging.debug("wrong year %s", start)

            elif not orgUrl:
                logging.warning("empty 'organisation' field")

            elif not orgUrl.startswith(OPARL_BASE_URL):
                logging.warning("invalid 'organisation' url %s", orgUrl)

            else:
                org = readUrlWithCache(orgUrl)
                if not org:
                    logging.warning("organisation url failed - %s", start)
                    if orgUrl in orgList:
                        orgName = orgList[orgUrl][0]
                    else:
                        logging.warning("organization not in org list")
                        orgName = 'Gremium "{}"'.format(orgUrl.replace(OPARL_BASE_URL, ''))

                else:
                    organisation = org.get('name')
                    orgShortName = org.get('shortName')
                    #members = len(org.get('membership'))
                    #startDate = org.get('startDate')
                    orgName = organisation if organisation else orgShortName

                logging.info('%s - %s | %s - %s',start, orgName, name, room)

                calendar[start] = [start, end, name, orgName, room, meetingId]

    for key, value in sorted(calendar.items()):
        logging.info("%s %s", key, value)

    writeIcal(calendar)

    raise SystemExit

    with open('index.html', 'w') as outfile:
        outfile.write(html)

    print(html)

getOrganizations()
getGremienList()
