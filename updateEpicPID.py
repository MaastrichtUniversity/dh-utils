import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import time
import os
import csv
from urllib.parse import urlparse


epicRequestURL = "http://epicpid.dev1.rit.unimaas.nl/epic/"
epicPreFix = "21.T12996"
epicUsername = "user"
epicPassword = "foobar"

inputFile = "dev2.csv"
expectedOldURL = "https://datahub.mumc-acc.maastrichtuniversity.nl"
newBaseURL = "https://rdm.acc.dh.unimaas.nl"

tme = time.localtime()
timeString = time.strftime("%m%d%y%H%M%S", tme)
outputFile = inputFile.split(".")[0] +'_'+timeString+'.csv'


def updatePID(pid,currentURL):
    url = epicRequestURL + pid
    parsed = urlparse(currentURL)
    replaced = parsed._replace(netloc=urlparse(currentURL).netloc)
    newURL = replaced.geturl()
    print (newURL)


def parseResponse(response):
    epicJson = response.json()
    if epicJson["values"][0]["type"] == "URL":
        currentURL = epicJson["values"][0]["data"]["value"]
        print(collection + "," + pid + "," + currentURL)
        if currentURL.startswith(expectedOldURL):
            updatePID(pid,currentURL)
        else:
            print ("Update not required no match")

########### MAIN ##################

with open(inputFile, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        collection = row[0]
        pid = row[1]
        preFix = pid.split("/")[0]
        if preFix != epicPreFix:
            print("Prefix mismatch between:" + preFix + " and " + epicPreFix )
            continue

        url = epicRequestURL + pid
        try:
            response = requests.get(url, auth=HTTPBasicAuth(epicUsername, epicPassword))
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            parseResponse(response)



