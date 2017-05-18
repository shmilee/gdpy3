# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
History figures
-------------------

This module needs history diagnosis data in group 'history' get by gdr.
'''

import os
import logging
import numpy as np
from gdpy3.plot import tools

__all__ = ['Group' 'Figures' 'get_figurestructure']

log = logging.getLogger('gdp')


__FigInfo = {
}
__keysgrp = 'history/'
__paragrp = 'gtcout/'

Group = 'history'
Figures = tuple(__FigInfo.keys())


def get_figurestructure(dictobj, name, figurestyle=[]):
    '''
    Get the FigureStructure by name.
    Return FigureStructure and calculation results.

    Parameters
    ----------
    dictobj: a dictionary-like object
        instance of :class:`gdpy3.read.readnpz.ReadNpz`, etc.
    name: figure name
    figurestyle: a list of mplstyles
    '''

    # check name
    if name not in Figures:
        log.error("'%s' is not in the '%s' Figures!" % (name, Group))
        return None, None
    # check key, get axdata #TODO
    Zkey = __keysgrp + __FigInfo[name]['key']
    tstep = __paragrp + 'tstep'
    ndiag = __paragrp + 'ndiag'
    if tools.in_dictobj(dictobj, Zkey, tstep, ndiag):
        Z = dictobj[Zkey]
        if Z.size == 0:
            log.debug("No data for Figure '%s/%s'." % (Group, name))
            return None, None
        else:
            tunit = dictobj[tstep] * dictobj[ndiag]
    else:
        return None, None

    log.debug("Get FigureStructure '%s/%s' ..." % (Group, name))
    figurestructure = {
        'Style': figurestyle,
        'AxesStructures': [] #TODO
    }
    calculation = None
    return figurestructure, calculation
