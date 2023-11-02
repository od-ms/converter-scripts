
## Issues aus Github exportieren
Als JSON exportieren:
```bash
# install github command line and login
sudo apt install gh
gh auth login

# change into directory of the repo
git clone [[repository-url]]
cd [[repository-directory]]

# test: get a list of all issues
gh issue list --limit 1000 --state al

# export all issues with details into json file
MAX_NUM=`gh issue list --limit 1 --json number | jq ".[].number"`; for n in `seq 1 $MAX_NUM`; do gh issue view $n --json assignees,author,body,closed,closedAt,comments,createdAt,id,labels,milestone,number,projectCards,reactionGroups,state,title,updatedAt,url >> github-dump.json; done
```

## Nach CSV konvertieren
Mit `jq` eine CSV-Datei aus dem JSON erstellen:

1. Header-Zeile schreiben
```bash
echo "[]"\
    | jq --raw-output '["Erstellungsdatum", "Geschlossen", "Status", "Ersteller", "Tags", "Titel", "Anz.Kommentare", "Bearbeiter", "ID", "Url", "Beschreibung"] | @csv'\
    > issue-list.csv
```

2 . Content-Zeilen schreiben

`cat github-dump.json | jq --raw-output '`
```bash
    .
        | select( .labels[].name == "Münster"  )
        |   [
                .createdAt, .closedAt, .state, .author.login,
                ( [.labels[].name]|join(", ") ),
                .title,
                ( [.comments[].createdAt]|length ),
                ( [.assignees[].login]|join(", ") ),
                .id, .url, .body
            ]
        | @csv
' >> issue-list.csv
```
