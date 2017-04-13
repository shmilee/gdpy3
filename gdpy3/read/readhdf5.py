# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import h5py

__all__ = ['ReadHdf5']


class ReadHdf5(object):
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

    def __init__(self, hdf5file):
        if os.path.isfile(hdf5file):
            self.file = hdf5file
        else:
            raise IOError("Failed to find file %s." % hdf5file)
        try:
            tempf = h5py.File(self.file, 'r')
            mykeys = []
            tempf.visititems(
                lambda name, obj: mykeys.append(name)
                if isinstance(obj, h5py.Dataset) else None)
            self.datakeys = tuple(mykeys)
            self.desc = str(tempf['description'].value)
            self.description = self.desc
        except (IOError, ValueError):
            print("Failed to read file %s." % self.file)
            raise
        finally:
            if 'tempf' in dir():
                tempf.close()

    def keys(self):
        return self.datakeys

    def __getitem__(self, key):
        if key not in self.datakeys:
            raise KeyError("%s is not in '%s'" % (key, self.file))
        try:
            tempf = h5py.File(self.file, 'r')
            value = tempf[key].value
        except (IOError, ValueError):
            print("Failed to get '%s' from '%s'!" % (key, self.file))
            raise
        finally:
            if 'tempf' in dir():
                tempf.close()
        return value

    get = __getitem__
