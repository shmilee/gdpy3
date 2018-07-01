# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
This is the subpackage ``processors`` of gdpy3.
``processor``, get by :func:`get_processor`, has attributes
:attr:`processor.Processor.name`,
:attr:`processor.Processor.rawloader`,
:attr:`processor.Processor.pcksaver`,
:attr:`processor.Processor.pckloader`,
:attr:`processor.Processor.plotter`,
:attr:`processor.Processor.digcores`,
:attr:`processor.Processor.laycores`,
:attr:`processor.Processor.layout`,
:attr:`processor.Processor.figurelabels`,
:attr:`processor.Processor.figurelabels_cooked`
and methods
:meth:`processor.Processor.set_prefer_pcksaver`,
:meth:`processor.Processor.convert`,
:meth:`processor.Processor.get`,
:meth:`processor.Processor.plot`,
:meth:`processor.Processor.see_figkwargs`,
:meth:`processor.Processor.refind`,
:meth:`processor.Processor.pick`.
'''

import inspect
import importlib

from . import processor

__all__ = ['get_processor', 'is_processor']

_processorlib = {
    'GTCProcessorV110922': 'GTC',
    'GTCSHMILEERZF110922': 'GTC.SHMILEE',
}
processor_names = sorted(_processorlib.keys())
processor_types = sorted(set(_processorlib.values()))
alias_processor_names = {
    'GTCV110922': 'GTCProcessorV110922',
    'GTC110922': 'GTCProcessorV110922',
    'GSRZF': 'GTCSHMILEERZF110922',
}


def get_processor(name, **kwargs):
    '''
    Given a str *name*, return a processor instance.

    Notes
    -----
    1. valid processor names:
       :data:`processor_names`, :data:`alias_processor_names`.
    2. Raises ValueError if name invalid.
    3. *kwargs*: parameters passed to :meth:`processor.Processor.pick`.
    '''
    if name in processor_names:
        pname = name
    elif name in alias_processor_names:
        pname = alias_processor_names[name]
    else:
        raise ValueError(
            'Invalid name: "%s"! Did you mean one of "%s" or alias "%s"?'
            % (name, ', '.join(processor_names),
               ', '.join(alias_processor_names)))
    ptype = _processorlib.get(pname)
    ppack = importlib.import_module('.%s' % ptype, package=__name__)
    gdp = getattr(ppack, pname)()
    if kwargs:
        sig = inspect.signature(gdp.pick)
        for k in list(kwargs.keys()):
            if k not in sig.parameters:
                remove = kwargs.pop(k, None)
        if kwargs:
            gdp.pick(**kwargs)
    return gdp


def is_processor(obj):
    '''
    Return True if obj is a processor instance, else return False.
    '''
    return isinstance(obj, processor.Processor)
