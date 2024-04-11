# -*- coding: utf-8 -*-

# Copyright (c) 2018-2021 shmilee

'''
Contains directory raw loader class.
'''

import os
import pathlib

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BaseRawLoader, _raw_copydoc_func

__all__ = ['DirRawLoader']
log = getGLogger('L')


@inherit_docstring((BaseRawLoader,), _raw_copydoc_func, template=None)
class DirRawLoader(BaseRawLoader):
    '''
    Load raw data from a directory. Return a dictionary-like object.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    {Notes}
    3. Directory tree maxdepth is 2.
    4. The representation of Windows's path also uses forward slashes (/)!
    '''
    __slots__ = ['_WinFilenames']
    loader_type = 'directory'

    def _special_check_path(self):
        if os.path.isdir(self.path):
            return True
        else:
            log.error("'%s' is not a directory!" % self.path)
            return False

    def _special_open(self):
        # for multiprocessing __setstate__
        self._WinFilenames = None
        return self.path

    def _special_close(self, pathobj):
        pass

    def _special_getkeys(self, pathobj):
        filenames = []
        for _root, _dirs, _files in os.walk(self.path):
            # _root: '/path/'->'', '/path/sub1'->'sub1', '/p/s1/s2'->'s1/s2'
            _root = _root[len(self.path):].strip(os.sep)
            # len(_root) == 0, !find path -maxdepth 1 -type f
            # len(_root)  > 0, maxdepth 2
            # _root.count(os.path.sep) == 1, maxdepth 3
            if len(_root) > 0:
                _dirs[:] = []
            else:
                _dirs[:] = [d for d in _dirs
                            if not self.exclude_match(d, dirname=True)]
            filenames.extend([os.path.join(_root, f) for f in _files
                              if not self.exclude_match(f)])
        if os.name == 'nt':
            self._WinFilenames = {}
            # new dict, use key:filenames as_posix, val: WindowsPath instance
            for f in filenames:
                P = pathlib.PurePath(f)
                self._WinFilenames[P.as_posix()] = P
            return sorted(self._WinFilenames.keys())
        else:
            return sorted(filenames)

    def _special_get(self, pathobj, key):
        if os.name == 'nt':
            key = self._WinFilenames[key]
        return open(pathlib.PurePath(self.path).joinpath(key))
