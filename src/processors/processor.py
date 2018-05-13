# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains processor base class.
'''

import re

from ..glogger import getGLogger
from ..loaders import is_rawloader, is_pckloader
from ..savers import is_pcksaver
from ..plotters import is_plotter

__all__ = ['Processor']
log = getGLogger('C')


class Processor(object):
    '''
    Serial Processor class.

    Attributes
    ----------
    name: name of this processor
    rawloader: rawloader object to get raw data
    pcksaver: pcksaver object to save pickled data
    pckloader: pckloader object to get pickled data
    plotter: plotter object to plot figures
    digcores: digcore objects to convert raw data to pickled data
    laycores: laycore objects to cook pickled data to figinfo
    figurelabels: figure labels in this processor
    '''
    __slots__ = ['_rawloader', '_pcksaver', '_pckloader', '_plotter',
                 '_digcores', '_laycores', '_figurelabelslib']
    DigCores = []
    LayCores = []

    def __init__(self, rawloader=None, pcksaver=None,
                 pckloader=None, plotter=None):
        self.rawloader = rawloader
        self.pcksaver = pcksaver
        self.pckloader = pckloader
        self.plotter = plotter

    @property
    def name(self):
        return "Processor %s" % type(self).__name__

    def _get_rawloader(self):
        return self._rawloader

    def _set_rawloader(self, rawloader):
        self._digcores = []
        if is_rawloader(rawloader):
            self._rawloader = rawloader
            for dc in self.DigCores:
                self._digcores.extend(dc.generate_cores(rawloader))
        else:
            self._rawloader = None

    rawloader = property(_get_rawloader, _set_rawloader)

    @property
    def digcores(self):
        return self._digcores

    def _get_pcksaver(self):
        return self._pcksaver

    def _set_pcksaver(self, pcksaver):
        if is_pcksaver(pcksaver):
            self._pcksaver = pcksaver
        else:
            self._pcksaver = None

    pcksaver = property(_get_pcksaver, _set_pcksaver)

    def _get_pckloader(self):
        return self._pckloader

    def _set_pckloader(self, pckloader):
        self._laycores = []
        if is_pckloader(pckloader):
            self._pckloader = pckloader
            for lc in self.LayCores:
                self._laycores.extend(lc.generate_cores(pckloader))
        else:
            self._pckloader = None
        self._figurelabelslib = {}
        for core in self._laycores:
            self._figurelabelslib.update({
                '%s/%s' % (core.scope, fnum): (core, fnum, 0, '-', None)
                for fnum in core.fignums})

    pckloader = property(_get_pckloader, _set_pckloader)

    @property
    def laycores(self):
        return self._laycores

    @property
    def figurelabels(self):
        return sorted(self._figurelabelslib.keys())

    def _get_plotter(self):
        return self._plotter

    def _set_plotter(self, plotter):
        if is_plotter(plotter):
            self._plotter = plotter
        else:
            self._plotter = None

    plotter = property(_get_plotter, _set_plotter)

    def convert(self):
        '''
        Convert raw data in rawloader, and save them in pcksaver.
        '''
        if not self.rawloader:
            log.error("%s: Need a rawloader object!" % self.name)
            return
        if not self.pcksaver:
            log.error("%s: Need a pcksaver object!" % self.name)
            return
        with self.pcksaver:
            for core in self.digcores:
                self.pcksaver.write(core.group, core.convert())

    def get(self, figlabel, **kwargs):
        '''
        Get cooked figinfo object of *figlabel*.
        Use :meth:`see_figkwargs` to get *kwargs* for *figlabel*.
        '''
        if not self.pckloader:
            log.error("%s: Need a pckloader object!" % self.name)
            return
        core, fignum, n, kstr, fobj = self._figurelabelslib.get(
            figlabel, (None, '', 0, '-', None))
        if not core:
            log.error("%s: Figure %s not found!" % (self.name, figlabel))
            return
        _docstr_ = self.see_figkwargs(figlabel, see='return')
        okstr = ','.join(['%s=%r' % (k, kwargs[k])
                          for k in sorted(kwargs)
                          if _docstr_.find('*%s*' % k) > 0])
        log.ddebug("%s: Some kwargs accepted for %s: %s"
                   % (self.name, figlabel, okstr))
        if okstr == kstr:
            # already cooked with kwargs
            return fobj
        fobj = core.cook(fignum, figkwargs=kwargs)
        if fobj:
            n += 1
            self._figurelabelslib[figlabel] = (core, fignum, n, okstr, fobj)
            return fobj
        else:
            log.error("%s: Figure %s not cooked!" % (self.name, figlabel))
            return

    def plot(self, figlabel, replot=False, show=True, **kwargs):
        '''
        Calculate pickled data, and plot the results.
        Use :meth:`see_figkwargs` to get *kwargs* for *figlabel*.

        Parameters
        ----------
        replot: bool
            replot *figlabel* if it was already ploted
        show: bool
            display *figlabel* after it ploted
        '''
        if not self.plotter:
            log.error("%s: Need a plotter object!" % self.name)
            return
        _, _, n0, _, _ = self._figurelabelslib.get(figlabel, (0, 0, 0, 0, 0))
        fobj = self.get(figlabel, **kwargs)
        if not fobj:
            return
        _, _, n1, _, _ = self._figurelabelslib.get(figlabel, (0, 0, 0, 0, 0))
        if n0 < n1:
            replot = True
        try:
            if replot or figlabel not in self.plotter.figures:
                axstrus, sty = fobj.serve(self.plotter)
                self.plotter.create_figure(
                    figlabel, *axstrus, add_style=sty, replace=replot)
        except Exception:
            log.error("%s: Figure %s not plotted!"
                      % (self.name, figlabel),  exc_info=1)
        else:
            if show:
                self.plotter.show_figure(figlabel)

    def see_figkwargs(self, figlabel, see='help'):
        '''
        Get :meth:`get`, :meth:`plot` *kwargs* for *figlabel*.
        *see*: str, 'help', 'print' or 'return'
        '''
        core, fignum, n, kstr, fobj = self._figurelabelslib.get(
            figlabel, (None, '', 0, '-', None))
        if not core:
            log.error("%s: Figure %s not found!" % (self.name, figlabel))
            return
        return core.see_figkwargs(fignum, see)

    def refind(self, pattern):
        '''
        Find the figlabels which match the regular expression *pattern*.
        '''
        pat = re.compile(pattern)
        return tuple(filter(
            lambda k: True if re.match(pat, k) else False, self.figurelabels))
