# -*- coding: utf-8 -*-

# Copyright (c) 2018-2022 shmilee

'''
Contains processor base class.
'''

import os
import re
import time
import pickle
import hashlib

from .. import __gversion__
from ..glogger import getGLogger
from ..tools import nparray_default_bitsize
from ..loaders import is_rawloader, get_rawloader, is_pckloader, get_pckloader
from ..savers import is_pcksaver, get_pcksaver, pcksaver_types
from ..cores.exporter import Exporter
from ..visplters import get_visplter, is_visplter

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

    exporters: dict
        exporters generated
    exporttemplates: list
        templates of generated exporters

    visplter: visplter object to create, show figures
    show_usecat: bool
        Set default action, show the figures in terminal or not.
        This is a class attribute. It affects all instances.

    Notes
    -----
    1. :attr:`saltname` means base name of salt file for `saver.path`.
       The :attr:`rawloader` must have at least one salt file.
       If more than one salt files, the one with min path depth will be used.
       :attr:`saltstr` is the salt string generated from salt file.
    2. :attr:`convert_array_bitsize` is the bits size of integer, float array
       when converting raw data to `numpy.ndarray`, like 64 for `numpy.int64`.
    3. :attr:`dig_acceptable_time` means if :meth:`dig` spends more
       time than this, the results will be saved in :attr:`resfilesaver`.
    '''
    __slots__ = []
    parallel = 'off'

    @property
    def name(self):
        return type(self).__name__

    # # Start Convert Part

    __slots__.extend(['_rawloader', '_pcksaver', '_converters', '_saltstr'])
    ConverterCores = []
    saltname = ''
    convert_array_bitsize = None

    def __check_rawloader(self, rawloader):
        if rawloader is None:
            return False
        if not is_rawloader(rawloader):
            plog.error("%s: Not a rawloader object!" % self.name)
            return False
        saltfiles = rawloader.refind('^(?:|.*/)%s$' % self.saltname)
        if len(saltfiles) == 0:
            plog.error("%s: Can't find '%s' in '%s'!"
                       % (self.name, self.saltname, rawloader.path))
            return False
        elif len(saltfiles) > 1:
            plog.warning(
                "%s: More than one '%s' %s found in '%s'!"
                % (self.name, self.saltname, saltfiles, rawloader.path))
            lth = [len(f.split('/')) for f in saltfiles]
            idx = lth.index(min(lth))  # min path depth
            ignore_dirs = [os.path.dirname(saltfiles[i])
                           for i in range(len(saltfiles)) if i != idx]
            plog.warning(
                "%s: Use '%s' as salt file, ignore other files in %s!"
                % (self.name, saltfiles[idx], ignore_dirs))
            _old_fe = rawloader.filenames_exclude
            _new_fe = [r'^%s.*$' % d for d in ignore_dirs]
            rawloader = get_rawloader(
                rawloader.path, dirnames_exclude=rawloader.dirnames_exclude,
                filenames_exclude=_old_fe + _new_fe)
        return rawloader

    def _get_rawloader(self):
        return self._rawloader

    def _set_rawloader(self, rawloader):
        self._converters = []
        rawloader = self.__check_rawloader(rawloader)
        if rawloader:
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

    def set_prefer_pcksaver(self, savetype, savedir, ext2='converted'):
        '''
        Set preferable pcksaver path in savedir or beside raw data.

        Parameters
        ----------
        savetype: str
            extension of pcksaver.path, like (.npz)
        savedir: str
            directory of pcksaver.path, None -> raw data directory
        ext2: str
            second extension, like name.(converted).npz
        '''
        if not self.rawloader:
            raise IOError("%s: Need a rawloader object!" % self.name)
        # salt
        saltfile = self.rawloader.refind('^(?:|.*/)%s$' % self.saltname)[0]
        try:
            with self.rawloader.get(saltfile) as f:
                salt = hashlib.sha1(f.read().encode('utf-8')).hexdigest()
        except Exception:
            plog.warning("Failed to read salt file '%s'!" % saltfile)
            salt = hashlib.sha1(saltfile.encode('utf-8')).hexdigest()
        plog.debug("Get salt string: '%s'." % salt)
        # prefix
        if savedir and os.path.isdir(savedir) and os.access(savedir, os.W_OK):
            prefix = os.path.join(savedir, self.name.lower())
        else:
            prefix = self.rawloader.beside_path(self.name.lower())
        # savetype
        if os.access(os.path.dirname(prefix) or '.', os.W_OK):  # '' -> '.'
            if savetype not in pcksaver_types[1:]:
                plog.warning("Use default savetype '.npz'.")
                savetype = '.npz'
        else:
            plog.debug("Use savetype '.cache' because %s isn't writable!"
                       % os.path.dirname(prefix))
            savetype = '.cache'
        # assemble
        savepath = '%s-%s.%s%s' % (prefix, salt[:6], ext2, savetype)
        self._saltstr = salt
        self.pcksaver = get_pcksaver(savepath)

    @property
    def saltstr(self):
        if getattr(self, '_saltstr', None):
            # has rawloader, pcksaver
            return self._saltstr
        elif getattr(self, 'pckloader', None):
            # no rawloader, pcksaver
            if 'saltstr' in self.pckloader:
                return self.pckloader.get('saltstr')
            else:
                m = re.match(r'.*-(.{6})\.converted\..*', self.pckloader.path)
                if m:
                    return m.groups()[0]
        # fallback
        return '123456'

    @property
    def _rawsummary(self):
        return "Raw data files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)

    def _pre_convert(self, add_desc=None):
        if not self.rawloader:
            plog.error("%s: Need a rawloader object!" % self.name)
            return
        if not self.pcksaver:
            plog.error("%s: Need a pcksaver object!" % self.name)
            return
        summary = "Pck data converted from %s." % self._rawsummary
        description = ("%s\nCreated by gdpy3 v%s.\nCreated on %s."
                       % (summary, __gversion__, time.asctime()))
        if add_desc:
            description += '\n' + str(add_desc)
        with self.pcksaver:
            self.pcksaver.write('/', {'description': description,
                                      'saltstr': self.saltstr,
                                      'processor': self.name})

    def _post_convert(self):
        plog.info("%s are converted to %s!"
                  % (self._rawsummary,  self.pcksaver.path))

    def convert(self, add_desc=None):
        '''
        Convert raw data in rawloader.path, and save them in pcksaver.
        '''
        self._pre_convert(add_desc=add_desc)
        with nparray_default_bitsize(size=self.convert_array_bitsize):
            with self.pcksaver:
                for core in self.converters:
                    self.pcksaver.write(core.group, core.convert())
        self._post_convert()

    # # End Convert Part

    # # Start Dig Part

    __slots__.extend(['_pckloader', '_ressaver', '_resfilesaver',
                      '_diggers', '_availablelabels_lib', '_availablelabels',
                      '_resloader', '_resfileloader', '_diggedlabels'])
    DiggerCores = []
    dig_acceptable_time = 30

    def _check_pckloader_backward_version(self, pckloader):
        return False

    def _check_pckloader_forward_version(self, pckloader):
        return False

    def __check_pckloader(self, pckloader):
        if not is_pckloader(pckloader):
            plog.error("%s: Not a pckloader object!" % self.name)
            return False
        if (self._check_pckloader_backward_version(pckloader)
                or self._check_pckloader_forward_version(pckloader)):
            return True
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

    def set_prefer_ressaver(self, ext2='digged', oldext2='converted',
                            overwrite=False):
        '''
        Set preferable ressaver resfilesaver beside converted data.

        Parameters
        ----------
        ext2: str
            second extension, like name.(digged).npz
        oldext2: str
            second extension of converted file, like name.(converted).npz
        overwrite: bool
            overwrite existing resfilesaver.path file or not, default False
        '''
        if not self.pckloader:
            raise IOError("%s: Need a pckloader object!" % self.name)
        saverstr, ext = os.path.splitext(self.pckloader.path)
        saverstr = saverstr.replace(oldext2, ext2)
        respath = '%s.cache' % saverstr
        ressaver = get_pcksaver(respath)
        with ressaver:
            ressaver.write('/', {'processor': self.name})
        self.ressaver = ressaver
        self.resloader = get_pckloader(ressaver.get_store())
        plog.debug("Default %s data cache is %s." % (ext2, respath))
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
                plog.info("Default %s data path is %s." % (ext2, respath))
            except Exception:
                plog.error("%s: Failed to set results file pcksaver, '%s'!"
                           % (self.name, respath), exc_info=1)
                self.resfilesaver = None

    def _before_new_dig(self, figlabel, redig, kwargs):
        '''Get digcore, try old dig results'''
        if not self.pckloader:
            plog.error("%s: Need a pckloader object!" % self.name)
            return None, 'No pckloader', None
        if not self.ressaver:
            plog.error("%s: Need a results pcksaver object!" % self.name)
            return None, 'No pcksaver', None
        if figlabel not in self.availablelabels:
            plog.error("%s: Figure %s not found!" % (self.name, figlabel))
            return None, 'Invalid figlabel', None
        digcore = self._availablelabels_lib[figlabel]
        gotkwargstr = digcore.str_dig_kwargs(kwargs) or 'DEFAULT'
        plog.debug("Get kwargstr '%s' for %s" % (gotkwargstr, figlabel))
        # TODO use 'DEFAULT'? gotkwargstr completion for partial kwargs
        gotfiglabel = '%s/%s' % (figlabel, gotkwargstr)
        if not redig and gotfiglabel in self.diggedlabels:
            if gotfiglabel in self.resloader.datagroups:
                # use resloader first
                gotresloader, fileloader = self.resloader, False
            elif (self.resfileloader and
                    gotfiglabel in self.resfileloader.datagroups):
                gotresloader, fileloader = self.resfileloader, True
            else:
                plog.error('%s: Not found %s in diggedlabels!'
                           % (self.name, gotfiglabel))
                return digcore, gotfiglabel, None
            plog.info('Find %s digged results in %s.' % (
                gotfiglabel, os.path.basename(gotresloader.path)))
            if gotfiglabel.endswith('/DEFAULT'):
                try_link_key = '%s/_LINK' % gotfiglabel
                if try_link_key in gotresloader:
                    linkgotfiglabel = gotresloader.get(try_link_key)
                    plog.debug('Find %s digged results link to %s.' % (
                        gotfiglabel, linkgotfiglabel))
                    gotfiglabel = linkgotfiglabel
            results = gotresloader.get_by_group(gotfiglabel)
            if fileloader:
                # reload kwoptions
                digcore.kwoptions = pickle.loads(
                    results.pop('kwoptions', None))
            return digcore, gotfiglabel, results
        else:
            return digcore, gotfiglabel, None

    def _do_new_dig(self, digcore, kwargs):
        '''Dig new results.'''
        results, acckwargstr, digtime = digcore.dig(**kwargs)
        if not acckwargstr:
            acckwargstr = 'DEFAULT'
        accfiglabel = '%s/%s' % (digcore.figlabel, acckwargstr)
        return accfiglabel, results, digtime

    def _cachesave_new_dig(self, accfiglabel, gotfiglabel, results):
        '''Cache dig results, link DEFAULT to accfiglabel.'''
        with self.ressaver:
            self.ressaver.write(accfiglabel, results)
            if (gotfiglabel.endswith('/DEFAULT')
                    and not accfiglabel.endswith('/DEFAULT')):
                # link double cache
                self.ressaver.write(gotfiglabel, dict(_LINK=accfiglabel))

    def _filesave_new_dig(self, accfiglabel, gotfiglabel, results, digcore):
        '''Save dig results in file, link DEFAULT to accfiglabel.'''
        # also save kwoptions
        kwopts = dict(kwoptions=pickle.dumps(digcore.kwoptions))
        with self.resfilesaver:
            shortpath = os.path.basename(self.resfilesaver.path)
            plog.info('Save %s digged results in %s.' % (
                accfiglabel, shortpath))
            self.resfilesaver.write(accfiglabel, results)
            self.resfilesaver.write(accfiglabel, kwopts)
            if (gotfiglabel.endswith('/DEFAULT')
                    and not accfiglabel.endswith('/DEFAULT')):
                # link double cache
                plog.info('Save %s digged results in %s.' % (
                    gotfiglabel, shortpath))
                self.resfilesaver.write(
                    gotfiglabel, dict(_LINK=accfiglabel))

    def dig(self, figlabel, redig=False, callback=None, post=True, **kwargs):
        '''
        Get digged results of *figlabel*.
        Use :meth:`dig_doc` to see *kwargs* for *figlabel*.
        Return accfiglabel, results and template name,
        and accfiglabel is 'figlabel/digkwargstr'.

        Parameters
        ----------
        redig: bool
            If :attr:`resfilesaver` type is '.npz', *redig* may cause warning:
                "zipfile.py: UserWarning: Duplicate name ..."
            Recommend using '.hdf5' when *redig* is True or
            setting :attr:`resfilesaver.duplicate_name`=False to rebuild
            a new zip archive when we get duplicate names.
        callback: a callable
            It accepts two arguments, accfiglabel and dig results before
            post_dig. This can be used to get some numbers from results.
        post: bool
            call post_dig
        '''
        data = self._before_new_dig(figlabel, redig, kwargs)
        if data[0] is None:
            return data
        digcore, gotfiglabel, results = data
        if results is None:
            accfiglabel, results, digtime = self._do_new_dig(digcore, kwargs)
            self._cachesave_new_dig(accfiglabel, gotfiglabel, results)
            self.resloader = get_pckloader(self.ressaver.get_store())
            if self.resfilesaver and digtime > self.dig_acceptable_time:
                # long execution time
                self._filesave_new_dig(
                    accfiglabel, gotfiglabel, results, digcore)
                self.resfileloader = get_pckloader(
                    self.resfilesaver.get_store())
        else:
            accfiglabel = gotfiglabel
        if callable(callback):
            callback(accfiglabel, results)
        if post:
            results = digcore.post_dig(results)
        return accfiglabel, results, digcore.post_template

    def dig_doc(self, figlabel, see='print'):
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

    # # Start Export Part

    ExporterCores = [Exporter]
    exporters = {pt: Exporter(pt) for pt in Exporter.template_available}
    _exporttemplates = list(Exporter.template_available)

    @property
    def exporttemplates(self):
        return self._exporttemplates

    def _get_exporter(self, post_tmpl):
        if post_tmpl in self._exporttemplates:
            return self.exporters[post_tmpl]
        else:
            try:
                ecore = Exporter(post_tmpl)
            except Exception:
                pass
            else:
                self.exporters[post_tmpl] = ecore
                self._exporttemplates.append(post_tmpl)
                return ecore
        return None

    def export(self, figlabel, what='axes', fmt='dict',
               callback=None, **kwargs):
        '''
        Get and assemble digged results, template of *figlabel*.
        Use :meth:`dig_doc` to see *kwargs* for *figlabel*.
        Use :meth:`export_doc` to see *kwargs* for :meth:`exportcore.export`.

        Returns
        -------
        assembled results in format *fmt*
        If *what* is 'axes', results['accfiglabel'] will be updated
        from 'figlabel/digkwargstr' to 'figlabel/digkwargstr,viskwargstr',
        where 'viskwargstr' is :meth:`exportcore.export` *kwargs* to str.

        Parameters
        ----------
        what: str
            'axes'(default), results for visplter
            'options', options for GUI widgets
        fmt: str
            export format, 'dict'(default), 'pickle' or 'json'
        callback: see :meth:`dig`, only for what='axes'
        '''
        if what not in ('axes', 'options'):
            waht = 'axes'
        if fmt not in ('dict', 'pickle', 'json'):
            fmt = 'dict'
        if figlabel in self.availablelabels:
            if what == 'axes':
                label_kw, res, tmpl = self.dig(
                    figlabel, callback=callback, post=True, **kwargs)
                exportcore = self._get_exporter(tmpl)
                if exportcore:
                    return exportcore.export(
                        res, otherinfo=dict(status=200,
                                            figlabel=figlabel,
                                            accfiglabel=label_kw,
                                            ), fmt=fmt, **kwargs)
                else:
                    status, reason = 500, 'invalid template'
            elif what == 'options':
                digcore = self._availablelabels_lib[figlabel]
                exportcore = self._get_exporter(digcore.post_template)
                if exportcore:
                    if digcore.kwoptions is None:
                        a, b, c = self.dig(figlabel, post=False, **kwargs)
                    return exportcore.export_options(
                        digcore.kwoptions, otherinfo=dict(status=200,
                                                          figlabel=figlabel,
                                                          ), fmt=fmt)
                else:
                    status, reason = 500, 'invalid template'
        else:
            plog.error("%s: Figure %s not found!" % (self.name, figlabel))
            status, reason = 404, 'figlabel not found'
        exportcore = self._get_exporter('tmpl_line')
        return exportcore.fmt_export(
            dict(status=status, reason=reason, figlabel=figlabel), fmt=fmt)

    def export_doc(self, template, see='print'):
        '''
        see docstring of :meth:`exportercore._export_*template*`

        Parameters
        ----------
        see: str
            'help', 'print' or 'return'
        '''
        if template not in Exporter.template_available:
            plog.error("%s: Template %s not found!" % (self.name, template))
            return
        exportcore = self._get_exporter(template)
        meth = getattr(exportcore, '_export_%s' % template)
        if see == 'help':
            help(meth)
        elif see == 'print':
            print(meth.__doc__)
        elif see == 'return':
            return meth.__doc__
        else:
            pass

    # # End Export Part

    # # Start Visplt Part

    __slots__.extend(['_visplter'])

    def _get_visplter(self):
        return self._visplter

    def _set_visplter(self, visplter):
        if is_visplter(visplter):
            self._visplter = visplter
        else:
            self._visplter = visplter

    visplter = property(_get_visplter, _set_visplter)
    _show_usecat = False

    def _get_show_usecat(self):
        return self._show_usecat

    def _set_show_usecat(self, val):
        cls = type(self)
        cls._show_usecat = val

    show_usecat = property(_get_show_usecat, _set_show_usecat)

    def visplt(self, figlabel, revis=False, show=True,
               callback=None, **kwargs):
        '''
        Get results of *figlabel* and visualize(plot).
        Use :meth:`dig_doc` :meth:`export_doc` to see *kwargs* for *figlabel*.
        Return accfiglabel or None.

        Parameters
        ----------
        revis: bool
            replot *figlabel* if it was already ploted
        show: bool
            display *figlabel* after it ploted
        _show_kwargs: parameters pick from *kwargs*
            They startswith('_show_') for :attr:`visplter`.show_figure,
            like '_show_usecat', '_show_width', '_show_mod' etc.
        callback: see :meth:`dig`
        '''
        if not self.visplter:
            plog.error("%s: Need a visplter object!" % self.name)
            return
        # pop show kwargs
        shkws = {'usecat': True} if self.show_usecat else {}
        shkws.update({k[6:]: kwargs.pop(k)
                      for k in tuple(kwargs.keys()) if k.startswith('_show_')})
        results = self.export(
            figlabel, what='axes', fmt='dict', callback=callback, **kwargs)
        if results['status'] == 200:
            try:
                figure = self.visplter.create_template_figure(
                    results, replace=revis)
            except Exception:
                plog.error("%s: Failed to create figure %s!" % (
                    self.name, results['accfiglabel']),  exc_info=1)
            else:
                if show:
                    self.visplter.show_figure(results['accfiglabel'], **shkws)
                return results['accfiglabel']
        else:
            plog.error("%s: Failed to create figure %s: %s" % (
                self.name, figlabel, results['status']),  exc_info=1)

    # # End Visplt Part

    def __repr__(self):
        # i = (' rawloader: %r\n pcksaver: %r\n'
        #     ' pckloader: %r\n ressaver: %r\n resfilesaver: %r\n'
        #     ' resloader: %r\n resfileloader: %r\n'
        #     ' visplter: %r'
        #     % (self.rawloader, self.pcksaver,
        #        self.pckloader, self.ressaver, self.resfilesaver,
        #        self.resloader, self.resfileloader,
        #        self.visplter))
        i = (' rawloader: %r\n pckloader: %r\n'
             ' resloader: %r\n resfileloader: %r\n'
             ' visplter: %r'
             % (self.rawloader, self.pckloader,
                self.resloader, self.resfileloader,
                self.visplter))
        return '<\n {0}.{1} object at {2},\n{3}\n>'.format(
            self.__module__, type(self).__name__, hex(id(self)), i)

    @property
    def _default_exclude_raw_dirs(self):
        return []

    def __init__(self, path, add_desc=None,
                 dirnames_exclude=None, filenames_exclude=None,
                 savedir=None, savetype='.npz', overwrite=False, Sid=False,
                 datagroups_exclude=None, add_visplter='mpl::'):
        '''
        Pick up raw data or converted data in *path*,
        set processor's rawloader, pcksaver and pckloader, etc.

        Parameters
        ----------
        path: str
            path of raw data or converted data to open
        add_desc: str
            additional description of raw data
        dirnames_exclude: list
            function or regular expression to exclude subdirectory names in
            rawloader, like, 'restart_dir1', 'restart_dir2' in GTC results
        filenames_exclude: list
            function or regular expressions to exclude filenames in rawloader
        savedir: str, default same as raw data
            directory path of converted data
        savetype: '.npz', '.hdf5' or '.jsonl', '.jsonz'
            extension of pcksaver.path, default '.npz'
            when pcksaver.path isn't writable, use '.cache'
        overwrite: bool
            overwrite existing pcksaver.path file or not, default False
        Sid: bool
            If Sid is True(here), only rawloader and pcksaver will be set
            and converted to a .npz, .hdf5 or .jsonl, .jsonz file if needed.
            And any other codes(like Buzz Lightyear) will be omitted.
            Default False.
        datagroups_exclude: list
            regular expressions to exclude datagroups in pckloader
        add_visplter: str
            add visplter by type *add_visplter*, default 'mpl::'
        '''
        root, ext1 = os.path.splitext(path)
        root, ext2 = os.path.splitext(root)
        if (ext2 == '' and ext1 in pcksaver_types[1:]
                and os.path.basename(root).startswith('gdpy3-pickled-data-')):
            # pckloader.path backward compatibility
            plog.warning("This is an old converted data path %s!" % path)
            ext2 = '.converted'
            old_pickled_path = True
        else:
            old_pickled_path = False
        if ext2 == '.digged' and ext1 in pcksaver_types[1:]:
            # resfileloader.path
            plog.warning("This is a digged data path %s!" % path)
            path = '%s%s%s' % (root, '.converted', ext1)
            plog.warning("Try converted data path %s beside it!" % path)
            if os.path.isfile(path):
                root, ext1 = os.path.splitext(path)
                root, ext2 = os.path.splitext(root)
            else:
                plog.error("%s: Can't find path %s!" % (self.name, path))
                return
        if ext2 == '.converted' and ext1 in pcksaver_types[1:]:
            # pckloader.path
            self.rawloader, self.pcksaver = None, None
            if Sid:
                return
            try:
                self.pckloader = get_pckloader(
                    path, datagroups_exclude=datagroups_exclude)
            except Exception:
                plog.error("%s: Invalid pckloader path '%s'!"
                           % (self.name, path), exc_info=1)
                return
            try:
                if old_pickled_path:
                    self.set_prefer_ressaver(
                        ext2='digged', oldext2='pickled', overwrite=overwrite)
                else:
                    self.set_prefer_ressaver(
                        ext2='digged', overwrite=overwrite)
            except Exception:
                plog.error("%s: Failed to set ressaver object!"
                           % self.name, exc_info=1)
        else:
            # rawloader.path
            try:
                dirnames_exclude = dirnames_exclude or []
                dirnames_exclude.extend(self._default_exclude_raw_dirs)
                self.rawloader = get_rawloader(
                    path, dirnames_exclude=dirnames_exclude,
                    filenames_exclude=filenames_exclude)
            except Exception:
                plog.error("%s: Invalid rawloader path '%s'!"
                           % (self.name, path), exc_info=1)
                return
            try:
                self.set_prefer_pcksaver(savetype, savedir, ext2='converted')
            except Exception:
                plog.error("%s: Failed to set pcksaver object!"
                           % self.name, exc_info=1)
                return
            plog.info("Default %s data path is %s." %
                      ('converted', self.pcksaver.path))
            if Sid and self.pcksaver._extension not in pcksaver_types[1:]:
                return
            if os.path.isfile(self.pcksaver.path):
                if overwrite:
                    plog.warning("Remove old %s data file: %s!"
                                 % ('converted', self.pcksaver.path))
                    os.remove(self.pcksaver.path)
                    self.convert(add_desc=add_desc)
            else:
                self.convert(add_desc=add_desc)
            if Sid and self.pcksaver._extension in pcksaver_types[1:]:
                return
            try:
                self.pckloader = get_pckloader(
                    self.pcksaver.get_store(), datagroups_exclude=datagroups_exclude)
            except Exception:
                plog.error("%s: Invalid pckloader path '%s'!"
                           % (self.name, path), exc_info=1)
                return
            try:
                self.set_prefer_ressaver(ext2='digged', overwrite=overwrite)
            except Exception:
                plog.error("%s: Failed to set ressaver object!"
                           % self.name, exc_info=1)
        # set visplter
        if add_visplter:
            self.visplter = get_visplter(str(add_visplter) + path)
        else:
            self.visplter = None
