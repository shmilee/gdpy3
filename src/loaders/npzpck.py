# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains Npz pickled file loader class.
'''

import numpy
import zipfile

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckLoader

__all__ = ['NpzPckLoader']
log = getGLogger('L')


@inherit_docstring(BasePckLoader, parse=None, template=None)
class NpzPckLoader(BasePckLoader):
    '''
    Load pickled data from ``.npz`` file. Return a dictionary-like object.

    Attributes
    ----------
    {Attributes}

    Parameters
    ----------
    {Parameters}

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
        return numpy.load(self.path, allow_pickle=True)

    def _special_close(self, pathobj):
        pathobj.close()

    def _special_getkeys(self, pathobj):
        return sorted(dict.fromkeys(pathobj.files))

    def _special_get(self, pathobj, key):
        value = pathobj[key]
        if value.size == 1:
            value = value.item()
        return value
