# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains Npz pickled file saver class.
'''

import os
import numpy
import zipfile
import tempfile

from ..glogger import getGLogger
from .base import BasePckSaver

__all__ = ['NpzPckSaver']
log = getGLogger('S')


class NpzPckSaver(BasePckSaver):
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez_compressed.html
    # /usr/lib/python3.x/site-packages/numpy/lib/npyio.py, funtion _savez
    '''
    Save dict data with a group name to a NumPy compressed archive file.
    '''
    __slots__ = []
    _extension = '.npz'

    def _open_append(self):
        return numpy.lib.npyio.zipfile_factory(
            self.path, mode="a", compression=zipfile.ZIP_DEFLATED)

    def _open_new(self):
        return numpy.lib.npyio.zipfile_factory(
            self.path, mode="w", compression=zipfile.ZIP_DEFLATED)

    def _write(self, group, data):
        file_dir, file_prefix = os.path.split(self.path)
        fd, tmpfile = tempfile.mkstemp(
            prefix=file_prefix, dir=file_dir, suffix='-numpy.npy')
        os.close(fd)
        log.debug("Using tempfile: %s" % tmpfile)
        try:
            for key, val in data.items():
                if group in ('/', ''):
                    fname = key + '.npy'
                else:
                    fname = group + '/' + key + '.npy'
                fid = open(tmpfile, mode='wb')
                try:
                    numpy.lib.format.write_array(fid, numpy.asanyarray(val),
                                                 allow_pickle=True,
                                                 pickle_kwargs=None)
                    fid.close()
                    fid = None
                    log.debug("Writting %s ..." % fname)
                    self._storeobj.write(tmpfile, arcname=fname)
                except Exception:
                    log.error("Failed to write %s." % fname, exc_info=1)
                finally:
                    if fid:
                        fid.close()
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)
        finally:
            os.remove(tmpfile)
