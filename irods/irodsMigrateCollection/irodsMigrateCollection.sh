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
LOGFILE="/tmp/${SCRIPTFILE%.sh}.log"
COLL_PATH="/nlmumc/projects"

### CONSTANTS #################################################################
OPTIONS=P:C:R:dhv:zyl:
LONGOPTS=PROJECT,COLLECTION,RESOURCE,display-logs,help,verbose:,z,yes,commit,logfile
#log levels
ERR=1
WRN=2
INF=3
DBG=9

INVALID_PARAM_ERROR=1
COLL_NOT_FOUND=2
CHECKSUM_ERROR=11
TRIM_ERROR=12
IRODS_ERROR=99



### LOCAL VARS ################################################################
LOGLEVEL=${WRN}
DISPLAY_LOGS=0
CONFIRM=true
CHECKSUM_FAILED=false
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
        -l --logfile=logfile    ; logfile to write to (overwriting ${LOGFILE})

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
            printf "%s | %-7s | %b\n" "$(date)" "${LVLARR[$LVL]}" "${TXT}" >>"${LOGFILE}"
        fi
        if [[ ${DISPLAY_LOGS} -gt 0 ]];then
            printf "%s | %-7s | %b\n" "$(date)" "${LVLARR[$LVL]}" "${TXT}"
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
  LOG $DBG " ${EXECSTR}: ichksum -r -a -K $COLL"
  if $COMMIT; then
    ichksum -r -a -K $COLL || CHECKSUM_FAILED=true
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



# In case the provided logfile is not accessible for writing, write the logs to output
if [ ! -w "$LOGFILE" ];then
    DISPLAY_LOGS=2
    echo "Cannot write to logfile ${LOGFILE}. Writing to standard out instead."
fi

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
        -l|--logfile)
            LOGFILE="$2"
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
LOG $DBG "Executing: iquest \"%s\" \"select DATA_RESC_NAME where COLL_NAME like '${COLL}%'\""
SRC_RESC=$(iquest "%s" "select DATA_RESC_NAME where COLL_NAME like '${COLL}%'")
if [[ -z ${SRC_RESC} ]]; then
    LOG $ERR "No resource found for collection '${COLL}' in irods!" ${IRODS_ERROR}
fi
RESC_NUM=$(echo "${SRC_RESC}"|wc -l)
SRC_RESC=${SRC_RESC//[$'\n\r']/,}

LOG $INF "CURR RESOURCE : ${SRC_RESC}"
LOG $INF "TARGET RESC.  : ${DST_RESC}"
LOG $INF "========================================"


# check if collection is located on multiple (compound) resources
if [[ ${RESC_NUM} -gt 1 ]]; then
    # resource is expected to exist on only ONE (compound) resource, if not ABORT
    LOG $ERR "Collection ${COLL} is located on multiple resources (${SRC_RESC}) where only 1 is expected! Please investigate and fix this situation."
    LOG $ERR "To remove the collection from one of the resources, use the following command \n\n    itrim -r -M -v -S <resource> ${COLL}\n"
    LOG $ERR "Script will be aborted!" ${IRODS_ERROR}
fi

# check if source and target resource are the same
if [[ "${DST_RESC}" == "${SRC_RESC}" ]]; then
    LOG $ERR "Target resource ($DST_RESC) and source resource ($SRC_RESC) are the same. So no actions required" ${IRODS_ERROR}
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
create_checksums


#
#   2 - VERIFY CHECKSUMS (among replicas)
#      a - iquest to query all checksum that are different
#      b - in case of results in step 2a, show result and abort script (with error)
#
#      info: grep -v inverts the match and returns all NON-matching lines

LOG $DBG "Verifying checksums and number of replicas"
QUERY="select count(DATA_NAME), DATA_RESC_NAME, DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where DATA_SIZE > '0' and COLL_NAME like '${COLL}%'"
LOG $DBG "iquest --no-page \"%2d %-14s %-52s %12d %s/%s\" \"${QUERY}\" \| grep -v \"^ 2\""
ISSUES=$(iquest --no-page "%2d %-14s %-52s %12d %s/%s" "${QUERY}" | grep -v "^ 2")

if [[ -n "${ISSUES}" ]]; then
  LOG $ERR "Errors encountered in checksums or number of replicas. Aborting before migration. Details: \n${ISSUES}" ${CHECKSUM_ERROR}
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
# TODO: Distinguishing between non-zero and empty files not necessary here? Since everything will be replicated (zero and non-zero files). Distinction was only required in verification of checksum between replicas...
QUERY="select count(DATA_NAME) where COLL_NAME like '${COLL}%' AND DATA_RESC_NAME = '${SRC_RESC}' AND DATA_SIZE > '0'"
LOG $DBG "Executing: iquest --no-page \"%d\" \"${QUERY}\""
SRC_COUNT=$(iquest --no-page "%d" "${QUERY}")

LOG $INF "Number of (non-zero) files to be migrated: ${SRC_COUNT} (note they are replicated, so ils will return half of this amount)"

if $CONFIRM; then read -r -n 1 -p "  --> press any key to start replication"; fi

LOG $INF "Replicating ${COLL} from ${SRC_RESC} to ${DST_RESC}"
LOG $DBG "${EXECSTR}: irepl -r -M -P ${VERBOSE_PARAM} -S \"${SRC_RESC}\" -R \"${DST_RESC}\" \"${COLL}\""
if $COMMIT; then
  irepl -r -M -P ${VERBOSE_PARAM} -S "${SRC_RESC}" -R "${DST_RESC}" "${COLL}" || LOG $ERR "irepl command returned errorcode '$?'" ${IRODS_ERROR}
fi
LOG $DBG "Replication finished"

if ${COMMIT}; then

  LOG $INF "Verify count of data objects on target resource ${DST_RESC}"
  QUERY="select count(DATA_NAME) where COLL_NAME like '${COLL}%' AND DATA_RESC_NAME = '${DST_RESC}' AND DATA_SIZE > '0'"
  LOG $DBG "Executing: iquest --no-page \"%d\" \"${QUERY}\""
  DST_COUNT=$(iquest --no-page "%d" "${QUERY}")
  LOG $INF "Number of (non-zero) files on target resource: ${DST_COUNT}"

  if [[ ! ${SRC_COUNT} -eq ${DST_COUNT} ]]; then
    LOG $ERR "Number of files not consistent on both resources (${SRC_COUNT} data objects on ${SRC_RESC}, ${DST_COUNT} data objects on ${DST_RESC})!"
    LOG $ERR "Aborting operation after replication!"
    LOG $ERR "To undo the replication, use the following command \n\n    itrim -r -M -v -S ${DST_RESC} ${COLL}\n" ${IRODS_ERROR}
  fi

  LOG $INF "Verify count of replicas and checksums on target resource ${DST_RESC}"
  QUERY="select count(DATA_NAME), DATA_RESC_NAME, DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where DATA_SIZE > '0' AND COLL_NAME like '${COLL}%' AND DATA_RESC_NAME = '${DST_RESC}'"
  LOG $DBG "Executing: iquest --no-page \"%2d %-14s %-52s %12d %s/%s\" \"${QUERY}\""
  ISSUES=$(iquest --no-page "%2d %-14s %-52s %12d %s/%s" "${QUERY}" | grep -v "^ 2")

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Errors encountered in checksums or number of replicas on target resource ${DST_RESC}."
    LOG $ERR "Please investigate issues before taking any further actions on this collection!"
    LOG $ERR "Aborted after replication. Details: \n${ISSUES}" ${CHECKSUM_ERROR}
    LOG $ERR "To undo the replication, use the following command \n\n    itrim -r -M -v -S ${DST_RESC} ${COLL}\n" ${IRODS_ERROR}
  fi
  LOG $DBG "Checksum and replication count done finished"

else

  LOG $INF "Post replication checks and NOT performed because they are only relevant if the replication is actually performed"

fi


#
#  4 - REMOVE COLLECTION FROM SOURCE RESOURCE
#      a - execute itrim to recursively remove all files files (and subcollections) from source resource
#          now we have 2 replicas on the target resource (2,3)
#      b - ensure no replicas are left on source resource
#      c - if results found in step 4b, abort immediately with error!
#      d - verify count of replicas and checksums on target resource
#      e - if results found in step 4d, abort immediately with error!
#
if $CONFIRM ; then read -r -n 1 -p "  --> press any key to start trimming"; fi
LOG $INF "Removing (trimming) files for ${COLL} from ${SRC_RESC}"
CMD="itrim -r -M ${VERBOSE_PARAM} -S ${SRC_RESC} ${COLL}"
LOG $DBG "${EXECSTR}: $CMD"
if ${COMMIT}; then
  $CMD || LOG $ERR "itrim command returned errorcode '$?'" ${IRODS_ERROR}
fi
LOG $DBG "Trim operations finished"

if $COMMIT; then

  LOG $INF "Verify that no files are left on original resource ${SRC_RESC} for collection ${COLL}"
  QUERY="select count(DATA_NAME), DATA_RESC_NAME, DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where COLL_NAME like '${COLL}%' AND DATA_RESC_NAME = '${SRC_RESC}'"
  LOG $DBG "Executing: iquest --no-page \"%2d %-14s %-52s %12d %s/%s\" \"${QUERY}\""
  ISSUES=$(iquest --no-page "%2d %-14s %-52s %12d %s/%s" "${QUERY}")
  ISSUES=${ISSUES//'CAT_NO_ROWS_FOUND: Nothing was found matching your query'}

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Still files left on original resource ${SRC_RESC}. Details: \n${ISSUES}" ${TRIM_ERROR}
  fi
  LOG $DBG "Verification finished"

  LOG $INF "Final verification for count of replicas and checksums "
  QUERY="select count(DATA_NAME), DATA_RESC_NAME, DATA_CHECKSUM, DATA_SIZE, COLL_NAME, DATA_NAME where DATA_SIZE > '0' AND COLL_NAME like '${COLL}%'"
  LOG $DBG "Executing: iquest --no-page \"%2d %-14s %-52s %12d %s/%s\" \"${QUERY}\""
  ISSUES=$(iquest --no-page "%2d %-14s %-52s %12d %s/%s" "${QUERY}" | grep -v "^ 2")

  if [[ -n "${ISSUES}" ]]; then
    LOG $ERR "Found data objects in collection ${COLL} that do not have exactly 2 replicas. Details: \n${ISSUES}" ${TRIM_ERROR}
  fi
  LOG $DBG "Final verification finished"

  LOG $INF "Collection ${COLL} has been succesfully migrated from ${SRC_RESC} to ${DST_RESC}\n"

else

  LOG $INF "Post trim checks and NOT performed because they are only relevant if the itrim is actually performed"
  LOG $INF "Migration of collection ${COLL} has been succesfully been simulated from ${SRC_RESC} to ${DST_RESC}\n"

fi

exit 0
