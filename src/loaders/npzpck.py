# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains Npz pickled file loader class.
'''

import numpy
import zipfile

from ..glogger import getGLogger
from .base import BasePckLoader

__all__ = ['NpzPckLoader']
log = getGLogger('L')


class NpzPckLoader(BasePckLoader):
    '''
    Load pickled data from ``.npz`` file. Return a dictionary-like object.

    Notes
    -----
    Q: How to read data from .npz file?
    A: npzfile[datakey]
    >>> npzfile = numpy.load('/tmp/test.npz')
    >>> datakey = 'group/key'
    >>> npzfile[datakey]
    '''
    __slots__ = []
    loader_type = '.npz'

    def _special_check_path(self):
        if zipfile.is_zipfile(self.path):
            return True
        else:
            log.error("'%s' is not a ZIP file!" % self.path)
            return False

    def _special_open(self):
        return numpy.load(self.path)

    def _special_close(self, tmpobj):
        tmpobj.close()

    def _special_getkeys(self, tmpobj):
        return tmpobj.files

    def _special_get(self, tmpobj, key):
        value = tmpobj[key]
        if value.size == 1:
            value = value.item()
        return value
