# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    This is the subpackage ``plot`` of package gdpy3.
'''

__all__ = ['tools', 'gtcfigures']

import os
import sys
import logging

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    # format='[%(asctime)s %(name)s] %(levelname)s - %(message)s',
    # datefmt='%Y-%m-%d %H:%M:%S',
    format='[%(name)s]%(levelname)s - %(message)s'
)

log = logging.getLogger('gdp')


def plot():
    pass
