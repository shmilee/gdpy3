# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Test data processor.
'''

from . import core

__all__ = ['Base_TDP']


class Base_TDP(object):
    __slots__ = []
    ConverterCores = [
        getattr(core, c)
        for c in core._all_Converters]
    DiggerCores = [
        getattr(core, d)
        for d in core._all_Diggers]
    saltname = 'test.out'
    dig_acceptable_time = 1

    @property
    def _rawsummary(self):
        return "Test '.out' files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)
