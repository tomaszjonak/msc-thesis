#!/usr/bin/env bash
sudo tc qdisc del dev $1 root &>/dev/null
sudo tc qdisc add dev $1 root tbf rate $2 latency $3 burst 1540
tc qdisc show dev $1

