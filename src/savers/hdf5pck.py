# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import numpy
try:
    import h5py
except ImportError as exc:
    raise ImportError('Hdf5PckSaver requires h5py. But %s' % exc) from None

from ..glogger import getGLogger
from .base import BasePckSaver

__all__ = ['Hdf5PckSaver']
log = getGLogger('S')


class Hdf5PckSaver(BasePckSaver):
    # http://docs.h5py.org/en/latest/index.html
    '''
    Save dict data with a group name to a HDF5 file.
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
                fgrp = self._storeobj
                for key in data.keys():
                    if key in self._storeobj:
                        log.debug("Delete dataset '/%s'." % key)
                        self._storeobj.__delitem__(key)
            else:
                if group in self._storeobj:
                    log.debug("Delete group '/%s'." % group)
                    self._storeobj.__delitem__(group)
                log.debug("Create group '/%s'." % group)
                fgrp = self._storeobj.create_group(group)
            for key, val in data.items():
                log.debug("Create dataset '%s/%s'." % (fgrp.name, key))
                if isinstance(val, (list, numpy.ndarray)):
                    fgrp.create_dataset(key, data=val, chunks=True,
                                        compression='gzip',
                                        compression_opts=9)
                else:
                    fgrp.create_dataset(key, data=val)
            self._storeobj.flush()
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)
