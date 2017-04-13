# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    This is the subpackage ``read`` of package gdpy3.
'''

__all__ = ['readhdf5', 'readmat', 'readnpz', 'readraw']

import os


def read(path, **kwargs):
    '''Read .npz, .hdf5 or .mat file
    Return a dictionary-like object.

    Parameters
    ----------
    path: str
        path of the .npz, .hdf5, .mat file to open
        or path of the directory of GTC .out files
    kwargs: other parameters for gdpy3.read.Readraw
        ``description``, ``version``, ``additionalpats``
        ``salt``
    '''

    if os.path.isdir(path):
        from . import readraw
        dictobj = readraw.ReadRaw(path, **kwargs)
    elif os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            from . import readnpz
            dictobj = readnpz.ReadNpz(path)
        elif ext == '.hdf5':
            from . import readhdf5
            dictobj = readhdf5.ReadHdf5(path)
        elif ext == '.mat':
            from . import readmat
            dictobj = readmat.ReadMat(path)
        else:
            raise ValueError("Unsupported file type: '%s'!" % path)
    else:
        raise IOError("Can't find path '%s'!" % path)
