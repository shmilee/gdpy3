#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Contains Digger core class.
'''

import re

from .base import BaseCore
from ..glogger import getGLogger

__all__ = ['Digger']
dlog = getGLogger('D')


class Digger(BaseCore):
    '''
    Calculate pickled data in pckloader needed by figure.
    Return results in a dict.

    Attributes
    ----------
    pckloader: pckloader object to get pickled data
    neededpattern: list or 'ALL'
        regular expressions for all needed data keys
        'ALL' means itemspattern + commonpattern
    numpattern: str or list
        regular expressions to get info for fignum
    srckeys: list
        matched datakeys of pickled data
    extrakeys: list
        common datakeys
    group: str
        group of results, default :attr:`section`[0]
    fignum: str
        figure num(label) of results
    fullnum: str
        full figure num(label)
    '''
    __slots__ = ['_group', '_fignum']
    neededpattern = ['datakey']
    numpattern = None

    @property
    def pckloader(self):
        return self.loader

    @property
    def srckeys(self):
        return self.items

    @property
    def extrakeys(self):
        return self.common

    @property
    def group(self):
        return self._group

    @property
    def fignum(self):
        return self._fignum

    @property
    def fullnum(self):
        '''Return full label.'''
        return '%s/%s' % (self._group, self._fignum)

    @classmethod
    def generate_cores(cls, pckloader):
        '''Return generated Core instances for *pckloader*.'''
        dcs = super(Digger, cls).generate_cores(pckloader, pckloader.datakeys)
        res = []
        for dc in dcs:
            if dc.check_needed_datakeys():
                dc._set_group()
                dc._set_fignum()
                res.append(dc)
                dlog.debug("%s: loader, %s; fullnum, %s."
                           % (dc.coreid, pckloader.path, dc.fullnum))
        return res

    def check_needed_datakeys(self):
        '''Return Ture if all :attr:`neededpattern` matched.'''
        if self.neededpattern == 'ALL':
            neededpattern = self.itemspattern + self.commonpattern
        else:
            neededpattern = self.neededpattern
        keys = self.srckeys + self.extrakeys
        for pat in neededpattern:
            match = False
            for it in keys:
                if re.match(pat, it):
                    match = True
                    break
            if not match:
                return False
        return True

    def _set_group(self):
        '''Set :attr:`group`, using :attr:`section`.'''
        self._group = self.section[0]

    def _set_fignum(self):
        '''Set :attr:`fignum`, using info get by :attr:`numpattern`.'''
        raise NotImplementedError()

    def _dig(self, **kwargs):
        '''Calculate pickled data.'''
        raise NotImplementedError()

    def dig(self, **kwargs):
        '''
        Calculate pickled data get from :attr:`pckloader`,
        return results in a dict.
        Use *data* get by keys, return calculation and layout.
        '''
        try:
            dlog.info("Dig pickled data for %s ..." % self.fullnum)
            return self._dig(**kwargs)
        except Exception:
            dlog.error("%s: can't dig data for %s!"
                       % (self.coreid, self.fullnum), exc_info=1)
