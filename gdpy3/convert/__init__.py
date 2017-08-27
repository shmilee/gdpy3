# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
    This is the subpackage ``convert`` of package gdpy3.
'''

import os
import time
import re

from . import (gtcout, data1d, equilibrium, history,
               meshgrid, snapshot, trackparticle)
from .. import __version__ as gdpy3_version
from ..glogger import getGLogger

__all__ = ['convert', 'gtcout', 'data1d', 'equilibrium', 'history',
           'meshgrid', 'snapshot', 'trackparticle']

log = getGLogger('gdc')

__FileClassMapDict = {
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
__SnapPattern = re.compile(r'^snap\d{5}\.out$')


def convert(datadir, savepath, **kwargs):
    '''Read all GTC .out files in directory ``datadir``.
    Save the results in ``savepath``.

    Parameters
    ----------
    datadir: str
        the path of GTC .out files
    savepath: str
        path of file which the data is save
    kwargs: other parameters
        ``description`` description of the simulation case
        ``version`` for setting gtc version, default is 110922
        ``additionalpats`` for reading gtc.out

    Notes
    -----
    1) GTC .out files should be named as:
       gtc.out, data1d.out, history.out, snap("%05d" % istep).out, etc.
       so that they can be auto-detected.
    2) ``additionalpats`` should be a list. See gtcout.convert.
    3) The ``savepath`` extension defines the filetype of saved data,
       which may be ``npz`` or ``hdf5``.
       If no one is matched, ".npz" will be adopted.

    Raises
    ------
    IOError
        Can't read .out files in``datadir``, or save file in ``savepath``.
    '''

    if not datadir:
        raise IOError("Please set the path of GTC .out files!")
    if not os.path.isdir(datadir):
        raise IOError("Can't find directory '%s'!" % datadir)
    if not os.access(os.path.dirname(savepath), os.W_OK):
        raise IOError("Can't access directory '%s'!" %
                      os.path.dirname(savepath))
    if not os.path.isfile(os.path.join(datadir, 'gtc.out')):
        raise IOError("Can't find 'gtc.out' in '%s'!" % datadir)

    if 'version' in kwargs and str(kwargs['version']) in __FileClassMapDict:
        __version = str(kwargs['version'])
    else:
        __version = '110922'
    log.info("Set the GTC data version: '%s'." % __version)
    FlClsMp = __FileClassMapDict[__version]

    # description for this case
    desc = ("GTC .out data from directory '%s'.\n"
            "Created by gdpy3 v%s.\n"
            "Created on %s." %
            (datadir, gdpy3_version, time.asctime()))
    if 'description' in kwargs:
        desc = desc + '\n' + str(kwargs['description'])

    # prepare savepath
    saveext = os.path.splitext(savepath)[1]
    # default filetype is '.npz'
    if saveext not in ('.npz', '.hdf5'):
        log.warn("Filetype of savepath should be '.npz' or '.hdf5'!")
        log.info("Use '.npz'.")
        saveext = '.npz'
        savepath = savepath + '.npz'

    # save all data
    def _get_fcls(f):
        if f in ('data1d.out', 'equilibrium.out',
                 'history.out', 'meshgrid.out'):
            return FlClsMp[f](file=os.path.join(datadir, f))
        elif __SnapPattern.match(f):
            return FlClsMp['snapshot.out'](file=os.path.join(datadir, f))
        elif f == 'trackp_dir':
            return FlClsMp[f](path=os.path.join(datadir, f))
        else:
            return None

    if saveext == '.npz':
        try:
            from . import wrapnpz as wrapfile
        except ImportError:
            log.error("Failed to import 'wrapnpz'!")
            raise
    elif saveext == '.hdf5':
        try:
            from . import wraphdf5 as wrapfile
        except ImportError:
            log.error("Failed to import 'wraphdf5'!")
            raise

    if os.path.isfile(savepath):
        log.warn("Remove file: '%s'!" % savepath)
        os.remove(savepath)

    savefid = wrapfile.iopen(savepath)
    log.debug("Saving '/description', '/version' to '%s' ..." % savepath)
    wrapfile.write(savefid, '/', {'description': desc, 'version': __version})
    # get gtc.out parameters
    try:
        paras = FlClsMp['gtc.out'](file=os.path.join(datadir, 'gtc.out'))
        log.info('getting data from %s ...' % paras.file)
        if ('additionalpats' in kwargs
                and type(kwargs['additionalpats']) is list):
            paras.convert(additionalpats=kwargs['additionalpats'])
        else:
            paras.convert()
        log.debug("Saving data of '%s' to '%s' ..." % ('gtc.out', savepath))
        wrapfile.write(savefid, paras.group, paras.data)
    except Exception:
        log.error('Failed to get data from %s.' % paras.file, exc_info=1)
    # get other data
    for f in sorted(os.listdir(datadir)):
        if f == 'gtc.out':
            continue
        fcls = _get_fcls(f)
        if not fcls:
            log.debug("Ignore file '%s'." % os.path.join(datadir, f))
            continue
        try:
            log.info('getting data from %s ...' % fcls.file)
            fcls.convert()
            log.debug("Saving data of '%s' to '%s' ..." %
                      (fcls.group, savepath))
            wrapfile.write(savefid, fcls.group, fcls.data)
        except Exception:
            log.error('Failed to get data from %s.' % fcls.file, exc_info=1)
    wrapfile.close(savefid)

    log.info("GTC '.out' files in %s are converted to %s!" %
             (datadir, savepath))
