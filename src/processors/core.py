# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains core and figure-information base classes.
'''

import re

from ..glogger import getGLogger
from ..loaders import is_rawloader, is_pckloader
from ..plotters import is_plotter

__all__ = ['DigCore', 'LayCore', 'FigInfo',
           'LineFigInfo', 'SharexTwinxFigInfo', 'PcolorFigInfo',
           ]
log = getGLogger('C')


class BaseCore(object):
    '''
    Base core class for DigCore, LayCore ...

    Parameters
    ----------
    loader: rawloader or pckloader ...
    items: files or groups ...
    '''
    __slots__ = ['loader', 'items', 'section']
    nitems = '?' or '+'
    itemspattern = ['^(?P<section>item)$']
    default_section = ''

    @classmethod
    def _check_itemstr(cls, item):
        '''Check if string *item* match with :attr:`itemspattern`.'''
        for pat in cls.itemspattern:
            if re.match(pat, item):
                return True
        return False

    @classmethod
    def match_items(cls, all_items):
        '''
        Return items matched with :attr:`itemspattern` in list *all_items*.
        '''
        return [it for it in all_items if cls._check_itemstr(it)]

    @classmethod
    def _find_items_section(cls, items):
        '''
        Find list *items* group accessible by 'section'
        in first match to :attr:`itemspattern`.
        '''
        for pat in cls.itemspattern:
            for it in items:
                m = re.match(pat, it)
                if m and 'section' in m.groupdict():
                    return m.groupdict()['section']
        return None

    @property
    def _short_items(self):
        '''
        When :attr:`items` is list, replace any decimal digit in it with '*'.
        Return a short string of unique items.
        '''
        if self.nitems == '?':
            return self.items
        else:
            result = list({re.sub('\d', '*', it) for it in self.items})
            if len(result) == 1:
                return result[0]
            else:
                return str(result)

    @property
    def coreid(self):
        return type(self).__name__

    def __init__(self, loader, items):
        self.loader = loader
        if self.nitems == '?':
            if not isinstance(items, str):
                raise ValueError("%s: items should be str, not '%s'!"
                                 % (self.coreid, type(items)))
        else:
            if not isinstance(items, list):
                raise ValueError("%s: items should be list, not '%s'!"
                                 % (self.coreid, type(items)))
        self.items = items
        _check_items = [items] if self.nitems == '?' else items
        section = self._find_items_section(_check_items)
        if section:
            self.section = section
        else:
            self.section = self.default_section
        log.debug("%s: loader, %s; items, %s; section, %s."
                  % (self.coreid, loader.path,
                     self._short_items, self.section))

    def __repr__(self):
        return '<{0}.{1} object at {2} for {3} in {4}>'.format(
            self.__module__, type(self).__name__, hex(id(self)),
            self._short_items, self.loader.path)

    @classmethod
    def generate_cores(cls, loader, all_items):
        '''
        Use *loader* and matched items in *all_items* to
        generate Core instances.

        Parameters
        ----------
        loader: rawloader or pckloader ...
        all_items: rawloader.filenames or pckloader.datagroups ...
        '''
        matched_items = cls.match_items(all_items)
        if len(matched_items) == 0:
            log.debug("%s: No items matched in loader %s!"
                      % (cls.__name__, loader.path))
            return []
        if cls.nitems == '?':
            return [cls(loader, items) for items in matched_items]
        else:
            return [cls(loader, matched_items)]


class DigCore(BaseCore):
    '''
    Dig Core: convert raw data to pickled data for saver.

    Attributes
    ----------
    nitems: '?' or '+', default '?'
        '?', take only one file; '+', more than one
    itemspattern: list
        regular expressions for files, need group name `(?P<sectionp>file)`
    rawloader: rawloader object to get raw data
    files: str or list
        file name(s) of raw data
    group: str
        group name of pickled data
    default_section: str
        default group name of pickled data, if can't get from *files*
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>file)\.ext$', '.*/(?P<section>file)\.ext$']
    default_section = ''

    @property
    def rawloader(self):
        return self.loader

    @property
    def files(self):
        return self.items

    @property
    def group(self):
        return self.section

    def __init__(self, rawloader, files):
        if not is_rawloader(rawloader):
            raise ValueError("%s: Not a rawloader object!" % self.coreid)
        super(DigCore, self).__init__(rawloader, files)

    @classmethod
    def generate_cores(cls, rawloader):
        '''Return generated Core instances for *rawloader*.'''
        return super(DigCore, cls).generate_cores(
            rawloader, rawloader.filenames)

    def _convert(self):
        '''Convert raw data.'''
        raise NotImplementedError()

    def convert(self):
        '''Read raw data, convert them. Return a dict.'''
        path = '%s: %s' % (self.rawloader.path, self._short_items)
        try:
            log.info('Converting raw data in %s ...' % path)
            return self._convert()
        except Exception:
            log.error('Failed to convert raw data in %s: %s.' % path,
                      exc_info=1)


class LayCore(BaseCore):
    '''
    Lay Core: cook pickled data from saver, save them to figinfo for plotter.

    Attributes
    ----------
    nitems: '?' or '+', default '?'
        '?', take only one group; '+', more than one
    itemspattern: list
        regular expressions for group, need scope name `(?P<section>group)`
    pckloader: pckloader object to get pickled data
    groups: str or list
        serial group name(s) of pickled data
    scope: str
        group name of figureinfos
    default_section: str
        default group name of figureinfos, if can't get from *groups*
    fignums: list
        figure nums(labels) in the *scope*
    '''
    __slots__ = ['_fignumslib']
    nitems = '?'
    itemspattern = ['^(?P<section>group)$']
    default_section = ''
    figinfoclasses = []

    @property
    def pckloader(self):
        return self.loader

    @property
    def groups(self):
        return self.items

    @property
    def scope(self):
        return self.section

    def __init__(self, pckloader, groups):
        if not is_pckloader(pckloader):
            raise ValueError("%s: Not a pckloader object!" % self.coreid)
        super(LayCore, self).__init__(pckloader, groups)
        self._fignumslib = {fnum: (fic, 0) for fic in self.figinfoclasses
                            for fnum in fic.figurenums}

    @classmethod
    def generate_cores(cls, pckloader):
        '''Return generated Core instances for *pckloader*.'''
        return super(LayCore, cls).generate_cores(
            pckloader, pckloader.datagroups)

    @classmethod
    def register_figinfoclasses(cls, *figinfoclses):
        '''Register FigInfo classes.'''
        for fic in figinfoclses:
            if fic in cls.figinfoclasses:
                continue
            if issubclass(fic, FigInfo):
                cls.figinfoclasses.append(fic)

    @property
    def fignums(self):
        return sorted(self._fignumslib.keys())

    def cook(self, fignum, figkwargs={}):
        '''
        Calculate pickled data. Return a :class:`FigInfo` instance.
        Use :meth:`see_figkwargs` to get
        :meth:`FigInfo.calculate` kwargs for the figinfo 'fignum'.
        '''
        fic, n = self._fignumslib.get(fignum, (None, 0))
        if not fic:
            log.error("%s: %s not found!" % (self.coreid, fignum))
            return
        figinfo = fic(fignum, self.scope, self.groups)
        log.info("Cook pck data for %s ..." % figinfo.fullnum)
        try:
            data = figinfo.get_data(self.pckloader)
        except Exception:
            log.error("%s: can't get data for %s!"
                      % (self.coreid, figinfo.fullnum), exc_info=1)
            return
        try:
            figinfo.calculate(data, **figkwargs)
        except Exception:
            log.error("%s: can't calculate data for %s!"
                      % (self.coreid, figinfo.fullnum), exc_info=1)
            return
        return figinfo

    def see_figkwargs(self, fignum, see='help'):
        '''
        help(figinfo.calculate) or figinfo.calculate.__doc__
        *see*: str, 'help', 'print' or 'return'
        '''
        fic, n = self._fignumslib.get(fignum, (None, 0))
        if not fic:
            log.error("%s: %s not found!" % (self.coreid, fignum))
            return
        if see == 'help':
            help(fic.calculate)
        elif see == 'print':
            print(fic.calculate.__doc__)
        elif see == 'return':
            return fic.calculate.__doc__
        else:
            pass


class FigInfo(object):
    '''
    Base Figure Information class.

    Attributes
    ----------
    fignum: str
        name(label) of figure
    scope: str
        group name of figure
    groups: str or list
        group name(s) of pck data
    srckey: list
        pck data keys needed in *groups*
    extrakey: list
        pck data keys needed not in *groups*
    calculation: dict
        results of cooked data
    layout: dict
        options used to get kwargs for :meth:`calculate`
    template: str
        name of 'bound template method of plotter'
    '''
    __slots__ = ['fignum', 'scope', 'groups', 'srckey', 'extrakey',
                 'calculation', 'layout', 'template']
    figurenums = []
    numpattern = '^.*$'

    def _pre_check_get(self, fignum, *names):
        '''
        1. check fignum;
        2. check *names* we needed in matched groupdict or not;
        3. return the groupdict.
        '''
        if fignum not in self.figurenums:
            raise ValueError("fignum %s not found in class %s!"
                             % (fignum, type(self).__name__))
        m = re.match(self.numpattern, fignum)
        if not m:
            raise ValueError("Can't get info of fignum %s in class %s!"
                             % (fignum, type(self).__name__))
        for k in names:
            if k not in m.groupdict():
                raise ValueError(
                    "Can't get '%s' info of fignum %s in class %s!"
                    % (k, fignum, type(self).__name__))
        return m.groupdict()

    def __init__(self, fignum, scope, groups, srckey, extrakey, template):
        self.fignum = fignum
        self.scope = scope
        self.groups = groups
        self.srckey = srckey
        self.extrakey = extrakey
        self.calculation = {}
        self.layout = {}
        self.template = template

    @property
    def fullnum(self):
        '''Return full label.'''
        return '%s/%s' % (self.scope, self.fignum)

    def get_data(self, pckloader):
        '''Use keys get pck data from *pckloader*, return a dict.'''
        result = {}
        if isinstance(self.groups, str):
            srckey = ['%s/%s' % (self.groups, k) for k in self.srckey]
            srcval = pckloader.get_many(*srckey)
            result.update(zip(srckey, srcval))
            result.update(zip(self.srckey, srcval))
        else:
            srckey = ['%s/%s' % (g, k)
                      for g in self.groups for k in self.srckey]
            result.update(zip(srckey, pckloader.get_many(*srckey)))
        result.update(zip(self.extrakey, pckloader.get_many(*self.extrakey)))
        return result

    def calculate(self, data, **kwargs):
        '''
        Use *data* get by keys, return calculation and layout.
        '''
        raise NotImplementedError()

    def _set_layout(self, key):
        '''Some common layout widgets.'''
        if key == 'xlim':
            xlim = self.calculation.get('xlim', False)
            if xlim:
                xlim = [float(xlim[0]), float(xlim[1])]
                self.layout['xlim'] = dict(
                    widget='FloatRangeSlider',
                    rangee=xlim + [min(0.1, (xlim[1] - xlim[0]) / 10)],
                    value=xlim,
                    description='xlim:')
        elif key == 'ylabel_rotation':
            self.layout['ylabel_rotation'] = dict(
                widget='IntSlider',
                rangee=(0, 360, 1),
                value=90,
                description='ylabel rotation:')
        elif key == 'hspace':
            self.layout['hspace'] = dict(
                widget='FloatSlider',
                rangee=(0, 0.5, 0.01),
                value=0.02,
                description='hspace:')

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


class LineFigInfo(FigInfo):
    '''Base class for figures use 'template_line_axstructs'.'''
    __slots__ = []

    def _get_srckey_extrakey(self, fignum):
        # groupdict = self._pre_check_get(fignum, '?')
        # return [], []
        raise NotImplementedError()

    def _get_data_LINE_title_etc(self, data):
        # return {'LINE': [], 'title': '', ...}
        raise NotImplementedError()

    def __init__(self, fignum, scope, groups):
        srckey, extrakey = self._get_srckey_extrakey(fignum)
        super(LineFigInfo, self).__init__(
            fignum, scope, groups, srckey, extrakey,
            'template_line_axstructs')

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *xlim*: (`left`, `right`)
            default [min(X), max(X)]
        *ylabel_rotation*: str or int
            default 'vertical'
        '''
        self.calculation.update(self._get_data_LINE_title_etc(data))
        if len(self.calculation['LINE']) == 0:
            log.warning("No data for %s." % self.fullnum)
        debug_kw = {}
        for k in ['xlim', 'ylabel_rotation']:
            if k in kwargs:
                self.calculation[k] = kwargs[k]
            if k in self.calculation:
                debug_kw[k] = self.calculation[k]
        log.debug("Some kwargs accepted: %s" % debug_kw)
        self._set_layout('xlim')
        self._set_layout('ylabel_rotation')


class SharexTwinxFigInfo(FigInfo):
    '''Base class for figures use 'template_sharex_twinx_axstructs'.'''
    __slots__ = []

    def _get_srckey_extrakey(self, fignum):
        # groupdict = self._pre_check_get(fignum, '?')
        # return [], []
        raise NotImplementedError()

    def _get_data_X_Y_title_etc(self, data):
        # return {'X': [], 'YINFO': [], 'title': '', ...}
        raise NotImplementedError()

    def __init__(self, fignum, scope, groups):
        srckey, extrakey = self._get_srckey_extrakey(fignum)
        super(SharexTwinxFigInfo, self).__init__(
            fignum, scope, groups, srckey, extrakey,
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
            log.warning("No data for %s." % self.fullnum)
        debug_kw = {}
        for k in ['hspace', 'xlim', 'ylabel_rotation']:
            if k in kwargs:
                self.calculation[k] = kwargs[k]
            if k in self.calculation:
                debug_kw[k] = self.calculation[k]
        log.debug("Some kwargs accepted: %s" % debug_kw)
        self._set_layout('hspace')
        self._set_layout('xlim')
        self._set_layout('ylabel_rotation')


class PcolorFigInfo(FigInfo):
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

    def __init__(self, fignum, scope, groups):
        srckey, extrakey = self._get_srckey_extrakey(fignum)
        super(PcolorFigInfo, self).__init__(
            fignum, scope, groups, srckey, extrakey,
            'template_pcolor_axstructs')

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
            log.warning("No data for %s." % self.fullnum)
        self.calculation['plot_method'] = self.default_plot_method
        debug_kw = {}
        for k in ['plot_method', 'plot_method_args',
                  'plot_method_kwargs', 'colorbar',
                  'grid_alpha', 'plot_surface_shadow']:
            if k in kwargs:
                self.calculation[k] = kwargs[k]
            if k in self.calculation:
                debug_kw[k] = self.calculation[k]
        log.debug("Some kwargs accepted: %s" % debug_kw)

        self.layout['plot_method'] = dict(
            widget='Dropdown',
            options=['pcolor', 'pcolormesh', 'contourf', 'plot_surface'],
            value=self.calculation['plot_method'],
            description='plot method:')
        self.layout['plot_surface_shadow'] = dict(
            widget='SelectMultiple',
            options=['x', 'y', 'z'],
            value=[],
            description='plot surface shadow:')
        self.layout['colorbar'] = dict(
            widget='Checkbox',
            value=True,
            description='colorbar')
        self.layout['grid_alpha'] = dict(
            widget='FloatSlider',
            rangee=(0, 1, 0.1),
            value=0.5,
            description='grid alpha:')
