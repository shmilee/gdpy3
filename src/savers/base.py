# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains saver base class.
'''

import os

from ..glogger import getGLogger

__all__ = ['BaseFileSaver']
log = getGLogger('S')


class BaseFileSaver(object):
    '''
    Save dict data with a group name to a file.

    Attributes
    ----------
    file: path of the file
    fobj: the initialized file object

    Parameters
    ----------
    file : str, path of the file

    Methods
    -------
    iopen()
    write(group, data)
    close()
    '''
    __slots__ = ['file', 'fobj']
    _extension = '.extension-of-file'

    def __init__(self, file):
        file = self._setpathname(file, self._extension)
        filedir = os.path.dirname(file)
        if os.access(filedir, os.W_OK):
            self.file = file
            self.fobj = None
        else:
            raise IOError("Can't access directory '%s'!" % filedir)

    @staticmethod
    def _setpathname(pathname, ext):
        '''
        If pathname extension is not ``ext``, change it's extension
        '''
        if os.path.splitext(pathname)[1] != ext:
            return pathname + ext
        else:
            return pathname

    def _open_append(self):
        '''
        return `append` mode file object
        '''
        raise NotImplementedError()

    def _open_new(self):
        '''
        return `write` mode file object
        '''
        raise NotImplementedError()

    def _write(self, group, data):
        '''
        Write *data* to file object.
        '''
        raise NotImplementedError()

    def _close(self):
        '''
        Close file object.
        '''
        raise NotImplementedError()

    def iopen(self):
        '''
        Initialize file object.
        Open ``file`` if exists, create otherwise.
        '''

        if self.fobj is not None:
            log.warn("The file object has been initialized.")
            return
        file = self.file
        if os.path.isfile(file):
            try:
                log.debug("Open file '%s' to append data." % file)
                self.fobj = self._open_append()
                return
            except Exception:
                log.error("Failed to open file '%s'." % file, exc_info=1)
                raise
        else:
            try:
                log.debug("Create file '%s' to store data." % file)
                self.fobj = self._open_new()
                return
            except Exception:
                log.error("Failed to create file '%s'." % file, exc_info=1)
                raise

    def write(self, group, data):
        '''
        Write dict *data* with *group* name to file object.

        Parameters
        ----------
        group: str, group name
        data: dict data in this group
        '''

        if self.fobj is None:
            log.error("File object is not initialized!")
            return False
        else:
            if not (isinstance(group, str) and isinstance(data, dict)):
                log.error("``group`` is not str, or ``data`` is not dict!")
                return False
            else:
                self._write(group, data)
                return True

    def close(self):
        '''
        Close initialized file object.
        '''
        if self.fobj is not None:
            log.debug("Close initialized file '%s'." % self.file)
            self._close()
            self.fobj = None
