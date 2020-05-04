# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Contains cache pickled dict saver class.
'''

from ..glogger import getGLogger
from ..utils import is_dict_like, inherit_docstring
from .base import BasePckSaver, _copydoc_func

__all__ = ['CachePckSaver']
log = getGLogger('S')


@inherit_docstring((BasePckSaver,), _copydoc_func, template=None)
class CachePckSaver(BasePckSaver):
    '''
    Save dict data with a group name to a cache dict.

    Attributes
    {Attributes}

    Parameters
    ----------
    path: dict, store object

    Notes
    {Notes}
    '''
    __slots__ = []
    _extension = '.cache'

    def _check_path_access(self):
        return True

    def _check_path_exists(self):
        return is_dict_like(self._storeobj)

    def _open_append(self):
        return self._storeobj

    def _open_new(self):
        return dict(pathstr=self.path)

    def _write(self, group, data):
        try:
            if group in ('/', ''):
                self._storeobj.update(data)
            else:
                if group in self._storeobj:
                    old = self._storeobj[group]
                    old.update(data)
                    self._storeobj[group] = old
                else:
                    self._storeobj[group] = data
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)

    def _close(self):
        pass

    def get_store(self):
        '''Return store path or object.'''
        return self._storeobj

    def set_store(self, obj):
        '''Set store path and object.'''
        self._storeobj.update(obj)
        obj.update(self._storeobj)
        self._storeobj = obj
        if 'pathstr' not in obj:
            self._storeobj['pathstr'] = self.path
