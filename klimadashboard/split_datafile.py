# -*- coding: UTF-8 -*-

import re
import json
import logging
import os.path
import csv
import os

from datetime import datetime, timezone

FILE = '05515000_csv_klimarelevante_daten.csv'

# Basic logger configuration
logging.basicConfig(level=logging.DEBUG, format='<%(asctime)s %(levelname)s> %(message)s')
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.info("=====> START %s <=====", datetime.now())


DATASET_DESCRIPTIONS = {
    "awm-abfallaufkommen-pro-kopf": [1, "Abfallaufkommen pro Kopf in kg", r"^Abfallaufkommen\s"],
    "awm-e-mobilitaet":             [17, "E-Mobilität awm", r"^AWM\sFahrzeuge\s-"],
    "oekoprofit":                   [7, "Ökoprofit", r"^Projektträger\sMünster\s-"],
    # Änderung 2025-07: pv-anlagen werden extern generiert und reingemerged
    # (Aber wir laden trotzdem erst rein und überschreiben sie später)
    # (Weil sonst gibt's sanity check fehlermeldungen, weil die sind ja erstmal noch in der inputdatei von 61 drin)
    "pv-anlagen":                   [15, "PV-Anlagen", r"^PV-Anlage\(n\):"],
    "verkehrsmittelwahl-zeitreihe": [4, "Zeitreihe Verkehrsmittelwahl", r"^Verkehrsmittelwahl", r"^Wege/Tag$"],
    "stadtradeln":                  [8, "Stadtradeln", r"^Stadtradeln"],
    "co2-emissionen-anwendungen":   [10, "CO2 Emissionen (Anwendungen)", r"^CO2-Emissionen\sAnwendung"],
    "co2-emissionen-sektoren":      [11, "CO2 Emissionen (Sekt. + ET)", r"^CO2-Emissionen\s-\s"],
    "co2-emissionen-tonnen":        [9, "CO2 Emissionen (Sektoren)", r"^CO2-Emissionen\s(in\s)?\(t\)\s+-"],
    "emissionen-strom":             [14, "Emissionen Strom", r"^Strom-Emissionen\snach\sEnergieträgern"],
    "endenergie":                   [12, "Endenergie (Sekt)", r"^Endenergieverbrauch"],
    "teilnehmer-startberatung":     [16, "Teilnehmer (Unternehmen) Startberatung", r"^Teilnehmer"],
    "verbrauch-erzeugung-strom":    [13, "Verbrauch-Erzeugung Strom", r"^Stromerzeugung/-bereitstellung"],
    "stadtwerke-bus-fahrzeuge":     [3, "BUS-Fahrzeuge der Stadtwerke", r"^Fahrzeuge"],
    "wachstum":                     [19, "Wachstumskennzahlen", r"^Sozialversicherungspflichtige"]
    # Änderung 2024-03: Das ist jetzt zusammen mit "4" Zeitreihe Verkehrsmittelwahl:
    # "modal-split-v-leistung":       ["Modal Split V.leistung", r"^(Absolut|Absolut\sin\skm|Modal\sSplit\sV\.leistung.*)$"],
}

FIX_STRINGS = {
    "CO2-Emissionen - Private Haushalt (Zielwert)": "CO2-Emissionen - Private Haushalte (Zielwert)"
}


# old 2023-04:
# FIRST_ROW_SETUP = 'ZEIT;RAUM;MERKMAL;WERT;QUELLANGABE'
# ENCODING = 'latin-1'

# old 2023-06-05:
# FIRST_ROW_SETUP = '"ZEIT";"RAUM";"MERKMAL";"WERT";"WERTEEINHEIT";"QUELLANGABE";"QUELLNAME"'
#                       X      X       X       X            X          X            => rausgeflogen

# new 2024-03-05:     X         alt:QUELLANGABE       NEU        X         X       X       X
FIRST_ROW_IN = '"RAUM";"DATENQUELLE";"THEMENBEREICH";"MERKMAL";"ZEIT";"WERT";"WERTEEINHEIT"'
FIRST_ROW_OUT = '"RAUM";"QUELLE_INSTITUTION";"THEMENBEREICH";"MERKMAL";"ZEIT";"WERT";"WERTEEINHEIT"'


ENCODING = 'utf-8-sig'  # utf8 mit bom


logging.info("Reading %s", FILE)


# Read data from input CSV file
# then group the data by dataset
# and add a name of the dataset in the first column
def group_rows_by_dataset():
    FIRST_ROW = []
    with open(FILE, 'r', encoding=ENCODING) as csvinput:
        line = 0
        unknowns = 0
        OUTFILES_DATA = {}
        NR_COLS = 0
        klimareader = csv.reader(csvinput, delimiter=';')
        for KLIMAROW in klimareader:
            if line < 1:
                NR_COLS = len(KLIMAROW)
                FIRST_ROW = KLIMAROW
                logging.info("%s Input Spalten: %s", NR_COLS, KLIMAROW)
                if ('"' + ('";"'.join(FIRST_ROW)) + '"') != FIRST_ROW_IN:
                    raise ValueError("Unexpected first row in CSV")
                FIRST_ROW = FIRST_ROW_OUT[1:-1].split('";"')
                logging.info("%s Output Spalten: %s", NR_COLS, FIRST_ROW)
            else:
                # fix broken rows ... append next row, if its too short ..

                if len(KLIMAROW) < NR_COLS:
                    nextrow = klimareader.__next__()
                    logging.debug("TOO FEW COLUMNS %s ..... %s", KLIMAROW, nextrow)
                    rest = nextrow.pop(0)
                    correct_string = KLIMAROW[-1] + rest
                    KLIMAROW = KLIMAROW[:-1] + [correct_string] + nextrow
                    logging.info("Fixed broken row: %s", KLIMAROW)

                quell_merkmal = KLIMAROW[3]
                quell_themenbereich_id = KLIMAROW[2]
                hit = ""
                for file_name, regexes in DATASET_DESCRIPTIONS.items():
                    direct_match = regexes[0]
                    themenbereich_name = regexes[1]
                    regex = regexes[2]
                    if (str(direct_match) == str(quell_themenbereich_id)):
                        hit = file_name
                        break
#                    elif re.match(regex, quell_merkmal):
#                        hit = file_name
#                        break

                if hit:
                    fix_strings(KLIMAROW)
                    if hit in OUTFILES_DATA:
                        OUTFILES_DATA[hit].append(KLIMAROW)
                    else:
                        OUTFILES_DATA[hit] = [KLIMAROW]
                    logging.debug("Row %s belongs to %s", line, hit)
                else:
                    logging.warning("Row %s = UNKNOWN: %s", line, KLIMAROW)
                    unknowns = unknowns + 1
            if unknowns > 0:
                logging.error("TOO MANY UNKNOWNS")
                raise ValueError("BYE")

            line = line + 1

    return OUTFILES_DATA, FIRST_ROW


def fix_strings(row):
    for index, item in enumerate(row):
        if item in FIX_STRINGS:
            row[index] = FIX_STRINGS[item]
    return row


def write_json_file(data, outfile_name):
    with open(outfile_name, "w") as outfile:
        json.dump(data, outfile, ensure_ascii=True, indent=2, sort_keys=True)


def write_csv_file_with_datsetname_in_first_column(data, HEAD_ROW, outfile_name):
    with open(outfile_name, 'w', newline='', encoding='utf-8') as outfile:
        outwriter = csv.writer(outfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        outwriter.writerow(["DATEINAME"] + HEAD_ROW)
        for dataset_name, rows in data.items():
            for row in rows:
                outwriter.writerow([dataset_name] + row)


def get_external_data(filename, quelle, einheit):
    new_data = []
    with open(filename) as user_file:
        parsed_json = json.load(user_file)
        for name, value in parsed_json["Summen"].items():
            if (name == "AnzahlSolarModule") and ("wind" in filename):
                continue
            new_data.append([
                "Münster, Gesamtstadt",
                quelle,
                23,
                name,
                str(datetime.now())[0:10],
                value,
                "Anzahl" if ("Anzahl" in name) else einheit
            ])
    return new_data


DATA_SPLIT, FIRST_ROW = group_rows_by_dataset()

# Add PV- and Solar-Data from Marktstammdatenregister
DATA_SPLIT['bestand-pv-anlagen'] = get_external_data(
    '../marktstammdatenregister/anlagen_solare_strahlungsenergie.json',
    "Marktstammdatenregister",
    "kW"
)
DATA_SPLIT['bestand-windanlagen'] = get_external_data(
    '../marktstammdatenregister/anlagen_wind.json',
    "Marktstammdatenregister",
    "kW"
)


# Merge pv_anlagen_stadt_muenster.csv into DATA_SPLIT
def load_pv_anlagen_csv(filename):
    rows = []
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        header = next(reader)
        for row in reader:
            rows.append(row)
    return rows

pv_anlagen_rows = load_pv_anlagen_csv('pv_anlagen_stadt_muenster.csv')
DATA_SPLIT['pv-anlagen'] = pv_anlagen_rows

write_json_file(DATA_SPLIT, "klimadata.json")
write_csv_file_with_datsetname_in_first_column(DATA_SPLIT, FIRST_ROW, "klimadata.csv")
