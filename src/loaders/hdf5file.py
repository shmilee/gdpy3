# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import numpy
try:
    import h5py
except ImportError as exc:
    raise ImportError('Hdf5FileLoader requires h5py(bindings for HDF5). But %s' % exc) from None

from ..glogger import getGLogger
from .base import BaseFileLoader

__all__ = ['Hdf5FileLoader']
log = getGLogger('L')


class Hdf5FileLoader(BaseFileLoader):
    '''
    Load datasets from ``.hdf5`` file. Return a dictionary-like object.

    Notes
    -----
    Q: How to read data from .hdf5 file?
    A: h5file[datakey].value
    >>> h5file = h5py.File('/tmp/test.hdf5', 'r')
    >>> datakey = 'group/key'
    >>> h5file[datakey].value
    >>> h5file[datakey][()]
    >>> h5file[datakey][...]
    '''
    __slots__ = []

    def _special_openfile(self):
        return h5py.File(self.file, 'r')

    def _special_closefile(self, tmpobj):
        tmpobj.close()

    def _special_getkeys(self, tmpobj):
        mykeys = []
        tmpobj.visititems(
            lambda name, obj: mykeys.append(name)
            if isinstance(obj, h5py.Dataset) else None)
        return mykeys

    def _special_getitem(self, tmpobj, key):
        return tmpobj[key].value
