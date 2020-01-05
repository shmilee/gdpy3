# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
This is the subpackage ``visplters`` of gdpy3.
``visplter``, get by :func:`get_visplter`, has attributes
:attr:`BaseVisplter.style_available`,
:attr:`BaseVisplter.example_axes`,
:attr:`BaseVisplter.template_available` etc.
and has methods
:meth:`BaseVisplter.create_figure`,
:meth:`BaseVisplter.get_figure`,
:meth:`BaseVisplter.show_figure`,
:meth:`BaseVisplter.close_figure`,
:meth:`BaseVisplter.save_figure` etc.
'''

from . import base

__all__ = ['get_visplter']

visplter_names = ['MatplotlibVisplter']
visplter_types = ['mpl::']


def get_visplter(name):
    '''
    Given a str *name*, return a visplter instance.

    The name must start with one type of ``visplter_types``,
    for example 'mpl::any-string-here'.
    Raises ValueError if name invalid or type not supported.

    Notes
    -----
    visplter types:
    1. 'mpl::' for :class:`mplvisplter.MatplotlibVisplter`.
    '''
    sep = '::'
    name = str(name)
    if name.find(sep) > 0:
        ptype = name.split(sep=sep)[0] + sep
        if ptype == 'mpl::':
            from .mplvisplter import MatplotlibVisplter
            visplter = MatplotlibVisplter(name)
        else:
            raise ValueError('Unsupported visplter type: "%s"! '
                             'Did you mean one of: "%s"?'
                             % (ptype, ', '.join(visplter_types)))
    else:
        raise ValueError('Invalid name: "%s"! '
                         'Name must start with one type of: "%s".'
                         % (name, ', '.join(visplter_types)))
    return visplter


def is_visplter(obj):
    '''
    Return True if obj is a visplter instance, else return False.
    '''
    return isinstance(obj, base.BaseVisplter)
