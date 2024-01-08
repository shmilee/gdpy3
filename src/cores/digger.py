# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

'''
Contains Digger core class.
'''

import re
import time

from .base import BaseCore, AppendDocstringMeta
from ..glogger import getGLogger

__all__ = ['Digger']
dlog = getGLogger('D')


class Digger(BaseCore, metaclass=AppendDocstringMeta):
    '''
    Calculate pickled data in pckloader needed by figure.
    Return results in a dict.

    Attributes
    ----------
    pckloader: pckloader object to get pickled data
    neededpattern: list or 'ALL'
        regular expressions for all needed data keys
        'ALL' means itemspattern + commonpattern
    srckeys: list
        matched datakeys of pickled data
    extrakeys: list
        common datakeys
    group: str
        group of results, default :attr:`section`[0]
    numseeds: None or list
        seeds info for fignum
        so one match can generate serial cores only differs in num
    fignum: str
        figure num of results
    figlabel: str
        full figure label, :attr:`group`/:attr:`fignum`
    kwoptions: dict or None
        kwargs option info for building widgets
    post_template: str or tuple
        post results template for :meth:`visplter.create_template_figure`
        tuple, should be ('tmpl_z111p', 'other zipped tmpl_...', ...)
    '''
    __slots__ = ['_group', '_fignum', 'kwoptions']
    nitems = '?'
    neededpattern = 'ALL'
    numseeds = None
    post_template = ''

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
    def figlabel(self):
        '''Return full label.'''
        return '%s/%s' % (self._group, self._fignum)

    @classmethod
    def generate_cores(cls, pckloader):
        '''Return generated Core instances for *pckloader*.'''
        start = time.time()
        dcss = super(Digger, cls).generate_cores(
            pckloader, pckloader.datakeys, duplicate=cls.numseeds)
        res = []
        figlabels = []
        if cls.numseeds:
            for dcs in dcss:
                assert len(cls.numseeds) == len(dcs)
                # only check first one
                if dcs[0].check_needed_datakeys():
                    for idx, dc in enumerate(dcs):
                        if dc.__second_init__(numseed=cls.numseeds[idx]):
                            res.append(dc)
                            figlabels.append(dc.figlabel)

        else:
            for dc in dcss:
                if dc.check_needed_datakeys():
                    if dc.__second_init__():
                        res.append(dc)
                        figlabels.append(dc.figlabel)
        end = time.time()
        if res:
            clsname, N = res[0].clsname, len(figlabels)
            dlog.debug("%s: loader, %s; %d figlabels, cost %.1fs."
                       % (clsname, pckloader.path, N, end-start))
            if N > 64:
                figlabels = figlabels[:32] + ['... ...'] + figlabels[-32:]
            dlog.debug("%s: %d figlabels, %s." % (clsname, N, figlabels))
        return res

    def __second_init__(self, numseed=None):
        try:
            self.kwoptions = {}
            self._set_group()
            self._set_fignum(numseed=numseed)
        except Exception:
            dlog.error("%s: Failed to initialize object %s!"
                       % (self.clsname, id(self)), exc_info=1)
            return False
        else:
            return True

    def __repr__(self):
        return '<{0}.{1} object at {2} for {3}>'.format(
            self.__module__, type(self).__name__, hex(id(self)), self.fignum)

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

    def _set_fignum(self, numseed=None):
        '''
        Set :attr:`fignum`
        Using :attr:`section` and info get from :attr:`numseeds`.
        Set :attr:`kwoptions` to None if needed.
        '''
        raise NotImplementedError()

    def _dig(self, kwargs):
        '''
        Calculate pickled data, return results and accepted kwargs.
        Set :attr:`kwoptions` if it is set to None in :meth:`_set_fignum`.
        '''
        raise NotImplementedError()

    def str_dig_kwargs(self, kwargs):
        '''
        Turn :meth:`dig` *kwargs* to str.
        Check if they in :attr:`kwoptions` or not, and sort by key.
        Return string like, "k1=1,k2=[2],k3='abc'".
        '''
        ckkws = ['%s=%r' % (k, list(v) if isinstance(v, tuple) else v)
                 for k, v in kwargs.items() if k in self.kwoptions]
        return ','.join(sorted(ckkws))

    def dig(self, **kwargs):
        '''
        Calculate pickled data get from :attr:`pckloader`.

        Returns
        -------
        results: dict
        kwargstr: accepted kwargs str
        time: :meth:`dig` real execution time in seconds
        '''
        dlog.info("Dig pickled data for %s ..." % self.figlabel)
        # dlog.info('dig in kwstr: %s' % self.str_dig_kwargs(kwargs))
        start = time.time()
        try:
            results, acckwargs = self._dig(kwargs)
        except Exception:
            dlog.error("%s: can't dig data for %s!"
                       % (self.clsname, self.figlabel), exc_info=1)
            results, acckwargs = {}, {}
        end = time.time()
        # dlog.info('dig acckwstr: %s' % self.str_dig_kwargs(acckwargs))
        return results, self.str_dig_kwargs(acckwargs), end-start

    def _post_dig(self, results):
        '''post-dig results'''
        raise NotImplementedError()

    def post_dig(self, results):
        '''
        post-dig results
        Return new results match with template name in exporter
        '''
        try:
            if results:
                new_results = self._post_dig(results)
            else:
                return {}
        except Exception:
            dlog.error("%s: can't post-dig data for %s!"
                       % (self.clsname, self.figlabel), exc_info=1)
            return results
        return new_results
