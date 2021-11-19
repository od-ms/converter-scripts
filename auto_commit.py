"""
automatic commit of corona .csv file
"""
import os
import datetime
import config as cfg


def main():
    """
    automatic commit of daily parkleitsystem data
    and of daily waiting time data in the citizen center of Muenster
    to github
    """
    # get current date and time
    now = datetime.datetime.today()
    date = now.strftime('%Y-%m-%d')
    add_command = 'git add coronavirus-fallzahlen-regierungsbezirk-muenster.csv'
    commit_command = 'git commit -m "Update ' + date + '"'
    push_command = 'git push https://' + cfg.github_token + '@github.com/od-ms/resources.git'

    od.system("cd ../resources")
    os.system(add_command)
    os.system(commit_command)
    os.system(push_command)


if __name__ == "__main__":
    main()
