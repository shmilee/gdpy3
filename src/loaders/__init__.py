# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
This is the subpackage ``loaders`` of gdpy3.
It contains two kinds of loaders.

1. ``RawLoader``, get by :func:`get_rawloader`.
   ``RawLoader`` has attributes
   :attr:`RawLoader.path``,
   :attr:`RawLoader.filenames`
   and methods
   :meth:`RawLoader.keys`,
   :meth:`RawLoader.get`,
   :meth:`Loader.find`,
   :meth:`Loader.refind`,
   :meth:`Loader.update`,
   :meth:`Loader.all_in_loader`.

2. ``PckLoader``, get by :func:`get_pckloader`.
   ``PckLoader`` has attributes
   :attr:`PckLoader.path``,
   :attr:`PckLoader.datakeys`,
   :attr:`PckLoader.datagroups`,
   :attr:`PckLoader.description`,
   :attr:`PckLoader.cache`,
   and methods
   :meth:`PckLoader.keys`,
   :meth:`PckLoader.get`,
   :meth:`PckLoader.get_many`,
   :meth:`Loader.find`,
   :meth:`Loader.refind`,
   :meth:`Loader.update`,   
   :meth:`Loader.all_in_loader`.
'''

import os

from . import base

__all__ = ['get_rawloader', 'is_rawloader', 'get_pckloader', 'is_pckloader']
rawloader_names = ['DirRawLoader', 'TarRawLoader', 'ZipRawLoader',
                   'SftpRawLoader']
rawloader_types = ['directory', 'tarfile', 'zipfile', 'sftp.directory']
pckloader_names = ['CachePckLoader', 'NpzPckLoader', 'Hdf5PckLoader']
pckloader_types = ['.cache', '.npz', '.hdf5']


def get_rawloader(path, filenames_filter=None):
    '''
    Given a path, return a raw loader instance.
    Raises IOError if path not found, ValueError if path type not supported.

    Notes
    -----
    *path* types:
    1. local directory
    2. tar archive file
    3. zip archive file
    4. directory in remote SSH server
       format: 'sftp://username[:passwd]@host[:port]##remote/path'
    '''

    path = str(path)
    if path.startswith('sftp://'):
        from .sftpraw import SftpRawLoader
        loader = SftpRawLoader(path, filenames_filter=filenames_filter)
    elif os.path.isdir(path):
        from .dirraw import DirRawLoader
        loader = DirRawLoader(path, filenames_filter=filenames_filter)
    elif os.path.isfile(path):
        import tarfile
        import zipfile
        if tarfile.is_tarfile(path):
            from .tarraw import TarRawLoader
            loader = TarRawLoader(path, filenames_filter=filenames_filter)
        elif zipfile.is_zipfile(path):
            from .zipraw import ZipRawLoader
            loader = ZipRawLoader(path, filenames_filter=filenames_filter)
        else:
            raise ValueError('Unsupported File "%s"! Try with one of: "%s"!'
                             % (path, ', '.join(rawloader_types[1:-1])))
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader


def is_rawloader(obj):
    '''
    Return True if obj is a raw loader instance, else return False.
    '''
    return isinstance(obj, base.BaseRawLoader)


def get_pckloader(path, datagroups_filter=None):
    '''
    Given a file path or dict cache, return a pickled loader instance.
    Raises IOError if path not found, ValueError if path type not supported.

    Notes
    -----
    *path* types:
    1. '.npz' file
    2. '.hdf5' file
    3. dict object
    '''

    if isinstance(path, dict):
        from .cachepck import CachePckLoader
        loader = CachePckLoader(path, datagroups_filter=datagroups_filter)
    elif isinstance(path, str) and os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            from .npzpck import NpzPckLoader
            loader = NpzPckLoader(path, datagroups_filter=datagroups_filter)
        elif ext == '.hdf5':
            from .hdf5pck import Hdf5PckLoader
            loader = Hdf5PckLoader(path, datagroups_filter=datagroups_filter)
        else:
            raise ValueError('Unsupported Filetype: "%s"! '
                             'Did you mean one of: "%s"?'
                             % (ext, ', '.join(pckloader_types[1:])))
    else:
        raise IOError("Can't find path '%s'!" % path)
    return loader


def is_pckloader(obj):
    '''
    Return True if obj is a pickled loader instance, else return False.
    '''
    return isinstance(obj, base.BasePckLoader)
