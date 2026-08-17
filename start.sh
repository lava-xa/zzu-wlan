#!/bin/bash

cd /home/radiolab/zzu-wlan

while true
do
    uv run --with-requirements requirements.txt python3 main.py
    sleep 10
done
