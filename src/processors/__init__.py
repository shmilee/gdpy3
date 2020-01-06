# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
This is the subpackage ``processors`` of gdpy3.
``processor``, get by :func:`get_processor`, has attributes
:attr:`Processor.rawloader`,
:attr:`Processor.converters`,
:attr:`Processor.pckloader`,
:attr:`Processor.diggers`,
:attr:`Processor.availablelabels`,
:attr:`Processor.diggedlabels` etc.
and has methods
:meth:`Processor.convert`,
:meth:`Processor.dig`,
:meth:`Processor.dig_doc`,
:meth:`Processor.export`,
:meth:`Processor.export_doc`,
:meth:`Processor.refind` etc.
'''

import inspect
import importlib

from . import processor

__all__ = ['get_processor', 'is_processor']

_processorlib = {
    'GTCv3': '..GTCv3',
    'GTCv4': '..GTCv4',
}
processor_names = sorted(_processorlib.keys())
alias_names = {
    'G3': 'GTCv3',
    'G4': 'GTCv4',
}


def get_processor(path=None, name='GTCv3', **kwargs):
    '''
    Generate a processor instance of *name*,
    then pick up raw data or converted data in *path*.
    If no *path* given, return processor class of *name*.

    Parameters
    ----------
    path: str
        data path
    name: str
        valid processor names :data:`processor_names` or :data:`alias_names`
        default 'GTCv3'
    kwargs: parameters passed to :meth:`Processor.__init__`
    '''
    if name in processor_names:
        pname = name
    elif name in alias_names:
        pname = alias_names[name]
    else:
        raise ValueError(
            'Invalid name: "%s"! Did you mean one of "%s" or alias "%s"?'
            % (name, ', '.join(processor_names), ', '.join(alias_names)))
    module_relative = _processorlib.get(pname)
    ppack = importlib.import_module(module_relative, package=__name__)
    gdpcls = getattr(ppack, pname)
    if path:
        if kwargs:
            sig = inspect.signature(gdpcls)
            for k in list(kwargs.keys()):
                if k not in sig.parameters:
                    remove = kwargs.pop(k, None)
        return gdpcls(path, **kwargs)
    else:
        return gdpcls


def is_processor(obj):
    '''
    Return True if obj is a processor instance, else return False.
    '''
    return isinstance(obj, processor.Processor)
