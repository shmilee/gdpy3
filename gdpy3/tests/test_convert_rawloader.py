# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile

from .. import glogger
from ..convert import RawLoader
from . import casedir

glogger.getGLogger('gdc').handlers[0].setLevel(60)


class TestRawLoader(unittest.TestCase):
    '''
    Test class RawLoader
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test.npz')
        if not os.path.isfile(os.path.join(casedir, 'gtc.out')):
            raise IOError("Can't find 'gtc.out' in '%s'!" % casedir)

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_rawloader_init(self):
        with self.assertRaises(IOError):
            RawLoader(self.tmpfile)
        with self.assertRaises(IOError):
            RawLoader(os.path.dirname(self.tmpfile))
        casenpz = RawLoader(casedir,
                            extension='.npz',
                            overwrite=True,
                            description='... test desc .npz ...')
        casehd5 = RawLoader(casedir,
                            extension='.hdf5',
                            overwrite=True,
                            description='... test desc .hdf5 ...')
        key = 'gtc/r0'
        self.assertEqual(casenpz[key], casehd5[key])

    def test_rawloader_convert(self):
        case = RawLoader(casedir, Sid=True)
        case._convert(self.tmpfile, description='... test desc Sid ...')
        self.assertTrue(os.path.isfile(self.tmpfile))
