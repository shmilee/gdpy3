#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
cache test
'''

import os
import logging
import gdpy3.read as gdr

log = logging.getLogger('gdr')

if __name__ == '__main__':
    # log.setLevel(20)
    log.setLevel(10)
    case = '/home/IFTS_shmilee/2017-D/obo-4T-50dots-0.1'
    dataobj = gdr.read(case,
                       extension='hdf5',
                       #extension='npz',
                       )

    print('1. desc:\n%s\n' % dataobj.desc)
    print('2. datakeys[10]:%s\n%s\n'
          % (dataobj.datakeys[10], dataobj[dataobj.datakeys[10]]))
    keys = ['gtcout/zfkrdltr', 'gtcout/zfkrrhoi', 'gtcout/r0']
    print('3. first: %s\n%s\n' % (keys, dataobj.get_many(*keys)))
    print('4. second: %s\n%s\n'
          % (keys, dataobj.get_many(*keys)))
    keys.extend(['data1d/field00-phi','gtcout/start_date'])
    print('5. first: %s\n%s\n' % (keys, dataobj.get_many(*keys)))
    print('6. cache:\n%s' % dataobj.cache)
