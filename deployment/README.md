# iRODS tests during/after deployment

This directory holds iRODS specific tests for during and/or after deployment.

## Manual

### irodsDeploymentTests.py

Tests to check the available resources and to put, replicate, get and remove a file.

#### How to test

You can run this script in our development/test iRODS container.

```./rit.sh up -d irods
$ docker cp ./irodsHousekeeping.py corpus_irods_1:/var/lib/irods/
./rit.sh exec irods
root@irods# apt-get install python3-pip
root@irods# su - irods
irods@irods$ pip3 install python-irodsclient
irods@irods$ python3 irodsHousekeeping.py
```

```bash
python3 irodsDeploymentTests.py --env-file None --exclusions "bundleResc, demoResc, rootResc" --source_file None --name None --dest None --overwrite --archive-file

-e, --env-file,     default = None,                             "Path to irods environment file containing connection settings"
-x, --exclusions,   default = "bundleResc, demoResc, rootResc", "Resources to exclude in resource availability check. This does not exclude these resources for put/get operations!"
-f, --source_file,  default = None, required = True,            "Local path to source file."
-n, --name,         default = None, required = True,            "Name of file, how it should be stored in iRODS."
-o, --overwrite,                                                "Overwrite files if they exist."
``` 
