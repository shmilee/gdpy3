# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Contains NpzFile loader class.
'''

import numpy

from ..glogger import getGLogger
from .base import BaseFileLoader

__all__ = ['NpzFileLoader']
log = getGLogger('L')

class NpzFileLoader(BaseFileLoader):
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

    def _special_openfile(self):
        return numpy.load(self.file)

    def _special_closefile(self, tmpobj):
        tmpobj.close()

    def _special_getkeys(self, tmpobj):
        return tmpobj.files

    def _special_getitem(self, tmpobj, key):
        value = tmpobj[key]
        if value.size == 1:
            value = value.item()
        return value
