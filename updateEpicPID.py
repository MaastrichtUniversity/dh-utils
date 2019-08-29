import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import time
import csv
from urllib.parse import urlparse
import logging

# Config
epicRequestURL = "http://epicpid.dev1.rit.unimaas.nl/epic/"
epicPreFix = "21.T12996"
epicUsername = "user"
epicPassword = "foobar"

inputFile = "dev2.csv"
expectedOldURL = "https://datahub.mumc-acc.maastrichtuniversity.nl"
newBaseURL = "https://rdm.acc.dh.unimaas.nl"

dryRun = False

tme = time.localtime()
timeString = time.strftime("%m%d%y%H%M%S", tme)
outputFile = inputFile.split(".")[0] + '_' + timeString+'.csv'

logging.basicConfig(filename=inputFile.split(".")[0] + '_' + timeString+'.log', level=logging.INFO, format='%(asctime)s %(message)s')


def updateURLforPID(pid, newURL):

    url = epicRequestURL + pid
    try:
        response = requests.post(url, data={'URL': newURL}, auth=HTTPBasicAuth(epicUsername, epicPassword))
        response = requests.get(url, auth=HTTPBasicAuth(epicUsername, epicPassword))
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        logging.error(f'Other error occurred: {err}')  # Python 3.6
    else:
        logging.info(pid + " updated with success. New url is " + newURL)


def updatePID(collection, pid, currentURL):

    parsed = urlparse(currentURL)
    replaced = parsed._replace(netloc=urlparse(newBaseURL).netloc)
    newURL = replaced.geturl()
    f = open(outputFile, 'a')
    f.write(collection+"," + pid+"," + currentURL + "," + newURL + "\n")
    f.close()
    logging.info("New url: " + newURL)
    if not dryRun:
        updateURLforPID(pid, newURL)


def parseResponse(collection, pid, response):
    epicJson = response.json()
    if epicJson["values"][0]["type"] == "URL":
        currentURL = epicJson["values"][0]["data"]["value"]
        logging.info(currentURL)
        if currentURL.startswith(expectedOldURL):
            updatePID(collection, pid, currentURL)
        else:
            logging.warning("Update not required no URL match")

########### MAIN ##################


with open(inputFile, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        collection = row[0]
        pid = row[1]
        logging.info(pid)
        preFix = pid.split("/")[0]
        if preFix != epicPreFix:
            logging.warning("Prefix mismatch between:" + preFix + " and " + epicPreFix)
            continue

        url = epicRequestURL + pid
        try:
            response = requests.get(url, auth=HTTPBasicAuth(epicUsername, epicPassword))
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
           logging.error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            logging.error(f'Other error occurred: {err}')  # Python 3.6
        else:
            parseResponse(collection, pid, response)



