# -*- coding: utf-8 -*-

# Copyright (c) 2018-2021 shmilee

'''
Contains loader base class.
'''

import os
import re
import contextlib

from ..glogger import getGLogger

__all__ = ['BaseLoader', 'BaseRawLoader', 'BasePckLoader']
log = getGLogger('L')


class BaseLoader(object):
    '''
    Base class of BaseRawLoader, BasePckLoader.

    Attributes
    ----------
    path: str
    '''
    __slots__ = ['path', 'pathobj']
    loader_type = 'base'

    def __init__(self, path):
        if self._check_path_access(path):
            self.path = path
            if not self._special_check_path():
                raise ValueError("Path '%s' checking failed." % path)
            self.pathobj = None
        else:
            raise IOError("Failed to access path '%s'." % path)

    def update(self, *args, **kwargs):
        '''
        Update path object, keys, etc.
        '''
        raise NotImplementedError()

    @staticmethod
    def _check_path_access(path):
        '''
        Check for access to *path*.
        '''
        if os.path.exists(path) and os.access(path, os.R_OK):
            return True
        else:
            return False

    def _special_check_path(self):
        '''
        Recheck the path. Return bool.
        '''
        raise NotImplementedError()

    def _special_open(self):
        '''
        Return path object to read.
        '''
        raise NotImplementedError()

    def _special_close(self, pathobj):
        '''
        Close path object.
        '''
        raise NotImplementedError()

    def _special_getkeys(self, pathobj):
        '''
        Return all keys in path object.
        '''
        raise NotImplementedError()

    def _special_get(self, pathobj, item):
        '''
        Return value object of key *item* in path object.
        '''
        raise NotImplementedError()

    def close(self):
        if self.pathobj:
            log.debug("Close path %s." % self.path)
            self._special_close(self.pathobj)
            self.pathobj = None

    def keys(self):
        '''Return loader keys.'''
        raise NotImplementedError()

    def gen_match_conditions(self, conditions):
        '''
        Generate & Return a functions tuple of match conditions.
        conditions: list of function or regular expression.
        '''
        conds = conditions if isinstance(conditions, (tuple, list)) else []
        return tuple(c if callable(c) else re.compile(c).match for c in conds)

    def match_item(self, item, conditions, logical='and'):
        '''
        Match *item* with *conditions* get by :meth:`gen_match_conditions`.
        *logical*(and/or) is used to combine conditions.
        '''
        if not conditions:
            return False  # [] ()
        for cond in conditions:
            if cond(item):
                if logical == 'or':
                    return True
            else:
                if logical == 'and':
                    return False
        return False if logical == 'or' else True

    def find(self, *strings, logical='and'):
        '''
        Find the loader keys which contain *strings*.
        '''
        conditions = tuple((lambda k: str(s) in k) for s in strings)
        return tuple(k for k in self.keys()
                     if self.match_item(k, conditions, logical=logical))

    def refind(self, *patterns, logical='and'):
        '''
        Find the loader keys which match the regular expression *patterns*.
        '''
        matchs = self.gen_match_conditions(patterns)
        return tuple(k for k in self.keys()
                     if self.match_item(k, matchs, logical=logical))

    def __contains__(self, item):
        '''
        Return true if item is in loader, false otherwise.
        '''
        return item in self.keys()

    def all_in_loader(self, *items):
        '''
        Check if all the *items* are in this loader.
        '''
        loaderkeys = self.keys()
        result = True
        for i in items:
            if i not in loaderkeys:
                # do not break, warning all lost keys!
                log.warning("Key '%s' not in %s!" % (i, self.path))
                result = False
        return result

    def __repr__(self):
        return '<{0} object at {1} for {2}>'.format(
            type(self).__name__, hex(id(self)), self.path)
        # return '<{0}.{1} object at {2} for {3}>'.format(
        #    self.__module__, type(self).__name__, hex(id(self)), self.path)

    def __getstate__(self):
        # self.pathobj may has '_io.BufferedReader' object,
        # which cannot be pickled, when use multiprocessing.
        return [(name, getattr(self, name))
                for cls in type(self).__mro__
                for name in getattr(cls, '__slots__', [])
                if name != 'pathobj']

    def __setstate__(self, state):
        for name, value in state:
            setattr(self, name, value)
        self.pathobj = self._special_open()


class BaseRawLoader(BaseLoader):
    '''
    Load raw data from a directory or archive file.
    Return a dictionary-like object.

    Attributes
    ----------
    pathobj: opened path object
    filenames: tuple
        filenames using forward slashes (/) in the directory or archive file

    Parameters
    ----------
    path: str
        path of directory or archive file
    dirnames_exclude: list
        function or regular expression to exclude subdirectory names,
        like, 'restart_dir1' for GTC. Only used by directory-like loader.
    filenames_exclude: list
        function or regular expression to exclude filenames,
        example: [r'.*\.txt$', 'bigdata.out'] or [r'(?!^include\.out$)']

    Notes
    -----
    1. Method *get()* must be used as with statement context managers.
    2. File-like object which returned by *get()* must has close method,
       and read, readline, or readlines.
    '''
    __slots__ = ['filenames', 'dirnames_exclude', 'filenames_exclude']

    def __init__(self, path, dirnames_exclude=None, filenames_exclude=None):
        super(BaseRawLoader, self).__init__(path)
        self.dirnames_exclude = self.gen_match_conditions(dirnames_exclude)
        self.filenames_exclude = self.gen_match_conditions(filenames_exclude)
        self.update()

    def exclude_match(self, name, dirname=False):
        exclude = self.dirnames_exclude if dirname else self.filenames_exclude
        return self.match_item(name, exclude, logical='or')

    def update(self):
        self.close()
        self.filenames = None
        try:
            log.debug("Open path %s." % self.path)
            pathobj = self._special_open()
            log.debug("Getting filenames from %s ..." % self.path)
            filenames = self._special_getkeys(pathobj)
            self.pathobj = pathobj
            self.filenames = tuple(sorted(filenames))
        except (IOError, ValueError):
            log.error("Failed to read path %s." % self.path, exc_info=1)
            raise

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
            log.debug("Getting file '%s' from %s ..." % (key, self.path))
            fileobj = self._special_get(self.pathobj, key)
            yield fileobj
        except (IOError, ValueError):
            log.error("Failed to get '%s' from %s!" %
                      (key, self.path), exc_info=1)
            raise
        finally:
            if 'fileobj' in dir():
                log.debug("Close file %s in path %s." % (key, self.path))
                fileobj.close()

    def beside_path(self, name):
        '''Get a path for *name*, join with :attr:`path`'''
        return os.path.join(self.path, name)


class BasePckLoader(BaseLoader):
    '''
    Load arrays data from a pickled(packaged) data file or cache.
    Return a dictionary-like object.

    Attributes
    ----------
    pathobj: opened path object
    datakeys: tuple
        keys in the loader, contain group name
    datagroups: tuple
        groups of datakeys
    description: str or None
        description of the data, if 'description' is in datakeys
    desc: alias description
    cache: dict
        cached datakeys from file

    Parameters
    ----------
    path: str
        path of the file to open
    datagroups_exclude: list
        a list of function or regular expression to exclude datagroups,
        example: [r'sanp\d+$', 'bigdata']
    '''
    __slots__ = ['datakeys', 'datagroups', 'datagroups_exclude',
                 'desc', 'description', 'cache']

    def _special_getgroups(self, pathobj):
        '''
        Return all keys' groups in path object.
        '''
        return set(os.path.dirname(k) for k in self.datakeys)

    def __init__(self, path, datagroups_exclude=None):
        super(BasePckLoader, self).__init__(path)
        self.datagroups_exclude = self.gen_match_conditions(datagroups_exclude)
        self.update()

    def update(self):
        self.close()
        self.datakeys, self.datagroups = None, None
        self.description, self.desc = None, None
        try:
            log.debug("Open path %s." % self.path)
            pathobj = self._special_open()
            self.pathobj = pathobj
            log.debug("Getting datakeys from %s ..." % self.path)
            self.datakeys = tuple(self._special_getkeys(pathobj))
            log.debug("Getting datagroups from %s ..." % self.path)
            all_datagroups = set(self._special_getgroups(pathobj))
            if '' in all_datagroups:
                all_datagroups.remove('')
            exc_datagroups = set(
                g for g in all_datagroups
                if self.match_item(g, self.datagroups_exclude, logical='or'))
            self.datagroups = tuple(sorted(all_datagroups - exc_datagroups))
            if exc_datagroups:
                for grp in exc_datagroups:
                    self.datakeys = tuple(
                        k for k in self.datakeys if not k.startswith(grp))
            log.debug("Getting description of %s ..." % self.path)
            if 'description' in self.datakeys:
                self.desc = str(self._special_get(pathobj, 'description'))
            else:
                self.desc = None
            self.description = self.desc
        except (IOError, ValueError):
            log.error("Failed to read path %s." % self.path, exc_info=1)
            raise
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
            raise KeyError("%s is not in '%s'" % (key, self.path))
        if key in self.cache:
            return self.cache[key]
        try:
            log.debug("Getting key '%s' from %s ..." % (key, self.path))
            value = self._special_get(self.pathobj, key)
            self.cache[key] = value
        except (IOError, ValueError):
            log.error("Failed to get '%s' from %s!" %
                      (key, self.path), exc_info=1)
            raise
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
            for i in idxtodo:
                key = keys[i]
                log.debug("Getting key '%s' from %s ..." % (key, self.path))
                value = self._special_get(self.pathobj, key)
                result[i] = value
                self.cache[key] = value
        except (IOError, ValueError):
            if 'key' in dir():
                log.error("Failed to get '%s' from %s!" %
                          (key, self.path), exc_info=1)
            else:
                log.error("Failed to open '%s'!" % self.path, exc_info=1)
            raise
        return tuple(result)

    def get_by_group(self, group):
        '''
        Get all values by ``keys`` in group.
        Return a dict of keys' basenames and values.
        '''
        allkeys = self.refind('^%s/' % re.escape(group))
        basekeys = [os.path.basename(k) for k in allkeys]
        resultstuple = self.get_many(*allkeys)
        results = {k: v for k, v in zip(basekeys, resultstuple)}
        return results

    def clear_cache(self):
        self.cache = {}
