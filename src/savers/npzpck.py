# -*- coding: utf-8 -*-

# Copyright (c) 2018-2022 shmilee

'''
Contains Npz pickled file saver class.
'''

import io
import numpy as np
import zipfile
import time

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckSaver
from .._zipfile import (
    Py_version_tuple, Compress_kwds,
    zipfile_factory, zipfile_delete
)

__all__ = ['NpzPckSaver']
log = getGLogger('S')
_np_write_array = np.lib.format.write_array
Use_ZipFile_open_mode_w = True


@inherit_docstring(BasePckSaver, parse=None, template=None)
class NpzPckSaver(BasePckSaver):
    '''
    Save dict data with a group name to a NumPy compressed archive file.

    Attributes
    ----------
    {Attributes}

    Parameters
    ----------
    {Parameters}
    duplicate_name: bool
        allow "zipfile.py: UserWarning: Duplicate name ..." or not

    Notes
    -----
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

    def __zf_open_write(self, name, val):
        """
        ZipFile.open, support 'w' mode
        ref: https://docs.python.org/3.6/library/zipfile.html#zipfile.ZipFile.open
        """
        # log.debug("Using ZipFile.open(name, 'w') ...")
        # use zinfo instead of name, fix date_time=1980.1.1.0.0
        # fix: https://github.com/python/cpython/blob/3.6/Lib/zipfile.py#L1371
        zinfo = zipfile.ZipInfo(filename=name,
                                date_time=time.localtime(time.time())[:6])
        zinfo.compress_type = Compress_kwds['compression']
        if 'compresslevel' in Compress_kwds:
            zinfo._compresslevel = Compress_kwds['compresslevel']
        with self._storeobj.open(zinfo, 'w', force_zip64=True) as f:
            _np_write_array(f, np.asanyarray(val), allow_pickle=True)

    def __zf_writestr(self, name, val):
        """
        ZipFile.writestr, data can be 'bytes' instance
        ref: https://github.com/python/cpython/blob/3.5/Lib/zipfile.py#L1530
        """
        # log.debug("Using ZipFile.writestr(name, bytes-data) ...")
        with io.BytesIO() as f:
            _np_write_array(f, np.asanyarray(val), allow_pickle=True)
            data = f.getvalue()
            self._storeobj.writestr(name, data)

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
                    name = key + '.npy'
                else:
                    name = group + '/' + key + '.npy'
                log.debug("Writting %s ..." % name)
                if Use_ZipFile_open_mode_w and Py_version_tuple >= (3, 6, 0):
                    self.__zf_open_write(name, val)  # ZipFile.open
                else:
                    self.__zf_writestr(name, val)  # ZipFile.writestr
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)
