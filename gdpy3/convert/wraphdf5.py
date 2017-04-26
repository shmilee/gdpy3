# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

# http://docs.h5py.org/en/latest/index.html

import os
import logging
import numpy

__all__ = ['open', 'write', 'close']

log = logging.getLogger('gdc')

try:
    import h5py
except ImportError:
    log.error('If you want to save data in a .hdf5 file, '
              'please install h5py(python bindings for HDF5).')
    raise


def open(hdf5file):
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
            log.debug("Open file '%s' to append data." % hdf5file)
            h5f = h5py.File(hdf5file, 'r+')
        except IOError:
            log.error("Failed to read file %s." % hdf5file)
            raise
    else:
        try:
            log.debug("Create file '%s' to store data." % hdf5file)
            h5f = h5py.File(hdf5file, 'w-')
        except IOError:
            log.error("Failed to create file %s." % hdf5file)
            raise
    return h5f


def write(h5pyfile, name, data):
    '''Write dict ``data`` in group ``name`` to h5pyfile.

    Parameters
    ----------
    h5pyfile: HDF5 file object
    name: str, group name
    data: dict in this group

    Raises
    ------
    ValueError
        ``name`` is not str, or ``data`` is not a dict
    '''

    try:
        if name in ('/', ''):
            fgrp = h5pyfile
            for key in data.keys():
                if key in h5pyfile:
                    log.debug("Delete dataset '/%s'." % key)
                    h5pyfile.__delitem__(key)
        else:
            if name in h5pyfile:
                log.debug("Delete group '/%s'." % name)
                h5pyfile.__delitem__(name)
            log.debug("Create group '/%s'." % name)
            fgrp = h5pyfile.create_group(name)
        for key, val in data.items():
            log.debug("Create dataset '%s/%s'." % (fgrp.name, key))
            if isinstance(val, (list, numpy.ndarray)):
                fgrp.create_dataset(key, data=val, chunks=True,
                                    compression='gzip',
                                    compression_opts=9)
            else:
                fgrp.create_dataset(key, data=val)
        h5pyfile.flush()
    except ValueError:
        log.error("``name`` must be a str. ``data`` must be a dict.")
    except Exception as e:
        log.error(e)
        log.error("Failed to save data of '%s'!" % name)


def close(h5pyfile):
    '''Close h5pyfile.
    '''
    h5pyfile.close()
