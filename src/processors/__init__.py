# -*- coding: utf-8 -*-

# Copyright (c) 2018-2022 shmilee

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

import re
import os
import inspect

from . import processor
from .lib import Processor_Names, Processor_Alias, find_Processor
from .lib import Processor_Lib, __userbase__

__all__ = ['get_processor', 'is_processor', 'copy_processor_files']
_sys_Processor_Names = [
    n for n in Processor_Names if Processor_Lib[n][1] == '$sys']


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


def copy_processor_files(name):
    '''
    Copy processor .py files to user's directory and edit import part.

    Parameters
    ----------
    name: str
        valid names in :data:`Processor_Names`, and its loc=='$sys'
    '''
    if name not in _sys_Processor_Names:
        raise ValueError('Invalid name: "%s"! Did you mean one of "%s"?'
                         % (name, ', '.join(_sys_Processor_Names)))
    path = os.path.join(__userbase__, 'user_processors')  # user path
    if not os.path.isdir(path):
        os.makedirs(path)
    newloc = os.path.join(path, name)
    if os.path.exists(newloc):
        raise FileExistsError("%s is already in %s!" % (name, path))
    os.mkdir(newloc)
    join = os.path.join
    path = os.path.dirname(os.path.dirname(__file__))  # sys path
    path = join(path, name)
    for py in os.listdir(path):
        if not py.endswith('.py'):
            continue
        src = join(path, py)
        dst = join(newloc, py)
        with open(src, "r", encoding="utf-8") as f1, \
                open(dst, "w", encoding="utf-8") as f2:
            for li in f1:
                if li.startswith('from . '):
                    li = li.replace('from . ', 'from gdpy3.%s ' % name)
                elif re.match('^from .[a-zA-Z_]\w*', li):
                    li = li.replace('from .', 'from gdpy3.%s.' % name)
                elif li.startswith('from .. '):
                    li = li.replace('from .. ', 'from gdpy3 ')
                elif re.match('^from ..[a-zA-Z_]\w*', li):
                    li = li.replace('from ..', 'from gdpy3.')
                f2.write(li)
    dst = join(newloc, '_example.py')
    with open(dst, "w", encoding="utf-8") as f:
        f.write('# -*- coding: utf-8 -*-\n\n')
        f.write('# Copyright (c) 20xx xxxx\n\n')
        f.write('import numpy\n'
                'from gdpy3 import tools\n'
                'from gdpy3.cores.converter import Converter, clog\n'
                'from gdpy3.cores.digger import Digger, dlog\n\n'
                "_all_Converters = ['ExampleConverter']\n"
                "_all_Diggers = ['ExampleDigger']\n"
                '__all__ = _all_Converters + _all_Diggers\n\n\n'
                'class ExampleConverter(Converter):\n'
                '    pass\n\n\n'
                'class ExampleDigger(Digger):\n'
                '    pass\n')
