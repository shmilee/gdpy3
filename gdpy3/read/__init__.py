# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
    This is the subpackage ``read`` of package gdpy3.
'''

import os

__all__ = ['read', 'readnpz', 'readhdf5', 'readraw']


def read(path, **kwargs):
    '''Read .npz, .hdf5 file or original data.
    Return a dictionary-like object.

    Parameters
    ----------
    path: str
        path of the .npz, .hdf5 file to open
        or path of the directory of GTC .out files
    kwargs: other parameters for gdpy3.read.readraw
        ``salt``, ``extension``, ``overwrite``,
        ``description``, ``version``, ``additionalpats``
    '''

    if os.path.isdir(path):
        from .readraw import ReadRaw
        dictobj = ReadRaw(path, **kwargs)
    elif os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            from .readnpz import ReadNpz
            dictobj = ReadNpz(path)
        elif ext == '.hdf5':
            from .readhdf5 import ReadHdf5
            dictobj = ReadHdf5(path)
        else:
            raise ValueError("Unsupported file type: '%s'!" % path)
    else:
        raise IOError("Can't find path '%s'!" % path)

    return dictobj
