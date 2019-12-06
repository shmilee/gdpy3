# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Contains Converter core class.
'''

import re

from .base import BaseCore, AppendDocstringMeta
from ..glogger import getGLogger

__all__ = ['Converter']
clog = getGLogger('C')


class Converter(BaseCore, metaclass=AppendDocstringMeta):
    '''
    Convert raw data in files to pickled data.
    Return results in a dict.

    Attributes
    ----------
    rawloader: rawloader object to get raw data
    files: str or list
        matched file name(s) of raw data
    group: str
        group name of pickled data
    short_files: str
        short files if list is too long
    '''
    __slots__ = ['_files', '_group', '_short_files']

    @property
    def rawloader(self):
        return self.loader

    @property
    def files(self):
        return self._files

    @property
    def group(self):
        return self._group

    @property
    def short_files(self):
        return self._short_files

    @classmethod
    def generate_cores(cls, rawloader):
        '''Return generated Core instances for *rawloader*.'''
        ccs = super(Converter, cls).generate_cores(
            rawloader, rawloader.filenames)
        if ccs:
            group_files = []
            for cc in ccs:
                group_files.append((cc.group, cc.short_files))
            clog.debug("%s: loader, %s; %d group and files, %s."
                       % (ccs[0].coreid, rawloader.path,
                          len(group_files), group_files))
        return ccs

    def __init__(self, rawloader, section, items, common):
        super(Converter, self).__init__(rawloader, section, items, common)
        if self.nitems == '?':
            self._files = self.items[0]
            self._short_files = self.items[0]
        else:
            self._files = self.items
            self._short_files = self._get_short_files()
        self._group = '/'.join(self.section)

    def _get_short_files(self):
        '''
        When :attr:`files` is list, replace any decimal digit in it with '*'.
        Return a short string of unique items.
        '''
        # preserve section
        items = self.items
        for idx, sect in enumerate(self.section, 65):
            items = [re.sub(sect, '#SECT#%s#' % chr(idx), it) for it in items]
        items = list({re.sub('\d', '*', it) for it in items})
        res = items
        for idx, sect in enumerate(self.section, 65):
            res = [re.sub('#SECT#%s#' % chr(idx), sect, it) for it in res]
        if len(res) == 1:
            return res[0]
        else:
            return str(res)

    def _convert(self):
        '''Convert raw data.'''
        raise NotImplementedError()

    def convert(self):
        '''Read raw data, convert them. Return a dict.'''
        path = self.rawloader.key_location(self.short_files)
        try:
            clog.info('Converting raw data in %s ...' % path)
            return self._convert()
        except Exception:
            clog.error('Failed to convert raw data in %s.' % path,
                       exc_info=1)
