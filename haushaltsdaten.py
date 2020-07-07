import csv
import re

""" 
# Zielformat "detailliert" (mit Kostenart)
Jahr	GsBe	Ver	Produktbereich	Produktgruppe	                    Kostenart	        Betrag	Budget_Richtung	Plan_Ist
2017			Innere Verwaltung	Verwaltungssteuerung und Service	Politische Gremien	83172.00	Aufwand	Plan
2017			Innere Verwaltung	Verwaltungssteuerung und Service	Politische Gremien	1827.00	Aufwand	Plan
2017			Innere Verwaltung	Verwaltungssteuerung und Service	Politische Gremien	9906.00	Aufwand	Plan

# Zielformat "einfach"
Produktbereich 	Produktgruppe 	Produktbereichsname 	Produktgruppenbezeichnung 	Jahr 	Richtung 	Betrag 	Betrag-Typ
01 	0101 	Innere Verwaltung 	Bezirksvertretungen (frei verfügbare Mittel) 	2007 	Aufwendungen 	0 	Ergebnis
01 	0102 	Innere Verwaltung 	Geschäftsführung für politische Gremien, Städtepartnerschaften 	2007 	Erträge 	83396.57 	Ergebnis
01 	0102 	Innere Verwaltung 	Geschäftsführung für politische Gremien, Städtepartnerschaften 	2007 	Aufwendungen 	3025165.2 	Ergebnis
 """

def fixMoney(eur):
    res = re.sub(r'[^-0-9,]', '', eur).replace(",", ".")
    return float(res if res else "0")


with open('data/2020-haushalt.csv') as csvinput:

    # Fields in source file
    #   0 1-stelliger Produktbereich - Kennung;
    #   1 1-stelliger Produktbereich - Bezeichnung;
    #   2 2-stelliger Produktbereich - Kennung;
    #   3 2-stelliger Produktbereich - Bezeichnung;
    #   4 Produktgruppe - Kennung;
    #   5 Produktgruppe  Bezeichnung;
    #   6 Geschäftsjahr;
    #   7 Steuern;
    #   8 Gebühren/Entgelte;
    #   9 Zuwendungen von Dritten;
    #   10 Sonstige Erträge;
    #   11 Summe Erträge;
    #   12 Personalaufwendungen;
    #   13 Sachaufwendungen;
    #   14 Zuwendungen an Dritte;
    #   15 Summe Aufwendungen;
    #   16 Ergebnis lt. Plan


    # Create "Simple" offenerhaushalt.de file format 
    outfile = 'data/2020-muenster-offenerhaushalt-summen.csv'
    with open(outfile, mode='w') as csvoutput:
        haushaltreader = csv.reader(csvinput, delimiter=';', quotechar='"')
        writer = csv.writer(csvoutput, dialect='excel')
        writer.writerow(['Produktbereich','Produktgruppe','Produktbereichsname','Produktgruppenbezeichnung','Jahr','Richtung','Betrag','Betrag-Typ'])
        for row in haushaltreader:
            if row[4]:  # Wenn die Produktkennung leer ist, dann ist es eine Summenzeile, die wir ignorieren
                part1 = [row[2], row[4], row[3], row[5], row[6] ]
                
                writer.writerow(part1 + ["Aufwendungen", "{:1.2f}".format(fixMoney(row[15])), "Plan"])
                writer.writerow(part1 + ["Erträge", "{:1.2f}".format(0-fixMoney(row[11])), "Plan"])

    # Create "Detailled" offenerhaushalt.de file format
    outfile = 'data/2020-muenster-offenerhaushalt-detail.csv'
    with open(outfile, mode='w') as csvoutput:
        csvinput.seek(0)
        haushaltreader = csv.reader(csvinput, delimiter=';', quotechar='"')
        writer = csv.writer(csvoutput, dialect='excel')
        writer.writerow(['ID-PB','ID-PG','Produktbereich','Produktgruppe','Jahr','Betrag-Typ','Kostenart','Richtung','Betrag'])
        for row in haushaltreader:
            if row[4]:
                part1 = [row[2], row[4], row[3], row[5], row[6], "Plan"]
                if row[7]:
                    writer.writerow(part1 + ["Steuern", "Erträge", "{:1.2f}".format(0-fixMoney(row[7]))])
                if row[8]:
                    writer.writerow(part1 + ["Gebühren/Entgelte", "Erträge", "{:1.2f}".format(0-fixMoney(row[8]))])
                if row[9]:
                    writer.writerow(part1 + ["Zuwendungen von Dritten", "Erträge", "{:1.2f}".format(0-fixMoney(row[9]))])
                if row[10]:
                    writer.writerow(part1 + ["Sonstige Erträge", "Erträge", "{:1.2f}".format(0-fixMoney(row[10]))])
                if row[12]:
                    writer.writerow(part1 + ["Personalaufwendungen", "Aufwendungen", "{:1.2f}".format(fixMoney(row[12]))])
                if row[13]:
                    writer.writerow(part1 + ["Sachaufwendungen", "Aufwendungen", "{:1.2f}".format(fixMoney(row[13]))])
                if row[14]:
                    writer.writerow(part1 + ["Zuwendungen an Dritte", "Aufwendungen", "{:1.2f}".format(fixMoney(row[14]))])

print("Done")