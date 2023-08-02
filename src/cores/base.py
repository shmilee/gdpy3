# -*- coding: utf-8 -*-

# Copyright (c) 2019-2020 shmilee

'''
Contains core base class.
'''

import re
import time
import types
import functools

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
    def clsname(self):
        return type(self).__name__

    match_cache = {}

    @classmethod
    def match_items(cls, all_items):
        '''
        Return {section: items} matched with :attr:`itemspattern`
        in list *all_items*.
        After (S1, S2), (S1, S2.1) found, (S1) will join in all of them.
        '''
        res = {}
        match_tuple = (tuple(cls.itemspattern), tuple(all_items))
        if match_tuple in cls.match_cache:
            log.debug("%s: Using match-cache for %s"
                      % (cls.__name__, cls.itemspattern))
            return cls.match_cache[match_tuple]
        start = time.time()
        # first pat
        pat = re.compile(cls.itemspattern[0])
        for itm in filter(None, map(pat.match, all_items)):
            sect, it = itm.groups(), itm.string
            if sect in res:
                res[sect].append(it)
            else:
                res[sect] = [it]
        # others
        for pat in map(re.compile, cls.itemspattern[1:]):
            for itm in filter(None, map(pat.match, all_items)):
                sect, it = itm.groups(), itm.string
                if sect in res:
                    res[sect].append(it)
                else:
                    subkey = False
                    _issub = set(sect).issubset
                    for key in filter(lambda k: _issub(set(k)), res.keys()):
                        res[key].append(it)
                        subkey = True
                    if not subkey:
                        res[sect] = [it]
        cls.match_cache[match_tuple] = res
        end = time.time()
        log.debug("%s: %d items matched, costs %.1fs."
                  % (cls.__name__, len(res), end-start))
        return res

    @classmethod
    def match_common(cls, all_items):
        '''
        Return items matched with :attr:`commonpattern` in list *all_items*.
        '''
        res = []
        for pat in map(re.compile, cls.commonpattern):
            res.extend(filter(pat.match, all_items))
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
        common = cls.match_common(all_items)
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
                                 % (self.clsname, len(items)))
        else:
            if not len(items) >= 1:
                raise ValueError("%s: must passing >= 1 items, not '%s'!"
                                 % (self.clsname, len(items)))
        self.items = items
        self.common = common


class AppendDocstringMeta(type):
    """
    Append docstring from one method(_xxyyzz) to another method(xxyyzz).

    This will affect inherited classes, so their Implemented method(_xxyyzz)
    docstring can be get in method(xxyyzz). We cannot simply modify the
    docstring of method(xxyyzz), because that will mess up their subclasses'
    method docstrings. Instead, we must actually copy the functions,
    and then modify the docstring for each subclasses.

    The subclass must have method(_xxyyzz) and its docstring is not None,
    otherwise nothing is modified in this subclass. Only choose the first
    baseclass which has method(xxyyzz) in subclass.__mro__,
    copy its method(xxyyzz) and combine docstrings.
    """
    _xxyyzz_methods = ['_convert', '_dig', '_export']

    def __new__(meta, name, bases, attrs):
        attr_todo = [an for an in attrs if an in meta._xxyyzz_methods]
        for attr_name in attr_todo:
            # print('found', attr_name, 'in', name)
            apdoc = attrs[attr_name].__doc__
            if not apdoc:
                continue
            sattr_name = attr_name[1:]
            # print(name, 'bases to check', bases)
            for base in bases:
                original = getattr(base, sattr_name, None)
                if original:
                    # print('using parent', base, sattr_name)
                    # copy function
                    copy = _copy_func(original)
                    ordoc = original.__doc__
                    copy.__doc__ = '%s%s' % (ordoc, apdoc)
                    attrs[sattr_name] = copy
                    break
        return type.__new__(meta, name, bases, attrs)


def _copy_func(f):
    '''ref: http://stackoverflow.com/a/13503277/2289509'''
    new_f = types.FunctionType(f.__code__, f.__globals__, name=f.__name__,
                               argdefs=f.__defaults__, closure=f.__closure__)
    new_f = functools.update_wrapper(new_f, f)
    new_f.__kwdefaults__ = f.__kwdefaults__
    return new_f
