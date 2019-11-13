# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Contains core base class.
'''

import re

from ..glogger import getGLogger

__all__ = ['BaseCore']
log = getGLogger('G')


class BaseCore(object):
    '''
    Base core class for Converter, Digger, Exporter.

    Match input items with :attr:`itemspattern` and :attr:`commonpattern`,
    then group them in :attr:`section`.

    Attributes
    ----------
    loader: loader object to get data
    nitems: '?' or '+'
        '?', take only one item; '+', more than one
    itemspattern: list
        complementary regular expressions for items
        First one is major, and contains all section names,
        while others can be partial.
        So combine (S1, S2) and (S1) to join section (S1, S2).
    commonpattern: list
        complementary regular expressions for common items
    section: tuple
    items: list
    common: list

    Parameters
    ----------
    items: loader keys
    '''
    __slots__ = ['loader', 'section', 'items', 'common']
    nitems = '?' or '+'
    itemspattern = ['^(?P<section1>sect)-(?P<section2>item)$']
    commonpattern = []

    @property
    def coreid(self):
        return type(self).__name__

    @classmethod
    def match_items(cls, all_items):
        '''
        Return {section: items} matched with :attr:`itemspattern`
        in list *all_items*.
        After (S1, S2), (S1, S2.1) found, (S1) will join in all of them.
        '''
        res = {}
        for pat in cls.itemspattern:
            for it in all_items:
                m = re.match(pat, it)
                if m:
                    sect = m.groups()
                    if sect in res:
                        res[sect].append(it)
                    else:
                        subkey = False
                        for key in res.keys():
                            if set(sect).issubset(set(key)):
                                res[key].append(it)
                                subkey = True
                        if not subkey:
                            res[sect] = [it]
        return res

    @classmethod
    def match_common(cls, all_items):
        '''
        Return items matched with :attr:`commonpattern` in list *all_items*.
        '''
        res = []
        for pat in cls.commonpattern:
            for it in all_items:
                if re.match(pat, it):
                    res.append(it)
        return res

    @classmethod
    def generate_cores(cls, loader, all_items, duplicate=None):
        '''
        Use *loader* and matched items in *all_items* to
        generate Core instances.

        Parameters
        ----------
        loader: rawloader or pckloader ...
        all_items: loader keys or part of them ...
        duplicate: list, len(list) duplicates for each core
        '''
        matched_items = cls.match_items(all_items)
        if len(matched_items) == 0:
            log.debug("%s: No items matched in loader %s!"
                      % (cls.__name__, loader.path))
            return []
        if cls.commonpattern:
            common = cls.match_common(all_items)
        else:
            common = None
        if duplicate:
            return [[cls(loader, section, matched_items[section], common)
                     for _ in duplicate]
                    for section in matched_items]
        else:
            return [cls(loader, section, matched_items[section], common)
                    for section in matched_items]

    def __init__(self, loader, section, items, common):
        self.loader = loader
        self.section = section
        if self.nitems == '?':
            if not len(items) == 1:
                raise ValueError("%s: must passing only one item, not '%s'!"
                                 % (self.coreid, len(items)))
        else:
            if not len(items) >= 1:
                raise ValueError("%s: must passing >= 1 items, not '%s'!"
                                 % (self.coreid, len(items)))
        self.items = items
        self.common = common
