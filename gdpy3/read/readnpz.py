# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import numpy

__all__ = ['ReadNpz']

log = logging.getLogger('gdr')


class ReadNpz(object):
    '''Load pickled objects from .npz file.
    Return a dictionary-like object NpzFile.

    Attributes
    ----------
    file: str
        path of .npz file
    datakeys: tuple
        keys of physical quantities in the .npz file
    desc: str
        description of the .npz file
    description: alias desc

    Parameters
    ----------
    npzfile: str
        the .npz file to open

    Examples
    --------
    >>> npzf = readnpz.ReadNpz('/tmp/test.npz')
    >>> npzf.keys()
    >>> npzf['a']
    '''
    __slots__ = ['file', 'datakeys', 'desc', 'description']

    def __init__(self, npzfile):
        if os.path.isfile(npzfile):
            self.file = npzfile
        else:
            raise IOError("Failed to find file %s." % npzfile)
        try:
            log.debug("Open file %s." % self.file)
            tempf = numpy.load(self.file)
            log.debug("Getting keys from %s ..." % self.file)
            self.datakeys = tuple(tempf.files)
            self.desc = str(tempf['description'])
            self.description = self.desc
        except (IOError, ValueError):
            log.critical("Failed to read file %s." % self.file)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                tempf.close()

    def keys(self):
        return self.datakeys

    def __getitem__(self, key):
        if key not in self.datakeys:
            raise KeyError("%s is not in '%s'" % (key, self.file))
        try:
            log.debug("Open file %s." % self.file)
            tempf = numpy.load(self.file)
            value = tempf[key]
            if value.size == 1:
                value = value.item()
        except (IOError, ValueError):
            log.critical("Failed to get '%s' from '%s'!" % (key, self.file))
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                tempf.close()
        return value

    get = __getitem__

    def find(self, *keys):
        '''find the datakeys which contain *keys
        '''
        result = self.datakeys
        for key in keys:
            key = str(key)
            result = tuple(
                filter(lambda k: True if key in k else False, result))
        return tuple(result)

    def get_many(self, *keys):
        '''
        Get values by keys. Return a tuple of values.
        '''
        result = []
        try:
            log.debug("Open file %s." % self.file)
            tempf = numpy.load(self.file)
            for key in keys:
                value = tempf[key]
                if value.size == 1:
                    value = value.item()
                result.append(value)
        except (IOError, ValueError):
            if 'key' in dir():
                log.critical("Failed to get '%s' from '%s'!"
                             % (key, self.file))
            else:
                log.critical("Failed to open '%s'!" % self.file)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                tempf.close()
        return tuple(result)
