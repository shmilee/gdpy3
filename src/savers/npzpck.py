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
from ..utils import inherit_docstring
from .base import BasePckSaver, _copydoc_func

__all__ = ['NpzPckSaver']
log = getGLogger('S')


@inherit_docstring((BasePckSaver,), _copydoc_func, template=None)
class NpzPckSaver(BasePckSaver):
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez_compressed.html
    # /usr/lib/python3.x/site-packages/numpy/lib/npyio.py, funtion _savez
    '''
    Save dict data with a group name to a NumPy compressed archive file.

    Attributes
    {Attributes}
    duplicate_name: bool
        allow "zipfile.py: UserWarning: Duplicate name ..." or not

    Parameters
    {Parameters}

    Notes
    {Notes}
    '''
    __slots__ = ['duplicate_name']
    _extension = '.npz'

    def __init__(self, path, duplicate_name=True):
        super(NpzPckSaver, self).__init__(path)
        self.duplicate_name = duplicate_name

    def _open_append(self):
        return numpy.lib.npyio.zipfile_factory(
            self.path, mode="a", compression=zipfile.ZIP_DEFLATED)

    def _open_new(self):
        return numpy.lib.npyio.zipfile_factory(
            self.path, mode="w", compression=zipfile.ZIP_DEFLATED)

    def _find_overwrite_names(self, group, data):
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

    @staticmethod
    def copy_zipfile(old, new, ignore):
        zf = numpy.lib.npyio.zipfile_factory
        with zf(old, mode="r", compression=zipfile.ZIP_DEFLATED) as zin:
            with zf(new, mode="w", compression=zipfile.ZIP_DEFLATED) as zout:
                zout.comment = zin.comment
                for item in zin.infolist():
                    if item.filename not in ignore:
                        zout.writestr(item, zin.read(item.filename))

    def _write(self, group, data):
        file_dir, file_prefix = os.path.split(self.path)
        if not self.duplicate_name:
            old_copy, old_over = self._find_overwrite_names(group, data)
            if old_over:
                # log.debug("%s\n%s" % (old_copy, old_over))
                # need to rebuild a new archive without old_over files
                fd, tmpfile = tempfile.mkstemp(
                    prefix=file_prefix, dir=file_dir, suffix='-copy.zip')
                os.close(fd)
                log.debug("Using temp zipfile: %s" % tmpfile)
                self.close()
                try:
                    self.copy_zipfile(self.path, tmpfile, old_over)
                except Exception:
                    log.error("Failed to part-copy zipfile %s!" % self.path)
                    os.remove(tmpfile)
                else:
                    os.remove(self.path)
                    os.rename(tmpfile, self.path)
                self.iopen()
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
