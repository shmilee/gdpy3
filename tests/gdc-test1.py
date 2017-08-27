# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import sys
import gdpy3.convert as gdc
import gdpy3.glogger 

log = gdpy3.glogger.getGLogger('gdc')

if __name__ == '__main__':
    log.setLevel(10)
    log.handlers[0].setLevel(10)
    print(log, log.handlers)
    gdc.convert(
        datadir=sys.argv[1],
        savepath='./gdc-test1.hdf5',
        #savepath='./gdc-test1.npz',
    )
