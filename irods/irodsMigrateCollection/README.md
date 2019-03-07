# irodsMigrateCollection

* **Name:** irodsMigrateCollection
* **Description**: Migrates a collection from one resource to another including checksum verification
* **Developer:** Roger Niesten, DataHub Maastricht University
* **License:** ?
* **Depends on:** 
  * iRODS icommands
  * DataHub irods-ruleset
  * iRODS version 4.1.12 (not compatible with iRODS 4.2.x)

## Syntax

    ./irodsMigrateCollection.sh [options] -C collection [-R targetresource]
        
    mandatory:
      -P --PROJECT=project  the project to be migrated
      -R --RESOURCE=target  the target resource (overwrites default target resource in script)

    optional:
      -C --COLLECTION=coll  the collection to be migrated
    
    options:
      -v --verbose=level    verbose output (Debug, Info, Warning, Error)
      -d --display-logs     display logs to console 
      -y                    don't ask for confirmation
      -l --logfile=logfile  path to logfile base name (overwriting default). Example: /tmp/mylogfile

## Usage
**TIP** Since this can be a long running process, you might want to do this in a screen session.

1. Login to an iRODS server of choice.
    1. **NOTE** that the _openProjectCollection.r_ and _closeProjectCollection.r_ rules need to be present on this server in _/rules/projectCollection/_
1. Clone this repository into _~/dh-utils_
1. Make a dir for the log files and give the irods user write permissions
    ```
    mkdir ~/irodsMigrateCollection_logs
    sudo chown irods:irods ~/irodsMigrateCollection_logs
    ```
1. Switch to the irods user account
    ```
    sudo su irods
    ```
1. Get a working _rodsadmin_ connection through `iinit`

1. **[DRY-RUN]** Test the script and review the output with 
    ```
    cd /home/<username who did step 2>/irodsMigrateCollection_logs
    /home/<username who did step 2>/dh-utils/irods/irodsMigrateCollection/irodsMigrateCollection.sh -P P000000001 -C C000000001 -R replRescUM02 -v DBG -d
    ```
1. **[COMMIT]** Execute the changes with
    ```
    cd /home/<username who did step 2>/irodsMigrateCollection_logs
    /home/<username who did step 2>/dh-utils/irods/irodsMigrateCollection/irodsMigrateCollection.sh -P P000000001 -C C000000001 -R replRescUM02 -v DBG -d -y --commit
    ```

## Logfile
By default, the logfile will be created in the current working dir. It has a name like `irodsMigrateCollection_<PROJECT><COLLECTION>_<DATE>-<TIMESTAMP>.log`.
If the logfile cannot be created in this default folder (or the override folder from the `--logfile` option), the script will notify you and write output only to stdout.
