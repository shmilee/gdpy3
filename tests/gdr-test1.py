# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import sys
import gdpy3.read as gdr
import gdpy3.glogger

log = gdpy3.glogger.getGLogger('gdr')


if __name__ == '__main__':
    log.setLevel(20)
    #log.handlers[0].setLevel(10)
    print(log, log.handlers)
    dataobj = gdr.read(path=sys.argv[1],
                       description='... test desc test ...',
                       version='110922',
                       extension='hdf5',
                       #extension='npz',
                       overwrite=True,
                       )
    print('1. desc:\n%s\n' % dataobj.desc)
    print('2. file:\n%s\n' % dataobj.file)
    print('3. datakeys[10]]:\n%s\n' % dataobj[dataobj.datakeys[10]])
    print("   dataobj['gtc/r0']:  %s\n" % dataobj['gtc/r0'])
    print("4. dataobj.find('phi', 'field'):\n%s\n" %
          str(dataobj.find('phi', 'field')))

    keys = ['gtc/b0', 'gtc/rho0']
    print('5. first: %s\n%s\n' % (keys, dataobj.get_many(*keys)))
    print('6. second: %s\n%s\n' % (keys, dataobj.get_many(*keys)))
    keys.extend(['data1d/field00-phi', 'gtc/start_date'])
    print('7. first: %s\n%s\n' % (keys, dataobj.get_many(*keys)))
    print('8. cache:\n%s' % dataobj.cache)
