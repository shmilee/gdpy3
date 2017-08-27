# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

# https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez_compressed.html
# /usr/lib/python3.x/site-packages/numpy/lib/npyio.py, funtion _savez

import os
import numpy
import zipfile
import tempfile

from ..glogger import getGLogger

__all__ = ['iopen', 'write', 'close']

log = getGLogger('gdc')


def iopen(npzfile):
    '''Open ``.npz`` file if exists, create otherwise.

    Parameters
    ----------
    npzfile: file path of ``.npz`` file which the data is saved.

    Raises
    ------
    IOError
        Cannot read or create the .npz file.

    Returns
    -------
    ZipFile: compressed zip file object, ``.npz`` format
    '''

    if os.path.isfile(npzfile):
        try:
            log.ddebug("Open file '%s' to append data." % npzfile)
            zipf = numpy.lib.npyio.zipfile_factory(
                npzfile, mode="a", compression=zipfile.ZIP_DEFLATED)
        except IOError:
            log.error("Failed to read file %s." % npzfile, exc_info=1)
            raise
    else:
        try:
            log.ddebug("Create file '%s' to store data." % npzfile)
            zipf = numpy.lib.npyio.zipfile_factory(
                npzfile, mode="w", compression=zipfile.ZIP_DEFLATED)
        except IOError:
            log.error("Failed to create file %s." % npzfile, exc_info=1)
            raise
    return zipf


def write(zipf, group, data):
    '''Write dict ``data`` in group ``group`` to zipfile.

    Parameters
    ----------
    zipf: zip file object, ``.npz`` format
    group: str, group name
    data: dict in this group

    Raises
    ------
    ValueError
        ``group`` is not str, or ``data`` is not a dict
    '''
    file_dir, file_prefix = os.path.split(zipf.filename)
    fd, tmpfile = tempfile.mkstemp(
        prefix=file_prefix, dir=file_dir, suffix='-numpy.npy')
    os.close(fd)
    log.ddebug("Using tempfile: %s" % tmpfile)

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
                log.ddebug("Writting %s ..." % fname)
                zipf.write(tmpfile, arcname=fname)
            except Exception:
                log.error("Failed to write %s." % fname, exc_info=1)
            finally:
                if fid:
                    fid.close()
    except Exception:
        log.error("Failed to save data of '%s'!" % group, exc_info=1)
    finally:
        os.remove(tmpfile)


def close(zipf):
    '''Close zipfile.
    '''
    zipf.close()
