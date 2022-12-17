# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains jsonl pickled file loader class.
'''

import numpy
from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckLoader, _pck_copydoc_func
from .._json import JsonLines

__all__ = ['JsonlPckLoader']
log = getGLogger('L')


@inherit_docstring((BasePckLoader,), _pck_copydoc_func, template=None)
class JsonlPckLoader(BasePckLoader):
    '''
    Load pickled data from `.jsonl` or `.jsonl-gz` file.
    Return a dictionary-like object.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    -----
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
