# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains core base class and figure information base class.
'''

import os
import re

from ..glogger import getGLogger
from ..loaders import is_rawloader, is_pckloader
from ..plotters import is_plotter

__all__ = ['BaseCore', 'BaseFigInfo']
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
    figureclasses = []

    def __init__(self, nfiles='?'):
        self.rawloader = None
        self.file = None
        if nfiles not in ['?', '+']:
            raise ValueError("'nfiles' should be '?' or '+', not '%s'!"
                             % self.nfiles)
        self.nfiles = nfiles
        self.group = None
        self.pckloader = None
        self.figurenums = tuple(self.get_figurenums())

    @classmethod
    def match_files(cls, rawloader):
        '''Return files matched with this class in *rawloader*.'''
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
        '''Return groups matched with this class in *pckloader*.'''
        if not is_pckloader(pckloader):
            raise ValueError("Not a pckloader object!")
        groups = []
        for group in pckloader.datagroups:
            if re.match(cls.grouppattern, group):
                groups.append(group)
        return groups

    @classmethod
    def _check_filestr(cls, file):
        '''If *file* match :attr:`filepatterns`'''
        if not isinstance(file, str):
            log.error("'file' should be str!")
            return False
        result = False
        for pat in cls.filepatterns:
            if re.match(pat, file):
                result = True
        if not result:
            log.error("Invalid 'file' str: %s, its pattern: '%s'."
                      % (file, cls.filepatterns))
        return result

    @classmethod
    def _check_groupstr(cls, group):
        '''If *group* match :attr:`groupattern`'''
        if not isinstance(group, str):
            log.error("'group' should be str!")
            return False
        if re.match(cls.grouppattern, group):
            return True
        else:
            log.error("Invalid 'group' str: %s, its pattern: '%s'."
                      % (group, cls.grouppattern))
            return False

    def set_dig_args(self, rawloader, file, group=None):
        '''Set :meth:`dig` arguments.'''
        if 'dig' not in self.instructions:
            log.error("Core %s: no '%s' instruction!"
                      % (self.__class__.__name__, 'dig'))
            return
        if not is_rawloader(rawloader):
            raise ValueError("Not a rawloader object!")
        self.rawloader = rawloader
        if self.nfiles == '?':
            if not isinstance(file, str):
                raise ValueError("'file' should be str, not '%s'!"
                                 % type(file))
            if file not in rawloader:
                raise ValueError("'%s' is not in rawloader: %s!"
                                 % (file, rawloader.path))
            if not self._check_filestr(file):
                raise ValueError("Invalid 'file' str: %s!" % file)
            self.file = file
        elif self.nfiles == '+':
            if not isinstance(file, list):
                raise ValueError("'file' should be list, not '%s'!"
                                 % type(file))
            for f in file:
                if f not in rawloader:
                    raise ValueError("'%s' is not in rawloader: %s!"
                                     % (f, rawloader.path))
                if not self._check_filestr(f):
                    raise ValueError("Invalid 'file' str: %s!" % f)
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
                raise ValueError("Invalid 'group' str: %s!" % group)
        else:
            if self.nfiles == '?':
                fs = [file]
            else:
                fs = file
            for pat in self.filepatterns:
                for f in fs:
                    m = re.match(pat, f)
                    if m and 'group' in m.groupdict():
                        tmpgroup = m.groupdict()['group']
                        if re.match(self.grouppattern, tmpgroup):
                            group = tmpgroup
                            break
                if group:
                    break
            if group:
                if self.group:
                    log.debug("'group': replace '%s' with '%s'!"
                              % (self.group, group))
                self.group = group
            else:
                raise ValueError("Please set 'group' by yourself!")
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

    def set_cook_args(self, pckloader, group):
        '''Set :meth:`cook` arguments.'''
        if 'cook' not in self.instructions:
            log.error("Core %s: no '%s' instruction!"
                      % (self.__class__.__name__, 'cook'))
            return
        if not is_pckloader(pckloader):
            raise ValueError("Not a pckloader object!")
        self.pckloader = pckloader
        if self._check_groupstr(group):
            if self.group:
                log.debug("'group': replace '%s' with '%s'!"
                          % (self.group, group))
            else:
                log.debug("Cook group: %s." % group)
            self.group = group
        else:
            raise ValueError("Invalid 'group' str: %s!" % group)

    @classmethod
    def get_figurenums(cls):
        result = []
        for c in cls.figureclasses:
            if c.figurenums:
                result.extend(c.figurenums)
        return sorted(result)

    def cook(self, fignum, figkwargs={}):
        '''
        Read and calculate pck data. Return a :class:`BaseFigInfo` instance.
        Use :meth:`see_figkwargs` to get
        :meth:`BaseFigInfo.calculate` kwargs for the figinfo 'fignum'.
        '''
        if not self.pckloader or not self.group:
            log.error(
                "Please set 'pckloader', 'group' before cook data!")
            return
        if fignum not in self.figurenums:
            log.error("%s not found in figurenums of class %s!"
                      % (fignum, self.__class__.__name__))
            return
        else:
            figinfocls = None
            for c in self.figureclasses:
                if fignum in c.figurenums:
                    figinfocls = c
                    break
        if figinfocls:
            log.debug('Cook pck data for %s/%s ...' % (self.group, fignum))
            figinfo = figinfocls(fignum, self.group)
            try:
                data = figinfo.get_data(self.pckloader)
            except Exception:
                log.error("figurenum %s/%s: can't get data!"
                          % (self.group, fignum), exc_info=1)
                return figinfo
            try:
                figinfo.calculate(data, **figkwargs)
            except Exception:
                log.error("figurenum %s/%s: calculate() failed!"
                          % (self.group, fignum), exc_info=1)
            return figinfo
        else:
            log.error("FigInfo class not found for figurenum: %s/%s!"
                      % (self.group, fignum))
            return

    def see_figkwargs(self, fignum, see='help'):
        '''
        help(figinfo.calculate) or print(figinfo.calculate.__doc__)
        *see*: str, 'help' or 'print'
        '''
        if fignum not in self.figurenums:
            log.error("%s not found in figurenums!" % fignum)
            return
        else:
            figinfocls = None
            for c in self.figureclasses:
                if fignum in c.figurenums:
                    figinfocls = c
                    break
        if figinfocls:
            if see == 'help':
                help(figinfocls.calculate)
            else:
                print(figinfocls.calculate.__doc__)
        else:
            log.error("FigInfo class not found for figurenum: %s/%s!"
                      % (self.group, fignum))
            return


class BaseFigInfo(object):
    '''
    Base Figure Information class.

    Attributes
    ----------
    fignum: str
        name(label) of figure
    group: str
        group of figure
    srckey: list
        pck data keys needed in same core
    extrakey: list
        pck data keys needed in other core
    calculation: dict
        results of cooked data
    template: str
        name of 'bound template method of plotter'
    '''
    __slots__ = ['fignum', 'group',
                 'srckey', 'extrakey', 'template', 'calculation']
    figurenums = []
    numpattern = '^.*$'

    def _pre_check_get(self, fignum, *names):
        '''
        1. check fignum;
        2. check *names* we needed in matched groupdict or not;
        3. return the groupdict.
        '''
        if fignum not in self.figurenums:
            raise ValueError("fignum: %s not found in class %s!"
                             % (fignum, self.__class__.__name__))
        m = re.match(self.numpattern, fignum)
        if not m:
            raise ValueError("Can't get info of fignum %s in class %s!"
                             % (fignum, self.__class__.__name__))
        for k in names:
            if k not in m.groupdict():
                raise ValueError(
                    "Can't get '%s' info of fignum %s in class %s!"
                    % (k, fignum, self.__class__.__name__))
        return m.groupdict()

    def __init__(self, fignum, group, srckey, extrakey, template):
        self.fignum = fignum
        self.group = group
        self.srckey = srckey
        self.extrakey = extrakey
        self.template = template
        self.calculation = {}

    def get_data(self, pckloader):
        '''Use keys get pck data from *pckloader*, return a dict.'''
        result = {}
        srckey = ['%s/%s' % (self.group, k) for k in self.srckey]
        result.update(zip(self.srckey, pckloader.get_many(*srckey)))
        result.update(zip(self.extrakey, pckloader.get_many(*self.extrakey)))
        return result

    def calculate(self, data, **kwargs):
        '''
        Use *data* get by keys, return calculation.
        '''
        raise NotImplementedError()

    def serve(self, plotter):
        '''
        Assemble calculation and template.
        Return AxesStructures and add_style for plotter.
        '''
        if is_plotter(plotter):
            try:
                template_method = getattr(plotter, self.template)
            except AttributeError:
                log.error("Template %s not found in plotter %s!"
                          % (self.template, plotter.name))
                raise
        else:
            raise ValueError("Not a plotter object!")
        return self._serve(plotter, *template_method(self.calculation))

    def _serve(self, plotter, AxStrus, add_style):
        '''patch assembled AxStrus, add_style'''
        return AxStrus, add_style


class BaseSharexTwinxFigInfo(BaseFigInfo):
    '''Base class for figures use 'template_sharex_twinx_axstructs'.'''
    __slots__ = []

    def _get_srckey_extrakey(self, fignum):
        # groupdict = self._pre_check_get(fignum, '?')
        # return [], []
        raise NotImplementedError()

    def _get_data_X_Y_title_etc(self, data):
        # return {'X': [], 'YINFO': [], 'title': '', ...}
        raise NotImplementedError()

    def __init__(self, fignum, group):
        srckey, extrakey = self._get_srckey_extrakey(fignum)
        super(BaseSharexTwinxFigInfo, self).__init__(
            fignum, group, srckey, extrakey,
            'template_sharex_twinx_axstructs')

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *hspace*: float
            subplot.hspace, default 0.02
        *xlim*: (`left`, `right`)
            default [min(X), max(X)]
        *ylabel_rotation*: str or int
            default 'vertical'
        '''
        self.calculation.update(self._get_data_X_Y_title_etc(data))
        if len(self.calculation['YINFO']) == 0:
            log.warn("No data for fignum %s." % self.fignum)
        debug_kw = {}
        for k in ['hspace', 'xlim', 'ylabel_rotation']:
            if k in kwargs:
                self.calculation[k] = kwargs[k]
            if k in self.calculation:
                debug_kw[k] = self.calculation[k]
        log.ddebug("Some kwargs accepted: %s" % debug_kw)


class BasePcolorFigInfo(BaseFigInfo):
    '''Base class for figures use 'template_pcolor_axstructs'.'''
    __slots__ = []
    default_plot_method = 'pcolor'

    def _get_srckey_extrakey(self, fignum):
        # groupdict = self._pre_check_get(fignum, '?')
        # return [], []
        raise NotImplementedError()

    def _get_data_X_Y_Z_title_etc(self, data):
        # return {'X': [], 'Y': [], 'Z': [], 'title': '', ...}
        raise NotImplementedError()

    def __init__(self, fignum, group):
        srckey, extrakey = self._get_srckey_extrakey(fignum)
        super(BasePcolorFigInfo, self).__init__(
            fignum, group, srckey, extrakey, 'template_pcolor_axstructs')

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *kwargs* passed on to :meth:`plotter.template_pcolor_axstructs`
        1. *plot_method*: default :attr:`default_plot_method`
        2. *colorbar* : default True
        3. other keyword arguments:
            *plot_method_args*, *plot_method_kwargs*,
            *grid_alpha*, *plot_surface_shadow*
        '''
        self.calculation.update(self._get_data_X_Y_Z_title_etc(data))
        if len(self.calculation['Z']) == 0:
            log.warn("No data for fignum %s." % self.fignum)
        self.calculation['plot_method'] = self.default_plot_method
        debug_kw = {}
        for k in ['plot_method', 'plot_method_args',
                  'plot_method_kwargs', 'colorbar',
                  'grid_alpha', 'plot_surface_shadow']:
            if k in kwargs:
                self.calculation[k] = kwargs[k]
            if k in self.calculation:
                debug_kw[k] = self.calculation[k]
        log.ddebug("Some kwargs accepted: %s" % debug_kw)


BaseCore.figureclasses = []  # [BaseFigInfo, BaseSharexTwinxFigInfo]
