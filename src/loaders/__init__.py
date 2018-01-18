# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os

from ..glogger import getGLogger
from . import base

__all__ = ['get_rawloader', 'is_rawloader', 'get_pckloader', 'is_pckloader']
log = getGLogger('L')
rawloader_names = ['DirRawLoader', 'TarRawLoader', 'SftpRawLoader']
pckloader_names = ['NpzPckLoader', 'Hdf5PckLoader']
pckloader_types = ['.npz', '.hdf5']


def get_rawloader(path, filenames_filter=None):
    '''
    Given a path, return a raw loader instance.
    Raises IOError if path not found, ValueError if path type not supported.

    Notes
    -----
    *path* types:
    1. local directory
    2. tar archive file
    3. directory in remote SSH server
       format: 'sftp://username[:passwd]@host[:port]##remote/path'
    '''

    if os.path.isdir(path):
        from .dirraw import DirRawLoader
        loader = DirRawLoader(path, filenames_filter=filenames_filter)
    elif os.path.isfile(path):
        import tarfile
        if tarfile.is_tarfile(path):
            from .tarraw import TarRawLoader
            loader = TarRawLoader(path, filenames_filter=filenames_filter)
        else:
            raise ValueError(
                "Unsupported File '%s'! Try with an tar archive!" % path)
    elif path.startswith('sftp://'):
        from .sftpraw import SftpRawLoader
        loader = SftpRawLoader(path, filenames_filter=filenames_filter)
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader


def is_rawloader(obj):
    '''
    Return True if obj is a raw loader instance, else return False.
    '''
    return isinstance(obj, base.BaseRawLoader)


def get_pckloader(path, groups_filter=None):
    '''
    Given a file or cache path, return a pickled loader instance.
    Raises IOError if path not found, ValueError if path type not supported.
    '''

    if os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            from .npzfile import NpzPckLoader
            loader = NpzPckLoader(path, groups_filter=groups_filter)
        elif ext == '.hdf5':
            from .hdf5file import Hdf5PckLoader
            loader = Hdf5PckLoader(path, groups_filter=groups_filter)
        else:
            raise ValueError('Unsupported Filetype: "%s"! '
                             'Did you mean one of: "%s"?'
                             % (ext, ', '.join(pckloader_types)))
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader


def is_pckloader(obj):
    '''
    Return True if obj is a pickled loader instance, else return False.
    '''
    return isinstance(obj, base.BasePckLoader)
