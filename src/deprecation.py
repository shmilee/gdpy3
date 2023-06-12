#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Helper functions for deprecating parts of Gdpy3's API
ref: matplotlib._api.deprecation
'''

import warnings
from .__about__ import VERSION
from .glogger import getGLogger

log = getGLogger('G')


class Gdpy3DeprecationWarning(DeprecationWarning):
    """A class for issuing deprecation warnings for Gdpy3 users."""


def _generate_deprecation_warning(
        since, removal, name, obj_type='', alternative='', addendum=''):
    '''since, removal : str'''
    message = (
        ("The %(name)s %(obj_type)s" if obj_type else "%(name)s")
        + (" was deprecated in Gdpy3 %(since)s")
        + (" and will be removed in %(removal)s.")
        + (" Use %(alternative)s instead." if alternative else "")
        + (" %(addendum)s" if addendum else ""))
    return Gdpy3DeprecationWarning(message % dict(
        name=name, obj_type=obj_type, since=since, removal=removal,
        alternative=alternative, addendum=addendum))


def warn_deprecated(since, removal, name, obj_type='',
                    alternative='', addendum='',
                    use_warnings=False, stacklevel=2):
    '''
    Display a standardized deprecation.

    Parameters
    ----------
    since: 3-tuple
        The release at which this API became deprecated, like triple (0, 9, 9).
    removal: 3-tuple
        The expected removal version.
    name: str, optional
        The name of the deprecated object.
    obj_type: str, optional
        The object type being deprecated.
    alternative: str, optional
        Alternative API that the user may use in place of the deprecated API.
    addendum: str, optional
        Additional text appended directly to the final message.
    use_warnings: bool, optional
        use `warnings` to display or not
    stacklevel: `warnings.warn` parameter, optional
    '''
    if VERSION >= since:
        since = '.'.join(map(str, since))
        removal = '.'.join(map(str, removal))
        w = _generate_deprecation_warning(
            since, removal, name, obj_type, alternative, addendum)
        if use_warnings:
            with warnings.catch_warnings():
                warnings.simplefilter("default")
                warnings.warn(w, category=Gdpy3DeprecationWarning,
                              stacklevel=stacklevel)
        else:
            log.warning('%r' % w)
