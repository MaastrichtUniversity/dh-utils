#!/usr/bin/env bash
#
# This script migrates all data in a collection (note that a project is also a collection!)
# from the current resource to another resource using several icommands. This
# implies that an irods connection is required via iinit.
# The following steps are performed:
#
#   1 - CALCULATE CHECKSUMS
#      a - open collection
#      b - calculate checksum on all files (ichksum)
#      c - close collection
#   2 - VERIFY CHECKSUMS (among replicas)
#      a - iquest to query all checksum that are different
#      b - in case of results in step 2a, show result and abort script (with error)
#   3 - REPLICATE COLLECTION TO TARGET RESOURCE
#      a - execute irepl to recursively replicate for all files (and subcollections) (only lowest replica number will be replicated (twice))
#          now we have 4 replicas (2 on source resource (0,1) and 2 on target resource (2,3)
#      b - verify count of replicas and checksums on target resource
#      c - if results found in step 3b, abort immediately with error!
#   4 - REMOVE COLLECTION FROM SOURCE RESOURCE
#      a - execute itrim to recursively remove all files files (and subcollections) from source resource
#          now we have 2 replicas on the target resource (2,3)
#      b - ensure no replicas are left on source resource
#      c - if results found in step 4b, abort immediately with error!
#      d - verify count of replicas and checksums on target resource
#      e - if results found in step 4d, abort immediately with error!
#
#


### CONFIGURATION #############################################################
SCRIPTFILE=${0##*/}
LOGFILEBASE="$PWD/${SCRIPTFILE%.sh}"    # Defaults to logfile in the current working dir
COLL_PATH="/nlmumc/projects"
#MAX_FILE_SIZE=343597383680             # 320GB; max. possible filesize that can me migrated to Ceph (with a bit of slack)
MAX_FILE_SIZE=450971566080	#420GB; max possible filesize to migrate to Ceph


### CONSTANTS #################################################################
OPTIONS=P:C:R:dhv:zyl:,r
LONGOPTS=PROJECT,COLLECTION,RESOURCE,display-logs,help,verbose:,z,yes,commit,logfile,resume
#log levels
ERR=1
WRN=2
INF=3
DBG=9

INVALID_PARAM_ERROR=1
COLL_NOT_FOUND=2
TOO_LARGE_FILES_ERROR=3
UNKNOWN_ERROR=9
CHECKSUM_ERROR=11
TRIM_ERROR=12
IRODS_ERROR=99



### LOCAL VARS ################################################################
LOGLEVEL=${WRN}
DISPLAY_LOGS=0
CONFIRM=true
DO_CHECKSUMS=true
CHECKSUM_FAILED=false
RESUME_MODE=false
COMMIT=false
EXECSTR="Simulating"
VERBOSE_PARAM=""
SRC_RESC=
DST_RESC=
PROJ_NAME=
COLL_NAME=
COLL=


### LOCAL FUNCTIONS ############################################################

#
# function: syntax [errormsg] [returnvalue]
#
# descr:    prints the syntax of this script
#
function syntax {

    if [[ -n $1 ]];then
        LOG $ERR "$1"
        echo ""
        echo "ERROR: $1"
        echo ""
    fi

    echo "SYNTAX: $0 <options> -P <project> [ -C <collection> ] -R <target-resource>

    Options:
        -P --PROJECT=<project>  ; project to be migrated
        -C --COLLECTION=<coll>  ; collection to be migrated
        -R --RESOURCE=<resc>    ; target resource to migrate to
        -v --verbose=<DBG|INF|WRN|ERR>
                                ; define the logging level (default=WRN)
        -d --display-logs       ; display logs on standard output
        -y                      ; don't ask for keypress to continue
        -l --logfile=logfile    ; path to logfile base name (overwriting ${LOGFILEBASE})
        -r --resume             ; resume an aborted migration (skip source resource check, skip the checksumming (if already done)

        --commit                ; actually perform the migration (without it's only a simulation)

    Example:
        - migrate collection 2 of project 1 (currently on resouce replRescUM01) to resource replRescUM02
            $0 -v INF -d -P P000000001 -C C000000002 -R replRescUM02
        - simulate migration of all collection of project 123 (currently on resouce replRescUM01) to resource replRescUM02
            $0 -v DBG -d --commit -P P000000123 -R replRescUM02
"
    if [[ -n $2 ]];then
        exit "$2"
    fi
}

#
# function:     log <LVL> <TXT> [<exit value>]
#
# description:  writes info to the logfile, depending on logging level
#
function LOG {
#TODO: parameter checks
    LVL=$1
    TXT=$2
    RET=$3
    LVLARR=(DUMMY ERROR WARNING INFO DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG)
# echo -e "\e[90m[ log '$LVL' '$TXT' '$RET' -> if $LVL < $LOGLEVEL then print text ]\e[39m"
    # write to logfile
    if [[ ${LVL} -le ${LOGLEVEL} ]];then
        if [[ ${DISPLAY_LOGS} -lt 2 ]];then
            printf "%s | %-7s | %b\n" "$(date --iso-8601=ns)" "${LVLARR[$LVL]}" "${TXT}" >>"${LOGFILE}"
        fi
        if [[ ${DISPLAY_LOGS} -gt 0 ]];then
            printf "%s | %-7s | %b\n" "$(date --iso-8601=ns)" "${LVLARR[$LVL]}" "${TXT}"
            #echo "$(date) | ${LVLARR[$LVL]} | ${TXT}"
        fi
    fi

    # in case of fatal error (returnvalue set), write to output and exit
    if [[ "${LVL}" == "${ERR}" ]];then
        if [ -n "${RET}" ];then
            echo -e "\n${TXT}\n"
            exit "${RET}"
        fi
    fi
}


#
# function: create_checksums <coll>
#
# descr:    create checksum for all files in collection
#
function create_checksums {

  LOG $INF "Checksumming $COLL ..."

  # Opening collection (or subcollections)
  LOG $DBG " - opening collection"
  if [[ -n ${COLL_NAME} ]];then
    if $COMMIT; then
      irule -F /rules/projectCollection/openProjectCollection.r "*project='${PROJ_NAME}'" "*projectCollection='${COLL_NAME}'" "*user='rods'" "*rights='own'"
    fi
  else
    # open all collections for this project
    for SUBCOLL_NAME in $(ils $COLL | grep '  C- ' | sed 's/  C- //g'); do
      SUBCOLL_NAME="${SUBCOLL_NAME##*/}"
      LOG $DBG "   - ${SUBCOLL_NAME}"
      if $COMMIT; then
        irule -F /rules/projectCollection/openProjectCollection.r "*project='${PROJ_NAME}'" "*projectCollection='${SUBCOLL_NAME}'" "*user='rods'" "*rights='own'"
      fi
    done
  fi

  # Do the checksum calculation and store in iRODS catalog
  LOG $DBG " - calculating checksums on all replicas"
  LOG $DBG " ${EXECSTR}: ichksum -r -a -K $COLL "
  if $COMMIT; then
    ichksum -r -a -K $COLL >>"${LOGFILE}"
    if [ $? -ne 0 ]; then
       CHECKSUM_FAILED=true
    fi
  fi

  # Closing collection (or subcollections)
  LOG $DBG " - closing collection"
  if [[ -n ${COLL_NAME} ]]; then
    if $COMMIT; then
      irule -F /rules/projectCollection/closeProjectCollection.r "*project='${PROJ_NAME}'" "*projectCollection='${COLL_NAME}'"
    fi
  else
    # close all collections for this project
    for SUBCOLL_NAME in $(ils $COLL | grep '  C- ' | sed 's/  C- //g'); do
      SUBCOLL_NAME="${SUBCOLL_NAME##*/}"
      LOG $DBG "   - ${SUBCOLL_NAME}"
      if $COMMIT; then
        irule -F /rules/projectCollection/closeProjectCollection.r "*project='${PROJ_NAME}'" "*projectCollection='${SUBCOLL_NAME}'"
      fi
    done
  fi

  LOG $INF "...done"

  if $CHECKSUM_FAILED; then
    LOG $ERR "Errors found in checksums! (see above for details). Please fix this first! Script is aborted!" ${CHECKSUM_ERROR}
  fi

}



### MAIN ROUTINE ##############################################################




# First pass command line args
! getopt --test > /dev/null
if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
    LOG $ERR "I’m sorry, 'getopt --test' failed in this environment." 1
fi


# -use ! and PIPESTATUS to get exit code with errexit set
# -temporarily store output to be able to check for errors
# -activate quoting/enhanced mode (e.g. by writing out “--options”)
# -pass arguments only via   -- "$@"   to separate them correctly
! PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    # e.g. return value is 1
    #  then getopt has complained about wrong arguments to stdout
    exit 2
fi
# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"


# now enjoy the options in order and nicely split until we see --
while true; do
    case "$1" in
        -P|--PROJECT)
            PROJ_NAME="$2"
            shift 2
            ;;
        -C|--COLLECTION)
            COLL_NAME="$2"
            shift 2
            ;;
        -R|--RESCOURCE)
            DST_RESC="$2"
            shift 2
            ;;
        -v|--VERBOSE)
                case "$2" in
                    1|ERR|Err|err|ERROR|Error|error)
                        LOGLEVEL=1
                        ;;
                    2|WRN|Wrn|wrn|WARNING|Warning|warning)
                        LOGLEVEL=2
                        ;;
                    3|INF|Inf|inf|INFO|Info|info)
                        LOGLEVEL=3
                        ;;
                    4|5|6|7|8|9|DBG|Dbg|dbg|DEBUG|Debug|debug)
                        LOGLEVEL=9
                        ;;
                esac
                shift

            shift
            ;;
        -d|--display-logs)
            DISPLAY_LOGS=1
            shift
            ;;
        -y)
            CONFIRM=false
            shift
            ;;
        -r|--resume)
            RESUME_MODE=true
            shift
            ;;
        -l|--logfile)
            LOGFILEBASE="$2"
            shift 2
            ;;
        --commit)
            COMMIT=true
            EXECSTR="Executing"
            shift
            ;;
        -h|--help)
            syntax "" 0
            shift
            break
            ;;
        --)
            shift
            break
            ;;
        *)
            LOG $ERR "Programming error" 3
            ;;
    esac
done

# handle mandatory arguments
if [[ -z ${PROJ_NAME} ]]; then
    syntax "Parameter PROJECT (-P) is required!" ${INVALID_PARAM_ERROR}
fi
COLL="${COLL_PATH}/${PROJ_NAME}"
if [[ -n ${COLL_NAME} ]]; then
  COLL="${COLL}/${COLL_NAME}"
fi

LOGFILE="${LOGFILEBASE}_${PROJ_NAME}${COLL_NAME}_$(date '+%Y%m%d-%H%M%S').log"

# In case the provided logfile is not accessible for writing, write the logs to output
touch $LOGFILE
if [ ! -w "$LOGFILE" ];then
    DISPLAY_LOGS=2
    echo "Cannot write to logfile ${LOGFILE}. Writing to standard out instead."
fi


# generate human readable max file size value
MAX_FILE_SIZE_H=${MAX_FILE_SIZE}
FILE_SIZE_UNIT="B"
while [ ${MAX_FILE_SIZE_H} -ge 10000 ]; do
  let MAX_FILE_SIZE_H=${MAX_FILE_SIZE_H}/1024
  if [[ "${FILE_SIZE_UNIT}" == "TB" ]]; then
    FILE_SIZE_UNIT="PB"
  elif [[ "${FILE_SIZE_UNIT}" == "GB" ]]; then
    FILE_SIZE_UNIT="TB"
  elif [[ "${FILE_SIZE_UNIT}" == "MB" ]]; then
    FILE_SIZE_UNIT="GB"
  elif [[ "${FILE_SIZE_UNIT}" == "KB" ]]; then
    FILE_SIZE_UNIT="MB"
  elif [[ "${FILE_SIZE_UNIT}" == "B" ]]; then
    FILE_SIZE_UNIT="KB"
  else
    LOG $ERR "UNKNOWN SIZE UNIT OR MAX_FILE_SIZE IS LARGER THEN 1024 PETABYTE!" $UNKNOWN_ERROR
  fi
done
MAX_FILE_SIZE_H="${MAX_FILE_SIZE_H}${FILE_SIZE_UNIT}"


LOG $DBG  ""
LOG $DBG  "Starting irods collection migration script for collection $COLL"

LOG $INF "========================================"
LOG $DBG "log-level     : $LOGLEVEL"
LOG $DBG "displ-logs    : $DISPLAY_LOGS"
if ! $CONFIRM ; then LOG $INF "Confirmation dialogs will be suppressed"; fi
if ! $COMMIT ; then LOG $INF "\e[32mTHIS IS A DRY RUN! Migration will only be simulated!\e[39m"; fi
LOG $INF "PROJECT       : $PROJ_NAME"
LOG $INF "COLLECTION    : $COLL_NAME"
LOG $DBG "----------------------------------------"



#
# Check if collection can be found
#
LOG $DBG "Verifying collecion access ${COLL}..."
ils "$COLL" 1>/dev/null || LOG $ERR "Can't access collection '${COLL}'. Script aborted!" ${COLL_NOT_FOUND}


#
# Determine and verify source resource of specified collection
#

# get rescource of specified collection
LOG $DBG "Executing: iquest \"%s\" \"select DATA_RESC_HIER where COLL_NAME like '${COLL}%'\""
tmprescfile=$(mktemp)
iquest "%s" "select DATA_RESC_HIER where COLL_NAME like '${COLL}%'" >$tmprescfile
if [ ! -f ${tmprescfile} ]; then
    LOG $ERR "No resource found for collection '${COLL}' in irods!" ${IRODS_ERROR}
fi

# CHANGED: Since iRODS 4.2 DATA_RESC_RESC doesn't return the composing resource, but the leaves
# whiched causes issues in checking the source resource.
# Now the DATA_RESC_HIER is retrieved, which returns the complete resource hierachie. In order to
# get unique values, we need to strip the leaves from variable SRC_RESC and deduplicate.
SRC_RESC=$(cut -d ';' -f 1 $tmprescfile | sort -u)
#SRC_RESC=$(echo ${SRC_RESC%%;*}|sort -u)


RESC_NUM=$(echo "${SRC_RESC}"|wc -l)
SRC_RESC=${SRC_RESC//[$'\n\r']/,}

LOG $INF "CURR RESOURCE : ${SRC_RESC}"
LOG $INF "TARGET RESC.  : ${DST_RESC}"
LOG $INF "========================================"


# check if collection is located on multiple (compound) resources
if [ $RESUME_MODE ]; then
    LOG $INF "Check for source resource is skipped due to -r, --resume parameter"
else
    if [[ ${RESC_NUM} -gt 1 ]] ; then
        # resource is expected to exist on only ONE (compound) resource, if not ABORT
        LOG $ERR "Collection ${COLL} is located on multiple resources (${SRC_RESC}) where only 1 is expected! Please investigate and fix this situation."
        LOG $ERR "To remove the replica's from one of the resources, use the following command \n\n    itrim -r -M -v -S <resource_of_replica_to_be_deleted> ${COLL}\n"
        LOG $ERR "If the collection is put offline, pull the whole collection online before migrating the collection\n"
        if [[ -z ${COLL_NAME} ]]; then
            LOG $INF "It looks like you tried to migrate an entire project recursively. Multiple resources within a project are likely to occur. Instead of using the itrim command above, try to migrate collections one by one."
        fi
        LOG $ERR "Script will be aborted!" ${IRODS_ERROR}
    fi
fi

# check if source and target resource are the same
if [[ "${DST_RESC}" == "${SRC_RESC}" ]]; then
    LOG $ERR "Target resource ($DST_RESC) and source resource ($SRC_RESC) are the same. So no actions required" ${IRODS_ERROR}
fi

# Search for files larger than allowed (Ceph resource has cache space of 300GB)
LOG $INF "Searching for very large files (>${MAX_FILE_SIZE_H})"
QUERY="\"select DATA_SIZE, COLL_NAME, DATA_NAME where COLL_NAME like '${COLL}%' AND DATA_SIZE > '${MAX_FILE_SIZE}'\""
LOG $DBG "Executing: iquest \"%15d  %s/%s\" \"${QUERY}\""
LARGE_FILE_LIST=$(iquest --no-page "%15s  %s/%s" "${QUERY}")
if [[ "${LARGE_FILE_LIST}" != "CAT_NO_ROWS_FOUND: Nothing was found matching your query" ]]; then
  #Collections containing files > 250GB will be aborted
    LOG $ERR "Collection ${COLL} contains files larger than ${MAX_FILE_SIZE_H} and will be aborted!\nDetails:\n${LARGE_FILE_LIST}" ${TOO_LARGE_FILES_ERROR}
fi


# check if resource of collection is a replicated compound resource
REPL_RESC=$(ilsresc | grep ':replication' | sed s/:replication//g | grep "${SRC_RESC}")
if [[ -z ${REPL_RESC} ]]; then
    # TODO: Not sure whether we should abort in this situation...
    LOG $WRN "Collection '${COLL}' is not located on a replicated resource!" # ${IRODS_ERROR}
fi


#
#   1 - CALCULATE CHECKSUMS
#      a - open collection
#      b - calculate checksum on all files (ichksum)
#      c - close collection
#
if $CONFIRM ; then read -r -n 1 -p "  --> press any key to start calculating checksums"; fi

if $RESUME_MODE; then
    QUERY="SELECT DATA_RESC_NAME, count(DATA_SIZE), sum(DATA_SIZE), max(DATA_SIZE) WHERE COLL_NAME like '${COLL}%' AND DATA_CHECKSUM = ''"
    FORMAT="%-20s  %8d files  total: %15d bytes   largest file: %d bytes"
    LOG $DBG "iquest --no-page \"${FORMAT}\" \"${QUERY}\""
    NO_CHECKSUMS=$(iquest --no-page "${FORMAT}" "${QUERY}")
    LOG $DBG "Files without checksums for %{COLL}:"
    LOG $DBG "$NO_CHECKSUMS"
    if [[ "$NO_CHECKSUMS" == "CAT_NO_ROWS_FOUND: Nothing was found matching your query" ]]; then
        DO_CHECKSUMS=false
        LOG $INF "Checksumming skipped due to option -r | --resume"
    fi
fi

if $DO_CHECKSUMS; then
  create_checksums
fi


#
#   2 - VERIFY CHECKSUMS (among replicas)
#      a - iquest to query all checksum that are different
#      b - in case of results in step 2a, show result and abort script (with error)
#
#      info: grep -v inverts the match and returns all NON-matching lines

if $DO_CHECKSUMS; then
    LOG $DBG "Verifying checksums and number of replicas"
    ## CHANGED: Since iRODS 4.2 DATA_RESC_NAME return leave resource instead of composing resource
    ## As we already know that all datafiles are on the same composing resource, the name of the
    ## resource is superfluous and can be removed
    QUERY="select count(DATA_NAME), DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where COLL_NAME like '${COLL}%'"
    LOG $DBG "iquest --no-page \"%2d %-52s %12d %s/%s\" \"${QUERY}\" \| grep -v \"^ 2\""
    ISSUES=$(iquest --no-page "%2d %-52s %12d %s/%s" "${QUERY}" | grep -v "^ 2")

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Errors encountered in checksums or number of replicas. Aborting before migration. Details: \n${ISSUES}" ${CHECKSUM_ERROR}
  fi
fi

#
#   3 - REPLICATE COLLECTION TO TARGET RESOURCE
#      a - count number of files on source resourse
#      b - execute irepl to recursively replicate for all files (and subcollections) (only lowest replica number will be replicated (twice))
#          now we have 4 replicas (2 on source resource (0,1) and 2 on target resource (2,3)
#      c - count number of files on target resource
#      d - compare number of files on both resources and report error if they are not identical!
#      e - verify count of replicas and checksums on target resource
#      f - if results found in step 3b, abort immediately with error!
#
# Note: We only count the non-zero files here, since that's the statistic we can reliably compare with the value of DST_COUNT.
QUERY="select count(DATA_NAME) where COLL_NAME like '${COLL}%' AND DATA_RESC_HIER like '${SRC_RESC}%' "
LOG $DBG "Executing: iquest --no-page \"%d\" \"${QUERY}\""
SRC_COUNT=$(iquest --no-page "%d" "${QUERY}")

LOG $INF "Number of (non-zero) files to be migrated: ${SRC_COUNT} (note they are replicated, so ils will return half of this amount)"

if $CONFIRM; then read -r -n 1 -p "  --> press any key to start replication"; fi

LOG $INF "Replicating ${COLL} from ${SRC_RESC} to ${DST_RESC}"
LOG $DBG "${EXECSTR}: irepl -r -M -P ${VERBOSE_PARAM} -R \"${DST_RESC}\" \"${COLL}\""
if $COMMIT; then
  irepl -r -M -P ${VERBOSE_PARAM} -R "${DST_RESC}" "${COLL}" >>"${LOGFILE}"
  if [ $? -ne 0 ]; then
    LOG $ERR "irepl command returned errorcode '$?'" ${IRODS_ERROR}
  fi
fi
LOG $DBG "Replication finished"

if ${COMMIT}; then

  LOG $INF "Verify count of data objects on target resource ${DST_RESC}"
  QUERY="select count(DATA_NAME) where COLL_NAME like '${COLL}%' AND DATA_RESC_HIER like '${DST_RESC}%' "
  LOG $DBG "Executing: iquest --no-page \"%d\" \"${QUERY}\""
  DST_COUNT=$(iquest --no-page "%d" "${QUERY}")
  LOG $INF "Number of (non-zero) files on target resource: ${DST_COUNT}"

  if [[ ! ${SRC_COUNT} -eq ${DST_COUNT} ]]; then
    LOG $ERR "Number of files not consistent on both resources (${SRC_COUNT} data objects on ${SRC_RESC}, ${DST_COUNT} data objects on ${DST_RESC})!"
    LOG $ERR "Aborting operation after replication!"
    LOG $ERR "To undo the replication, use the following command for each child resource \n\n    itrim -r -M -v -S ${DST_RESC};<child-resource> ${COLL}\n" ${IRODS_ERROR}
  fi

  LOG $INF "Verify count of replicas and checksums on target resource ${DST_RESC}"
  QUERY="select count(DATA_NAME), DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where COLL_NAME like '${COLL}%' AND DATA_RESC_HIER like '${DST_RESC}%'"
  LOG $DBG "Executing: iquest --no-page \"%2d %-52s %12d %s/%s\" \"${QUERY}\""
  ISSUES=$(iquest --no-page "%2d %-52s %12d %s/%s" "${QUERY}" | grep -v "^ 2")

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Errors encountered in checksums or number of replicas on target resource ${DST_RESC}."
    LOG $ERR "Please investigate issues before taking any further actions on this collection!"
    LOG $ERR "Aborted after replication. Details: \n${ISSUES}" ${CHECKSUM_ERROR}
    LOG $ERR "To undo the replication, use the following command for each child resource \n\n    itrim -r -M -v -S ${DST_RESC};<child-resource> ${COLL}\n" ${IRODS_ERROR}
  fi
  LOG $DBG "Checksum and replication count done finished"

else

  LOG $INF "Post replication checks and NOT performed because they are only relevant if the replication is actually performed"

fi


#
#  4 - REMOVE COLLECTION FROM SOURCE RESOURCE
#      a - execute itrim to recursively remove all files files (and subcollections) from source resource child-resources
#          now we have 2 replicas on the target resource (2,3)
#      b - ensure no replicas are left on source resource
#      c - if results found in step 4b, abort immediately with error!
#      d - verify count of replicas and checksums on target resource
#      e - if results found in step 4d, abort immediately with error!
#
if $CONFIRM ; then read -r -n 1 -p "  --> press any key to start trimming"; fi
LOG $INF "Removing (trimming) files for ${COLL} from ${SRC_RESC}"

# get child resource names of source resource
QUERY="select DATA_RESC_NAME where COLL_NAME like '${COLL}%' AND DATA_RESC_HIER like '${SRC_RESC}%'"
for RESC in $(iquest "%s" "${QUERY}"); do

  # WORKAROUND: apparently when resource 4k is trimmed, 4k-repl is trimmed implicitly as well (visa versa thatś not the case)
  #             trimming 4k-repl afterwards will fail because there is nothing to trim...
  #             So letś first check the amount of dataobjects to trim on the (child) resource and only trim if there is
  #             something to trim.

  # check if dataobjects exist on the RESC resource
  count=$(iquest "%d" "select count(DATA_NAME) where COLL_NAME like '${COLL}%' AND DATA_RESC_NAME = '${RESC}'")
  LOG $DBG "${EXECSTR}: Found ${count} data objects found on resource '${RESC}'"
  if [ $count -gt 0 ]; then
    CMD="itrim -r -M ${VERBOSE_PARAM} -S ${RESC} ${COLL}"
    LOG $DBG "${EXECSTR}: $CMD"
    if ${COMMIT}; then
      $CMD >>"${LOGFILE}"
      if [ $? -ne 0 ]; then
        LOG $ERR "itrim command returned errorcode '$?'" ${IRODS_ERROR}
      fi
    fi
  else
    LOG $DBG "${EXECSTR}: No data objects found on resource '${RESC}', trim is skipped"
  fi
done
LOG $DBG "Trim operations finished"

if $COMMIT; then

  LOG $INF "Verify that no files are left on original resource ${SRC_RESC} for collection ${COLL}"
  QUERY="select count(DATA_NAME), DATA_RESC_HIER, DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where COLL_NAME like '${COLL}%' AND DATA_RESC_HIER like '${SRC_RESC}%'"
  LOG $DBG "Executing: iquest --no-page \"%2d %-24s %-52s %12d %s/%s\" \"${QUERY}\""
  ISSUES=$(iquest --no-page "%2d %-24s %-52s %12d %s/%s" "${QUERY}")
  ISSUES=${ISSUES//'CAT_NO_ROWS_FOUND: Nothing was found matching your query'}

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Still files left on original resource ${SRC_RESC}. Details: \n${ISSUES}" ${TRIM_ERROR}
  fi
  LOG $DBG "Verification finished"

  LOG $INF "Final verification for count of replicas and checksums "
  QUERY="select count(DATA_NAME), DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where COLL_NAME like '${COLL}%'"
  LOG $DBG "Executing: iquest --no-page \"%2d %-24s %-52s %12d %s/%s\" \"${QUERY}\""
  ISSUES=$(iquest --no-page "%2d %-24s %12d %s/%s" "${QUERY}" | grep -v "^ 2")

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Found data objects in collection ${COLL} that do not have exactly 2 replicas. Details: \n${ISSUES}" ${TRIM_ERROR}
  fi
  LOG $DBG "Final verification finished"

  LOG $INF "Collection ${COLL} has been succesfully migrated from ${SRC_RESC} to ${DST_RESC}"

  # Update project cost (or subcollections)
  LOG $INF "Update project cost"
  if [[ -n ${COLL_NAME} ]];then
    if $COMMIT; then
      COSTS_OLD=$(irule -F /rules/projects/getProjectCost.r "*project='${PROJ_NAME}'")
      irule -F /rules/misc/setCollectionSize.r "*project='${PROJ_NAME}'" "*projectCollection='${COLL_NAME}'" "*openPC='true'" "*closePC='true'"
      COSTS_NEW=$(irule -F /rules/projects/getProjectCost.r "*project='${PROJ_NAME}'")
      LOG $INF "Costs for project ${PROJ_NAME} are decreased from ${COSTS_OLD} to ${COSTS_NEW}"
    fi
  else
    # Update collections costs for this project
    COSTS_OLD=$(irule -F /rules/projects/getProjectCost.r "*project='${PROJ_NAME}'")
    if $COMMIT; then
      for SUBCOLL_NAME in $(ils $COLL | grep '  C- ' | sed 's/  C- //g'); do
        SUBCOLL_NAME="${SUBCOLL_NAME##*/}"
        LOG $DBG "   - ${SUBCOLL_NAME}"
        irule -F /rules/misc/setCollectionSize.r "*project='${PROJ_NAME}'" "*projectCollection='${SUBCOLL_NAME}'" "*openPC='true'" "*closePC='true'"
      done
    fi
    COSTS_NEW=$(irule -F /rules/projects/getProjectCost.r "*project='${PROJ_NAME}'")
    LOG $INF "Costs for project ${PROJ_NAME} are decreased from ${COSTS_OLD} to ${COSTS_NEW}"
  fi

else

  LOG $INF "Post trim checks and NOT performed because they are only relevant if the itrim is actually performed"
  LOG $INF "Migration of collection ${COLL} has been succesfully been simulated from ${SRC_RESC} to ${DST_RESC}\n"

fi

exit 0

