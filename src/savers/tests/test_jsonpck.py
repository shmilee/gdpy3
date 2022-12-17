# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest
from . import PckSaverTest
from ..jsonpck import JsonLines, JsonZip, JsonlPckSaver, JsonzPckSaver


class TestJsonlPckSaver(PckSaverTest, unittest.TestCase):
    ''' Test class JsonlPckSaver '''
    PckSaver = JsonlPckSaver

    def test_jsonlsaver_iopen_close(self):
        self.saver_iopen_close()

    def test_jsonlsaver_write(self):
        self.saver_write()

    def saver_get_keys(self, store):
        jl = JsonLines(store)
        return set(k for k in jl.index if k != '__RecordCount__')

    def saver_get(self, store, *keys):
        jl = JsonLines(store)
        return jl.get_records(*keys)

    def test_jsonlsaver_write_str_byte(self):
        self.saver_write_str_byte()

    def test_jsonlsaver_write_num_arr(self):
        self.saver_write_num_arr()

    def test_jsonlsaver_with(self):
        self.saver_with()


class TestJsonzPckSaver(PckSaverTest, unittest.TestCase):
    ''' Test class JsonzPckSaver '''
    PckSaver = JsonzPckSaver

    def test_jsonzsaver_iopen_close(self):
        self.saver_iopen_close()

    def test_jsonzsaver_write(self):
        self.saver_write()

    def saver_get_keys(self, store):
        jz = JsonZip(store)
        return set(jz.record_keys)

    def saver_get(self, store, *keys):
        jz = JsonZip(store)
        return jz.get_records(*keys)

    def test_jsonzsaver_write_str_byte(self):
        self.saver_write_str_byte()

    def test_jsonzsaver_write_num_arr(self):
        self.saver_write_num_arr()

    def test_jsonzsaver_with(self):
        self.saver_with()
