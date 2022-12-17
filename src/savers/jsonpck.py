#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 shmilee

'''
Contains jsonlines & jsonzip saver class.
'''

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckSaver, _copydoc_func
from .._json import JsonLines, JsonZip

__all__ = ['JsonlPckSaver', 'JsonzPckSaver']
log = getGLogger('S')


@inherit_docstring((BasePckSaver,), _copydoc_func, template=None)
class JsonlPckSaver(BasePckSaver):
    '''
    Save dict data with a group name to a jsonlines file.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    {Notes}
    '''
    __slots__ = []
    _extension = '.jsonl'

    def _open_append(self):
        return JsonLines(self.path)

    def _open_new(self):
        return JsonLines(self.path)

    def _write(self, group, data):
        try:
            if group in ('/', ''):
                records = data
            else:
                records = {'%s/%s' % (group, k): v for k, v in data.items()}
            self._storeobj.update(records)
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)

    def _close(self):
        self._storeobj = None


@inherit_docstring((BasePckSaver,), _copydoc_func, template=None)
class JsonzPckSaver(JsonlPckSaver):
    '''
    Save dict data with a group name to a json zip file.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    {Notes}
    '''
    __slots__ = []
    _extension = '.jsonz'

    def _open_append(self):
        return JsonZip(self.path)

    def _open_new(self):
        return JsonZip(self.path)
