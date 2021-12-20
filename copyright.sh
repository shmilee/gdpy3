#!/bin/bash
# Copyright (C) 2021 shmilee
YEAR=$(date +%Y)
sed -i "s|\(20..-\)20..\( shmilee\)|\1${YEAR}\2|" \
    ./LICENSE \
    ./docs/source/conf.py \
    ./src/__about__.py
