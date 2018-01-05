# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os

from ..glogger import getGLogger
from .npzfile import NpzFileSaver

__all__ = ['get_filesaver']
log = getGLogger('S')
filesaver_names = ['NpzFileSaver', 'Hdf5FileSaver']
filesaver_filetypes = ['.npz', '.hdf5']

def get_filesaver(path):
    '''
    Given a saver path, return a saver instance.
    Raises IOError if path not available.

    Notes
    -----
    filetype not in *filesaver_filetypes* -> '.npz'
    '''

    ext = os.path.splitext(path)[1]
    if ext not in filesaver_filetypes:
        log.warn("Saver filetype must be '.npz' or '.hdf5'! Use '.npz'.")
        ext = '.npz'
        path = path + ext
    if os.path.exists(path):
        raise IOError("Path '%s' exists!" % path)
    else:
        if ext  == '.npz':
            saver = NpzFileSaver(path)
        elif ext == '.hdf5':
            from .hdf5file import Hdf5FileSaver
            saver = Hdf5FileSaver(path)
        else:
            raise ValueError('Save ha? Who am I? Why am I here?')
    return saver
