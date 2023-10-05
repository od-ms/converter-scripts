from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
import logging
import traceback

LOGFILE_NAME = 'check_all.log'

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, filename=LOGFILE_NAME, format='<%(asctime)s %(levelname)s> %(message)s')

LOGGER = logging.getLogger(__name__)
TODAY = datetime.now()
YESTERDAY = datetime.now() - timedelta(1)
ERROR_WORD = '-FAIL-'

LOGGER.info("=====> CHECK START %s <=====", TODAY)


def read_url(endpoint: str) -> str:
    # Read data from URL
    # and send our user agent string because [insert reason here]

    LOGGER.debug("Requesting %s", endpoint)
    req = Request(endpoint)
    req.add_header("User-Agent", "MS OpenData Uptimebot v0.9")
    response = ""
    try:
        response = urlopen(req).read().decode('utf-8')

    except HTTPError as exception:
        response = str(exception) + "\n\n\n\n"
        print("<p>Error: %s</p>" % str(exception))
        LOGGER.error(exception)

    return response


def print_result(name, value):
    # In the monitoring tool, we search for "-FAIL-" on this page,
    # so let's print that out in case of error

    LOGGER.info("Result %s => %s", name, value)
    if value:
        print("<p>{}: -OK-</p>".format(name))
    else:
        print("<p>{}: {}</p>".format(name, ERROR_WORD))


def check_radverkehr():
    # Load current month's data of Zählstelle "100031297 - Promenade"
    # and check if it has the newest date in last line

    currentDate = '{0}-{1:02d}'.format(YESTERDAY.year, YESTERDAY.month)
    url = 'https://raw.githubusercontent.com/od-ms/radverkehr-zaehlstellen/main/100031297/{}.csv'.format(currentDate)
    data = read_url(url)
    lines = data.splitlines()
    lastLine = lines[-1]
    checkDate = '{0}-{1:02d}-{2:02d}'.format(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day)
    LOGGER.debug("Last line: %s", lastLine)
    return lastLine[0:10] == checkDate


def check_coronazahlen():
    # Check if the date in the 2nd line of the file is at least 3 days old

    url = 'https://raw.githubusercontent.com/od-ms/resources/master/coronavirus-fallzahlen-regierungsbezirk-muenster.csv'
    data = read_url(url)
    firstLine = data.splitlines()[1]
    firstRow = firstLine.split(',')
    dateInFile = firstRow[1]
    checkDate = datetime.strptime(dateInFile, "%d.%m.%Y")
    lastDate = datetime.now() - timedelta(3)
    LOGGER.debug("Check: %s <= %s ", lastDate, checkDate)
    return checkDate >= lastDate


def check_parkplaetze():
    # Check if file with the current date exists and has date in it

    currentDate = '{0}-{1:02d}-{2:02d}'.format(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day)
    url = 'https://raw.githubusercontent.com/codeformuenster/parking-decks-muenster/master/data/{}.csv'.format(currentDate)
    data = read_url(url)
    firstLine = data.splitlines()[2]
    LOGGER.debug("First line: %s", firstLine)
    return firstLine[0:10] == currentDate


def check_aasee():
    # Load current month's CSV data and check if it has the newest date in last line

    currentDate = '{0}-{1:02d}'.format(YESTERDAY.year, YESTERDAY.month)
    url = 'https://raw.githubusercontent.com/od-ms/aasee-monitoring/main/data/{}.csv'.format(currentDate)
    data = read_url(url)
    lines = data.splitlines()
    lastLine = lines[-1]
    checkDate = '{0}-{1:02d}-{2:02d}'.format(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day)
    LOGGER.debug("Last line: %s", lastLine)
    return lastLine[0:10] == checkDate


def check_dcat_ap_harvesting():
    # Check if the harvesting endpoint of our Open Data Portal returns valid XML

    response = False
    try:
        url = 'https://opendata.stadt-muenster.de/dcatapde.xml'
        data = read_url(url)
        x = ET.fromstring(data)
        response = True
    except ET.ParseError as e:
        response = False
        e = traceback.format_exc()
        LOGGER.debug("Error while reading harvesting file: %s", e)

    return response


def main():
    # Master control program

    try:
        # print_result('Coronazahlen', check_coronazahlen())
        print_result('Parkplaetze', check_parkplaetze())
        print_result('Radverkehr', check_radverkehr())
        print_result('Aasee', check_aasee())
        print_result('OpenDataHarvesting', check_dcat_ap_harvesting())
    except:
        print(ERROR_WORD)
        e = traceback.format_exc()
        print("<p>Error: %s</p>" % e)
        LOGGER.error("ERROR: %s", e)


main()

print("<hr />Check date: %s<p>For more info see logfile: %s</p>" % (TODAY, LOGFILE_NAME))
