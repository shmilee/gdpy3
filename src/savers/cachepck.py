# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains cache pickled dict saver class.
'''

from ..glogger import getGLogger
from .base import BasePckSaver

__all__ = ['CachePckSaver']
log = getGLogger('S')


class CachePckSaver(BasePckSaver):
    '''
    Save dict data with a group name to a cache dict.

    Parameters
    ----------
    path: dict, store object
    '''
    __slots__ = []
    _extension = '.cache'

    def _check_path_access(self):
        return True

    def _check_path_exists(self):
        return isinstance(self._storeobj, dict)

    def _open_append(self):
        return self._storeobj

    def _open_new(self):
        return {}

    def _write(self, group, data):
        try:
            if group in ('/', ''):
                self._storeobj.update(data)
            else:
                if group in self._storeobj:
                    self._storeobj[group].update(data)
                else:
                    self._storeobj[group] = data
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)

    def _close(self):
        pass

    def get_store(self):
        '''Return store path or object.'''
        return self._storeobj
