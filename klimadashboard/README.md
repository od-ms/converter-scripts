# Aktualisierung der Klimadashboard-Datei: 

`./update-all.sh`


## Anleitung zum Aktualisieren der PV-Anlagen-der-Stadt-Münster-Datei

Die Datei `pv_anlagen_stadt_muenster.csv` wird vom Skript "split_datafile.py" benötigt, damit in der Klimadashboard-Datendatei aktuelle Solardaten auftauchen. 

Wenn man das Jupyter Notebook aktualisiert hat, kann man die Update-Datei folgendermaßen neu generieren: 

```bash
# Erzeuge die python Datei aus dem Juypter Notebook
jupyter nbconvert --to python generate_pv_anlagen.ipynb

# Schreibe die Datei `pv_anlagen_stadt_muenster.csv`
python3 generate_pv_anlagen.py

```
## Infos zur Baumkachel

Vorschau: https://klimadashboard.ms/share/climate-trees

```bash 
# Einheiten
  Kronenschirmfläche
  [Zahl] km²

  Kühlleistung pro Jahr
  [Zahl] kWh

  Sauerstoffproduktion pro Jahr
  [Zahl] L

  CO2-Bindung pro Jahr
  [Zahl] t

# Alter der Bäume, erstes Intervall: 0-15 (nicht 1 bis 20)
    1 mal jung
    2 mal mittel (bis 60)
    3 mal alt
    [0, 15, 40, 60, 80, 100]
```
 
