# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import gdpy3.convert as gdc

if __name__ == '__main__':
    gdc.convert(
        # datadir='/home/IFTS_shmilee/obo20170421-300600',
        # savepath='./largetest.hdf5',
        datadir='/home/IFTS_shmilee/phiobo-4-test',
        savepath='./test.npz',
        # loglevel='error',
        # loglevel='debug'
    )
