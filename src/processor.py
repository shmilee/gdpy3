#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import os
import re
import time
import hashlib

from . import __version__ as gdpy3_version
from .glogger import getGLogger
from .loaders import is_rawloader, get_rawloader, is_pckloader, get_pckloader
from .savers import is_pcksaver, get_pcksaver

__all__ = ['Processor']
plog = getGLogger('P')


class Processor(object):
    '''
    Serial Processor class.

    Attributes
    ----------

    name: class name of this processor
    rawloader: rawloader object to get raw data
    converters: converter cores to convert raw data to pickled data
    pcksaver: pcksaver object to save pickled data

    pckloader: pckloader object to get pickled data
    ressaver: cachepcksaver object to save dig results
    resfilesaver: pcksaver object to save long time dig results
    diggers: digger cores to calculate pickled data to results
    availablelabels: list
        figure labels in this processor, like 'group/fignum'
    resloader: cachepckloader object to get dig results
    resfileloader: pckloader object to get long time dig results
    diggedlabels: set
        figlabels/kwargstr digged in ressaver or resfilesaver
        like 'group/fignum/a=1,b=2'

    Notes
    -----
    1. :attr:`saltname` means base name of salt file for `saver.path`.
       The :attr:`rawloader` must have exactly one salt file.
    2. :attr:`execution_time_limit` means if :meth:`dig` spends more
       time than this, the results will be saved in :attr:`resfilesaver`.
    '''

    @property
    def name(self):
        return type(self).__name__

    # # Start Convert Part

    __slots__ = ['_rawloader', '_pcksaver', '_converters']
    ConverterCores = []
    saltname = ''

    def __check_rawloader(self, rawloader):
        if not is_rawloader(rawloader):
            plog.error("%s: Not a rawloader object!" % self.name)
            return False
        saltfiles = rawloader.refind('^(?:|.*/)%s$' % self.saltname)
        if len(saltfiles) == 0:
            plog.error("%s: Can't find '%s' in '%s'!"
                       % (self.name, self.saltname, rawloader.path))
            return False
        elif len(saltfiles) > 1:
            plog.error("%s: More than one '%s' found in '%s'!"
                       % (self.name, self.saltname, rawloader.path))
            return False
        else:
            return saltfiles[0]

    def _get_rawloader(self):
        return self._rawloader

    def _set_rawloader(self, rawloader):
        self._converters = []
        if rawloader and self.__check_rawloader(rawloader):
            self._rawloader = rawloader
            for Cc in self.ConverterCores:
                self._converters.extend(Cc.generate_cores(rawloader))
        else:
            self._rawloader = None
    rawloader = property(_get_rawloader, _set_rawloader)

    @property
    def converters(self):
        return self._converters

    def _get_pcksaver(self):
        return self._pcksaver

    def _set_pcksaver(self, pcksaver):
        if is_pcksaver(pcksaver):
            self._pcksaver = pcksaver
        else:
            self._pcksaver = None

    pcksaver = property(_get_pcksaver, _set_pcksaver)

    def set_prefer_pcksaver(self, savetype, ext2='converted'):
        '''
        Set preferable pcksaver path beside raw data.

        Parameters
        ----------
        savetype: str
            extension of pcksaver.path, like (.npz)
        ext2: str
            second extension, like name.(converted).npz
        '''
        if not self.rawloader:
            raise IOError("%s: Need a rawloader object!" % self.name)
        # salt
        saltfile = self.rawloader.refind('^(?:|.*/)%s$' % self.saltname)[0]
        if self.rawloader.loader_type in ['sftp.directory']:
            salt = hashlib.sha1(saltfile.encode('utf-8')).hexdigest()
        else:
            try:
                with self.rawloader.get(saltfile) as f:
                    salt = hashlib.sha1(f.read().encode('utf-8')).hexdigest()
            except Exception:
                plog.error("Failed to read salt file '%s'!" % saltfile)
                salt = hashlib.sha1(saltfile.encode('utf-8')).hexdigest()
        plog.debug("Get salt string: '%s'." % salt)
        # prefix
        prefix = self.rawloader.beside_path(self.name.lower())
        # savetype
        if os.access(os.path.dirname(prefix), os.W_OK):
            if savetype not in ['.npz', '.hdf5']:
                plog.warning("Use default savetype '.npz'.")
                savetype = '.npz'
        else:
            plog.debug("Use savetype '.cache' because %s isn't writable!"
                       % os.path.dirname(prefix))
            savetype = '.cache'
        # assemble
        savepath = '%s-%s.%s%s' % (prefix, salt[:6], ext2, savetype)
        self.pcksaver = get_pcksaver(savepath)

    @property
    def _rawsummary(self):
        return "Raw data files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)

    def convert(self, add_desc=None):
        '''
        Convert raw data in rawloader.path, and save them in pcksaver.
        '''
        if not self.rawloader:
            log.error("%s: Need a rawloader object!" % self.name)
            return
        if not self.pcksaver:
            log.error("%s: Need a pcksaver object!" % self.name)
            return
        summary = "Pck data converted from %s." % self._rawsummary
        description = ("%s\nCreated by gdpy3 v%s.\nCreated on %s."
                       % (summary, gdpy3_version, time.asctime()))
        if add_desc:
            description += '\n' + str(add_desc)
        with self.pcksaver:
            self.pcksaver.write('/', {'description': description,
                                      'processor': self.name})
            for core in self.converters:
                self.pcksaver.write(core.group, core.convert())
        plog.info("%s are converted to %s!"
                  % (self._rawsummary,  self.pcksaver.path))

    # # End Convert Part

    # # Start Dig Part

    __slots__.extend(['_pckloader', '_ressaver', '_resfilesaver',
                      '_diggers', '_availablelabels_lib', '_availablelabels',
                      '_resloader', '_resfileloader', '_diggedlabels'])
    DiggerCores = []
    execution_time_limit = 30

    def __check_pckloader(self, pckloader):
        if not is_pckloader(pckloader):
            plog.error("%s: Not a pckloader object!" % self.name)
            return
        if 'processor' not in pckloader:
            plog.error("%s: Can't find 'processor' in '%s'!"
                       % (self.name, pckloader.path))
            return False
        pname = pckloader.get('processor')
        if pname != self.name:
            plog.error("%s: Invalid 'processor' '%s'! Did you mean '%s'?"
                       % (self.name, pname, self.name))
            return False
        return True

    def _get_pckloader(self):
        return self._pckloader

    def _set_pckloader(self, pckloader):
        self._diggers = []
        if pckloader and self.__check_pckloader(pckloader):
            self._pckloader = pckloader
            for Dc in self.DiggerCores:
                self._diggers.extend(Dc.generate_cores(pckloader))
        else:
            self._pckloader = None
        self._availablelabels_lib = {dc.figlabel: dc for dc in self._diggers}
        self._availablelabels = sorted(self._availablelabels_lib.keys())

    pckloader = property(_get_pckloader, _set_pckloader)

    @property
    def diggers(self):
        return self._diggers

    @property
    def availablelabels(self):
        return self._availablelabels

    # save results
    def _get_ressaver(self):
        return self._ressaver

    def _set_ressaver(self, ressaver):
        if is_pcksaver(ressaver):
            self._ressaver = ressaver
        else:
            self._ressaver = None

    ressaver = property(_get_ressaver, _set_ressaver)

    def _get_resfilesaver(self):
        return self._resfilesaver

    def _set_resfilesaver(self, resfilesaver):
        if is_pcksaver(resfilesaver):
            self._resfilesaver = resfilesaver
        else:
            self._resfilesaver = None

    resfilesaver = property(_get_resfilesaver, _set_resfilesaver)

    # reload results
    def _get_resloader(self):
        return self._resloader

    def _set_resloader(self, resloader):
        if not getattr(self, '_diggedlabels', None):
            self._diggedlabels = set()
        if resloader and self.__check_pckloader(resloader):
            self._resloader = resloader
            self._diggedlabels.update(resloader.datagroups)
        else:
            self._resloader = None

    resloader = property(_get_resloader, _set_resloader)

    def _get_resfileloader(self):
        return self._resfileloader

    def _set_resfileloader(self, resfileloader):
        if not getattr(self, '_diggedlabels', None):
            self._diggedlabels = set()
        if resfileloader and self.__check_pckloader(resfileloader):
            self._resfileloader = resfileloader
            self._diggedlabels.update(resfileloader.datagroups)
        else:
            self._resfileloader = None

    resfileloader = property(_get_resfileloader, _set_resfileloader)

    @property
    def diggedlabels(self):
        return self._diggedlabels

    def set_prefer_ressaver(self, ext2='digged', overwrite=False):
        '''
        Set preferable ressaver resfilesaver beside converted data.

        Parameters
        ----------
        ext2: str
            second extension, like name.(digged).npz
        overwrite: bool
            overwrite existing resfilesaver.path file or not, default False
        '''
        if not self.pckloader:
            raise IOError("%s: Need a pckloader object!" % self.name)
        saverstr, ext = os.path.splitext(self.pckloader.path)
        saverstr = saverstr.replace('converted', ext2)
        respath = '%s.cache' % saverstr
        ressaver = get_pcksaver(respath)
        with ressaver:
            ressaver.write('/', {'processor': self.name})
        self.ressaver = ressaver
        self.resloader = get_pckloader(ressaver.get_store())
        plog.info("Default %s data cache is %s." % (ext2, respath))
        if ext != '.cache':
            try:
                respath = '%s%s' % (saverstr, ext)
                resfilesaver = get_pcksaver(respath)
                if overwrite and os.path.isfile(respath):
                    plog.warning("Remove old %s data file: %s!"
                                 % (ext2, respath))
                    os.remove(respath)
                if not os.path.isfile(respath):
                    # new file
                    with resfilesaver:
                        resfilesaver.write('/', {'processor': self.name})
                self.resfilesaver = resfilesaver
                self.resfileloader = get_pckloader(resfilesaver.get_store())
                plog.info("Default %s data file is %s." % (ext2, respath))
            except Exception:
                plog.error("%s: Failed to set results file pcksaver, '%s'!"
                           % (self.name, respath), exc_info=1)
                self.resfilesaver = None

    def dig(self, figlabel, post=True, **kwargs):
        '''
        Get digged results of *figlabel*.
        Return figlabel/kwargstr, results and template name if *post* True.
        Use :meth:`dig_doc` to see *kwargs* for *figlabel*.
        '''
        if not self.pckloader:
            plog.error("%s: Need a pckloader object!" % self.name)
            return
        if not self.ressaver:
            plog.error("%s: Need a results pcksaver object!" % self.name)
            return
        if figlabel not in self.availablelabels:
            plog.error("%s: Figure %s not found!" % (self.name, figlabel))
            return
        digcore = self._availablelabels_lib[figlabel]
        gotkwargstr = digcore.str_dig_kwargs(kwargs) or 'DEFAULT'
        gotfiglabel = '%s/%s' % (figlabel, gotkwargstr)
        # find old
        if gotfiglabel in self.diggedlabels:
            if gotfiglabel in self.resloader.datagroups:
                # use resloader first
                gotresloader = self.resloader
            elif (self.resfilesaver
                    and gotfiglabel in self.resfileloader.datagroups):
                gotresloader = self.resfileloader
            else:
                gotresloader = None
                plog.error('%s: Not found %s in diggedlabels!'
                           % (self.name, gotfiglabel))
            if gotresloader:
                plog.info('%s, find %s digged results in %s.'
                          % (self.name, gotfiglabel, gotresloader.path))
                allkeys = gotresloader.refind(
                    '^%s/' % re.escape(gotfiglabel))
                basekeys = [os.path.basename(k) for k in allkeys]
                resultstuple = gotresloader.get_many(*allkeys)
                results = {k: v for k, v in zip(basekeys, resultstuple)}
                if post:
                    results, template = digcore.post_dig(results)
                    return gotfiglabel, results, template
                else:
                    return gotfiglabel, results
        # dig new
        results, acckwargstr, digtime = digcore.dig(**kwargs)
        if not acckwargstr:
            acckwargstr = 'DEFAULT'
        accfiglabel = '%s/%s' % (figlabel, acckwargstr)
        with self.ressaver:
            self.ressaver.write(accfiglabel, results)
            if gotkwargstr == 'DEFAULT' and acckwargstr != gotkwargstr:
                # TODO link double cache
                self.ressaver.write(gotfiglabel, results)
        # update resloader & diggedlabels
        self.resloader = get_pckloader(self.ressaver.get_store())
        # long execution time
        if self.resfilesaver and digtime > self.execution_time_limit:
            with self.resfilesaver:
                plog.info('%s, save digged results in %s.'
                          % (self.name, self.resfilesaver.path))
                self.resfilesaver.write(accfiglabel, results)
                if gotkwargstr == 'DEFAULT' and acckwargstr != gotkwargstr:
                    # TODO link double cache
                    self.resfilesaver.write(gotfiglabel, results)
            # update resfileloader & diggedlabels
            self.resfileloader = get_pckloader(self.resfilesaver.get_store())
        if post:
            results, template = digcore.post_dig(results)
            return gotfiglabel, results, template
        else:
            return accfiglabel, results

    def dig_doc(self, figlabel, see='help'):
        '''
        help(digcore.dig) or digcore.dig.__doc__

        Parameters
        ----------
        see: str
            'help', 'print' or 'return'
        '''
        if figlabel not in self.availablelabels:
            plog.error("%s: Figure %s not found!" % (self.name, figlabel))
            return
        digcore = self._availablelabels_lib[figlabel]
        if see == 'help':
            help(digcore.dig)
        elif see == 'print':
            print(digcore.dig.__doc__)
        elif see == 'return':
            return digcore.dig.__doc__
        else:
            pass

    def refind(self, pattern):
        '''Find the figlabels which match the regular expression *pattern*.'''
        pat = re.compile(pattern)
        return tuple(filter(
            lambda k: True if re.match(pat, k) else False, self.availablelabels))

    # # End Dig Part

    def __repr__(self):
        i = (' rawloader: %r\n pcksaver: %r\n'
             ' pckloader: %r\n ressaver: %r\n resfilesaver: %r\n'
             ' resloader: %r\n resfileloader: %r'
             % (self.rawloader, self.pcksaver,
                self.pckloader, self.ressaver, self.resfilesaver,
                self.resloader, self.resfileloader))
        return '<\n {0}.{1} object at {2},\n{3}\n>'.format(
            self.__module__, type(self).__name__, hex(id(self)), i)

    def __init__(self, path, add_desc=None, filenames_filter=None,
                 savetype='.npz', overwrite=False, Sid=False,
                 datagroups_filter=None):
        '''
        Pick up raw data or converted data in *path*,
        set processor's rawloader, pcksaver and pckloader, etc.

        Parameters
        ----------
        path: str
            path of raw data or converted data to open
        add_desc: str
            additional description of raw data
        filenames_filter: function
            function to filter filenames in rawloader
        savetype: '.npz' or '.hdf5'
            extension of pcksaver.path, default '.npz'
            when pcksaver.path isn't writable, use '.cache'
        overwrite: bool
            overwrite existing pcksaver.path file or not, default False
        Sid: bool
            If Sid is True(here), only rawloader and pcksaver will be set
            and converted to a .npz or .hdf5 file if needed. And any other
            codes(like Buzz Lightyear) will be omitted(destroyed).
            Default False.
        datagroups_filter: function
            function to filter datagroups in pckloader
        '''
        root, ext1 = os.path.splitext(path)
        root, ext2 = os.path.splitext(root)
        if (ext2, ext1) in [('.converted', '.npz'), ('.converted', '.hdf5')]:
            # pckloader.path
            self.rawloader, self.pcksaver = None, None
            if Sid:
                return
            try:
                self.pckloader = get_pckloader(
                    path, datagroups_filter=datagroups_filter)
            except Exception:
                plog.error("%s: Invalid pckloader path '%s'!"
                           % (self.name, path), exc_info=1)
                return
            try:
                self.set_prefer_ressaver(ext2='digged', overwrite=overwrite)
            except Exception:
                plog.error("%s: Failed to set ressaver object!"
                           % self.name, exc_info=1)
        else:
            # rawloader.path
            try:
                self.rawloader = get_rawloader(
                    path, filenames_filter=filenames_filter)
            except Exception:
                plog.error("%s: Invalid rawloader path '%s'!"
                           % (self.name, path), exc_info=1)
                return
            try:
                self.set_prefer_pcksaver(savetype, ext2='converted')
            except Exception:
                plog.error("%s: Failed to set pcksaver object!"
                           % self.name, exc_info=1)
                return
            plog.info("Default %s data path is %s." %
                      ('converted', self.pcksaver.path))
            if Sid and self.pcksaver._extension not in ['.npz', '.hdf5']:
                return
            if os.path.isfile(self.pcksaver.path):
                if overwrite:
                    plog.warning("Remove old %s data file: %s!"
                                 % ('converted', self.pcksaver.path))
                    os.remove(self.pcksaver.path)
                    self.convert(add_desc=add_desc)
            else:
                self.convert(add_desc=add_desc)
            if Sid and self.pcksaver._extension in ['.npz', '.hdf5']:
                return
            try:
                self.pckloader = get_pckloader(
                    self.pcksaver.get_store(), datagroups_filter=datagroups_filter)
            except Exception:
                plog.error("%s: Invalid pckloader path '%s'!"
                           % (self.name, path), exc_info=1)
                return
            try:
                self.set_prefer_ressaver(ext2='digged', overwrite=overwrite)
            except Exception:
                plog.error("%s: Failed to set ressaver object!"
                           % self.name, exc_info=1)