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

Processor_Lib = {}
Processor_Names = []
Processor_Alias = {}


def register_processor(name, module_relative_path, alias=None):
    '''
    Add processor *name* module and its alias in *Processor_Lib*.
    Processor_Lib[name] = (module_relative_path, {class_cache_dict})
    '''
    if name not in Processor_Lib:
        Processor_Lib[name] = (module_relative_path, {})
        # update names
        Processor_Names.append(name)
        Processor_Names.sort()
        if alias:
            Processor_Alias[alias] = name


register_processor('GTCv3', '..GTCv3', 'G3')
register_processor('GTCv4', '..GTCv4', 'G4')


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
        pname = name
    elif name in Processor_Alias:
        pname = Processor_Alias[name]
    else:
        raise ValueError(
            'Invalid name: "%s"! Did you mean one of "%s" or alias "%s"?'
            % (name, ', '.join(Processor_Names), ', '.join(Processor_Alias)))
    module_relative, class_cache = Processor_Lib.get(pname)
    if parallel in class_cache:
        gdpcls = class_cache[parallel]
    else:
        ppack = importlib.import_module(module_relative, package=__name__)
        get_gdpcls = getattr(ppack, 'get_%s' % pname)
        # which Base
        if parallel == 'off':
            from .processor import Processor as Base
        elif parallel == 'multiprocess':
            from .multiprocessor import MultiProcessor as Base
        elif parallel == 'mpi4py':
            raise ValueError('TODO %s' % parallel)
        else:
            raise ValueError('Unsupported parallel-lib: %s' % parallel)
        gdpcls = get_gdpcls(Base)
        Processor_Lib[name][1][parallel] = gdpcls
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
