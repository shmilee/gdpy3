# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import matplotlib.style.core as score
import gdpy3.read as gdr

__all__ = ['is_dictobj', 'in_dictobj',
           'mplstyle_available', 'mplstylelib',
           'colorbar_revise_function',
           ]

log = logging.getLogger('gdp')


# 1. dictobj

def is_dictobj(dictobj):
    '''
    Check if *dictobj* is a instance of :class:`gdpy3.read.readnpz.ReadNpz`.
    '''
    if isinstance(dictobj, gdr.ReadNpz):
        return True
    else:
        return False


def in_dictobj(dictobj, *keys):
    '''
    Check if all the *keys* are in *dictobj*.
    '''
    result = True
    for key in keys:
        if key not in dictobj.datakeys:
            log.warn("Key '%s' not in %s!" % (key, dictobj.file))
            result = False
    return result


# 2. mplstyle

__mplstylepath = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'mpl-stylelib')
mplstyle_available = score.available


def __update_gdpy3_mplstyle_library():
    global mplstyle_available
    for path, name in score.iter_style_files(__mplstylepath):
        mplstyle_available.append(name)
__update_gdpy3_mplstyle_library()


def mplstylelib(style=None):
    '''
    Filter the *style*.
    If the name starts with 'gdpy3-', change it to absolute path.
    Return str of mplstyle.
    '''
    if style not in mplstyle_available:
        log.warn("'%s' not found in the style library! Use 'default'!" % style)
        return 'default'
    # start with 'gdpy3-'
    if style.startswith('gdpy3-'):
        return os.path.join(__mplstylepath, style + '.mplstyle')
    # score.available
    return style


# 3. FigureStructure, revise function

def colorbar_revise_function(label, grid_alpha=0.3, **kwargs):
    '''
    Return a colorbar `revise function` for FigureStructure.

    Parameters
    ----------
    label: label of mappable which the colorbar applies
    keyword arguments: kwargs passed to colorbar
        *cax*, *ax*, *fraction*, *pad*, *ticks*, etc.
    '''
    def revise_func(figure, axes):
        axes.grid(alpha=grid_alpha)
        mappable = None
        for child in axes.get_children():
            if child.get_label() == label:
                mappable = child
        if mappable:
            figure.colorbar(mappable, **kwargs)
    return revise_func
