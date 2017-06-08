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
    datagroups: tuple
        groups of datakeys
    desc: str
        description of the .npz file
    description: alias desc
    cache: dict
        cached keys from NpzFile

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
    __slots__ = ['file', 'datakeys', 'datagroups',
                 'desc', 'description', 'cache']

    def _special_openfile(self):
        return numpy.load(self.file)

    def _special_closefile(self, tempf):
        tempf.close()

    def _special_getkeys(self, tempf):
        return tempf.files

    def _special_getitem(self, tempf, key):
        value = tempf[key]
        if value.size == 1:
            value = value.item()
        return value

    def __init__(self, npzfile):
        if os.path.isfile(npzfile):
            self.file = npzfile
        else:
            raise IOError("Failed to find file %s." % npzfile)
        try:
            log.debug("Open file %s." % self.file)
            tempf = self._special_openfile()
            log.debug("Getting keys from %s ..." % self.file)
            self.datakeys = tuple(self._special_getkeys(tempf))
            self.datagroups = tuple(
                os.path.dirname(k) for k in self.datakeys
                if k.endswith('/description'))
            self.desc = str(self._special_getitem(tempf, 'description'))
            self.description = self.desc
        except (IOError, ValueError):
            log.critical("Failed to read file %s." % self.file)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tempf)
        self.cache = {}

    def keys(self):
        return self.datakeys

    def __getitem__(self, key):
        if key not in self.datakeys:
            raise KeyError("%s is not in '%s'" % (key, self.file))
        if key in self.cache:
            return self.cache[key]
        try:
            log.debug("Open file %s." % self.file)
            tempf = self._special_openfile()
            value = self._special_getitem(tempf, key)
            self.cache[key] = value
        except (IOError, ValueError):
            log.critical("Failed to get '%s' from '%s'!" % (key, self.file))
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tempf)
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
        result = [self.cache[k] if k in self.cache else None for k in keys]
        idxtodo = [i for i, k in enumerate(result) if k is None]
        if len(idxtodo) == 0:
            return tuple(result)
        try:
            log.debug("Open file %s." % self.file)
            tempf = self._special_openfile()
            for i in idxtodo:
                key = keys[i]
                value = self._special_getitem(tempf, key)
                result[i] = value
                self.cache[key] = value
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
                self._special_closefile(tempf)
        return tuple(result)
