# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains cache pickled dict loader class.
'''

from ..glogger import getGLogger
from .base import BasePckLoader

__all__ = ['CachePckLoader']
log = getGLogger('L')


class CachePckLoader(BasePckLoader):
    '''
    Load datasets from cache dict. Return a dictionary-like object.

    Notes
    -----
    1. *path*: a name of cache loader, is 'dict.cache'.
    2. keys: (k1, k2, g1/k3, g1/k4, g2/k5).
       invalid: (/k0, /g2/k6, /g2/k7/, /g2/k8/k9)
    '''
    __slots__ = ['_cache_dict']
    loader_type = '.cache'

    def _check_path_access(self, path):
        self._cache_dict = path
        return True

    def _special_check_path(self):
        if isinstance(self.path, dict):
            self.path = 'dict.cache'
            return True
        else:
            log.error("'%s' is not a dict!" % self.path)
            return False

    def _special_open(self):
        return self._cache_dict

    def _special_close(self, tmpobj):
        pass

    def _special_getkeys(self, tmpobj):
        mykeys = []
        for k in tmpobj.keys():
            if isinstance(tmpobj[k], dict):
                mykeys.extend([k + '/' + kk for kk in tmpobj[k]])
            else:
                mykeys.append(k)
        return mykeys

    def _special_getgroups(self, tmpobj):
        return [k for k in tmpobj.keys() if isinstance(tmpobj[k], dict)]

    def _special_get(self, tmpobj, key):
        keyl = key.strip('/').split('/')
        if len(keyl) == 1:
            return tmpobj[key]
        elif len(keyl) == 2:
            return tmpobj[keyl[0]][keyl[1]]
        else:
            raise ValueError('Wrong key "%s"!' % key)
