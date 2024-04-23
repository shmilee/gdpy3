# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains TarFile raw loader class.
'''

import os
import io
import tarfile

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BaseRawLoader

__all__ = ['TarRawLoader']
log = getGLogger('L')


@inherit_docstring(BaseRawLoader, parse=None, template=None)
class TarRawLoader(BaseRawLoader):
    # https://docs.python.org/3/library/tarfile.html
    '''
    Load raw data from a tar archive. Return a dictionary-like object.

    Attributes
    ----------
    {Attributes}

    Parameters
    ----------
    {Parameters}

    Notes
    -----
    {Notes}
    '''
    __slots__ = []
    loader_type = 'tarfile'

    def _special_check_path(self):
        if os.path.isfile(self.path) and tarfile.is_tarfile(self.path):
            return True
        else:
            log.error("'%s' is not a tar archive file!" % self.path)
            return False

    def _special_open(self):
        return tarfile.open(self.path, mode='r')

    def _special_close(self, pathobj):
        pathobj.close()

    def _special_getkeys(self, pathobj):
        return sorted([
            n for n in pathobj.getnames()
            if pathobj.getmember(n).isfile() and not self.exclude_match(n)])

    def _special_get(self, pathobj, key):
        # bytes -> str
        # BufferedReader -> TextIOWrapper encoding='UTF-8'
        return io.TextIOWrapper(pathobj.extractfile(key))

    def beside_path(self, name):
        return '-'.join([self.path[:self.path.rfind('.tar')], name])
