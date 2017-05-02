# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import gdpy3.read as gdr

log = logging.getLogger('gdr')

if __name__ == '__main__':
    # log.setLevel(20)
    log.setLevel(10)
    datadir = '/home/IFTS_shmilee/phiobo-4-test'
    numpat = r'[-+]?\d+[\.]?\d*[eE]?[-+]?\d*'
    mypats = [r'\*{6}\s+k_r\*rhoi=\s*?(?P<krrhoi>' + numpat + r'?)\s*?,'
              + r'\s+k_r\*rho0=\s*?(?P<krrho0>' + numpat + r'?)\s+?\*{6}',
              r'\*{5}\s+k_r\*dlt_r=\s*?(?P<krdltr>' + numpat + r'?)\s+?\*{5}']
    obj = gdr.read(datadir,
                   description='set kr*rho=0.1, q=1.4, e=0.2',
                   version='110922',
                   extension='hdf5',
                   # extension='npz',
                   additionalpats=mypats)
    print('1. obj.datadir:\n%s\n' % obj.datadir)
    print('2. obj.file:\n%s\n' % obj.file)
    print('3. obj.datakeys:\n%s\n' % str(obj.datakeys))
    print('4. obj.desc:\n%s\n' % obj.desc)
    print('5. obj[obj.datakeys[10]]:\n%s\n' % obj[obj.datakeys[10]])
    print("   obj['gtcout/krdltr']:  %s\n" % obj['gtcout/krdltr'])
    print("   obj['gtcout/krrhoi']:  %s\n" % obj['gtcout/krrhoi'])
    print("6. obj.keys():\n%s\n" % str(obj.keys()))
    print("7. obj.find('phi', 'field'):\n%s\n" % str(obj.find('phi', 'field')))
