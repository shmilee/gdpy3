# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Run me in different terminals.
'''

import sys
import unittest

from ..imgcat import Display


class TestDisplay(unittest.TestCase):
    '''
    Test class :py:class:`imgcat.Display`
    '''

    def setUp(self):
        self.imcat = Display(max_width=800)

    def test_imcat_init(self):
        self.assertTrue(isinstance(self.imcat.cmd, (str, type(None))))
        self.assertTrue(isinstance(self.imcat.mod, (type(sys), type(None))))
        #self.assertTrue(self.imcat.output == sys.stdout)
        self.assertEqual(self.imcat.max_width, 800)


def test_dispaly_mplfig(imcat=None):
    from ..mplvisplter import MatplotlibVisplter
    from .test_mplvisplter import temp_lineresults

    visplter = MatplotlibVisplter('mpl::test')
    visplter.style = ['gdpy3-notebook', {'figure.figsize': (15.0, 12.0)}]
    axstruct, sty = visplter.tmpl_line(temp_lineresults)
    fig = visplter.create_figure('test-line', *axstruct, add_style=sty)
    imcat = imcat if isinstance(imcat, Display) else Display(max_width=1000)
    imcat.show_attr_info()
    input('[I]nterrupt, to see imcat info')

    imcat.display(fig)
    input('[I]nterrupt, to see figure size 1000x800')
    imcat.display(fig, width=500)
    input('[I]nterrupt, to see figure size 500x400')
    imcat.display(fig, height=500)
    input('[I]nterrupt, to see figure size 625x500')
    imcat.display(fig, width=50)
    input('[I]nterrupt, to see figure size 50x40, for cell count only!')
    imcat.display(fig, width=500, usemod=True)
    input('[I]nterrupt, to see figure size 500x400, usemod=True')


def test_dispaly_file(path, imcat=None):
    imcat = imcat if isinstance(imcat, Display) else Display(max_width=1366)
    imcat.show_attr_info()
    input('[I]nterrupt, to see imcat info')
    with open(path, 'rb') as f:
        data = f.read()
    for put in (path, data):
        input('[I]nterrupt, the input image is %s' % type(put))
        imcat.display(put)
        input('[I]nterrupt, to see image original size')
        imcat.display(put, width=500)
        input('[I]nterrupt, to see image width 500')
        imcat.display(put, height=500)
        input('[I]nterrupt, to see image height 500')
        imcat.display(put, width=50)
        input('[I]nterrupt, to see image width 50, for cell count only!')
        imcat.display(put, width=500, usemod=True)
        input('[I]nterrupt, to see image width 500, usemod=True')
