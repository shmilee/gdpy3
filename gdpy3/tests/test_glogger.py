# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import unittest

from .. import glogger


class TestGLoggerMethods(unittest.TestCase):
    '''
    Test GLogger class methods
    '''

    def setUp(self):
        self.gd3 = glogger.getGLogger('gd3')
        self.gdc = glogger.getGLogger('gdc')
        self.gdp = glogger.getGLogger('gdp')

    def test_glogger_change_level(self):
        self.gd3.handlers[0].setLevel(40)
        self.gdc.handlers[0].setLevel(40)
        self.gdp.handlers[0].setLevel(40)

    def test_glogger_parameter(self):
        self.gd3.parameter("PARAMETER")
        self.gdc.parameter("PARAMETER")
        self.gdp.parameter("PARAMETER")

    def test_glogger_verbose(self):
        self.gd3.verbose("VERBOSE")
        self.gdc.verbose("VERBOSE")
        self.gdp.verbose("VERBOSE")

    def test_glogger_ddebug(self):
        self.gd3.ddebug("DDEBUG")
        self.gdc.ddebug("DDEBUG")
        self.gdp.ddebug("DDEBUG")
