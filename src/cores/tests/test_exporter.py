# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

import unittest

from ..exporter import Exporter


class TestDigger(unittest.TestCase):
    '''
    Test class Exporter
    '''

    def test_tmpl_contourf_exporter(self):
        core = Exporter('tmpl_contourf')
        self.assertEqual(core.template, 'tmpl_contourf')
        self.assertEqual(core.export(
            {}, {}, plot_method='plot_surface')['results']['plot_method'],
            'plot_surface')
        self.assertEqual(len(core.export_options({})['visoptions']), 8)

    def test_tmpl_line_exporter(self):
        core = Exporter('tmpl_line')
        self.assertEqual(core.template, 'tmpl_line')
        self.assertEqual(core.export({})['template'], 'tmpl_line')

    def test_exporter_fmt(self):
        core = Exporter('tmpl_line')
        self.assertEqual(type(core.export({}, fmt='dict')), dict)
        self.assertEqual(type(core.export({}, fmt='pickle')), bytes)
        self.assertEqual(type(core.export({}, fmt='json')), str)
