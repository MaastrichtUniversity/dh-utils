# irodsSetEnableUnarchiveAvu

* **Name:** irodsSetLatestProjectCollectionNumber
* **Description**: Loop over all existing projects set the latestProjectCollectionNumber AVU to a correct value (based on the latest collection)
* **Developer:** Daniel Theunissens, DataHub Maastricht University
* **License:** ?
* **Depends on:** python-irodsclient >=1.1.5

## How to install the dependencies
```
sudo apt-get install python3-virtualenv
python3 -m virtualenv --python=python3 venv3
source ./venv3/bin/activate

pip install python-irodsclient==1.1.5

# To exit the venv
# deactivate
```


# Usage
```
source ./venv3/bin/activate

python3 sset_latest_project_collection_number.py [-h] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -c, --commit          commit to actually modify the latestProjectCollectionNumber
```
