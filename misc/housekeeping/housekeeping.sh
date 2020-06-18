#!/bin/bash
###############################################################################
#
# Syntax        : housekeeping.sh
#
# Description   : this script deletes or compresses files older that X days in
#                 folders mentioned in a specified config file
# Parameters    : config file
#
# Changes       :
# 19-11-2018 | R.Niesten | Initial version
#
###############################################################################


##### Local variables #########################################################
LOGFILE=/var/log/housekeeping-$(date +%Y%m%d_%H%M%S).log
CFG_FILE=$1
CFG_LINE=0
DEL_COUNT=0
ZIP_COUNT=0
DEL_FLDRS=0
ZIP_FLDRS=0
ERR_FLDRS=0

ERR=1
WRN=2
INF=3
FIN=4
FNR=5
FST=6
LOGTRESHOLD=$FNR
DISPLAY_LOGS=1  #0=no (only logfile), #1=display on output and in logfile, 2=output only


##### Local functions #########################################################

#==============================================================================
#
# Syntax        log <lvl> "<txt>" [exit-code]
#
# Params        <lvl> logging level (1=ERR, 2=WRN, 3=INF, 4=DBG)
#               <txt> text for logging
#
# Description   This function writes the log-text (txt) to stdout if the level (lvl)
#               is lower or equal to the set logging-treshold
#
# Changes
# 10-07-18 | R.Niesten | Initial version
#==============================================================================
function log {
    LVL=$1
    TXT=$2
    RET=$3
    DAT=$(date +"%d-%m-%Y %H:%M:%S")
    LVLARR=(DUMMY ERROR   WARNING INFO    FINEÿ   FINER   FINEST  DEBUG   DEBUG   DEBUG  )
    PREFIX=(DUMMY "\e[31m" "\e[33m"        )
    POSTFIX=(DUMMY "\e[0m" "\e[0m"       )

    # validate params
    if [[ -z ${LVL} ]]; then abort "${FUNCNAME[0]}: missing parameter [level]"; fi
    if ! [[ "$ERR $WRN $INF $FIN $FNR $FST" = *"${LVL}"* ]]; then  echo "${FUNCNAME[0]}: invalid value (${LVL}) for paramter 'level'"; exit 1; fi

    if [[ -z "$logtxt" ]]; then
        logtxt="<no text>"
    fi

    # write to logfile and potentially to disk
    if [[ ${LVL} -le ${LOGTRESHOLD} ]];then
        if [[ ${DISPLAY_LOGS} -lt 2 ]];then
            # write to logfile
            echo -e "${DAT} | ${LVLARR[$LVL]} | ${TXT}" >>${LOGFILE}
        fi
        if [[ $DISPLAY_LOGS -gt 0 ]];then
            # write to standard output
            echo -e "${PREFIX[$LVL]}${DAT} | ${LVLARR[$LVL]} | ${TXT}${POSTFIX[$LVL]}"
        fi
    fi

    # in case of fatal error (returvalue set), write to output and exit
    if [[ ${LVL} == ${ERR} ]];then
        if [ ! -z ${RET} ];then
            echo -e "\n${PREFIX[$LVL]}${TXT}${POSTFIX[$LVL]}\n"
            exit ${RET}
        fi
    fi
}


##### Check params ############################################################
log $FIN "checking parameters..."
if [[ -z ${CFG_FILE} ]]; then log $ERR "Parameter config file is mandatory! Script aborted!" 1; fi
if [ ! -f ${CFG_FILE} ]; then log $ERR "Config file '${CFG_FILE}' cannot be found! Script aborted!" 1; fi
if [ ! -r ${CFG_FILE} ]; then log $ERR "Can't read config file '${CFG_FILE}'! Script aborted!" 1; fi
log $FIN "..done"


##### Main routine ############################################################
IFS=,
while read -r action path args ; do

    ((CFG_LINE++))
    log $FNR "${CFG_LINE}: $action,$path,$args"

    ## Ignore empty lines
    if [[ -z "${action}" ]]; then continue; fi

    ## Ignore line if it starts with a # (comment line)
    if [[ "${action:0:1}" == "#" ]]; then continue; fi

    ## check existence of path
#    if [ ! -f ${path} ]; then
#        echo "${CFG_LINE}: Path '${path}' does not exist! Line is skipped!"; continue;
#    fi


    ## Expected format: <<action>>,<<path>>,days
    case ${action} in
      del)
        # check args (arg is days to retain)
        days=${args}
        if [[ ! ${days} == ?(-)+([0-9]) ]]; then log $WRN "#${CFG_LINE}: Third parameter (days) for action 'del' must be numeric! Line is skipped!"; continue; fi
        log $FST "${CFG_LINE}: find ${path} -mtime +${days} -exec rm -r {}\" "
        COUNT=$(find ${path} -mtime +${days}|wc -l)
        log $FIN "Files removed:\n$(find ${path} -mtime +${days})"
        find ${path} -mtime +${days} -exec rm -fr {} \;
        log $INF "${CFG_LINE}: ${COUNT} files deleted in folder ${path}"
        ((DEL_COUNT+=${COUNT}))
        ((DEL_FLDRS++))
        ;;
      *)
        log $WRN "${CFG_LINE}: Action '${action}' is not a valid action! Line is skipped!"
        ((ERR_FLDRS++))
        continue;
        ;;
    esac

done < "${CFG_FILE}"

log $INF "Summary:"
log $INF " - ${DEL_COUNT} files deleted in ${DEL_FLDRS} folders"
if [ ${ERR_FLDRS} -gt 0 ]; then
    log $ERR " - ${ERR_FLDRS} lines contained errors in configfile ${CFG_FILE}"
    exit 1
fi

exit 0


