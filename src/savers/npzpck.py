# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

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

    def _not_use_find_overwrite_names(self, group, data):
        old_all = self._storeobj.namelist()
        if group in ('/', ''):
            new = ['%s.npy' % key for key in data.keys()]
            old_copy = [n for n in old_all if ('/' in n or n not in new)]
            old_over = [n for n in old_all if ('/' not in n and n in new)]
        else:
            new = ['%s/%s.npy' % (group, key) for key in data.keys()]
            old_copy = [n for n in old_all
                        if (not n.startswith('%s/' % group) or n not in new)]
            old_over = [n for n in old_all
                        if (n.startswith('%s/' % group) and n in new)]
        return old_copy, old_over

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
