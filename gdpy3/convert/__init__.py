# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    This is the subpackage ``convert`` of package gdpy3.
'''

__all__ = ['convert', 'data1d', 'gtcout', 'history', 'snapshot']

import os
from . import data1d, gtcout, history, snapshot

__FileClassMapDict = {
    '110922': {
        'gtc.out': gtcout.GtcOutV110922,
        'data1d.out': data1d.Data1dBlockV110922,
        'history.out': history.HistoryBlockV110922,
        'snapshot.out': snapshot.SnapshotBlockV110922,
    }
}


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
       which may be ``npz``, ``hdf5`` or ``mat``.
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
    if 'version' in kwargs and str(kwargs['version']) in __FileClassMapDict:
        __version = str(kwargs['version'])
    else:
        __version = '110922'
    FlClsMp = __FileClassMapDict[__version]

    # get gtc.out parameters
    if not os.path.isfile(datadir + '/gtc.out'):
        raise IOError("Can't find 'gtc.out' in '%s'!" % datadir)
    paras = FlClsMp['gtc.out'](file=datadir + '/gtc.out')
    if 'additionalpats' in kwargs and type(kwargs['additionalpats']) is list:
        paras.convert(additionalpats=kwargs['additionalpats'])
    else:
        paras.convert()

    # convert other .out files
    otherfiles = {}
    for f in os.listdir(datadir):
        if f in ('data1d.out', 'history.out'):
            otherfiles[f] = FlClsMp[f](file=datadir + '/' + f)
        elif 'the-snap' in 'the-' + f:
            otherfiles[f] = FlClsMp['snapshot.out'](file=datadir + '/' + f)
    otherdatas = []
    for key, fcls in otherfiles.items():
        try:
            fcls.convert()
        except:
            print('Failed to get data from %s.' % datadir + '/' + key)
        otherdatas.append((fcls.name, fcls.data))

    # description for this case
    desc = ("GTC .out data from directory '%s'.\n"
            "Created by gdpy3.convert, '%s'.\n" %
            (datadir, __version))
    if 'description' in kwargs:
        desc = desc + '\n' + str(kwargs['description'])
    otherdatas.append(('/', {'description': desc}))

    # save all data
    saveext = os.path.splitext(savepath)[1]
    if saveext == '.npz':
        paras.save2npz(savepath, additional=otherdatas)
    elif saveext == '.hdf5':
        paras.save2hdf5(savepath, additional=otherdatas)
    elif saveext == '.mat':
        # paras.save2mat(savepath,additional=otherdatas)
        # TODO(nobody): '.mat' is not ready. Use '.npz'
        savepath = savepath + '.npz'
        paras.save2npz(savepath, additional=otherdatas)
    else:
        savepath = savepath + '.npz'
        paras.save2npz(savepath, additional=otherdatas)

    print('GTC .out files in %s are converted to %s!' % (datadir, savepath))
