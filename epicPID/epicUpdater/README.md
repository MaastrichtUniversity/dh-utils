# epicUpdater

* **Name:** epicUpdater
* **Description**: This script can be used when underlying data location to which the persistent identifier redirects changes. 
  The script updates an existing hdl.handle.net record with a new value for URL.
* **Developer:** Daniel Theunissen, DataHub Maastricht University
* **License:** ?
* **Depends on:** python requests, a running instance of [epicpid-microservice](https://github.com/MaastrichtUniversity/epicpid-microservice).

# Usage
1. Retrieve all existing PIDs from iRODS using this query:
   ```
   iquest --no-page "%s,%s" "select COLL_NAME, META_COLL_ATTR_VALUE where META_COLL_ATTR_NAME like 'PID'" 
   ```

1. Construct a csv file with the following structure: `projectcollection,PID`.  
   Effectively, this is just copy-pasting the result from the iRODS query into a csv file.
   
   Example:
   ```
   /nlmumc/projects/P000000014/C000000001,21.T12996/P000000014C000000001
   /nlmumc/projects/P000000014/C000000002,21.T12996/P000000014C000000002
   /nlmumc/projects/P000000015/C000000001,21.T12996/P000000015C000000001
   ```

1. Modify the settings. Open the script `updateEpicPID.py` in a text editor and change the following values to your liking:
   ```
   # The URL to the epicpid-microservice container
   epicRequestURL = "http://epicpid.dev1.rit.unimaas.nl/epic/"
   
   # The handle prefix you use for the PIDs
   epicPreFix = "21.T12996"
   
   # Credentials for the epicpid-microservice
   epicUsername = "user"
   epicPassword = "foobar"
   
   # Filename of the csv file you've created in step 2 
   inputFile = "dev1_pids.csv"
   
   # The (base)URL you want to change.  
   expectedOldURL = "http://pacman.dev1.rit.unimaas.nl/"
   
   # The base URL of the new data location, so that redirects go to the proper data location
   newBaseURL = "http://mdr.dev1.dh.unimaas.nl/"
   
   # Toggle to control dry run mode.
   dryRun = True
   ```

1. Run the script. When you have chosen for dry-run mode above, nothing will be committed to the epic handle server.

1. Check the outcome *on your computer*
   1. on the command line
      ```
      epicRequestURL is: http://epicpid.dev1.rit.unimaas.nl/epic/
      epicPreFix is: 21.T12996
      inputFile is: dev1_pids.csv
      expectedOldURL is: http://pacman.dev1.rit.unimaas.nl/
      newBaseURL is: http://mdr.dev1.dh.unimaas.nl/
      dryRun is: True
      Starting....
      -------------------------------
      21.T12996/P000000014C000000001
      currentURL is: http://pacman.dev1.rit.unimaas.nl/hdl/P000000014/C000000001
      New url: http://mdr.dev1.dh.unimaas.nl/hdl/P000000014/C000000001
      -------------------------------
      21.T12996/P000000014C000000002
      currentURL is: http://pacman.dev1.rit.unimaas.nl/hdl/P000000014/C000000002
      New url: http://mdr.dev1.dh.unimaas.nl/hdl/P000000014/C000000002
      -------------------------------
      21.T12996/P000000015C000000001
      currentURL is: http://pacman.dev1.rit.unimaas.nl/hdl/P000000015/C000000001
      New url: http://mdr.dev1.dh.unimaas.nl/hdl/P000000015/C000000001
      -------------------------------
      ...Finished

      ```
   1. The same information is written to disk in the log file `*_<timestamp>.log`
   1. The `*_<timestamp>_original.csv` file shows the values as they were present in the HDL service.
   1. The `*_<timestamp>_changed.csv` file lists the PIDs that were updated by this run of the script.

1. Check the outcome *online*. 
   1. Go to http://hdl.handle.net/
   1. Enter the handle value (e.g. 21.T12996/P000000014C000000001)
   1. Check the box "Don't Redirect to URLs"
   1. Inspect the handle record to see if the value for URL has been updated correctly.
   
**NOTICE:** There is a synchronisation delay of a few minutes between SURF's epic service https://epic5.storage.surfsara.nl:8003/ (to which we commit) and the 
global http://hdl.handle.net service. Please double-check SURF's epic service first if you doubt the outcome of the PID updater script.
