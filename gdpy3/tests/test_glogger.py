# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import unittest

from .. import glogger


class TestGLoggerMethods(unittest.TestCase):
    '''
    Test GLogger class methods
    '''

    def setUp(self):
        self.gdpy3 = glogger.getGLogger('G')
        self.gdc = glogger.getGLogger('C')
        self.gdp = glogger.getGLogger('P')

    def test_glogger_change_level(self):
        self.gdpy3.handlers[0].setLevel(40)
        self.gdc.handlers[0].setLevel(40)
        self.gdp.handlers[0].setLevel(40)

    def test_glogger_parameter(self):
        self.gdpy3.parameter("PARAMETER")
        self.gdc.parameter("PARAMETER")
        self.gdp.parameter("PARAMETER")

    def test_glogger_verbose(self):
        self.gdpy3.verbose("VERBOSE")
        self.gdc.verbose("VERBOSE")
        self.gdp.verbose("VERBOSE")

    def test_glogger_ddebug(self):
        self.gdpy3.ddebug("DDEBUG")
        self.gdc.ddebug("DDEBUG")
        self.gdp.ddebug("DDEBUG")
