#!/bin/bash

cd /home/rune/code/RuneOrg/northy
git pull
source venv/bin/activate
python cli_signal.py watch