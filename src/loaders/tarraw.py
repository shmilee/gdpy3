# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains TarFile raw loader class.
'''

import os
import io
import tarfile

from ..glogger import getGLogger
from .base import BaseRawLoader

__all__ = ['TarRawLoader']
log = getGLogger('L')


class TarRawLoader(BaseRawLoader):
    # https://docs.python.org/3/library/tarfile.html
    '''
    Load raw data from a tar archive. Return a dictionary-like object.
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

    def _special_close(self, tmpobj):
        tmpobj.close()

    def _special_getkeys(self, tmpobj):
        return sorted(
            [n for n in tmpobj.getnames() if tmpobj.getmember(n).isfile()])

    def _special_get(self, tmpobj, key):
        # bytes -> str
        # BufferedReader -> TextIOWrapper encoding='UTF-8'
        return io.TextIOWrapper(tmpobj.extractfile(key))
