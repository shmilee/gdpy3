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

from . import processor
from .lib import Processor_Names, Processor_Alias, find_Processor

__all__ = ['get_processor', 'is_processor']


def get_processor(path=None, name='GTCv3', parallel='multiprocess', **kwargs):
    '''
    Generate a processor instance of *name*,
    then pick up raw data or converted data in *path*.
    If no *path* given, return processor class of *name*.

    Parameters
    ----------
    path: str
        data path
    name: str
        valid names :data:`Processor_Names` or :data:`Processor_Alias`
        default 'GTCv3'
    parallel: str
        'off', 'multiprocess' or 'mpi4py', default 'multiprocess'
    kwargs: parameters passed to :meth:`Processor.__init__`
    '''
    if name in Processor_Names:
        pass
    elif name in Processor_Alias:
        name = Processor_Alias[name]
    else:
        raise ValueError(
            'Invalid name: "%s"! Did you mean one of "%s" or alias "%s"?'
            % (name, ', '.join(Processor_Names), ', '.join(Processor_Alias)))
    gdpcls = find_Processor(name, parallel)
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
