# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains cache pickled dict loader class.
'''

from ..glogger import getGLogger
from ..utils import is_dict_like, inherit_docstring
from .base import BasePckLoader, _pck_copydoc_func

__all__ = ['CachePckLoader']
log = getGLogger('L')


@inherit_docstring((BasePckLoader,), _pck_copydoc_func, template=None)
class CachePckLoader(BasePckLoader):
    '''
    Load datasets from cache dict. Return a dictionary-like object.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    -----
    1. *path*: a name of cache loader, is 'dict.cache'.
    2. keys: (k1, k2, g1/k3, g1/k4, g2/k5, g3/sg3/k6).
       invalid: (/k0, /g2/k6, /g2/k7/, /g2/k8/k9)
    '''
    __slots__ = ['_cache_dict']
    loader_type = '.cache'

    def _check_path_access(self, path):
        self._cache_dict = path
        return True

    def _special_check_path(self):
        if is_dict_like(self.path):
            self.path = self.path.get('pathstr', 'dict.cache')
            return True
        else:
            log.error("'%s' is not a dict!" % self.path)
            return False

    def _special_open(self):
        return self._cache_dict

    def _special_close(self, pathobj):
        pass

    def _special_getkeys(self, pathobj):
        mykeys = []
        for k in pathobj.keys():
            if isinstance(pathobj[k], dict):
                mykeys.extend([k + '/' + kk for kk in pathobj[k]])
            else:
                mykeys.append(k)
        return mykeys

    def _special_getgroups(self, pathobj):
        return [k for k in pathobj.keys() if isinstance(pathobj[k], dict)]

    def _special_get(self, pathobj, key):
        gstop = key.rfind('/')
        if gstop == -1:
            return pathobj[key]
        elif gstop > 0:
            return pathobj[key[:gstop]][key[gstop+1:]]
        else:
            raise ValueError('Wrong key "%s"!' % key)
