# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Defines :class:`.Engine`
'''

import types

from ...glogger import getGLogger

__all__ = ['Engine']

log = getGLogger('P')


class Engine(object):
    '''
    engine class

    Attributes
    ----------
    name: str
    figure_factory: function
        Use FigureStructure to create a Figure instance
    style_available: list
        available styles for Figure in this engine
    show: function
        display the figure
    close: function
        close the entire figure
    tool: dict
        useful functions: key, val = name, function

    Notes
    -----
    The Engine instance is callable.
    instance() is equivalent to instance.figure_factory().
    '''

    def __init__(self, name):
        self.name = name

    @property
    def figure_factory(self):
        return self._figure_factory

    @figure_factory.setter
    def figure_factory(self, function):
        if not isinstance(function, types.FunctionType):
            raise ValueError("'figure_factory' must be function!")
        self._figure_factory = function

    def __call__(self, *args, **kwargs):
        return self._figure_factory(*args, **kwargs)

    @property
    def style_available(self):
        return self._style_available

    @style_available.setter
    def style_available(self, styles):
        if not isinstance(styles, list):
            raise ValueError("'style_available' must be list!")
        self._style_available = styles

    @property
    def show(self):
        return self._show

    @show.setter
    def show(self, function):
        if not isinstance(function, types.FunctionType):
            raise ValueError("'show' must be function!")
        self._show = function

    @property
    def close(self):
        return self._close

    @close.setter
    def close(self, function):
        if not isinstance(function, types.FunctionType):
            raise ValueError("'close' must be function!")
        self._close = function

    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, tols):
        if not isinstance(tols, dict):
            raise ValueError("'tool' must be dict!")
        self._tool = {}
        for key, val in tols.items():
            if not isinstance(val, types.FunctionType):
                log.error("'tool[%s]' must be function!" % key)
            else:
                self._tool[key] = val
