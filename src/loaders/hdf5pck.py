# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains Hdf5 pickled file loader class.
'''

try:
    import h5py
except ImportError as exc:
    raise ImportError(
        'Hdf5PckLoader requires h5py(bindings for HDF5). But %s' % exc) from None

from ..glogger import getGLogger
from .base import BasePckLoader

__all__ = ['Hdf5PckLoader']
log = getGLogger('L')


class Hdf5PckLoader(BasePckLoader):
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
    loader_type = '.hdf5'

    def _special_check_path(self):
        if h5py.is_hdf5(self.path):
            return True
        else:
            log.error("'%s' is not a valid HDF5 file!" % self.path)
            return False

    def _special_open(self):
        return h5py.File(self.path, 'r')

    def _special_close(self, tmpobj):
        tmpobj.close()

    def _special_getkeys(self, tmpobj):
        mykeys = []
        tmpobj.visititems(
            lambda name, obj: mykeys.append(name)
            if isinstance(obj, h5py.Dataset) else None)
        return mykeys

    def _special_getgroups(self, tmpobj):
        mygroups = []
        tmpobj.visititems(
            lambda name, obj: mygroups.append(name)
            if isinstance(obj, h5py.Group) else None)
        return mygroups

    def _special_get(self, tmpobj, key):
        return tmpobj[key].value
