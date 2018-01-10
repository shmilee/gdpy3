# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains loader base class.
'''

import os
import types
import contextlib

from ..glogger import getGLogger

__all__ = ['BaseRawLoader', 'BaseFileLoader']
log = getGLogger('L')


class BaseRawLoader(object):
    '''
    Load raw data from a directory or archive file.
    Return a dictionary-like object.

    Attributes
    ----------
    path: str
        path of archive file or directory
    filenames: tuple
        filenames in the archive file or the directory

    Parameters
    ----------
    path: str
        path of file or directory
    filenames_filter: function
        a function to filter filenames, example:
        lambda name: True if name.endswith('.out') else False

    Notes
    -----
    1. Method *get()* must be used as with statement context managers.
    2. File-like object which returned by *get()* must has close method,
       and read, readline, or readlines.
    '''
    __slots__ = ['path', 'filenames']

    def _special_check_path(self):
        '''
        Check the directory or archive file. Return bool.
        '''
        raise NotImplementedError()

    def _special_open(self):
        '''
        Return path object to read.
        '''
        raise NotImplementedError()

    def _special_close(self, tmpobj):
        '''
        Close path object.
        '''
        raise NotImplementedError()

    def _special_getkeys(self, tmpobj):
        '''
        Return filenames in path object.
        '''
        raise NotImplementedError()

    def _special_getfile(self, tmpobj, key):
        '''
        Return file-like object of filename *key* in path object.
        '''
        raise NotImplementedError()

    def __init__(self, path, filenames_filter=None):
        if os.path.exists(path) and os.access(path, os.R_OK):
            self.path = path
            if not self._special_check_path():
                raise ValueError("Path '%s' checking failed." % path)
        else:
            raise IOError("Failed to access path '%s'." % path)
        try:
            log.debug("Open path %s." % self.path)
            tmpobj = self._special_open()
            log.debug("Getting filenames from %s ..." % self.path)
            filenames = tuple(self._special_getkeys(tmpobj))
            if isinstance(filenames_filter, types.FunctionType):
                filenames = [k for k in filenames if filenames_filter(k)]
            self.filenames = tuple(sorted(filenames))
        except (IOError, ValueError):
            log.critical("Failed to read path %s." % self.path, exc_info=1)
            raise
        finally:
            if 'tmpobj' in dir():
                log.debug("Close path %s." % self.path)
                self._special_close(tmpobj)

    def keys(self):
        return self.filenames

    @contextlib.contextmanager
    def get(self, key):
        '''
        Get file-like object by filename *key*.
        A function for with statement context managers.
        '''
        if key not in self.filenames:
            raise KeyError("%s is not in '%s'" % (key, self.path))
        try:
            log.debug("Open path %s." % self.path)
            tmpobj = self._special_open()
            log.debug("Getting file '%s' from %s ..." % (key, self.path))
            fileobj = self._special_getfile(tmpobj, key)
            yield fileobj
        except (IOError, ValueError):
            log.critical("Failed to get '%s' from %s!" %
                         (key, self.path), exc_info=1)
            raise
        finally:
            if 'fileobj' in dir():
                log.debug("Close file %s in path %s." % (key, self.path))
                fileobj.close()
            if 'tmpobj' in dir():
                log.debug("Close path %s." % self.path)
                self._special_close(tmpobj)


class BaseFileLoader(object):
    '''
    Load arrays data from a file. Return a dictionary-like object.

    Attributes
    ----------
    file: str
        path of the file
    datakeys: tuple
        keys in the file, contain group name
    datagroups: tuple
        groups of datakeys
    description: str or None
        description of the file, if 'description' is in datakeys
    desc: alias description
    cache: dict
        cached datakeys from file

    Parameters
    ----------
    file: str
        path of the file to open
    groups_filter: function
        a function to filter datakeys, used to get datagroups
        example, lambda key: True if key.endswith('/description') else False
    '''
    __slots__ = ['file', 'datakeys', 'datagroups',
                 'desc', 'description', 'cache']

    def _special_openfile(self):
        '''
        Return pickled object from file.
        '''
        raise NotImplementedError()

    def _special_closefile(self, tmpobj):
        '''
        Close pickled object.
        '''
        raise NotImplementedError()

    def _special_getkeys(self, tmpobj):
        '''
        Return datakeys in pickled object.
        '''
        raise NotImplementedError()

    def _special_getitem(self, tmpobj, key):
        '''
        Return value of *key* in pickled object.
        '''
        raise NotImplementedError()

    def __init__(self, file, groups_filter=None):
        if os.path.isfile(file):
            self.file = file
        else:
            raise IOError("Failed to find file %s." % file)
        try:
            log.debug("Open file %s." % self.file)
            tmpobj = self._special_openfile()
            log.debug("Getting datakeys from %s ..." % self.file)
            self.datakeys = tuple(self._special_getkeys(tmpobj))
            log.debug("Getting datagroups from %s ..." % self.file)
            if isinstance(groups_filter, types.FunctionType):
                datagroups = set(os.path.dirname(k)
                                 for k in self.datakeys if groups_filter(k))
            else:
                datagroups = set(os.path.dirname(k) for k in self.datakeys)
                datagroups.remove('')
            self.datagroups = tuple(sorted(datagroups))
            log.debug("Getting description of %s ..." % self.file)
            if 'description' in self.datakeys:
                self.desc = str(self._special_getitem(tmpobj, 'description'))
            else:
                self.desc = None
            self.description = self.desc
        except (IOError, ValueError):
            log.critical("Failed to read file %s." % self.file, exc_info=1)
            raise
        finally:
            if 'tmpobj' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tmpobj)
        self.cache = {}

    def keys(self):
        return self.datakeys

    def groups(self):
        return self.datagroups

    def get(self, key):
        '''
        Get value by ``key`.
        '''
        if key not in self.datakeys:
            raise KeyError("%s is not in '%s'" % (key, self.file))
        if key in self.cache:
            return self.cache[key]
        try:
            log.debug("Open file %s." % self.file)
            tmpobj = self._special_openfile()
            log.debug("Getting key '%s' from %s ..." % (key, self.file))
            value = self._special_getitem(tmpobj, key)
            self.cache[key] = value
        except (IOError, ValueError):
            log.critical("Failed to get '%s' from %s!" %
                         (key, self.file), exc_info=1)
            raise
        finally:
            if 'tmpobj' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tmpobj)
        return value

    __getitem__ = get

    def get_many(self, *keys):
        '''
        Get values by ``keys``. Return a tuple of values.
        '''
        result = [self.cache[k] if k in self.cache else None for k in keys]
        idxtodo = [i for i, k in enumerate(result) if k is None]
        if len(idxtodo) == 0:
            return tuple(result)
        try:
            log.debug("Open file %s." % self.file)
            tmpobj = self._special_openfile()
            for i in idxtodo:
                key = keys[i]
                log.debug("Getting key '%s' from %s ..." % (key, self.file))
                value = self._special_getitem(tmpobj, key)
                result[i] = value
                self.cache[key] = value
        except (IOError, ValueError):
            if 'key' in dir():
                log.critical("Failed to get '%s' from %s!" %
                             (key, self.file), exc_info=1)
            else:
                log.critical("Failed to open '%s'!" % self.file, exc_info=1)
            raise
        finally:
            if 'tmpobj' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tmpobj)
        return tuple(result)

    def find(self, *keys):
        '''
        Find the datakeys which contain ``keys``
        '''
        result = self.datakeys
        for key in keys:
            key = str(key)
            result = tuple(
                filter(lambda k: True if key in k else False, result))
        return tuple(result)

    def is_in_this(self, *keys):
        '''
        Check if all the *keys* are in this loader.
        '''
        result = True
        for key in keys:
            if key not in self.datakeys:
                log.warn("Key '%s' not in %s!" % (key, self.file))
                result = False
        return result

    def clear_cache(self):
        self.cache = {}