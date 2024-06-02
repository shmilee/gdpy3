# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
This is the subpackage ``loaders`` of gdpy3.
It contains two kinds of loaders.

1. ``RawLoader``, get by :func:`get_rawloader`.
   ``RawLoader`` has attributes
   :attr:`RawLoader.path`,
   :attr:`RawLoader.pathobj`,
   :attr:`RawLoader.filenames`,
   :attr:`RawLoader.filenames_exclude`,
   and methods
   :meth:`RawLoader.keys`,
   :meth:`RawLoader.get`,
   :meth:`RawLoader.find`,
   :meth:`RawLoader.refind`,
   :meth:`RawLoader.update`,
   :meth:`RawLoader.all_in_loader`.

2. ``PckLoader``, get by :func:`get_pckloader`.
   ``PckLoader`` has attributes
   :attr:`PckLoader.path`,
   :attr:`PckLoader.pathobj`,
   :attr:`PckLoader.datakeys`,
   :attr:`PckLoader.virtualkeys`,
   :attr:`PckLoader.datagroups`,
   :attr:`PckLoader.datagroups_exclude`,
   :attr:`PckLoader.description`,
   :attr:`PckLoader.cache`,
   and methods
   :meth:`PckLoader.keys`,
   :meth:`PckLoader.get`,
   :meth:`PckLoader.get_many`,
   :meth:`PckLoader.get_by_group`,
   :meth:`PckLoader.find`,
   :meth:`PckLoader.refind`,
   :meth:`PckLoader.update`,   
   :meth:`PckLoader.all_in_loader`.
'''

import os

from . import base
from ..utils import is_dict_like

__all__ = ['get_rawloader', 'is_rawloader', 'get_pckloader', 'is_pckloader']
rawloader_names = ['DirRawLoader', 'TarRawLoader', 'ZipRawLoader',
                   'SftpRawLoader']
rawloader_types = ['directory', 'tarfile', 'zipfile', 'sftp.directory']
pckloader_names = ['CachePckLoader', 'NpzPckLoader', 'Hdf5PckLoader',
                   'JsonlPckLoader', 'JsonzPckLoader']
pckloader_types = ['.cache', '.npz', '.hdf5',
                   '.jsonl', '.jsonz']


def get_rawloader(path, dirnames_exclude=None, filenames_exclude=None):
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

    path = os.path.expanduser(str(path))
    if path.startswith('sftp://'):
        from .sftpraw import SftpRawLoader as Loader
    elif os.path.isdir(path):
        from .dirraw import DirRawLoader as Loader
    elif os.path.isfile(path):
        import tarfile
        import zipfile
        if tarfile.is_tarfile(path):
            from .tarraw import TarRawLoader as Loader
        elif zipfile.is_zipfile(path):
            from .zipraw import ZipRawLoader as Loader
        else:
            raise ValueError('Unsupported File "%s"! Try with one of: "%s"!'
                             % (path, ', '.join(rawloader_types[1:-1])))
    else:
        raise IOError("Can't find path '%s'!" % path)
    return Loader(path, dirnames_exclude=dirnames_exclude,
                  filenames_exclude=filenames_exclude)


def is_rawloader(obj):
    '''
    Return True if obj is a raw loader instance, else return False.
    '''
    return isinstance(obj, base.BaseRawLoader)


def get_pckloader(path, virtualdata=None, datagroups_exclude=None):
    '''
    Given a file path or dict cache, return a pickled loader instance.
    Raises IOError if path not found, ValueError if path type not supported.

    Notes
    -----
    *path* types:
    1. dict-like object
    2. '.npz' file
    3. '.hdf5' file
    4. '.jsonl' file
    5. '.jsonz' file
    '''

    if is_dict_like(path):
        from .cachepck import CachePckLoader as Loader
    elif isinstance(path, str):
        path = os.path.expanduser(path)
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1]
            if ext == '.npz':
                from .npzpck import NpzPckLoader as Loader
            elif ext == '.hdf5':
                from .hdf5pck import Hdf5PckLoader as Loader
            elif ext == '.jsonl':
                from .jsonpck import JsonlPckLoader as Loader
            elif ext == '.jsonz':
                from .jsonpck import JsonzPckLoader as Loader
            else:
                raise ValueError('Unsupported Filetype: "%s"! '
                                 'Did you mean one of: "%s"?'
                                 % (ext, ', '.join(pckloader_types[1:])))
        else:
            raise IOError("Can't find path '%s'!" % path)
    else:
        raise ValueError("Var *path* should be str or dict object!")
    return Loader(
        path, virtualdata=virtualdata, datagroups_exclude=datagroups_exclude)


def is_pckloader(obj):
    '''
    Return True if obj is a pickled loader instance, else return False.
    '''
    return isinstance(obj, base.BasePckLoader)
