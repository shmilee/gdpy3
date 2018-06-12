# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import unittest

from . import SFTP_PATH


@unittest.skipUnless(SFTP_PATH, "requires SFTP_PATH to connect SSH server!")
class TestSftpRawLoader(unittest.TestCase):
    '''
    Test class SftpRawLoader
    '''

    def setUp(self):
        from ..sftpraw import SftpRawLoader
        self.SftpRawLoader = SftpRawLoader

    def test_sftploader_init(self):
        with self.assertRaises(IOError):
            loader = self.SftpRawLoader('Break/path')
        loader = self.SftpRawLoader(
            SFTP_PATH,
            filenames_filter=lambda n: True if n == 'gtc.out' else False)
        self.assertTupleEqual(loader.filenames, ('gtc.out',))

    def test_sftploader_get(self):
        loader = self.SftpRawLoader(
            SFTP_PATH,
            filenames_filter=lambda n: True if n == 'gtc.out' else False)
        with loader.get('gtc.out') as f1:
            f1.readline()
            self.assertEqual(
                f1.readline(), '===================================\n')
        with self.assertRaises(ValueError):
            f1.read()
