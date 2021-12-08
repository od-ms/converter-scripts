import os
import re
from chardet import detect
import logging
from datetime import datetime, timedelta

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
LOGGER = logging.getLogger(__name__)
TODAY = datetime.now()
LOGGER.info("=====> START %s <=====", TODAY)


def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']


def convert_file(srcfile):
    trgfile = srcfile.replace('_csv_','_')
    srcfile = srcfile +'.csv'
    trgfile = trgfile +'.csv'
    LOGGER.info("Files: %s => %s", srcfile, trgfile)

    from_codec = get_encoding_type(srcfile)

    try:
        with open(srcfile, 'r', encoding=from_codec) as f, open(trgfile, 'w', encoding='utf-8') as e:

            firstline = True
            for line in f:
                matches = re.search('Kalenderwoche (\d+)/(\d+).KW', line, flags=re.IGNORECASE)
                line = re.sub(r"^[^;]+;", "", line)
                if firstline:
                    firstline = False
                    line = '"JAHR";"WOCHE";' + line
                else:
                    line = "{};{};".format(matches.group(1), matches.group(2)) + line
                e.write(line.replace(';', ','))

    except UnicodeDecodeError:
        print('Decode Error')
    except UnicodeEncodeError:
        print('Encode Error')


sourceFiles = ['05515000_csv_CORONA_GEIMPFT', '05515000_csv_CORONA_NEUINF', '05515000_csv_CORONA_NEUINF_AG', '05515000_csv_CORONA_NEUINF_STADTTEILE']
for filename in sourceFiles:
    convert_file(filename)