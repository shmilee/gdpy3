# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import numpy

DATA = {
    'description': 'test\ndata',
    'bver': b'v1',
    'test/array': numpy.random.rand(3, 2),
    'test/vector': numpy.random.rand(4),
    'test/float': 3.1415,
    'te/st/int': 1,
}

DATA_C = {
    'description': 'test\ndata',
    'bver': b'v1',
    'test': {
        'array': DATA['test/array'],
        'vector': DATA['test/vector'],
        'float': 3.1415,
    },
    'te/st': {'int': 1},
}

# SFTP_PATH = 'sftp://user[:passwd]@host[:port]##test/path'
SFTP_PATH = None
