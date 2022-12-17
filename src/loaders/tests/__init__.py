# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import tempfile
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


class PckLoaderTest(object):
    ''' Common test methods for PckLoader '''
    PckLoader = None

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + self.PckLoader.loader_type

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def loader_init(self, path=None):
        loader = self.PckLoader(path or self.tmpfile)
        self.assertSetEqual(set(loader.datakeys), set(DATA.keys()))
        self.assertSetEqual(set(loader.datagroups), {'test', 'te/st'})
        self.assertMultiLineEqual(loader.description, DATA['description'])

    def loader_get(self, path=None):
        loader = self.PckLoader(path or self.tmpfile)
        self.assertEqual(loader.get('bver'), DATA['bver'])
        self.assertTrue(
            numpy.array_equal(loader.get('test/array'), DATA['test/array']))
        self.assertEqual(loader.get('test/float'), 3.1415)
        self.assertEqual(loader.get('te/st/int'), 1)
