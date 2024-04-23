# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains jsonl pickled file loader class.
'''

import numpy
from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckLoader
from .._json import JsonLines, JsonZip

__all__ = ['JsonlPckLoader', 'JsonzPckLoader']
log = getGLogger('L')


@inherit_docstring(BasePckLoader, parse=None, template=None)
class JsonlPckLoader(BasePckLoader):
    '''
    Load pickled data from `.jsonl` file.
    Return a dictionary-like object.

    Attributes
    ----------
    {Attributes}

    Parameters
    ----------
    {Parameters}
    '''
    __slots__ = []
    loader_type = '.jsonl'

    def _special_check_path(self):
        try:
            i = JsonLines(self.path).index
            return True
        except Exception:
            log.error("'%s' is not a valid jsonl file!" % self.path)
            return False

    def _special_open(self):
        return JsonLines(self.path)

    def _special_close(self, pathobj):
        pathobj.clear_cache()

    def _special_getkeys(self, pathobj):
        return sorted(pathobj.keys())

    def _special_get(self, pathobj, key):
        value = pathobj.get_record(key)
        if isinstance(value, list):
            return numpy.array(value)
        else:
            return value


@inherit_docstring(BasePckLoader, parse=None, template=None)
class JsonzPckLoader(JsonlPckLoader):
    '''
    Load pickled data from `.jsonz` zip file.
    Return a dictionary-like object.

    Attributes
    ----------
    {Attributes}

    Parameters
    ----------
    {Parameters}
    '''
    __slots__ = []
    loader_type = '.jsonz'

    def _special_check_path(self):
        try:
            k = JsonZip(self.path).keys()
            return True
        except Exception:
            log.error("'%s' is not a valid jsonz file!" % self.path)
            return False

    def _special_open(self):
        return JsonZip(self.path)
