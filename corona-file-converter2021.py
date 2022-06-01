import os
import re
from chardet import detect
import logging
from datetime import datetime, timedelta

# Basic logger configuration
logging.basicConfig(level=logging.INFO, format='<%(asctime)s %(levelname)s> %(message)s')
# Colors on the console
logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
LOGGER = logging.getLogger(__name__)
TODAY = datetime.now()
LOGGER.info("=====> START %s <=====", TODAY)

def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']


def convert_file(srcfilename):
    trgfile = srcfilename.replace('_csv_','_')
    srcfile = srcfilename +'.csv'
    trgfile = trgfile +'.csv'
    LOGGER.info("Files: %s => %s", srcfile, trgfile)

    from_codec = get_encoding_type(srcfile)

    try:
        with open(srcfile, 'r', encoding=from_codec) as f, open(trgfile, 'w', encoding='utf-8') as e:

            line_nr = 0
            for line in f:
                # Match data from first column and remove it
                regex = 'Kalenderwoche (\d+)/(\d+).KW'
                matches = re.search(regex, line, flags=re.IGNORECASE)
                line = re.sub(r"^[^;]+;", "", line)
                line_nr = line_nr + 1
                if line_nr == 1:
                    line = '"JAHR";"WOCHE";' + line
                else:
                    # For some reason one file is broken / add the missing Gänsefüßchen here
                    if srcfilename == '05515000_csv_CORONA_GEIMPFT':
                        line = line.replace(
                            'Münster gesamt;Corona-Neuinfizierungen von geimpften Personen - mit oder ohne Krankheitsanzeichen',
                            '"Münster gesamt";"Corona-Neuinfizierungen von geimpften Personen - mit oder ohne Krankheitsanzeichen"'
                            )
                        LOGGER.debug("replaced line %s", line)
                    # Re- insert data from first column into two new columns

                    if not matches:
                        LOGGER.error("Did not match Regex '%s' in line %s: %s", regex, line_nr, line)
                        continue;

                    line = "{};{};".format(matches.group(1), matches.group(2)) + line
                e.write(line.replace(';', ','))

    except UnicodeDecodeError:
        print('Decode Error')
    except UnicodeEncodeError:
        print('Encode Error')


sourceFiles = ['05515000_csv_CORONA_GEIMPFT', '05515000_csv_CORONA_NEUINF', '05515000_csv_CORONA_NEUINF_AG', '05515000_csv_CORONA_NEUINF_STADTTEILE']
for filename in sourceFiles:
    convert_file(filename)