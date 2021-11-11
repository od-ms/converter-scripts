import json
from urllib.request import Request, urlopen
from datetime import datetime, timedelta, timezone
import logging
import sys
import os
import config as cfg
import pytz

# config
LOGFILE_NAME = 'datahub-api-reader.log'
ALWAYS_USE_CACHE_FILE = 0

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, filename=LOGFILE_NAME, format='<%(asctime)s %(levelname)s> %(message)s')

LOGGER = logging.getLogger(__name__)
TZ = pytz.timezone('Europe/Berlin')
TODAY = datetime.now(TZ)
LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
LOGGER.info("=====> START %s %s <=====", TODAY, LOCAL_TIMEZONE)


def read_api_url(endpoint: str) -> list:
    # Read data from URL
    # and send our user agent string because [insert reason here]

    LOGGER.debug("Requesting %s", endpoint)
    req = Request(endpoint)
    req.add_header("User-Agent", "MS OpenData ETL v0.9")
    return urlopen(req).read().decode('utf-8')


def get_api_json():
    # load & cache the api file and return the json

    sitefile = 'data/datahub-cache.json'

    if ALWAYS_USE_CACHE_FILE and os.path.exists(sitefile):

        # load cached site file
        f = open(sitefile, "r")
        content = f.read()

    else:

        # read api sites and write cache file
        content = read_api_url(cfg.datahub_api_url)
        with open(sitefile, 'w') as file:
            file.write(content)

    return json.loads(content)

def get_time(timestring):
    return datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

def main():
    try:
        data_time_now = datetime.now(TZ)

        datahub = get_api_json()

        p_ph = None
        p_oxy = None
        p_temp = None
        p_date = None
        for item in datahub['data']['packets']:

            # check if data entry is older than 10 minutes (= that is our cronjob time)
            date_time_obj = get_time(item['source_time'])
            data_age = data_time_now - date_time_obj
            if data_age.total_seconds() > 600:
                LOGGER.debug("Data age: %ss", data_age.total_seconds())
                LOGGER.error("Data older than 15 minutes, skipping")
                continue

            # assemble a data row:
            # we collect all data entries within 5 minutes and create one data row from it
            # (every entry has different values set, so we collect entries until we have all values)
            if not p_date:
                p_date = item['source_time']
                LOGGER.debug("Time from API: %s", p_date)
            else:

                # calculate the time difference to our last entry
                date_time_obj1 = datetime.strptime(p_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                date_time_obj2 = datetime.strptime(item['source_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                difference = date_time_obj1 - date_time_obj2
                # LOGGER.debug("Time difference: %ss", difference.total_seconds())

                # if nothing has changed, use the new entry's timestamp
                value_has_changed = 0
                for key, value in item['parsed'].items():
                    if key == 'water_temperature':
                        if value and (p_temp != value):
                            value_has_changed += 1
                    if key == 'dissolved_oxygen':
                        if value and (p_oxy != value):
                            value_has_changed += 1
                    if key == 'pH':
                        if value and (p_ph != value):
                            value_has_changed += 1
                if not value_has_changed:
                    p_date = item['source_time']
                    LOGGER.debug("New Time: %s (no data change)", p_date)
                    continue

                else:
                    # data points should be within 5 minutes
                    if abs(difference.total_seconds()) > 300:
                        LOGGER.debug("Time reset ====> difference: %ss too large", abs(difference.total_seconds()))
                        p_date = item['source_time']
                        p_ph = None
                        p_oxy = None
                        p_temp = None

            # now get the values
            for key, value in item['parsed'].items():
                if key == 'water_temperature':
                    p_temp = value
                if key == 'dissolved_oxygen':
                    p_oxy = value
                if key == 'pH':
                    p_ph = value

                if p_temp or p_ph or p_oxy:
                    LOGGER.debug("Got values: temp=%s ph=%s oxy=%s", p_temp, p_ph, p_oxy)

                if p_temp and p_ph and p_oxy:
                    break
            else:
                # Continue if the inner loop wasn't broken.
                continue
            # Inner loop was broken, break the outer.
            break


        if p_date:
            # prepare csv content (and convert data's utc timestamp to our timezone)
            current_timestamp = get_time(p_date).replace(tzinfo=timezone.utc).astimezone(tz=None)
            p_date_str = str(current_timestamp)
            csv_line = "{},{:.2f},{:.2f},{:.2f}\n".format(p_date_str[0:16].replace("T", " "), p_temp, p_ph, p_oxy)
            print(csv_line)

            # check if file exists
            outdir = '../aasee-monitoring/data/'
            outfile = outdir + "{}-{:02d}.csv".format(data_time_now.year,data_time_now.month)
            file_exists = (os.path.exists(outfile) and os.path.isfile(outfile))

            # finally write the data to csv
            with open(outfile, mode='a') as csv_file:
                if not file_exists:
                    csv_file.write("Datum,Wassertemperatur,pH-Wert,Sauerstoffgehalt\n")

                csv_file.write(csv_line)
        else:
            LOGGER.warning("SKIPPING CSV WRITE, did not get data")

    except:
        e = sys.exc_info()
        print( "<p>Error: %s</p>" % str(e) )
        LOGGER.exception("This went horribly wrong")

main()
