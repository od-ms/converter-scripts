# coding=utf-8
import csv
import datetime
from urllib.request import urlopen
import config as cfg
from pprint import pprint
import re

url = 'https://www.bezreg-muenster.de/de/im_fokus/uebergreifende_themen/coronavirus/coronavirus_allgemein/index.html'
print("Data url:", url)
f = urlopen(url)
htmlPage = f.read().decode('utf-8')
path = 'data/'


# --- This is the HTML that we want to parse -- 
# <li><strong>Stadt Bottrop: </strong>Aktuell Infizierte 0 (1),&nbsp;Infizierte 211 (211), Verstorbene 7 (7), Genesene 204 (203)</li>
# <li><strong>Kreis Borken:</strong>&nbsp;Aktuell Infizierte 5 (7), Infizierte 1.111 (1.111), Verstorbene 38 (38), Genesene 1.068 (1.066)</li>
# <li><strong>Kreis Coesfeld:</strong>&nbsp;Aktuell Infizierte 4 (5), Infizierte 871 (871), Verstorbene 24 (24), Genesene 843 (842)</li>

# --- Debug command ---
# print(htmlPage)
numPat = '[^(]*\((-?[\d.]+)\)'
pattern = '<li><strong>([SK][^:]+)[^<]*<\/strong>[^<]*[aA]ktuell Infizierte\s*-?([\d.]+)'+numPat+'[^<]*Infizierte\s*([\d.]+)'+numPat+'[^,]*,\s*Verstorbene\s*([\d.]+)'+numPat+'[^,]*,\s*Genesene\s*([\d.]+)'+numPat;
result = re.findall(pattern, htmlPage.replace('&uuml;', 'ü')) 
print(result)

today = datetime.date.today()
mydate = today.strftime('%d.%m.%Y')

outfile = path + 'covid191.csv'
with open(outfile, mode='w') as csv_file:
    writer = csv.writer(csv_file, dialect='excel')
    for item in result:
        writer.writerow([item[0], mydate, item[3].replace('.',''), item[7].replace('.',''), item[5].replace('.','')])

today = datetime.date.today() - datetime.timedelta(days=1)
mydate = today.strftime('%d.%m.%Y')
outfile = path + 'covid192.csv'
with open(outfile, mode='w') as csv_file:
    writer = csv.writer(csv_file, dialect='excel')
    for item in result:
        writer.writerow([item[0], mydate, item[4].replace('.',''), item[8].replace('.',''), item[6].replace('.','')])

print()
print("Wrote file:", outfile)
