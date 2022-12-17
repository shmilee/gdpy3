# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest

from . import DATA, PckLoaderTest
from ..jsonpck import JsonLines, JsonlPckLoader, JsonZip, JsonzPckLoader


class TestJsonlPckLoader(PckLoaderTest, unittest.TestCase):
    ''' Test class JsonlPckLoader '''
    PckLoader = JsonlPckLoader

    def setUp(self):
        super(TestJsonlPckLoader, self).setUp()
        jl = JsonLines(self.tmpfile)
        jl.update(DATA)

    def test_jsonlloader_init(self):
        self.loader_init()

    def test_jsonlloader_get(self):
        self.loader_get()


class TestJsonzPckLoader(PckLoaderTest, unittest.TestCase):
    ''' Test class JsonzPckLoader '''
    PckLoader = JsonzPckLoader

    def setUp(self):
        super(TestJsonzPckLoader, self).setUp()
        jz = JsonZip(self.tmpfile)
        jz.update(DATA)

    def test_jsonzloader_init(self):
        self.loader_init()

    def test_jsonzloader_get(self):
        self.loader_get()
