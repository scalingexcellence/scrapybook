#!/bin/bash

trap "" SIGINT

sleep 3

while read line
do
    # 4 per second
    sleep 0.25
    echo "1.20 * $line" | bc -l
done
