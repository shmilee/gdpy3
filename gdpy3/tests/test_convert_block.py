# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy
import unittest
import tempfile

from .. import glogger
from ..convert import block

glogger.getGLogger('C').handlers[0].setLevel(60)


class TestBlock(unittest.TestCase):
    '''
    Test class Block
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test.npz')

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_block_init(self):
        outfile = os.path.join(self.tmpfile, 'group.out')
        with self.assertRaises(IOError):
            block.Block(outfile)
        outblock = block.Block(outfile, check_file=False)
        self.assertEqual(outblock.file, outfile)
        self.assertEqual(outblock.group, 'group')
        self.assertEqual(outblock.datakeys, ('description',))

    def test_block_save(self):
        db = block.Block(file='', group='grp', check_file=False)
        db.data.update({'a': 100, 'b': 200})
        saver = block.NpzSaver(self.tmpfile)
        add_data = [('group1', {'a': 1, 'b': 2}),
                    ('group2', {'a': 4, 'b': 6})]
        db.save(saver)
        with self.assertWarns(UserWarning):
            db.save(saver, additional=add_data)
        db.save(saver, additional=add_data, deal_with_npz='new')
