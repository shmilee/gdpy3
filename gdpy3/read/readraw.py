# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import numpy
from hashlib import sha1

import gdpy3.convert as gdc
from .readnpz import ReadNpz

__all__ = ['ReadRaw']

log = logging.getLogger('gdr')


class ReadRaw(ReadNpz):
    '''Read all GTC .out files in directory ``datadir``.
    Convert them to a .npz file saved in ``datadir``.
    Then this cls behaves as ``read.ReadNpz``.

    Attributes
    ----------
    datadir: str
        path of GTC .out files
    file: str
        path of .npz file
    datakeys: tuple
        keys of physical quantities in the .out files
    desc: str
        description of the .out files
    description: alias desc

    Parameters
    ----------
    datadir: str
        the GTC .out files to open
    kwargs: other parameters
        ``description``, ``version``, ``additionalpats`` for gdc.convert
        ``salt`` for name of saved .npz file, default 'gtc.out'

    Examples
    --------
    >>> npzf = readraw.ReadRaw('/tmp/testdir/')
    >>> npzf.datadir
    >>> npzf.file
    >>> npzf.keys()
    >>> npzf['gtcout/b0']
    '''

    def __init__(self, datadir, **kwargs):
        if not os.path.isdir(datadir):
            raise IOError("Can't find directory '%s'!" % datadir)

        # salt
        if 'salt' in kwargs:
            salt = str(kwargs['salt'])
        else:
            salt = 'gtc.out'
        if not os.path.isfile(datadir + '/' + salt):
            raise IOError("Can't find '%s' in '%s'!" % (salt, datadir))
        try:
            with open(datadir + '/' + salt, 'r') as f:
                salt = sha1(f.read().encode('utf-8')).hexdigest()
        except:
            raise IOError("Failed to read data from '%s'!" % datadir)

        # convert to .npz
        npzfile = datadir + '/gdpy3-pickled-data-%s.npz' % salt[:10]
        if not os.path.isfile(npzfile):
            try:
                gdc.convert(datadir, npzfile, **kwargs)
            except:
                raise IOError("Failed to create file %s." % npzfile)

        self.datadir = datadir
        self.file = npzfile
        try:
            tempf = numpy.load(self.file)
            self.datakeys = tuple(tempf.files)
            self.desc = str(tempf['description'])
            self.description = self.desc
        except (IOError, ValueError):
            log.error("Failed to read file %s." % self.file)
            raise
        finally:
            if 'tempf' in dir():
                tempf.close()
