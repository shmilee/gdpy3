# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

import os
import unittest
import tempfile
import numpy

from ..base import BaseVisplter


class ImpBaseVisplter(BaseVisplter):
    style_available = ['s1', 's2', 's99', 'gdpy3-test']

    def __init__(self, name):
        super(ImpBaseVisplter, self).__init__(
            name, style=['s99'], example_axes='{d,l,s}')

    def _check_style(self, sty):
        return sty in self.style_available

    def _filter_style(self, sty):
        return '/path/%s.style' % sty

    def _param_from_style(self, param):
        return 'param-%s' % param

    def _add_axes(self, fig, data, layout, axstyle):
        fig['datalist'].append(data)
        fig['layoutlist'].append(layout)
        fig['axstylelist'].append(axstyle)

    def _create_figure(self, num, axesstructures, figstyle):
        # fake figure object: dict
        fig = {'num': num, 'figstyle': figstyle,
               'datalist': [], 'layoutlist': [], 'axstylelist': []}
        for axstructure in axesstructures:
            self.add_axes(fig, axstructure)
        return fig

    def _show_figure(self, fig):
        return fig['num']

    def _close_figure(self, fig):
        pass

    def _save_figure(self, fig, fpath, **kwargs):
        with open(fpath, 'w') as f:
            f.write(fig['num'])

    @staticmethod
    def _tmpl_contourf(*input_list):
        return input_list, []

    @staticmethod
    def _tmpl_line(*input_list):
        return input_list, []

    @staticmethod
    def _tmpl_sharextwinx(*input_list):
        return input_list, []

    @staticmethod
    def _tmpl_z111p(*input_list):
        return input_list, []


class TestBaseVisplter(unittest.TestCase):
    '''
    Test class BaseVisplter
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test')
        self.ImpBaseVisplter = ImpBaseVisplter
        self.visplter = ImpBaseVisplter('test-visplter')

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_visplter_init(self):
        self.assertEqual(self.visplter.name, 'test-visplter')
        self.assertListEqual(self.visplter.style, ['s99'])
        self.assertEqual(self.visplter.example_axes, '{d,l,s}')
        self.assertListEqual(self.visplter.figures, [])

    def test_visplter_style(self):
        style = self.visplter.style
        self.visplter.style = ['s1']
        self.assertListEqual(self.visplter.style, ['s1'])
        self.visplter.style = ['s99']

    def test_visplter_check_style(self):
        self.assertListEqual(
            self.visplter.check_style(['s1', 's10', 's99', 's100']),
            ['s1', 's99'])

    def test_visplter_filter_style(self):
        self.assertListEqual(
            self.visplter.filter_style(['s1', 's10', 'gdpy3-test']),
            ['s1', 's10', '/path/gdpy3-test.style'])

    def test_visplter_param_from_style(self):
        self.assertEqual(self.visplter.param_from_style('tp'), 'param-tp')

    def test_visplter_add_axes(self):
        fig = {'datalist': [], 'layoutlist': [], 'axstylelist': []}
        self.visplter.add_axes(
            fig, dict(data=['data1'], layout=[1, 'layout1'], axstyle=['s1']))
        self.visplter.add_axes(
            fig, dict(data=['data2'], layout=[2, 'layout2'], axstyle=['s9']))
        self.assertListEqual(fig['datalist'], [['data1'], ['data2']])
        self.assertListEqual(fig['layoutlist'],
                             [[1, 'layout1'], [2, 'layout2']])
        self.assertListEqual(fig['axstylelist'], [['s1'], []])

    def test_visplter_create_figure(self):
        fig = self.visplter.create_figure(
            'test-f1',
            dict(data=['data1'], layout=[1, 'layout1'], axstyle=['s1']),
            dict(data=['data2'], layout=[2, 'layout2'], axstyle=['s2']),
            add_style=['gdpy3-test'])
        self.assertEqual(fig['num'], 'test-f1')
        self.assertListEqual(fig['figstyle'], ['s99', 'gdpy3-test'])
        self.assertListEqual(fig['datalist'], [['data1'], ['data2']])
        self.assertListEqual(fig['layoutlist'],
                             [[1, 'layout1'], [2, 'layout2']])
        self.assertListEqual(fig['axstylelist'], [['s1'], ['s2']])

    def test_visplter_get_show_save_figure(self):
        self.visplter.create_figure('test-f2')
        self.assertTrue(isinstance(self.visplter.get_figure('test-f2'), dict))
        self.assertEqual(self.visplter.show_figure('test-f2'), 'test-f2')
        self.visplter.save_figure('test-f2', self.tmpfile)
        with open(self.tmpfile, 'r') as f:
            self.assertEqual(f.read(), 'test-f2')

    def test_visplter_tmpl_contourf(self):
        fun = self.visplter.tmpl_contourf
        calculation = dict(
            X=numpy.array(range(3)),
            Y=numpy.array(range(4)),
            Z=numpy.eye(3, 4),
        )
        axstruct, add_style = fun(calculation)
        self.assertListEqual([], axstruct)
        calculation['Z'] = numpy.eye(4, 3)
        axstruct, add_style = fun(calculation)
        self.assertNotEqual([], axstruct)
        X, Y = numpy.meshgrid(range(3), range(4))
        calculation.update(X=X, Y=Y)
        axstruct, add_style = fun(calculation)
        self.assertNotEqual([], axstruct)
        self.assertIsNone(axstruct[6])
        calculation.update(
            plot_method='contourf',
            title='t', xlabel='x', ylabel='y',
            plot_surface_shadow=['a', 'x', 'c', 'z'],
        )
        axstruct, add_style = fun(calculation)
        self.assertEqual('contourf', axstruct[8])
        self.assertIsNotNone(axstruct[10])
        self.assertListEqual(['x', 'z'], axstruct[-1])

    def test_visplter_tmpl_line(self):
        fun = self.visplter.tmpl_line
        calculation = dict(
            LINE=[
                (range(10), range(10, 0, -1), 'dec'),
                ([3, 6], [5, 7, 8], 'dot2'),
                (numpy.array(range(20)), numpy.linspace(5, 7, 20)),
            ],
        )
        axstruct, add_style = fun(calculation)
        self.assertListEqual([], axstruct)
        calculation['LINE'][1] = ([3, 6], [5, 7], 'dot2')
        axstruct, add_style = fun(calculation)
        self.assertNotEqual([], axstruct)
        self.assertIsNone(axstruct[2])

    def test_visplter_tmpl_sharextwinx(self):
        fun = self.visplter.tmpl_sharextwinx
        calculation = dict(
            X=range(1, 100),
            YINFO=[{
                'left': [(range(100, 1, -1), 'dec'), (range(1, 10), 'inc')],
                'right': [],
            }],
        )
        axstruct, add_style = fun(calculation)
        self.assertListEqual([], axstruct)
        calculation['YINFO'] = [{
            'left': [(range(100, 1, -1), 'dec'), (range(1, 100), 'inc')],
            'right': [(range(10), numpy.array(range(10))), ([1], [2], 'pl')],
        }, ]
        axstruct, add_style = fun(calculation)
        self.assertListEqual(list(calculation['X']), list(axstruct[0]))
        self.assertIsNone(axstruct[3])
        calculation.update(dict(
            hspace=0.1,
            title='t',
            xlabel='x',
            xlim=[1, 50],
            ylabel_rotation=20,
        ))
        axstruct, add_style = fun(calculation)
        self.assertEqual(calculation['hspace'], axstruct[2])
        self.assertEqual(calculation['title'], axstruct[3])
        self.assertEqual(calculation['xlabel'], axstruct[4])
        self.assertListEqual(calculation['xlim'], axstruct[5])
        self.assertEqual(calculation['ylabel_rotation'], axstruct[6])

    def test_visplter_tmpl_z111p(self):
        fun = self.visplter.tmpl_z111p
        calculation = {
            'zip_results': [(
                'tmpl_line', 121,
                dict(LINE=[(range(10), range(10, 0, -1), 'dec'),
                           ([3, 6], [5, 7], 'dot2')],
                     title='f1')
            ), (
                'tmpl_contourf', 122,
                dict(X=numpy.array(range(3)), Y=numpy.array(range(4)),
                     Z=numpy.eye(4, 3))
            )],
            'suptitle': '2figs',
        }
        axstruct, add_style = fun(calculation)
        self.assertListEqual(
            calculation['zip_results'][0][2]['LINE'],
            axstruct[0][0][0])
