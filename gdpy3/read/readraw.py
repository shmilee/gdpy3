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
    If the extension of saved file is given as .npz or .hdf5,
    they will be converted to a .[extension] file.

    Attributes
    ----------
    datadir: str
        path of GTC .out files
    file: str
        path of .npz, .hdf5 file
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
        ``loglevel``, ``description``,
        ``version``, ``additionalpats`` for gdc.convert
        ``salt`` for name of saved file, default 'gtc.out'
        ``extension`` for extension of saved file, default 'npz'

    Examples
    --------
    >>> npzf = readraw.ReadRaw('/tmp/testdir/')
    >>> npzf.datadir
    >>> npzf.file
    >>> npzf.keys()
    >>> npzf['gtcout/b0']
    '''
    __slots__ = ['datadir', 'file', 'datakeys', 'desc', 'description']

    def __init__(self, datadir, **kwargs):
        if not os.path.isdir(datadir):
            raise IOError("Can't find directory '%s'!" % datadir)

        # salt
        if 'salt' in kwargs:
            salt = os.path.join(datadir, str(kwargs['salt']))
            if not os.path.isfile(salt):
                log.error("Can't find file '%s'!" % salt)
            else:
                salt = os.path.join(datadir, 'gtc.out')
        else:
            salt = os.path.join(datadir, 'gtc.out')
        log.debug("Use file %s as salt." % salt)

        try:
            with open(salt, 'r') as f:
                salt = sha1(f.read().encode('utf-8')).hexdigest()
                log.debug("Get salt string: '%s'." % salt)
        except:
            raise IOError("Failed to read file '%s'!" % salt)

        # extension
        if 'extension' in kwargs:
            ext = str(kwargs['extension'])
            if ext not in ('npz', 'hdf5'):
                log.error("Extension '%s' is not supported!" % ext)
                ext = 'npz'
        else:
            ext = 'npz'
        log.debug("Use extension '%s'." % ext)

        # convert
        savefile = 'gdpy3-pickled-data-%s.%s' % (salt[:10], ext)
        savefile = os.path.join(datadir, savefile)
        log.info("Pickled data file is %s." % savefile)
        if not os.path.isfile(savefile):
            try:
                gdc.convert(datadir, savefile, **kwargs)
            except:
                raise IOError("Failed to create file %s." % savefile)

        # __init__
        self.datadir = datadir
        if ext == 'npz':
            ReadNpz.__init__(self, savefile)
        elif ext == 'hdf5':
            from .readhdf5 import ReadHdf5
            ReadHdf5.__init__(self, savefile)
        else:
            log.error('Unknown extension.')

    def __getitem__(self, key):
        if os.path.splitext(self.file)[1] == '.npz':
            return ReadNpz.__getitem__(self, key)
        elif os.path.splitext(self.file)[1] == '.hdf5':
            from .readhdf5 import ReadHdf5
            return ReadHdf5.__getitem__(self, key)
        else:
            log.error('Unknown extension.')
