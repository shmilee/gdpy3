# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
This is the subpackage ``savers`` of gdpy3.
``PckSaver``, get by :func:`get_pcksaver`, has attributes
:attr:`base.BasePckSaver.path``,
:attr:`base.BasePckSaver.status`
and methods
:meth:`base.BasePckSaver.iopen`,
:meth:`base.BasePckSaver.write`,
:meth:`base.BasePckSaver.close`,
:meth:`base.BasePckSaver.get_store`.
'''

import os

from ..glogger import getGLogger
from . import base

__all__ = ['get_pcksaver', 'is_pcksaver']
log = getGLogger('S')
pcksaver_names = ['CachePckSaver', 'NpzPckSaver', 'Hdf5PckSaver']
pcksaver_types = ['.cache', '.npz', '.hdf5']


def get_pcksaver(path):
    '''
    Given a saver path, return a saver instance.
    Raises ValueError if path type not supported.

    Notes
    -----
    *path* types:
    1. '.cache', dict cache name
    2. '.npz', file path
    3. '.hdf5', file path
    '''
    path = str(path)
    ext = os.path.splitext(path)[1]
    if ext not in pcksaver_types:
        log.warning("PckSaver type must be in '%s'! Use default '.npz'."
                    % ', '.join(pcksaver_types))
        ext = '.npz'
        path = path + ext

    if ext == '.cache':
        from .cachepck import CachePckSaver
        saver = CachePckSaver(path)
    elif ext == '.npz':
        from .npzpck import NpzPckSaver
        saver = NpzPckSaver(path)
    elif ext == '.hdf5':
        from .hdf5pck import Hdf5PckSaver
        saver = Hdf5PckSaver(path)
    else:
        raise ValueError('Save ha? Who am I? Why am I here?')
    return saver


def is_pcksaver(obj):
    '''
    Return True if obj is a pickled saver instance, else return False.
    '''
    return isinstance(obj, base.BasePckSaver)
