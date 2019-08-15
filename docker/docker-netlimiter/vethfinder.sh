#!/bin/bash

# Script adapted from original at https://superuser.com/questions/1183454/finding-out-the-veth-interface-of-a-docker-container

# Get Docker container name from input argument
container=$1

# Find the veth network interface via iflink (in container) and ifindex (on docker host)
iflink=`docker exec -it $container bash -c 'cat /sys/class/net/eth0/iflink'`
iflink=`echo $iflink|tr -d '\r'`
veth=`grep -l $iflink /sys/class/net/veth*/ifindex`
veth=`echo $veth|sed -e 's;^.*net/\(.*\)/ifindex$;\1;'`
echo $veth
