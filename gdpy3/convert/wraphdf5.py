# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

# http://docs.h5py.org/en/latest/index.html

import os
import numpy

from ..glogger import getGLogger

__all__ = ['iopen', 'write', 'close']

log = getGLogger('gdc')

try:
    import h5py
except ImportError:
    log.error('If you want to save data in a .hdf5 file, '
              'please install h5py(python bindings for HDF5).')
    raise


def iopen(hdf5file):
    '''Open ``.hdf5`` file

    Parameters
    ----------
    hdf5file: file path of ``.hdf5`` file which the data is saved.

    Raises
    ------
    IOError
        Cannot read or create the .hdf5 file.

    Returns
    -------
    h5py.File: HDF5 file object
    '''

    if os.path.isfile(hdf5file):
        try:
            log.ddebug("Open file '%s' to append data." % hdf5file)
            h5f = h5py.File(hdf5file, 'r+')
        except IOError:
            log.error("Failed to read file %s." % hdf5file, exc_info=1)
            raise
    else:
        try:
            log.ddebug("Create file '%s' to store data." % hdf5file)
            h5f = h5py.File(hdf5file, 'w-')
        except IOError:
            log.error("Failed to create file %s." % hdf5file, exc_info=1)
            raise
    return h5f


def write(h5pyfile, group, data):
    '''Write dict ``data`` in group ``group`` to h5pyfile.

    Parameters
    ----------
    h5pyfile: HDF5 file object
    group: str, group name
    data: dict in this group

    Raises
    ------
    ValueError
        ``group`` is not str, or ``data`` is not a dict
    '''

    try:
        if group in ('/', ''):
            fgrp = h5pyfile
            for key in data.keys():
                if key in h5pyfile:
                    log.ddebug("Delete dataset '/%s'." % key)
                    h5pyfile.__delitem__(key)
        else:
            if group in h5pyfile:
                log.ddebug("Delete group '/%s'." % group)
                h5pyfile.__delitem__(group)
            log.ddebug("Create group '/%s'." % group)
            fgrp = h5pyfile.create_group(group)
        for key, val in data.items():
            log.ddebug("Create dataset '%s/%s'." % (fgrp.name, key))
            if isinstance(val, (list, numpy.ndarray)):
                fgrp.create_dataset(key, data=val, chunks=True,
                                    compression='gzip',
                                    compression_opts=9)
            else:
                fgrp.create_dataset(key, data=val)
        h5pyfile.flush()
    except ValueError:
        log.error("``group`` must be a str. ``data`` must be a dict.",
                  exc_info=1)
    except Exception:
        log.error("Failed to save data of '%s'!" % group, exc_info=1)


def close(h5pyfile):
    '''Close h5pyfile.
    '''
    h5pyfile.close()
