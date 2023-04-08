# -*- coding: utf-8 -*-

# Copyright (c) 2018-2022 shmilee

'''
Contains Npz pickled file saver class.
'''

import os
import numpy

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckSaver, _copydoc_func
from .._zipfile import Compress_kwds, zipfile_factory, zipfile_delete

__all__ = ['NpzPckSaver']
log = getGLogger('S')


@inherit_docstring((BasePckSaver,), _copydoc_func, template=None)
class NpzPckSaver(BasePckSaver):
    '''
    Save dict data with a group name to a NumPy compressed archive file.

    Attributes
    {Attributes}

    Parameters
    {Parameters}
    duplicate_name: bool
        allow "zipfile.py: UserWarning: Duplicate name ..." or not

    Notes
    {Notes}

    References
    ----------
    1. https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez_compressed.html
    2. /usr/lib/python3.x/site-packages/numpy/lib/npyio.py, funtion zipfile_factory _savez
    3. https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile
    '''
    __slots__ = ['duplicate_name']
    _extension = '.npz'

    def __init__(self, path, duplicate_name=True):
        super(NpzPckSaver, self).__init__(path)
        self.duplicate_name = duplicate_name
        log.debug('Using ZipFile compression parameters: %s' % Compress_kwds)

    def _open_append(self):
        return zipfile_factory(self.path, mode="a")

    def _open_new(self):
        return zipfile_factory(self.path, mode="w")

    def _write(self, group, data):
        if not self.duplicate_name:
            prefix = '' if group in ('/', '') else ('%s/' % group)
            new = ['%s%s.npy' % (prefix, key) for key in data.keys()]
            old_over = [n for n in self._storeobj.namelist() if n in new]
            if old_over:
                # need to rebuild a new archive without old_over files
                # log.debug("\n%s\n" % (old_over,))
                self.close()
                zipfile_delete(self.path, old_over)
                self.iopen()
        try:
            for key, val in data.items():
                if group in ('/', ''):
                    fname = key + '.npy'
                else:
                    fname = group + '/' + key + '.npy'
                log.debug("Writting %s ..." % fname)
                with self._storeobj.open(fname, 'w', force_zip64=True) as fid:
                    numpy.lib.format.write_array(fid, numpy.asanyarray(val),
                                                 allow_pickle=True,
                                                 pickle_kwargs=None)
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)
