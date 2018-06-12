# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains processor base class.
'''

import os
import re
import time
import hashlib

from .. import __version__ as gdpy3_version
from ..glogger import getGLogger
from ..loaders import is_rawloader, get_rawloader, is_pckloader, get_pckloader
from ..savers import is_pcksaver, get_pcksaver
from ..plotters import is_plotter, get_plotter

__all__ = ['Processor']
log = getGLogger('C')


class Processor(object):
    '''
    Serial Processor class.

    Attributes
    ----------
    name: class name of this processor
    rawloader: rawloader object to get raw data
    pcksaver: pcksaver object to save pickled data
    pckloader: pckloader object to get pickled data
    plotter: plotter object to plot figures
    digcores: digcore objects to convert raw data to pickled data
    laycores: laycore objects to cook pickled data to figinfo
    layout: layout of all figure labels
    figurelabels: figure labels in this processor
    figurelabels_cooked: figure labels cooked in this processor

    Notes
    -----
    1. `pckversion` means version of pck data.
    2. `pcksaltname` means base name of salt file for `pcksaver.path`.
       The `rawloader` must have and have only one salt file.
    '''
    __slots__ = ['_rawloader', '_pcksaver', '_pckloader', '_plotter',
                 '_digcores', '_laycores', '_layout', '_figurelabelslib']
    DigCores = []
    LayCores = []
    pckversion = 'P0'
    pcksaltname = ''

    def __init__(self, rawloader=None, pcksaver=None,
                 pckloader=None, plotter=None):
        self.rawloader = rawloader
        self.pcksaver = pcksaver
        self.pckloader = pckloader
        self.plotter = plotter

    def __repr__(self):
        i = ('rawloader: %r, pcksaver: %r, pckloader: %r, plotter: %r'
             % (self.rawloader, self.pcksaver, self.pckloader, self.plotter))
        return '<{0}.{1} object at {2}, {3}>'.format(
            self.__module__, type(self).__name__, hex(id(self)), i)

    @property
    def name(self):
        return type(self).__name__

    def _get_rawloader(self):
        return self._rawloader

    def _check_rawloader(self, rawloader):
        saltfiles = rawloader.refind('^(?:|.*/)%s$' % self.pcksaltname)
        if len(saltfiles) == 0:
            log.error("%s: Can't find '%s' in '%s'!"
                      % (self.name, self.pcksaltname, rawloader.path))
            return False
        elif len(saltfiles) > 1:
            log.error("%s: More than one '%s' found in '%s'!"
                      % (self.name, self.pcksaltname, rawloader.path))
            return False
        else:
            return saltfiles[0]

    def _set_rawloader(self, rawloader):
        self._digcores = []
        if is_rawloader(rawloader) and self._check_rawloader(rawloader):
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

    def _check_pckloader(self, pckloader):
        if 'version' not in pckloader:
            log.error("%s: Can't find 'version' in '%s'!"
                      % (self.name, pckloader.path))
            return False
        version = pckloader.get('version')
        if version != self.pckversion:
            log.error("%s: Invalid 'version' '%s'! Did you mean '%s'?"
                      % (self.name, version, self.pckversion))
            return False
        return True

    def _set_pckloader(self, pckloader):
        self._laycores = []
        if is_pckloader(pckloader) and self._check_pckloader(pckloader):
            self._pckloader = pckloader
            for lc in self.LayCores:
                self._laycores.extend(lc.generate_cores(pckloader))
        else:
            self._pckloader = None
        self._figurelabelslib = {}
        self._layout = {}
        for core in self._laycores:
            self._figurelabelslib.update({
                '%s/%s' % (core.scope, fnum): (core, fnum, 0, '-', None)
                for fnum in core.fignums})
            if core.scope in self._layout:
                self._layout[core.scope].extend(core.fignums)
            else:
                self._layout[core.scope] = core.fignums

    pckloader = property(_get_pckloader, _set_pckloader)

    @property
    def laycores(self):
        return self._laycores

    @property
    def layout(self):
        return self._layout

    @property
    def figurelabels(self):
        return sorted(self._figurelabelslib.keys())

    @property
    def figurelabels_cooked(self):
        flp = []
        for k, v in self._figurelabelslib.items():
            if v[2] > 0:
                flp.append((k, v[2]))
        return sorted(flp)

    def _get_plotter(self):
        return self._plotter

    def _set_plotter(self, plotter):
        if is_plotter(plotter):
            self._plotter = plotter
        else:
            self._plotter = None

    plotter = property(_get_plotter, _set_plotter)

    def set_prefer_pcksaver(self, savetype):
        '''
        Set preferable pcksaver beside raw data.

        Parameters
        ----------
        savetype: str
            extension of pcksaver.path
        '''
        if not self.rawloader:
            log.error("%s: Need a rawloader object!" % self.name)
            return
        if self.rawloader.loader_type in ['directory', 'sftp.directory']:
            prefix = os.path.join(self.rawloader.path, 'gdpy3-pickled-data')
        elif self.rawloader.loader_type == 'tarfile':
            prefix = self.rawloader.path[:self.rawloader.path.rfind('.tar')]
        elif self.rawloader.loader_type == 'zipfile':
            prefix = self.rawloader.path[:self.rawloader.path.rfind('.zip')]
        else:
            prefix = os.path.splitext(self.rawloader.path)[0]
        saltfile = self.rawloader.refind('^(?:|.*/)%s$' % self.pcksaltname)[0]
        if self.rawloader.loader_type in ['sftp.directory']:
            salt = hashlib.sha1(saltfile.encode('utf-8')).hexdigest()
        else:
            try:
                with self.rawloader.get(saltfile) as f:
                    salt = hashlib.sha1(f.read().encode('utf-8')).hexdigest()
            except Exception:
                log.error("Failed to read salt file '%s'!" % saltfile)
                salt = hashlib.sha1(saltfile.encode('utf-8')).hexdigest()
        log.debug("Get salt string: '%s'." % salt)
        psalt = hashlib.sha1(type(self).__name__.encode('utf-8')).hexdigest()
        if self.rawloader.loader_type in ['tarfile', 'zipfile']:
            _check_w_path = os.path.dirname(self.rawloader.path)
        else:
            _check_w_path = self.rawloader.path
        if os.access(_check_w_path, os.W_OK):
            if savetype == '.cache':
                log.debug("Use savetype '.cache' while %s is writable!"
                          % _check_w_path)
            if savetype not in ['.cache', '.npz', '.hdf5']:
                log.warning("Use default savetype '.npz'.")
                savetype = '.npz'
        else:
            log.debug("Use savetype '.cache' because %s isn't writable!"
                      % _check_w_path)
            savetype = '.cache'
        savepath = '%s-%s%s' % (prefix, salt[:10] + psalt[:2], savetype)
        log.info("Default pickled data path is '%s'." % savepath)
        self.pcksaver = get_pcksaver(savepath)

    @property
    def _rawdata_summary(self):
        return "Raw data files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)

    def convert(self, add_desc=None):
        '''
        Convert raw data in rawloader, and save them in pcksaver.
        '''
        if not self.rawloader:
            log.error("%s: Need a rawloader object!" % self.name)
            return
        if not self.pcksaver:
            log.error("%s: Need a pcksaver object!" % self.name)
            return
        summary = "Pck data converted from %s." % self._rawdata_summary
        description = ("%s\nCreated by gdpy3 v%s.\nCreated on %s."
                       % (summary, gdpy3_version, time.asctime()))
        if add_desc:
            description += '\n' + str(add_desc)
        with self.pcksaver:
            self.pcksaver.write('/', {'description': description,
                                      'version': self.pckversion})
            for core in self.digcores:
                self.pcksaver.write(core.group, core.convert())
        log.info("%s are converted to %s!"
                 % (self._rawdata_summary, self.pcksaver.path))

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
        okstr = ','.join(sorted([
            '%s=%r' % (k, list(v) if isinstance(v, tuple) else v)
            for k, v in kwargs.items() if _docstr_.find('*%s*' % k) > 0]))
        log.debug("%s: Some kwargs accepted for %s: %s"
                  % (self.name, figlabel, okstr))
        if okstr == '' and kstr.startswith('DEFAULT'):
            # already cooked with default kwargs
            return fobj
        kstr = re.sub('^DEFAULT(?:,|)', '', kstr, 1)
        if okstr == kstr:
            # already cooked with kwargs
            return fobj
        fobj = core.cook(fignum, figkwargs=kwargs)
        if fobj:
            n += 1
            if not kwargs or okstr == '':
                # empty kwargs -> default kwargs(layout)
                oklist = ['%s=%r' % (
                    k, list(v['value'])
                    if isinstance(v['value'], tuple) else v['value'])
                    for k, v in fobj.layout.items()]
                okstr = ','.join(['DEFAULT'] + sorted(oklist))
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
                return self.plotter.show_figure(figlabel)

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

    def pick(self, path, add_desc=None, filenames_filter=None,
             savetype='.npz', overwrite=False, Sid=False,
             datagroups_filter=None, add_plotter=True):
        '''
        Pick up raw data or pickled data in *path*,
        set processor's rawloader, pcksaver and pckloader, plotter.

        Parameters
        ----------
        path: str
            path of raw data or pickled data to open
        add_desc: str
            additional description of raw data
        filenames_filter: function
            function to filter filenames in rawloader
        savetype: '.cache', '.npz' or '.hdf5'
            extension of pcksaver.path, default '.npz'
            when pcksaver.path isn't writable, default '.cache'
        overwrite: bool
            overwrite existing pcksaver.path file or not, default False
        Sid: bool
            If Sid is True(here), only rawloader and pcksaver will be set
            and converted to a .npz or .hdf5 file if needed. And any other
            codes(like Buzz Lightyear) will be omitted(destroyed).
            Default False.
        datagroups_filter: function
            function to filter datagroups in pckloader
        add_plotter: bool
            set default plotter ('mpl::*path*') or not, default True
        '''

        self.__init__(rawloader=None, pcksaver=None,
                      pckloader=None, plotter=None)
        root, ext = os.path.splitext(path)
        if ext in ['.npz', '.hdf5']:
            # pckloader.path?
            if Sid:
                return
            try:
                self.pckloader = get_pckloader(
                    path, datagroups_filter=datagroups_filter)
            except Exception:
                log.error("%s: Invalid pckloader path '%s'!"
                          % (self.name, path), exc_info=1)
                return
            if self.pckloader:
                if add_plotter:
                    self.plotter = get_plotter('mpl::%s' % path)
            else:
                log.error("%s: Failed to set pckloader object!" % self.name)
        else:
            # rawloader.path?
            try:
                self.rawloader = get_rawloader(
                    path, filenames_filter=filenames_filter)
            except Exception:
                log.error("%s: Invalid rawloader path '%s'!"
                          % (self.name, path), exc_info=1)
                return
            if not self.rawloader:
                log.error("%s: Failed to set rawloader object!" % self.name)
                return
            self.set_prefer_pcksaver(savetype)
            if not self.pcksaver:
                log.error("%s: Failed to set pcksaver object!" % self.name)
                return
            if Sid and self.pcksaver._extension not in ['.npz', '.hdf5']:
                return
            if os.path.isfile(self.pcksaver.path):
                if overwrite:
                    log.warning("Remove old pickled data file: %s!"
                                % self.pcksaver.path)
                    os.remove(self.pcksaver.path)
                    self.convert(add_desc=add_desc)
            else:
                self.convert(add_desc=add_desc)
            if Sid and self.pcksaver._extension in ['.npz', '.hdf5']:
                return
            self.pckloader = get_pckloader(
                self.pcksaver.get_store(),
                datagroups_filter=datagroups_filter)
            if self.pckloader:
                if add_plotter:
                    self.plotter = get_plotter('mpl::%s' % path)
            else:
                log.error("%s: Failed to set pckloader object!" % self.name)
