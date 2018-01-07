# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import tarfile

from ..glogger import getGLogger
from .base import BaseRawLoader, BaseFileLoader
from .dirraw import DirRawLoader
from .tarraw import TarRawLoader
from .npzfile import NpzFileLoader

__all__ = ['get_rawloader', 'is_rawloader', 'get_fileloader', 'is_fileloader']
log = getGLogger('L')
rawloader_names = ['DirRawLoader', 'TarRawLoader']
fileloader_names = ['NpzFileLoader', 'Hdf5FileLoader']
fileloader_filetypes = ['.npz', '.hdf5']


def get_rawloader(path, filenames_filter=None):
    '''
    Given a path, return a raw loader instance.
    Raises IOError if path not found, ValueError if filetype not supported.
    '''

    if os.path.isdir(path):
        loader = DirRawLoader(path, filenames_filter=filenames_filter)
    elif os.path.isfile(path):
        if tarfile.is_tarfile(path):
            loader = TarRawLoader(path, filenames_filter=filenames_filter)
        else:
            raise ValueError(
                "Unsupported File '%s'! Try with an tar archive!" % path)
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader


def is_rawloader(obj):
    '''
    Return True if obj is a raw loader instance, else return False.
    '''
    return isinstance(obj, BaseRawLoader)


def get_fileloader(path, groups_filter=None):
    '''
    Given a file path, return a file loader instance.
    Raises IOError if path not found, ValueError if filetype not supported.
    '''

    if os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            loader = NpzFileLoader(path, groups_filter=groups_filter)
        elif ext == '.hdf5':
            from .hdf5file import Hdf5FileLoader
            loader = Hdf5FileLoader(path, groups_filter=groups_filter)
        else:
            raise ValueError('Unsupported Filetype: "%s"! '
                             'Did you mean one of: "%s"?'
                             % (ext, ', '.join(fileloader_filetypes)))
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader


def is_fileloader(obj):
    '''
    Return True if obj is a file loader instance, else return False.
    '''
    return isinstance(obj, BaseFileLoader)
