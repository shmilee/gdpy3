# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os

from ..glogger import getGLogger
from .npzfile import NpzFileLoader
from .base import BaseFileLoader

log = getGLogger('L')
fileloader_names = ['NpzFileLoader', 'Hdf5FileLoader']
fileloader_filetypes = ['.npz', '.hdf5']

def get_fileloader(path):
    '''
    Given a file path, return a loader instance.
    Raises IOError if path not found, ValueError if filetype not supported.
    '''

    if os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            loader = NpzFileLoader(path)
        elif ext == '.hdf5':
            from .hdf5file import Hdf5FileLoader
            loader = Hdf5FileLoader(path)
        else:
            raise ValueError('Unsupported Filetype: "%s"! Did you mean one of: "%s"?' % (ext, ', '.join(fileloader_filetypes)))
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader
