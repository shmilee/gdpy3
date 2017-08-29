# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import h5py

from .readnpz import ReadNpz

__all__ = ['ReadHdf5']


class ReadHdf5(ReadNpz):
    '''Load datasets from .hdf5 file.
    Return a dictionary-like object Hdf5File.

    Attributes
    ----------
    file: str
        path of .hdf5 file
    datakeys: tuple
        keys of physical quantities in the .hdf5 file
    desc: str
        description of the .hdf5 file
    description: alias desc
    cache: dict
        cached keys from Hdf5File

    Parameters
    ----------
    hdf5file: str
        the .hdf5 file to open

    Examples
    --------
    >>> h5f = readhdf5.ReadHdf5('/tmp/test.hdf5')
    >>> h5f.keys()
    >>> h5f['a']
    '''
    __slots__ = []

    def _special_openfile(self):
        return h5py.File(self.file, 'r')

    def _special_closefile(self, tempf):
        tempf.close()

    def _special_getkeys(self, tempf):
        mykeys = []
        tempf.visititems(
            lambda name, obj: mykeys.append(name)
            if isinstance(obj, h5py.Dataset) else None)
        return mykeys

    def _special_getitem(self, tempf, key):
        return tempf[key].value
