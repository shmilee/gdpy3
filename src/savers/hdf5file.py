# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import numpy
try:
    import h5py
except ImportError as exc:
    raise ImportError(
        'Hdf5FileSaver requires h5py(bindings for HDF5). But %s' % exc) from None

from ..glogger import getGLogger
from .base import BaseFileSaver

__all__ = ['Hdf5FileSaver']
log = getGLogger('S')


class Hdf5FileSaver(BaseFileSaver):
    # http://docs.h5py.org/en/latest/index.html
    '''
    Save dict data with a group name to a HDF5 file.
    '''
    __slots__ = []
    _extension = '.hdf5'

    def _open_append(self):
        return h5py.File(self.file, 'r+')

    def _open_new(self):
        return h5py.File(self.file, 'w-')

    def _write(self, group, data):
        try:
            if group in ('/', ''):
                fgrp = self.fobj
                for key in data.keys():
                    if key in self.fobj:
                        log.ddebug("Delete dataset '/%s'." % key)
                        self.fobj.__delitem__(key)
            else:
                if group in self.fobj:
                    log.ddebug("Delete group '/%s'." % group)
                    self.fobj.__delitem__(group)
                log.ddebug("Create group '/%s'." % group)
                fgrp = self.fobj.create_group(group)
            for key, val in data.items():
                log.ddebug("Create dataset '%s/%s'." % (fgrp.name, key))
                if isinstance(val, (list, numpy.ndarray)):
                    fgrp.create_dataset(key, data=val, chunks=True,
                                        compression='gzip',
                                        compression_opts=9)
                else:
                    fgrp.create_dataset(key, data=val)
            self.fobj.flush()
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)

    def _close(self):
        self.fobj.close()
