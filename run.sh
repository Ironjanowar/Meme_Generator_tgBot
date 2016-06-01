#! /bin/bash

while true; do
    git pull
    python3 bot.py
    sleep 1
done
