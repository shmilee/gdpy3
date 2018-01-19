# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import numpy

DATA = {
    'description': 'test data',
    'test/array': numpy.random.rand(3, 2),
    'test/vector': numpy.random.rand(4),
    'test/float': 3.1415,
}

DATA_C = {
    'description': 'test data',
    'test': {
        'array': DATA['test/array'],
        'vector': DATA['test/vector'],
        'float': 3.1415,
    },
}

# SFTP_PATH = 'sftp://user[:passwd]@host[:port]##test/path'
SFTP_PATH = None
