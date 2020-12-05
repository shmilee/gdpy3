# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import numpy
try:
    import h5py
except ImportError as exc:
    raise ImportError('Hdf5PckSaver requires h5py. But %s' % exc) from None

from ..glogger import getGLogger
from ..utils import inherit_docstring
from .base import BasePckSaver, _copydoc_func

__all__ = ['Hdf5PckSaver']
log = getGLogger('S')


@inherit_docstring((BasePckSaver,), _copydoc_func, template=None)
class Hdf5PckSaver(BasePckSaver):
    # http://docs.h5py.org/en/latest/index.html
    '''
    Save dict data with a group name to a HDF5 file.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    {Notes}
    '''
    __slots__ = []
    _extension = '.hdf5'

    def _open_append(self):
        return h5py.File(self.path, 'r+')

    def _open_new(self):
        return h5py.File(self.path, 'w-')

    def _write(self, group, data):
        try:
            if group in ('/', ''):
                group = '/'
            if group in self._storeobj:
                fgrp = self._storeobj[group]
                for key in data.keys():
                    if key in fgrp:
                        log.debug("Delete dataset %s/%s." % (group, key))
                        fgrp.__delitem__(key)
            else:
                log.debug("Create group '/%s'." % group)
                fgrp = self._storeobj.create_group(group)
            for key, val in data.items():
                log.debug("Create dataset %s/%s." % (fgrp.name, key))
                if isinstance(val, (list, numpy.ndarray)):
                    if isinstance(val, list):
                        val = numpy.array(val)
                    fgrp.create_dataset(key, data=val,
                                        chunks=val.shape,  # only one chunk
                                        compression='gzip',
                                        compression_opts=9)
                else:
                    # str -> bytes; bytes -> void
                    if isinstance(val, str):
                        val = val.encode(encoding='utf-8')
                    elif isinstance(val, bytes):
                        val = numpy.void(val)
                    fgrp.create_dataset(key, data=val)
            self._storeobj.flush()
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)
