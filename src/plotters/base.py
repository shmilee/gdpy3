# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains plotter base class.
'''

import os

from ..glogger import getGLogger

__all__ = ['BasePlotter']
log = getGLogger('P')


class BasePlotter(object):
    '''
    Plot data, create figures.

    Attributes
    ----------
    name: str
        plotter name
    style_available: list of str
        available styles for this plotter
    style: list of str
        list of default styles, valid elements can be in *style_available*
    figures: list
        list of figure nums(labels) created by this plotter
    example_axes: str
        example structure of an axes

    Notes
    -----
    The plotter instance is callable.
    instance() is equivalent to instance.create_figure().
    '''
    __slots__ = ['name', 'example_axes', '_style', '_figureslib']
    style_available = []

    def __init__(self, name, style=[], example_axes=None):
        self.name = name
        self.style = style
        self.example_axes = example_axes
        self._figureslib = {}

    def _get_style(self):
        return self._style

    def _set_style(self, style):
        self._style = []
        for sty in style:
            if self._check_style(sty):
                self._style.append(sty)
            else:
                log.warn("Ignore style '%s': %s" % (sty, 'not available'))

    style = property(_get_style, _set_style)

    def _check_style(self, sty):
        '''Check single style *sty* available or not.'''
        # return sty in self.style_available
        raise NotImplementedError()

    def check_style(self, style):
        '''
        Check the *style* available or not.
        Accept a list. Return available style list.
        '''
        return [sty for sty in style if self._check_style(sty)]

    def _filter_style(self, sty):
        '''Change *sty* str to absolute path.'''
        raise NotImplementedError()

    def filter_style(self, style):
        '''
        Filter the *style* list before use it.
        If the str starts with 'gdpy3-', change it to absolute path.
        Accept a list. Return a list.
        '''
        newstyle = []
        for sty in style:
            if isinstance(sty, str) and sty.startswith('gdpy3-'):
                newstyle.append(self._filter_style(sty))
            else:
                newstyle.append(sty)
        return newstyle

    def _param_from_style(self, param):
        raise NotImplementedError()

    def param_from_style(self, param):
        '''
        Return *param* value from self.style
        '''
        return self._param_from_style(param)

    @property
    def figures(self):
        return list(self._figureslib.keys())

    def _add_axes(self, fig, data, layout, axstyle):
        '''Add axes to figure.'''
        raise NotImplementedError()

    def add_axes(self, fig, axstructure):
        '''
        Add axes to figure *fig*.

        Parameters
        ----------
        fig: figure object
        axstructure: dict, structure of an axes
        '''
        # simple check
        if not isinstance(axstructure, dict):
            log.error("AxesStructure must be dict. Not %s. Ignore this axes."
                      % type(axstructure))
            return
        check_pass = True
        for k in ('data', 'layout'):
            if k not in axstructure:
                check_pass = False
                log.error("AxesStructure must contain key: '%s'!" % k)
            if not isinstance(axstructure[k], list):
                check_pass = False
                log.error("AxesStructure[%s] must be list. Not %s."
                          % (k, type(axstructure[k])))
        layout = axstructure['layout']
        if not(isinstance(layout, list) and len(layout) == 2):
            check_pass = False
            log.error("AxesStructure['layout'] must have 2 elements.")
        if not check_pass:
            log.error("Ignore this axes.")
            return
        # check axstyle
        axstyle = []
        if 'axstyle' in axstructure:
            if isinstance(axstructure['axstyle'], list):
                axstyle = self.check_style(axstructure['axstyle'])
            else:
                log.error("AxesStructure['axstyle'] must be list. Not %s. "
                          % type(axstructure['axstyle'])
                          + "Ignore 'axstyle' setting!")
        log.ddebug("Axes Style: %s" % str(axstyle))
        return self._add_axes(fig, axstructure['data'], layout, axstyle)

    def _create_figure(self, num, axesstructures, figstyle):
        '''Create a figure object.'''
        raise NotImplementedError()

    def create_figure(self, num, *axesstructures, add_style=None, replace=True):
        '''
        Use *axesstructures* to create a figure object.

        Parameters
        ----------
        num: integer or string
            figure's number or figlabel, do not use 'all'
        axestructures: list of AxesStructure dict
        add_style: list of style, default: none
            more style for this figure
        replace: bool
            if figure *num* was created, replace it or just return it

        Notes
        -----
        1. Value of *axesstructures* is a list of `AxesStructure`.
           Each `AxesStructure` is a dict which has 3 keys:
           'data', 'layout' and 'axstyle'. 'axstyle' is optional.
        2. Value of 'data' is a list of plot items. items[0] is an order
           number. items[1] is a name of plot method. It can be any plot
           function supported by the backend. items[2] is a tuple of args
           for plot function. items[3] is a dict of kwargs for plot function.
        3. Value of 'layout' is a list of two elements. layout[0] is
           position. layout[1] is a dict of kwargs.
        4. Value of 'axstyle' is a list of style. The axstyle will only
           affect this axes except others.
        '''
        if num in self._figureslib:
            if replace:
                log.warn("Figure %s was created. Closing it!" % num)
                self.close_figure(num)
            else:
                return self.get_figure(num)
        figstyle = self.style.copy()
        if add_style and isinstance(add_style, list):
            figstyle.extend(self.check_style(add_style))
        log.ddebug("Figure Style: %s" % str(figstyle))
        figure = self._create_figure(num, axesstructures, figstyle)
        if figure:
            self._figureslib[num] = figure
            return figure
        else:
            return None

    def __call__(self, *args, **kwargs):
        '''callable'''
        return self.create_figure(*args, **kwargs)

    def get_figure(self, num):
        '''
        Return figure *num* if already created.
        '''
        if num in self._figureslib:
            return self._figureslib[num]
        else:
            return None

    def _show_figure(self, fig):
        '''Display figure object *fig*.'''
        raise NotImplementedError()

    def show_figure(self, num):
        '''
        Display figure *num* if already created.
        '''
        if num in self._figureslib:
            return self._show_figure(self._figureslib[num])
        else:
            log.error("Figure %s is not created!" % num)

    def _close_figure(self, fig):
        '''Close figure object *fig*.'''
        raise NotImplementedError()

    def close_figure(self, num):
        '''
        Close figure *num* if already created.
        ``close_figure('all')`` closes all the figure
        '''
        if num == 'all':
            for n in tuple(self._figureslib.keys()):
                fig = self._figureslib.pop(n, None)
                if fig:
                    self._close_figure(fig)
                del fig
        elif num in self._figureslib:
            fig = self._figureslib.pop(num, None)
            if fig:
                self._close_figure(fig)
            del fig

    def _save_figure(self, fig, fpath, **kwargs):
        '''Save figure object *fig*.'''
        raise NotImplementedError()

    def save_figure(self, num, fpath, **kwargs):
        '''
        Save figure *num* to *fpath* if already created.
        '''
        if num in self._figureslib:
            log.info("Save figure to %s ..." % fpath)
            self._save_figure(self._figureslib[num], fpath, **kwargs)
        else:
            log.error("Figure %s is not created!" % num)
