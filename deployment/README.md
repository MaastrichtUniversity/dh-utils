# iRODS tests during/after deployment

This directory holds iRODS specific tests for during and/or after deployment.

## Manual

### irodsDeploymentTests.py

Tests to check the available resources and to put, replicate, get and remove a file.

```bash
python3 irodsDeploymentTests.py --env-file None --exclusions "bundleResc, demoResc, rootResc" --source_file None --name None --dest None --overwrite --archive-file

-e, --env-file,     default = None,                             "Path to irods environment file containing connection settings"
-x, --exclusions,   default = "bundleResc, demoResc, rootResc", "Resources to exclude in resource availability check. This does not exclude these resources for put/get operations!"
-f, --source_file,  default = None, required = True,            "Local path to source file."
-n, --name,         default = None, required = True,            "Name of file, how it should be stored in iRODS."
-o, --overwrite,                                                "Overwrite files if they exist."
``` 
