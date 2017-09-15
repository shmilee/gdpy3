# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
This module contains the default values and the validation code for
customization using gdpy3's config settings.
'''

import os
import io
import sys
import logging

# a map from key -> value, validatetype
defaultParams = {
    # gdpy3
    'gdpy3.log.level': [logging.INFO, int],
    'gdpy3.log.format': ['[%(name)s]%(levelname)s - %(message)s', str],
    'gdpy3.log.datefmt': ['%Y-%m-%d %H:%M:%S',  str],
    'gdpy3.log.handlers': [['StreamHandler', 'FileHandler'], list],
    'gdpy3.log.stream': [sys.stdout, io.TextIOWrapper],
    'gdpy3.log.filename': ['/tmp/gdpy3.log', str],
    'gdpy3.gtc.version': ['110922', str],
    # gdpy3.convert
    'gdc.log.level': [logging.INFO, int],
    'gdc.save.ext': ['.npz', str],
    'gdc.gtcout.additionalpats': [[], list],
    'gdc.raw.salt': ['gtc.out', str],
    'gdc.raw.ext': ['.npz', str],
    'gdc.raw.overwrite': [False, bool],
    # gdpy3.plot
    'gdp.log.level': [logging.INFO, int],
    'gdp.engine.default': ['matplotlib', str],
    'gdp.engine.mpl.': [],
}
