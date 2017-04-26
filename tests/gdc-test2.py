# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import sys
import logging
import gdpy3.convert as gdc
import gdpy3.convert.datablock as gdcdata

log = logging.getLogger('gdc')

if __name__ == '__main__':
    # log.setLevel(20)
    log.setLevel(10)
    datadir = '/home/IFTS_shmilee/phiobo-4-test'

    example = gdcdata.DataBlock()
    paras = gdc.gtcout.GtcOutV110922(file=datadir + '/gtc.out')
    log.info('getting data from %s ...' % paras.file)
    paras.convert()
    histo = gdc.history.HistoryBlockV110922(file=datadir + '/history.out')
    log.info('getting data from %s ...' % histo.file)
    histo.convert()

    # only example
    example.savez('./test-example.npz')
    # all
    example.savez('./test-all.npz')
    paras.savez('./test-all.npz')
    histo.savez('./test-all.npz')

    # only example
    example.saveh5('./test-example.hdf5')
    # all
    example.saveh5('./test-all.hdf5')
    paras.saveh5('./test-all.hdf5')
    histo.saveh5('./test-all.hdf5')
