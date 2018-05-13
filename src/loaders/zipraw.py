# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains ZipFile raw loader class.
'''

import os
import io
import zipfile

from ..glogger import getGLogger
from .base import BaseRawLoader

__all__ = ['ZipRawLoader']
log = getGLogger('L')


class ZipRawLoader(BaseRawLoader):
    # https://docs.python.org/3/library/zipfile.html
    '''
    Load raw data from a ZIP archive. Return a dictionary-like object.
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

    def _special_close(self, tmpobj):
        tmpobj.close()

    def _special_getkeys(self, tmpobj):
        return sorted(
            [n for n in tmpobj.namelist() if not tmpobj.getinfo(n).is_dir()])

    def _special_get(self, tmpobj, key):
        # BufferedReader -> TextIOWrapper encoding='UTF-8'
        return io.TextIOWrapper(tmpobj.open(key))
