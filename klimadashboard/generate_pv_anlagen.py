#!/usr/bin/env python
# coding: utf-8

# # Solaranlagen auf städtischen Gebäuden

# In[26]:


import pandas as pd

# CSV-Datei laden
df = pd.read_csv('../../solar-und-windkraft-muenster/alle-anlagen-muenster.csv')

# Zeilen filtern, z.B. nur Zeilen mit Wert 'foo' in der ersten Spalte
gefiltert = df[(df['AnlagenbetreiberMaStRNummer'] == 'ABR979186451947') | (df['AnlagenbetreiberMaStRNummer'] == 'ABR990157438859')]
print(f"Anzahl Anlagen mit InbetriebnahmeDatum: {gefiltert["InbetriebnahmeDatum"].count()}")
gefiltert = gefiltert.sort_values(by="InbetriebnahmeDatum", ascending=True)
gefiltert.iloc[:5, :]


# ## Felder
# 
# ```
# DATEINAME;RAUM;QUELLE_INSTITUTION;THEMENBEREICH;MERKMAL;ZEIT;WERT;WERTEEINHEIT
# pv-anlagen;Stadt Münster - PV Anlage Grundschule Wolbeck-Nord (1443) Inbetriebnahme: 30.01.2020;Stadt Münster - Amt für Immobilienmanagement;15;Leistung ab Jahr
# ;2020;41,50;kWp
# pv-anlagen;Stadt Münster;Stadt Münster - Amt für Immobilienmanagement;15;Leistung aller Anlagen (Summe);2019;56,10;kWp
# ```

# In[27]:


# iteriere über alle anlagen
pro_jahr_leistung = {}
pro_jahr_anzahl = {}
for index, row in gefiltert.iterrows():
    print(f"Anlage: {row['AnlagenbetreiberMaStRNummer']}, Leistung: {row['Nettonennleistung']}, Inbetriebnahme: {row['InbetriebnahmeDatum']}")  # Beispielausgabe
    inbetriebnahme = row['InbetriebnahmeDatum']
    if isinstance(inbetriebnahme, str) and len(inbetriebnahme) >= 4:
        jahr = inbetriebnahme[:4]  # Extrahiere das Jahr aus dem Datum
        pro_jahr_leistung[jahr] = pro_jahr_leistung.get(jahr, 0) + row['Nettonennleistung']
        pro_jahr_anzahl[jahr] = pro_jahr_anzahl.get(jahr, 0) + 1

leistungssummen = {}
anzahlsummen = {}
for jahr, wert in pro_jahr_leistung.items():
    leistungssummen[jahr] = sum(
        v for j, v in pro_jahr_leistung.items() if j <= jahr
    )
    anzahlsummen[jahr] = sum(
        v for j, v in pro_jahr_anzahl.items() if j <= jahr
    )

anzahlsummen


# In[ ]:


import math

csv_content = []
for jahr, leistung in leistungssummen.items():
    anzahl = anzahlsummen[jahr]
    print(f"Hinzufügen: Jahr {jahr}, Leistung {math.floor(leistung)}, Anzahl {anzahl}")  
 
    csv_content.append({
        "DATEINAME": "pv-anlagen",
        "RAUM": "Stadt Münster",
        "QUELLE_INSTITUTION": "Marktstammdatenregister",
        "THEMENBEREICH": 15,
        "MERKMAL": "Leistung aller Anlagen (Summe)",
        "ZEIT": jahr,
        "WERT": math.floor(leistung),
        "WERTEEINHEIT": "kWp"
    })
    csv_content.append({
        "DATEINAME": "pv-anlagen",
        "RAUM": "Stadt Münster",
        "QUELLE_INSTITUTION": "Marktstammdatenregister",
        "THEMENBEREICH": 15,
        "MERKMAL": "Anzahl aller PV-Anlagen",
        "ZEIT": jahr,
        "WERT": anzahl,
        "WERTEEINHEIT": "Anzahl"
    })

for gefiltert_row in gefiltert.itertuples():
    # Extract year only if InbetriebnahmeDatum is a string and has at least 4 characters
    inbetriebnahme = gefiltert_row.InbetriebnahmeDatum
    if isinstance(inbetriebnahme, str) and len(inbetriebnahme) >= 4:
        jahr = inbetriebnahme[:4]
        csv_content.append({
            "DATEINAME": "pv-anlagen",
            "RAUM": f"Stadt Münster - PV Anlage {gefiltert_row.EinheitName} ({math.floor(gefiltert_row.AnzahlSolarModule)}), Inbetriebnahme: {gefiltert_row.InbetriebnahmeDatum}",
            "QUELLE_INSTITUTION": "Stadtverwaltung Münster",
            "THEMENBEREICH": 15,
            "MERKMAL": "Leistung ab Jahr",
            "ZEIT": jahr,
            "WERT": gefiltert_row.Nettonennleistung,
            "WERTEEINHEIT": "kWp"
        })

csv_content


# In[ ]:


# script zum Schreiben der CSV-Datei
import csv
# Schreibe die CSV mit Semikolon als Trennzeichen
csv.register_dialect('semicolon', delimiter=';', quoting=csv.QUOTE_MINIMAL)
output_file = 'pv_anlagen_stadt_muenster.csv'
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, dialect='semicolon', fieldnames=["DATEINAME", "RAUM", "QUELLE_INSTITUTION", "THEMENBEREICH", "MERKMAL", "ZEIT", "WERT", "WERTEEINHEIT"])
    writer.writeheader()
    for row in csv_content:
        writer.writerow(row)

