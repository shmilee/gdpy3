#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2020 shmilee

import os
import unittest

from HTMLTestRunner import HTMLTestRunner

if __name__ == "__main__":
    start_dir = os.path.join(os.path.dirname(__file__), 'src')
    start_dir = os.path.dirname(__file__)
    print("Loader discover start_dir: '%s'" % start_dir)
    loader = unittest.TestLoader()
    cases = loader.discover(start_dir=start_dir)
    tests = unittest.TestSuite()
    tests.addTests(cases)

    with open("tests-report.html", 'wb') as fo:
        runner = HTMLTestRunner(stream=fo,
                                verbosity=2,
                                title='Gdpy3 Test Report',
                                description='')
        runner.run(tests)
