#!/bin/bash

set -e

# Docker netlimiter
#
# NOTE! Run this script as root or sudo!
#

help() {
    echo ""
    echo "Example usage"
    echo "Set bandwidth limiting:    sudo ./docker-netlimiter.sh -n containerName -d 8mbit -u 8mbit"
    echo "Clear all rules:           sudo ./docker-netlimiter.sh -n containerName -C"
    echo ""
    exit
}

clearlimits () {
    if [ -z ${CONTAINER} ]; then
        echo "Error: Container name option '-n' required!"
        exit 1
    fi

    VETH=$(./vethfinder.sh ${CONTAINER} )
    echo "Clearing network limits on interface '${VETH}' for container '${CONTAINER}'...";

    # Clear the traffic control queue for this interface
    tc qdisc del dev ${VETH} root

    if [ $? == 0 ]; then
        echo "Cleared!";
    fi
    exit
}

status () {
    if [ -z ${CONTAINER} ]; then
        echo "Error: Container name option '-n' required!"
        exit 1
    fi

    VETH=$(./vethfinder.sh ${CONTAINER} )

    tc -s qdisc ls dev ${VETH}
	exit
}


# Get CLI arguments
while getopts n:d:u:hCs option
do
    case "${option}"
    in
        n) CONTAINER=${OPTARG};;
        d) DOWNLIM=${OPTARG};;
        u) UPLIM=${OPTARG};;
        h) help;;
        C) clearlimits;;
		s) status;;
    esac
done

# Start main script
if [ -z ${CONTAINER} ]; then
    echo "Error: Container name '-n' is missing!"
    help
    exit 1
fi

if [ -z ${DOWNLIM} ] || [ -z ${UPLIM} ]; then
    echo "Error: Download '-d' or upload limit '-u' is missing!"
    help
    exit 1
fi


# Find the veth network adapter and IP-address of the container
VETH=$(./vethfinder.sh ${CONTAINER} )
IP=$(docker exec ${CONTAINER} bash -c "ip addr show | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' ")

# Classless implementation (quick-and-dirty)
# tc qdisc add dev ${VETH} root tbf rate ${DOWNLIM} burst 32kbit latency 400ms

#Add root qdisc (queueing discipline) and create child classes for download and upload limit
tc qdisc add dev ${VETH} root handle 1: htb default 30
tc class add dev ${VETH} parent 1: classid 1:1 htb rate ${DOWNLIM}
tc class add dev ${VETH} parent 1: classid 1:2 htb rate ${UPLIM}


# Differentiate between upload and download limit using 'tc filter'
# It can match on all fields of a packet header, as well as on the firewall mark applied by ipchains or iptables.
# TODO: Upload is not limited yet. Fix mistake below with 'src ${IP}'
# TODO: Some websites indicate that only upload speed can be limited easily using tc (contd. on next line)
# TODO: Think about the meaning of upload and download. A download from the internet would be an upload to the docker container as seen from host machine's perspective?!
tc filter add dev ${VETH} protocol ip parent 1:0 prio 1 u32 match ip dst ${IP}/32 flowid 1:1
tc filter add dev ${VETH} protocol ip parent 1:0 prio 1 u32 match ip src ${IP}/32 flowid 1:2


echo "Setting network limits on interface '${VETH}' for container '${CONTAINER}'...";
if [ $? == 0 ]; then
    echo "Done!";
fi
