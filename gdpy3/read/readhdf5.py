# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import h5py

from .readnpz import ReadNpz

__all__ = ['ReadHdf5']

log = logging.getLogger('gdr')


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
    __slots__ = ['file', 'datakeys', 'desc', 'description']

    def __init__(self, hdf5file):
        if os.path.isfile(hdf5file):
            self.file = hdf5file
        else:
            raise IOError("Failed to find file %s." % hdf5file)
        try:
            log.debug("Open file %s." % self.file)
            tempf = h5py.File(self.file, 'r')
            log.debug("Getting keys from %s ..." % self.file)
            mykeys = []
            tempf.visititems(
                lambda name, obj: mykeys.append(name)
                if isinstance(obj, h5py.Dataset) else None)
            self.datakeys = tuple(mykeys)
            self.desc = str(tempf['description'].value)
            self.description = self.desc
        except (IOError, ValueError):
            log.critical("Failed to read file %s." % self.file)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                tempf.close()

    def __getitem__(self, key):
        if key not in self.datakeys:
            raise KeyError("%s is not in '%s'" % (key, self.file))
        try:
            log.debug("Open file %s." % self.file)
            tempf = h5py.File(self.file, 'r')
            value = tempf[key].value
        except (IOError, ValueError):
            log.critical("Failed to get '%s' from '%s'!" % (key, self.file))
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                tempf.close()
        return value
