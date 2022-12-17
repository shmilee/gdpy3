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


class RawLoaderTest(object):
    ''' Common test methods for RawLoader '''
    RawLoader = None
    RawPath = None
    RawFilenames = {'f1.ignore', 'f1.out', 'd1/f2.out', 'd1/d2/f3.out'}

    def setUp(self):
        self.tmpfile = tempfile.mktemp() + '.' + self.RawLoader.loader_type
        with open(self.tmpfile, mode='w') as f:
            f.write('test')

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def loader_init(self):
        with self.assertRaises(IOError):
            loader = self.RawLoader(self.tmpfile + 'BreakSuffix')
        with self.assertRaises(ValueError):
            loader = self.RawLoader(self.tmpfile)
        loader = self.RawLoader(self.RawPath)
        self.assertSetEqual(set(loader.filenames), self.RawFilenames)
        loader = self.RawLoader(
            self.RawPath, filenames_exclude=[r'(?!^.*\.out$)'])
        self.assertSetEqual(
            set(loader.filenames),
            {f for f in self.RawFilenames if f.endswith('.out')})

    def loader_get(self):
        loader = self.RawLoader(self.RawPath)
        with loader.get('f1.out') as f1:
            self.assertEqual(f1.readlines(), ['test1'])
        with loader.get('d1/f2.out') as f2:
            self.assertEqual(f2.read(), 'test2')
        with self.assertRaises(ValueError):
            f2.read()


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
