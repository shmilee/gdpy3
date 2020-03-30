# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

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
        short files if :attr:`files` list is too long
    '''
    __slots__ = ['_files', '_group']

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
    def groupnote(self):
        return self._group

    # None,
    # tuple ('items index 0', 'pat','repl'),
    # etc
    _short_files_subs = None

    @property
    def short_files(self):
        if self.nitems == '?':
            return self.items[0]
        # else nitems == '+'
        if self._short_files_subs is None:
            # default re sub, preserve section, filter all items
            items = self.items
            for idx, sect in enumerate(self.section, 65):
                items = [re.sub(sect, '#ST%s#' % chr(idx), i) for i in items]
            items = list({re.sub('\d', '*', i) for i in items})
            res = items
            for idx, sect in enumerate(self.section, 65):
                res = [re.sub('#ST%s#' % chr(idx), sect, i) for i in res]
            if len(res) == 1:
                return res[0]
            else:
                return str(res)
        else:
            # use specified _short_files_subs
            if self._short_files_subs[0] == 0:
                pat, repl = self._short_files_subs[1:]
                return re.sub(pat, repl, self.items[0])
            # etc

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
                       % (ccs[0].clsname, rawloader.path,
                          len(group_files), group_files))
        return ccs

    def __init__(self, rawloader, section, items, common):
        super(Converter, self).__init__(rawloader, section, items, common)
        if self.nitems == '?':
            self._files = self.items[0]
        else:
            self._files = self.items
        self._group = '/'.join(self.section)

    def _convert(self):
        '''Convert raw data.'''
        raise NotImplementedError()

    def convert(self):
        '''Read raw data, convert them. Return a dict.'''
        try:
            clog.info('Converting raw data in %s ...' % self.short_files)
            return self._convert()
        except Exception:
            clog.error('Failed to convert raw data in %s.' % self.short_files,
                       exc_info=1)
