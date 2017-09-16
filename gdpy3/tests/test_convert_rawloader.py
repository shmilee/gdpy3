# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile

from .. import glogger
from ..convert import RawLoader
from . import casedir

glogger.getGLogger('C').handlers[0].setLevel(60)


@unittest.skipUnless(os.path.isfile(os.path.join(casedir, 'gtc.out')),
                     "Can't find 'gtc.out' in '%s'!" % casedir)
class TestRawLoader(unittest.TestCase):
    '''
    Test class RawLoader
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test.npz')

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
        self.assertEqual(casenpz.casedir, casedir)
        self.assertRegex(casenpz.desc, 'desc .npz ...')
        self.assertEqual(casenpz['version'], '110922')
        casehd5 = RawLoader(casedir,
                            extension='.hdf5',
                            overwrite=True,
                            description='... test desc .hdf5 ...')
        self.assertEqual(casehd5.casedir, casedir)
        self.assertRegex(casehd5.desc, 'desc .hdf5 ...')
        self.assertEqual(casehd5['version'], '110922')
        for key in ['gtc/r0', 'gtc/b0']:
            self.assertEqual(casenpz[key], casehd5[key])
        self.assertListEqual(sorted(casenpz.datagroups),
                             sorted(casehd5.datagroups))
        self.assertListEqual(sorted(casenpz.datakeys),
                             sorted(casehd5.datakeys))

    def test_rawloader_convert(self):
        case = RawLoader(casedir, Sid=True)
        t = case.casedir, case.file
        with self.assertRaises(AttributeError):
            t = case.desc, case.cache
        case._convert(savefile=self.tmpfile,
                      description='... test desc Sid ...')
        self.assertTrue(os.path.isfile(self.tmpfile))
