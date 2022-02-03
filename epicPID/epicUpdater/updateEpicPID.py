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

inputFile = "dev1_pids.csv"
expectedOldURL = "http://pacman.dev1.rit.unimaas.nl/"
newBaseURL = "http://mdr.dev1.dh.unimaas.nl/"

dryRun = True

tme = time.localtime()
timeString = time.strftime("%m%d%y%H%M%S", tme)
outputFileChanged = inputFile.split(".")[0] + "_" + timeString + "_changed.csv"
outputFileOriginal = inputFile.split(".")[0] + "_" + timeString + "_original.csv"

logging.basicConfig(
    filename=inputFile.split(".")[0] + "_" + timeString + ".log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())


def updateURLforPID(pid, newURL):

    url = epicRequestURL + pid
    try:
        response = requests.post(url, data={"URL": newURL}, auth=HTTPBasicAuth(epicUsername, epicPassword))
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")  # Python 3.6
    except Exception as err:
        logging.error(f"Other error occurred: {err}")  # Python 3.6
    else:
        logging.info(pid + " updated with success. New url is " + newURL)


def updatePID(collection, pid, currentURL):

    parsed = urlparse(currentURL)
    replaced = parsed._replace(netloc=urlparse(newBaseURL).netloc)
    replaced = replaced._replace(scheme=urlparse(newBaseURL).scheme)
    newURL = replaced.geturl()
    f = open(outputFileChanged, "a")
    f.write(collection + "," + pid + "," + currentURL + "," + newURL + "\n")
    f.close()
    logging.info("New url: " + newURL)
    if not dryRun:
        updateURLforPID(pid, newURL)


def parseResponse(collection, pid, response):
    epicJson = response.json()
    if epicJson["values"][0]["type"] == "URL":
        currentURL = epicJson["values"][0]["data"]["value"]
        f = open(outputFileOriginal, "a")
        f.write(collection + "," + pid + "," + currentURL + "\n")
        f.close()
        logging.info("currentURL is: " + currentURL)
        if currentURL.startswith(expectedOldURL):
            updatePID(collection, pid, currentURL)
        else:
            logging.warning("Update not required. Did not match on URL.")


########### MAIN ##################


def main():
    logging.info("epicRequestURL is: " + epicRequestURL)
    logging.info("epicPreFix is: " + epicPreFix)
    logging.info("inputFile is: " + inputFile)
    logging.info("expectedOldURL is: " + expectedOldURL)
    logging.info("newBaseURL is: " + newBaseURL)
    logging.info("dryRun is: " + str(dryRun))
    logging.info("Starting....")

    with open(inputFile, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            collection = row[0]
            pid = row[1]
            logging.info("-------------------------------")
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
                logging.error(f"HTTP error occurred: {http_err}")  # Python 3.6
            except Exception as err:
                logging.error(f"Other error occurred: {err}")  # Python 3.6
            else:
                parseResponse(collection, pid, response)

    logging.info("-------------------------------")
    logging.info("...Finished")


if __name__ == "__main__":
    main()
