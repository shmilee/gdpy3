# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains processor base class.
'''

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
                '%s/%s' % (core.scope, fnum): (core, fnum, 0)
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

    def convert(self, rawfilter=[]):
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

    def plot(self, figlabel, show=True, figkwargs={}):
        '''
        Calculate pickled data, and plot the results.
        Use :meth:`see_figkwargs` to get *figkwargs* for *figlabel*.
        '''
        if not self.pckloader:
            log.error("%s: Need a pckloader object!" % self.name)
            return
        if not self.plotter:
            log.error("%s: Need a plotter object!" % self.name)
            return
        core, fignum, n = self._figurelabelslib.get(figlabel, (None, '', 0))
        if not core:
            log.error("%s: Figure %s not found!" % (self.name, figlabel))
            return
        figinfo = core.cook(fignum, figkwargs=figkwargs)
        if not figinfo:
            log.error("%s: Figure %s not cooked!" % (self.name, figlabel))
            return
        try:
            axstrus, sty = figinfo.serve(self.plotter)
            self.plotter.create_figure(figlabel, *axstrus, add_style=sty)
        except Exception:
            log.error("%s: Figure %s not plotted!"
                      % (self.name, figlabel),  exc_info=1)
        else:
            if show:
                self.plotter.show_figure(figlabel)

    def see_figkwargs(self, figlabel, see='help'):
        '''
        Get *figkwargs* for *figlabel*.
        *see*: str, 'help', 'print' or 'return'
        '''
        core, fignum, n = self._figurelabelslib.get(figlabel, (None, '', 0))
        if not core:
            log.error("%s: Figure %s not found!" % (self.name, figlabel))
            return
        return core.see_figkwargs(fignum, see)
