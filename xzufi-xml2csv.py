# coding=utf-8
"""
    convert xzufi xml format to csv
"""
import csv
import xml.etree.ElementTree as ET


def main():
    """
    convert xzufi xml format to csv
    """
    url = 'leika-xzufi-leistung.030104_01.xml'
    outfile = 'data/xzufi2csv.csv'
    print("Data file:", url)
    print("Outfile:", outfile)

    xmlroot = ET.parse(url).getroot()


    namespace = {'xzufi': 'http://xoev.de/schemata/xzufi/2_1_0'}

    with open(outfile, mode='w') as csv_file:
        fieldnames = ['id', 'idSekundaer', 'leistungsbezeichnung', 'volltext', 'kurztext', 'weiterfuehrende_informationen', 
                      'erforderliche_unterlagen', 'voraussetzungen', 'kategorien', 'kosten', 'begriffImKontext'
                     ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for xzufi_leistung in xmlroot.findall('.//xzufi:leistung', namespace):
            result_row = {}
            result_row['id'] = xzufi_leistung.find('xzufi:id', namespace).text
            result_row['idSekundaer'] = xzufi_leistung.find('xzufi:idSekundaer', namespace).text

            for xzufi_modultext in xzufi_leistung.findall('.//xzufi:modulText', namespace):
                inhalt = xzufi_modultext.find('xzufi:inhalt', namespace).text
                name = xzufi_modultext.find('xzufi:leikaTextmodul/name', namespace).text
                if inhalt and inhalt != "<br>":
                    result_row[name.lower()] = inhalt

            kategorien = []
            for xzufi_kategorie in xzufi_leistung.findall('.//xzufi:kategorie', namespace):
                kategorien.append(xzufi_kategorie.find('xzufi:bezeichnung', namespace).text)
            result_row['kategorien'] = ", ".join(kategorien)

            kosten = xzufi_leistung.find('.//xzufi:modulKosten/xzufi:beschreibung', namespace)
            if kosten is not None and kosten.text:
                result_row['kosten'] = kosten.text

            begriff = xzufi_leistung.find('.//xzufi:begriffImKontext/xzufi:begriff', namespace)
            if begriff is not None and begriff.text:
                result_row['begriffImKontext'] = begriff.text


            print(result_row)
            writer.writerow(result_row)


main()
