# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy
from hashlib import sha1

from .. import convert as gdc
from .readnpz import ReadNpz, log

__all__ = ['ReadRaw']


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
    cache: dict
        cached keys from .npz, .hdf5 file

    Parameters
    ----------
    datadir: str
        the GTC .out files to open
    salt: str, a .out file name
        salt for the name of saved file, default 'gtc.out'
    extension: 'npz' or 'hdf5'
        extension of saved file, default 'npz'
    overwrite: bool
        overwrite existing saved file or not, default False
    kwargs: other parameters for gdc.convert
        ``description``, ``version``, ``additionalpats``

    Examples
    --------
    >>> npzf = readraw.ReadRaw('/tmp/testdir/')
    >>> npzf.datadir
    >>> npzf.file
    >>> npzf.keys()
    >>> npzf['gtcout/b0']
    '''
    __slots__ = ['datadir', '_special_parent']

    def __init__(self, datadir,
                 salt='gtc.out', extension='npz', overwrite=False, **kwargs):
        if not os.path.isdir(datadir):
            raise IOError("Can't find directory '%s'!" % datadir)

        # salt
        salt = os.path.join(datadir, str(salt))
        if not os.path.isfile(salt):
            log.error("Can't find file '%s'!" % salt)
        else:
            salt = os.path.join(datadir, 'gtc.out')
        log.debug("Use file '%s' as salt." % salt)

        try:
            with open(salt, 'r') as f:
                salt = sha1(f.read().encode('utf-8')).hexdigest()
                log.debug("Get salt string: '%s'." % salt)
        except:
            raise IOError("Failed to read file '%s'!" % salt)

        # extension
        ext = str(extension)
        if ext not in ('npz', 'hdf5'):
            log.error("Extension '%s' is not supported!" % ext)
            ext = 'npz'
        log.debug("Use extension '%s'." % ext)

        # convert
        savefile = 'gdpy3-pickled-data-%s.%s' % (salt[:10], ext)
        savefile = os.path.join(datadir, savefile)
        log.info("Pickled data file is %s." % savefile)
        overwrite = bool(overwrite)
        if not (overwrite is False and os.path.isfile(savefile)):
            try:
                gdc.convert(datadir, savefile, **kwargs)
            except:
                log.critical("Failed to create file %s." %
                             savefile, exc_info=1)
                raise

        # __init__
        self.datadir = datadir
        if ext == 'npz':
            self._special_parent = ReadNpz
        elif ext == 'hdf5':
            from .readhdf5 import ReadHdf5
            self._special_parent = ReadHdf5
        else:
            raise IOError('Unknown file extension. Never!')
        super(ReadRaw, self).__init__(savefile)

    def _special_openfile(self):
        return self._special_parent._special_openfile(self)

    def _special_closefile(self, tempf):
        return self._special_parent._special_closefile(self, tempf)

    def _special_getkeys(self, tempf):
        return self._special_parent._special_getkeys(self, tempf)

    def _special_getitem(self, tempf, key):
        return self._special_parent._special_getitem(self, tempf, key)
