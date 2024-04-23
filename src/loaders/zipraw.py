# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains ZipFile raw loader class.
'''

import os
import io
import zipfile

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BaseRawLoader

__all__ = ['ZipRawLoader']
log = getGLogger('L')


@inherit_docstring(BaseRawLoader, parse=None, template=None)
class ZipRawLoader(BaseRawLoader):
    # https://docs.python.org/3/library/zipfile.html
    '''
    Load raw data from a ZIP archive. Return a dictionary-like object.

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
    loader_type = 'zipfile'

    def _special_check_path(self):
        if os.path.isfile(self.path) and zipfile.is_zipfile(self.path):
            return True
        else:
            log.error("'%s' is not a ZIP archive file!" % self.path)
            return False

    def _special_open(self):
        return zipfile.ZipFile(self.path, mode='r')

    def _special_close(self, pathobj):
        pathobj.close()

    def _special_getkeys(self, pathobj):
        return sorted([
            n for n in pathobj.namelist()
            if not pathobj.getinfo(n).is_dir() and not self.exclude_match(n)])

    def _special_get(self, pathobj, key):
        # BufferedReader -> TextIOWrapper encoding='UTF-8'
        return io.TextIOWrapper(pathobj.open(key))

    def beside_path(self, name):
        return '-'.join([self.path[:self.path.rfind('.zip')], name])
