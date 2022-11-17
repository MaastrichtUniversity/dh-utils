# irodsSetEnableUnarchiveAvu

* **Name:** irodsSetEnableUnarchiveAvu
* **Description**: Loop over all existing projects set the enableUnarchive AVU to a default value (the value of EnableArchive if exists, 'false' if it does not)
* **Developer:** Dean Linssen, DataHub Maastricht University
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

python3 set_enable_unarchive_avu.py [-h] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -c, --commit          commit to actually modify the budget number
```
