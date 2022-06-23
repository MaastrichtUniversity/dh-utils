# irodsConvertBudgetNumber

* **Name:** irodsConvertBudgetNumber
* **Description**: Loop over all existing projects and modify the budget number to the new format
* **Developer:** Dean Linssen, DataHub Maastricht University
* **License:** ?
* **Depends on:** python-irodsclient

# Before usage
1. Clone this repository
2. Get the budget number dictionary from the Jira ticket and move it to this directory

## How to install the dependencies
```
sudo apt-get install python3-virtualenv
python3 -m virtualenv --python=python3 venv3
source ./venv3/bin/activate

pip install python-irodsclient

# To exit the venv
# deactivate
```


# Usage
```
source ./venv3/bin/activate

python3 convert_budget_numbers.py [-h] [-c] path to the json dictionary

optional arguments:
  -h, --help            show this help message and exit
  -c, --commit          commit to actually modify the budget number
```