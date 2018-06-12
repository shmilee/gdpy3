# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains saver base class.
'''

import os

from ..glogger import getGLogger

__all__ = ['BasePckSaver']
log = getGLogger('S')


class BasePckSaver(object):
    '''
    Save arrays data in dict with a group name to a file or cache.

    Attributes
    ----------
    path: str
        path of the file or cache name
    status: bool
        True, store object open; False, store object closed

    Parameters
    ----------
    path: str

    Notes
    -----
    1. Instances of the class can be used with the ``with`` statement.
    2. Use :meth:`iopen` to open saver, then :meth:`write` data,
       finally, remember to :meth:`close` saver.
    3. :meth:`get_store` is for cooperation with
       :class:`gdpy3.loaders.base.BasePckLoader`.
    '''
    __slots__ = ['path', '_storeobj', 'status']
    _extension = '.extension-of-path'

    def _check_path_access(self):
        '''Check for access to *path*.'''
        pathdir = os.path.dirname(self.path) or '.'
        return (os.access(self.path, os.W_OK) or os.access(pathdir, os.W_OK))

    def _check_path_exists(self):
        '''*path* exists or not'''
        return os.path.exists(self.path)

    def _open_append(self):
        '''
        Return `append` mode store object.
        '''
        raise NotImplementedError()

    def _open_new(self):
        '''
        Return `write` mode store object.
        '''
        raise NotImplementedError()

    def _write(self, group, data):
        '''
        Write *data* to store object.
        '''
        raise NotImplementedError()

    def _close(self):
        '''
        Close store object.
        '''
        self._storeobj.close()
        self._storeobj = None

    def get_store(self):
        '''Return store path or object.'''
        return self.path

    def __init__(self, path):
        self.path = path
        self._storeobj = None
        self.status = False
        if not self._check_path_access():
            raise IOError("Can't access path '%s'!" % self.path)
        _p, ext = os.path.splitext(self.path)
        if ext != self._extension:
            log.warning("Path's extension should be '%s', not '%s'!"
                        % (self._extension, ext))
            self.path = _p + self._extension

    def iopen(self):
        '''
        Initialize store object.
        Open *path* if exists, create otherwise.
        '''
        if self.status:
            log.warning("The store object has been initialized.")
            return
        path = self.path
        if self._check_path_exists():
            try:
                log.debug("Open path '%s' to append data." % path)
                self._storeobj = self._open_append()
                self.status = True
            except Exception:
                log.error("Failed to open path '%s'." % path, exc_info=1)
                raise
        else:
            try:
                log.debug("Create path '%s' to store data." % path)
                self._storeobj = self._open_new()
                self.status = True
            except Exception:
                log.error("Failed to create path '%s'." % path, exc_info=1)
                raise

    def write(self, group, data):
        '''
        Write dict *data* with *group* name to store object.

        Parameters
        ----------
        group: str, group name
        data: dict, data in this *group*
        '''
        if not self.status:
            log.error("Store object is not initialized!")
            return False
        else:
            if not (isinstance(group, str) and isinstance(data, dict)):
                log.error("'group' is not str, or 'data' is not dict!")
                return False
            else:
                self._write(group, data)
                return True

    def close(self):
        '''
        Close initialized file object.
        '''
        if self.status:
            log.debug("Close path '%s'." % self.path)
            self._close()
            self.status = False

    def __enter__(self):
        self.iopen()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return '<{0}.{1} object at {2} for {3}>'.format(
            self.__module__, type(self).__name__, hex(id(self)), self.path)
