# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains core base class.
'''

import os
import re

from ..glogger import getGLogger
from ..loaders import is_rawloader, is_pckloader

__all__ = ['BaseCore']
log = getGLogger('C')


class BaseCore(object):
    '''
    Base core class.

    Instructions
    ------------
    1. dig: convert raw data to pickled data for saver
    2. cook: calculate pickled data, save them to figinfo for plotter

    Attributes
    ----------
    rawloader: rawloader object to get raw data
    file: str or list
        file name(s) of raw data
    nfiles: '?' or '+', default '?'
        '?', take only one file; '+', more than one
    group: str
        group of raw data, pickled data and figures
    pckloader: pckloader object to get pickled data
    figurenums: tuple
        figure nums(labels) in the *group*
    '''
    __slots__ = ['rawloader', 'file', 'nfiles', 'group',
                 'pckloader', 'figurenums']
    instructions = ['dig', 'cook']
    filepatterns = ['^(?P<group>file)\.ext$', '.*/(?P<group>file)\.ext$']
    grouppattern = '^group$'

    def __init__(self, nfiles='?'):
        self.rawloader = None
        self.file = None
        if nfiles not in ['?', '+']:
            raise ValueError("'nfiles' should be '?' or '+', not '%s'!"
                             % self.nfiles)
        self.nfiles = nfiles
        self.group = None
        self.pckloader = None
        self.figurenums = None

    @classmethod
    def match_files(cls, rawloader):
        if not is_rawloader(rawloader):
            raise ValueError("Not a rawloader object!")
        files = []
        for pat in cls.filepatterns:
            for key in rawloader.keys():
                if re.match(pat, key):
                    files.append(key)
        return files

    @classmethod
    def match_groups(cls, pckloader):
        if not is_pckloader(pckloader):
            raise ValueError("Not a pckloader object!")
        groups = []
        for group in pckloader.datagroups:
            if re.match(cls.grouppattern, group):
                groups.append(group)
        return groups

    @classmethod
    def _check_groupstr(cls, group):
        if not isinstance(group, str):
            raise ValueError("'group' should be str!")
        if not re.match(cls.grouppattern, group):
            raise ValueError("Invalid 'group' str, its pattern: '%s'."
                             % cls.grouppattern)
        return True

    def set_dig_args(self, rawloader, file, group=None):
        '''Set :meth:`dig` arguments.'''
        if not is_rawloader(rawloader):
            raise ValueError("Not a rawloader object!")
        self.rawloader = rawloader
        if self.nfiles == '?':
            if not isinstance(file, str):
                raise ValueError("'file' should be str, not '%s'!"
                                 % type(file))
            self.file = file
        elif self.nfiles == '+':
            if not isinstance(file, list):
                raise ValueError("'file' should be list, not '%s'!"
                                 % type(file))
            self.file = file
        else:
            pass
        if group:
            if self._check_groupstr(group):
                if self.group:
                    log.debug("'group': replace '%s' with '%s'!"
                              % (self.group, group))
                self.group = group
        else:
            if self.nfiles == '?':
                fs = [file]
            else:
                fs = file
            for pat in self.filepatterns:
                for f in fs:
                    m = re.match(pat, f)
                    if m and 'group' in m.groupdict():
                        group = m.groupdict()['group']
                        if re.match(self.grouppattern, group):
                            break
                if group:
                    break
            if self.group:
                log.debug("'group': replace '%s' with '%s'!"
                          % (self.group, group or ''))
            self.group = group or ''
        log.debug("Dig file: %s; group: %s." % (self.file, self.group))

    def dig(self):
        '''
        Read raw data, convert them. Return a dict.
        '''
        if not self.rawloader or not self.file or not self.group:
            log.error(
                "Please set 'rawloader', 'file', 'group' before dig data!")
            return
        log.debug('Dig raw data in %s ...' % self.file)
        return self._dig()
