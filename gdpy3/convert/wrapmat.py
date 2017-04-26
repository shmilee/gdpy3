# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging

__all__ = ['iopen', 'write', 'close']

log = logging.getLogger('gdc')


try:
    import scipy
except ImportError:
    log.error('If you want to save data in a .mat file, '
              'please install scipy.')
    raise

# TODO(nobody): scipy.io.savemat, share data with matlab


def iopen(hdf5file):
    pass


def write(h5pyfile, name, data):
    pass


def close(h5pyfile):
    pass
