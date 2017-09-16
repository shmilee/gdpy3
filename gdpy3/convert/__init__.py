# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
This is the subpackage ``convert`` of package gdpy3.
'''

import os
import time
import re
from hashlib import sha1

from .utils import NpzSaver, Hdf5Saver, NpzLoader, Hdf5Loader, log
from . import (gtcout, data1d, equilibrium, history,
               meshgrid, snapshot, trackparticle)
from .. import __version__ as gdpy3_version

__all__ = ['gtcout', 'data1d', 'equilibrium', 'history',
           'meshgrid', 'snapshot', 'trackparticle',
           'RawLoader', 'convert', 'load']


class RawLoader(NpzLoader):
    '''
    Read all GTC .out files in directory ``casedir``.
    Convert them to a .npz or .hdf5 file in ``casedir``.
    Then this cls behaves as ``NpzLoader``.

    Attributes
    ----------
    casedir: str
        path of GTC .out files
    file: str
        path of .npz or .hdf5 file
    datakeys: tuple
        keys of physical quantities in the .out files
    datagroups: tuple
        groups of datakeys
    desc: str
        description of the GTC case
    description: alias desc
    cache: dict
        cached keys from .npz or .hdf5 file

    Parameters
    ----------
    casedir: str
        path of GTC .out files to open
    salt: str, a .out file name
        salt for the name of saved file, default 'gtc.out'
    extension: '.npz' or '.hdf5'
        extension of saved file, default '.npz'
    gtcver: str
        GTC code version, default is '110922'
    overwrite: bool
        overwrite existing saved file or not, default False
    Sid: bool
        If Sid is here(True), Buzz Lightyear will be destroyed,
        so self.__init__ will stop after setting self.casedir, self.file.
    kwargs: other parameters for self._convert()
        ``description``, ``additionalpats``

    Raises
    ------
    IOError
        Can't read .out files or write in ``casedir``.

    Notes
    -----
    1) GTC .out files should be named as:
       gtc.out, history.out, snap("%05d" % istep).out, trackp_dir, etc.
       so they can be auto-detected.
    2) ``additionalpats`` should be a list. See gtcout.convert.
    '''
    __slots__ = ['casedir', '_special_parent']

    _GTCFilesMap = {
        '110922': {
            'gtc.out': gtcout.GtcOutV110922,
            'data1d.out': data1d.Data1dBlockV110922,
            'equilibrium.out': equilibrium.EquilibriumBlockV110922,
            'history.out': history.HistoryBlockV110922,
            'meshgrid.out': meshgrid.MeshgridBlockV110922,
            'snapshot.out': snapshot.SnapshotBlockV110922,
            'trackp_dir': trackparticle.TrackParticleBlockV110922,
        }
    }
    _SnapPattern = re.compile(r'^snap\d{5}\.out$')

    def __init__(self, casedir, salt='gtc.out', extension='.npz',
                 gtcver='110922', overwrite=False, Sid=False, **kwargs):
        if not os.path.isdir(casedir):
            raise IOError("Can't find directory '%s'!" % casedir)
        if not os.access(casedir, os.W_OK):
            raise IOError("Can't access directory '%s'!" % casedir)
        if not os.path.isfile(os.path.join(casedir, 'gtc.out')):
            log.error("'%s' is not a GTC case directory!" % casedir)
            raise IOError("Can't find 'gtc.out' in '%s'!" % casedir)
        self.casedir = casedir
        # salt
        salt = os.path.join(casedir, str(salt))
        if not os.path.isfile(salt):
            log.warn("Can't find salt file '%s'! Use 'gtc.out'." % salt)
            salt = os.path.join(casedir, 'gtc.out')
        log.debug("Use file '%s' as salt." % salt)
        try:
            with open(salt, 'r') as f:
                salt = sha1(f.read().encode('utf-8')).hexdigest()
                log.debug("Get salt string: '%s'." % salt)
        except Exception:
            raise IOError("Failed to read file '%s'!" % salt)
        # extension
        ext = str(extension)
        if ext not in ('.npz', '.hdf5'):
            log.warn("Extension '%s' not supported! USe '.npz'" % ext)
            ext = '.npz'
        log.debug("Use extension '%s'." % ext)
        if ext == '.npz':
            self._special_parent = NpzLoader
        elif ext == '.hdf5':
            self._special_parent = Hdf5Loader
        else:
            raise IOError('Unknown file extension. Never!')
        # savefile
        savefile = 'gdpy3-pickled-data-%s%s' % (salt[:10], ext)
        savefile = os.path.join(casedir, savefile)
        log.info("Default pickled data file is %s." % savefile)
        self.file = savefile

        # Sid is here?
        if bool(Sid):
            return None

        # overwrite
        overwrite = bool(overwrite)
        if not (overwrite is False and os.path.isfile(savefile)):
            # _convert
            try:
                self._convert(gtcver=gtcver, **kwargs)
            except:
                log.critical("Failed to create file %s." %
                             savefile, exc_info=1)
                raise
        # __init__
        if os.path.isfile(savefile):
            super(RawLoader, self).__init__(savefile)

    def _set_speciallib(self):
        self._special_parent._set_speciallib(self)

    def _special_openfile(self):
        return self._special_parent._special_openfile(self)

    def _special_closefile(self, tempf):
        return self._special_parent._special_closefile(self, tempf)

    def _special_getkeys(self, tempf):
        return self._special_parent._special_getkeys(self, tempf)

    def _special_getitem(self, tempf, key):
        return self._special_parent._special_getitem(self, tempf, key)

    def _convert(self, gtcver='110922', savefile=None, **kwargs):
        '''
        Convert GTC .out files to a .npz or .hdf5 file.
        Save the results in ``savefile``.

        Parameters
        ----------
        gtcver: str
            GTC code version, default is '110922'
        savefile: specified path of the saved file
            The extension may be '.npz' or '.hdf5.
            If no one is matched, '.npz' will be adopted.
        kwargs: other parameters
            ``description`` of the simulation case
            ``additionalpats`` for reading 'gtc.out'
        '''

        casedir = self.casedir
        # description for this case
        desc = ("GTC .out data from directory '%s'.\n"
                "Created by gdpy3 v%s.\n"
                "Created on %s." %
                (casedir, gdpy3_version, time.asctime()))
        if 'description' in kwargs:
            desc = desc + '\n' + str(kwargs['description'])
        # gtcver
        gtcver = str(gtcver)
        if not gtcver in self._GTCFilesMap:
            log.warn("GTC version '%s' not supported! Use '110922'." % gtcver)
            gtcver = '110922'
        log.info("Set the GTC version: '%s'." % gtcver)
        GTCFilesMap = self._GTCFilesMap[gtcver]
        # savefile
        if not savefile:
            savefile = self.file
            saveext = os.path.splitext(savefile)[1]
        else:
            saveext = os.path.splitext(savefile)[1]
            if saveext not in ('.npz', '.hdf5'):
                # fix Sid, prepare savefile, default filetype is '.npz'
                log.warn("Pickled data filetype must be '.npz' or '.hdf5'! "
                         "Use '.npz'.")
                saveext = '.npz'
                savefile = savefile + '.npz'
            log.info("Set pickled data file: %s." % savefile)
        try:
            if saveext == '.npz':
                casesaver = NpzSaver(savefile)
            elif saveext == '.hdf5':
                casesaver = Hdf5Saver(savefile)
            else:
                raise ValueError("Wrong file extension!")
        except Exception:
            log.error("Failed to initialize the saver!")
            raise

        # save all data
        if os.path.isfile(savefile):
            log.warn("Remove previous file: %s!" % savefile)
            os.remove(savefile)
        casesaver.iopen()
        log.verbose("Saving '/description', '/version' to %s ..." % savefile)
        casesaver.write('/', {'description': desc, 'version': gtcver})
        # get gtc.out parameters
        try:
            paras = GTCFilesMap['gtc.out'](
                file=os.path.join(casedir, 'gtc.out'))
            log.info('Getting data from %s ...' % paras.file)
            if ('additionalpats' in kwargs
                    and type(kwargs['additionalpats']) is list):
                paras.convert(additionalpats=kwargs['additionalpats'])
            else:
                paras.convert()
            log.verbose("Saving data of '%s' to %s ..." %
                        ('gtc.out', savefile))
            paras.save(casesaver, auto_close=False)
        except Exception:
            log.error('Failed to get data from %s.' % paras.file, exc_info=1)
        # get other data
        for f in sorted(os.listdir(casedir)):
            try:
                fpath = os.path.join(casedir, f)
                if f == 'gtc.out':
                    continue
                elif f in ('data1d.out', 'equilibrium.out',
                           'history.out', 'meshgrid.out'):
                    fcls = GTCFilesMap[f](file=fpath)
                elif self._SnapPattern.match(f):
                    fcls = GTCFilesMap['snapshot.out'](file=fpath)
                elif f == 'trackp_dir':
                    fcls = GTCFilesMap[f](path=fpath)
                else:
                    log.debug("Ignore file '%s'." % fpath)
                    continue
                log.info('Getting data from %s ...' % fcls.file)
                fcls.convert()
                log.verbose("Saving data of '%s' to %s ..." %
                            (fcls.group, savefile))
                fcls.save(casesaver, auto_close=False)
            except Exception:
                log.error('Failed to get data from %s.' % fpath, exc_info=1)
        casesaver.close()

        log.info("GTC '.out' files in %s are converted to %s!" %
                 (casedir, savefile))


def convert(casedir, savefile=None, **kwargs):
    '''
    Convert GTC .out files to a .npz or .hdf5 file.

    Parameters
    ----------
    casedir: path of GTC .out files
    savefile: path of the saved file
    kwargs: other parameters for RawLoader.__init__()
        ``salt``, ``extension``,
        or for RawLoader._convert()
        ``gtcver``, ``description``, ``additionalpats``
    '''
    case = RawLoader(casedir, Sid=True, **kwargs)
    case._convert(savefile=savefile, **kwargs)


def load(path, **kwargs):
    '''
    Load .npz, .hdf5 file or original GTC .out files.
    Return a dictionary-like object: NpzLoader, Hdf5Loader or RawLoader.

    Parameters
    ----------
    path: str
        path of the .npz, .hdf5 file to open
        or path of the directory of GTC .out files
    kwargs: other parameters for RawLoader
        ``gtcver``, ``salt``, ``extension``, ``overwrite``, ``Sid``,
        ``description``, ``additionalpats``
    '''

    if os.path.isdir(path):
        dictobj = RawLoader(path, **kwargs)
    elif os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        if ext == '.npz':
            dictobj = NpzLoader(path)
        elif ext == '.hdf5':
            dictobj = Hdf5Loader(path)
        else:
            raise ValueError("Unsupported Filetype: '%s'!" % ext)
    else:
        raise IOError("Can't find path '%s'!" % path)
    return dictobj
