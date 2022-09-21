## How to run

This script expects to be run as `irods`. Meaning, it expects to find a
`~/.irods/irods_environment.json` file containing all necessary information to
"log into" iRODS. An alternative `irods_environment.json` path can be provided
via the `-e|--env-file` argument.

## How to test

You can run this script in our development/test iRODS container. For example,
you could do something like:
```
./rit.sh up -d irods
$ docker cp ./irodsHousekeeping.py corpus_irods_1:/var/lib/irods/
./rit.sh exec irods
root@irods# apt-get install python3-pip
root@irods# su - irods
irods@irods$ pip3 install python-irodsclient
irods@irods$ python3 irodsHousekeeping.py
```

Or volume map the `dh-utils` repo, or use vs-code and attach to a live container.

:construction: TODO: Better / easier set up and testing process! :construction:


## Quick recap on iRODS terminology

There are 4 different types of **_iRODS objects_**:
* **_data objects_**
* **_collections_**
* **_resources_**
* **_users_**

Any directory (in the UNIX sense) in iRODS, is a **_collection_** to iRODS.

We (DataHub) have **_projects_** (e.g. `P000000001`), and **_project collections_**
(e.g. `C000000001`). Note that both **_projects_**, and **_project collections_** are
actually "directories", therefore to iRODS they are both **_collections_**.

Keep in mind that all **_data objects_** are **_iRODS objects_** but not all **_iRODS
objects_** are **_data objects_**. :)

And to run a bit of salt into the wound, we sometimes use the word
"**_collection_**" when we mean "**_project collection_**".



## non-sql vs sql

The current code includes two families of functions. Unfortunately
python-irodsclient does not provide a "not exist" statement for Queries, so ([as
suggested by iRODS developers](https://github.com/irods/irods/issues/2437)), you
can use direct SQL queries to accomplish this via `SpecificQuery`.
However, these SQL queries go unchecked, and we might not feel comfortable
running them. Therefore a non-sql versions (potentially slower) are provided as
well as a drop-in-place replacement.

### iRODS SQL internals

iCAT uses (or seems to use!) these tables (among others):
* `r_data_main`: **_data objects_**
* `r_coll_main`: **_collections_**
* `r_resc_main`: **_resources_**
* `r_user_main`: **_users_**
* `r_meta_main`: metadata (AVUs)
* `r_objt_metamap`: for associating **_iRODS objects_** (**_data objects_**, **_collections_**, etc) to metadata (AVUs)
