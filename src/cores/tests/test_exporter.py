# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import unittest

from ..exporter import TmplLoader, ContourfExporter, LineExporter


class TestDigger(unittest.TestCase):
    '''
    Test class Exporter
    '''

    def setUp(self):
        self.ldr = TmplLoader()

    def test_contourf_Exporter_core(self):
        cores = ContourfExporter.generate_cores(self.ldr, self.ldr.templates)
        self.assertEqual(len(cores), 1)
        self.assertEqual(cores[0].template, 'tmpl-contourf')
        self.assertEqual(cores[0].export(
            {}, plot_method='plot_surface')['results']['plot_method'],
            'plot_surface')
        self.assertEqual(len(cores[0].export_options({})['visoptions']), 4)

    def test_line_exporter_core(self):
        cores = LineExporter.generate_cores(self.ldr, self.ldr.templates)
        self.assertEqual(len(cores), 1)
        self.assertEqual(cores[0].template, 'tmpl-line')
        self.assertEqual(cores[0].export(
            {})['template'], 'template_line_axstructs')

    def test_exporter_core_fmt(self):
        cores = LineExporter.generate_cores(self.ldr, self.ldr.templates)
        self.assertEqual(type(cores[0].export({}, fmt='dict')), dict)
        self.assertEqual(type(cores[0].export({}, fmt='pickle')), bytes)
        self.assertEqual(type(cores[0].export({}, fmt='json')), str)
