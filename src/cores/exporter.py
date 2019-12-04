#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Contains Exporter core class.
'''
from .base import BaseCore, AppendDocstringMeta
from ..glogger import getGLogger

__all__ = ['TmplLoader',
           'ContourfExporter', 'LineExporter',
           'SharexTwinxExporter', 'Z111pExporter']
elog = getGLogger('E')


class Exporter(BaseCore, metaclass=AppendDocstringMeta):
    '''
    Assemble dig results, options and template.


    Attributes
    ----------
    template: template name, like 'tmpl-line'
    '''
    __slots__ = []
    nitems = '?'
    visoptions = {}

    @property
    def template(self):
        return self.items[0]

    def fmt_export(self, data, fmt):
        '''Convert *data* format from dict to *fmt*.'''
        if fmt == 'dict':
            return data
        elif fmt == 'pickle':
            import pickle
            return pickle.dumps(data)
        elif fmt == 'json':
            import json
            import numpy as np

            class NpEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, np.integer):
                        return int(obj)
                    elif isinstance(obj, np.floating):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    else:
                        return super(NpEncoder, self).default(obj)
            return json.dumps(data, cls=NpEncoder)
        else:
            pass

    def export(self, results, fmt='dict', **kwargs):
        '''
        Export results, template name for plotter.

        Parameters
        ----------
        fmt: format 'dict', 'pickle' or 'json'
        '''
        results, tmpl = self._export(results, kwargs)
        return self.fmt_export(dict(results=results, template=tmpl), fmt)

    def _export(self, results, kwargs):
        '''Return results, template name.'''
        raise NotImplementedError()

    def export_options(self, digoptions, fmt='dict'):
        '''
        Export dig options and plotter(vis) template options for GUI widgets.

        Parameters
        ----------
        fmt: format 'dict', 'pickle' or 'json'
        '''
        return self.fmt_export(
            dict(digoptions=digoptions,
                 visoptions=self.visoptions),
            fmt)


class TmplLoader(object):
    path = 'tmpl/lodaer'
    templates = [
        'tmpl-contourf',
        'tmpl-line',
        'tmpl-line3d',
        'tmpl-sharextwinx',
        'tmpl-z111p',
    ]


class ContourfExporter(Exporter):
    '''
    For :meth:`plotter.template_contourf_axstructs`.

    Template
    --------
    .. code::

             title
           +----------+ +-+
    ylabel | contourf | |-|colorbar
           +----------+ +-+
             xlabel
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>tmpl)-contourf$']
    visoptions = dict(
        plot_method=dict(
            widget='Dropdown',
            options=['contourf', 'pcolor', 'pcolormesh', 'plot_surface'],
            value='contourf',
            description='plot method:'),
        colorbar=dict(
            widget='Checkbox',
            value=True,
            description='colorbar'),
        grid_alpha=dict(
            widget='FloatSlider',
            rangee=(0, 1, 0.1),
            value=0.5,
            description='grid alpha:'),
        plot_surface_shadow=dict(
            widget='SelectMultiple',
            options=['x', 'y', 'z'],
            value=[],
            description='plot surface shadow:')
    )

    def _export(self, results, kwargs):
        '''
        kwargs
        ------
        kwargs passed on to :meth:`plotter.template_contourf_axstructs`
        *plot_method*, *plot_method_args*, *plot_method_kwargs*,
        *colorbar*, *grid_alpha*, *plot_surface_shadow*
        '''
        results['plot_method'] = 'contourf'
        debug_kw = {}
        for k in ['plot_method', 'plot_method_args',
                  'plot_method_kwargs', 'colorbar',
                  'grid_alpha', 'plot_surface_shadow']:
            if k in kwargs:
                results[k] = kwargs[k]
            if k in results:
                debug_kw[k] = results[k]
        elog.debug("Some template contourf kwargs: %s" % debug_kw)
        return results, 'template_contourf_axstructs'


class LineExporter(Exporter):
    '''
    For :meth:`plotter.template_line_axstructs`.

    Template
    --------
    .. code::

             title
           +--------+
    ylabel | Line2D |
           +--------+
             xlabel
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>tmpl)-line$']
    visoptions = dict(
        ylabel_rotation=dict(
            widget='IntSlider',
            rangee=(0, 360, 1),
            value=90,
            description='ylabel rotation:')
    )

    def _export(self, results, kwargs):
        '''
        kwargs
        ------
        kwargs passed on to :meth:`plotter.template_line_axstructs`
        *ylabel_rotation*: str or int
            default 'vertical'
        '''
        debug_kw = {}
        for k in ['ylabel_rotation']:
            if k in kwargs:
                results[k] = kwargs[k]
            if k in results:
                debug_kw[k] = results[k]
        elog.debug("Some template line kwargs: %s" % debug_kw)
        return results, 'template_line_axstructs'


class SharexTwinxExporter(Exporter):
    '''
    For :meth:`plotter.template_sharex_twinx_axstructs`.

    Template
    --------
    .. code::

             title
           +--------+
    ylabel | axes 1 | ylabel
           +--------+
    ylabel | axes 2 | ylabel
           +--------+
             xlabel
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>tmpl)-sharextwinx$']
    visoptions = dict(
        hspace=dict(
            widget='FloatSlider',
            rangee=(0, 0.5, 0.01),
            value=0.02,
            description='hspace:'),
        ylabel_rotation=dict(
            widget='IntSlider',
            rangee=(0, 360, 1),
            value=90,
            description='ylabel rotation:')
    )

    def _export(self, results, kwargs):
        '''
        kwargs
        ------
        kwargs passed on to :meth:`plotter.template_sharex_twinx_axstructs`
        *hspace*: float
            subplot.hspace, default 0.02
        *ylabel_rotation*: str or int
            default 'vertical'
        '''
        debug_kw = {}
        for k in ['hspace', 'ylabel_rotation']:
            if k in kwargs:
                results[k] = kwargs[k]
            if k in results:
                debug_kw[k] = results[k]
        elog.debug("Some template sharextwinx kwargs: %s" % debug_kw)
        return results, 'template_sharex_twinx_axstructs'


class Z111pExporter(Exporter):
    '''
    For :meth:`plotter.template_z111p_axstructs`.
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>tmpl)-z111p$']

    def _export(self, results, kwargs):
        return results
