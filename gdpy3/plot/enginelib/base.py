# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Defines :class:`.Engine`
'''

import types

__all__ = ['Engine']


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
    style_param: function
        get param value from Figure style
    clear: function
        clear the entire figure
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

    @property
    def style_available(self):
        return self._style_available

    @style_available.setter
    def style_available(self, styles):
        if not isinstance(styles, list):
            raise ValueError("'style_available' must be list!")
        self._style_available = styles

    @property
    def style_param(self):
        return self._style_param

    @style_param.setter
    def style_param(self, function):
        if not isinstance(function, types.FunctionType):
            raise ValueError("'style_param' must be function!")
        self._style_param = function

    @property
    def clear(self):
        return self._clear

    @clear.setter
    def clear(self, function):
        if not isinstance(function, types.FunctionType):
            raise ValueError("'clear' must be function!")
        self._clear = function
