# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import sys
import gdpy3.convert.datablock as gdcdata
import gdpy3.convert.gtcout as gtcout
import gdpy3.glogger 

log = gdpy3.glogger.getGLogger('gdc')

if __name__ == '__main__':
    #log.setLevel(10)
    log.handlers[0].setLevel(10)
    print(log, log.handlers)

    datadir = sys.argv[1]

    example = gdcdata.DataBlock('', check_file=False)
    paras = gtcout.GtcOutV110922(file=datadir + '/gtc.out')
    log.info('getting data from %s ...' % paras.file)
    paras.convert()

    # only example
    example.savez('./test-example.npz')
    # all
    example.savez('./test-all.npz')
    paras.savez('./test-all.npz')

    # only example
    example.saveh5('./test-example.hdf5')
    # all
    example.saveh5('./test-all.hdf5')
    paras.saveh5('./test-all.hdf5')
