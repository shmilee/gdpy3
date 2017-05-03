# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import gdpy3.read as gdr

log0 = logging.getLogger('test')
log1 = logging.getLogger('gdc')
log2 = logging.getLogger('gdr')

if __name__ == '__main__':
    log0.setLevel(10)
    log1.setLevel(20)
    log2.setLevel(20)

    numpat = r'[-+]?\d+[\.]?\d*[eE]?[-+]?\d*'
    mypats = [r'\*{6}\s+k_r\*rhoi=\s*?(?P<krrhoi>' + numpat + r'?)\s*?,'
              + r'\s+k_r\*rho0=\s*?(?P<krrho0>' + numpat + r'?)\s+?\*{6}',
              r'\*{5}\s+k_r\*dlt_r=\s*?(?P<krdltr>' + numpat + r'?)\s+?\*{5}']

    # walk
    for root, dirs, files in os.walk('/home/IFTS_shmilee/2017-D'):
        if 'gtc.out' in files:
            obj = gdr.read(root,
                           description='deuterium, q=1.4, e=0.2',
                           #extension='npz',
                           extension='hdf5',
                           overwrite=True,
                           additionalpats=mypats)
            # check
            print()
            log0.info("'krdltr': %s, 'krrho0': %s, 'krrhoi': %s" %
                      (obj['gtcout/krdltr'], obj['gtcout/krrho0'],
                          obj['gtcout/krrhoi']))
            print()
