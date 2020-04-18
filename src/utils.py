# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee
'''
Utils.
'''

__all__ = ['is_dict_like', 'inherit_docstring']


def is_dict_like(obj):
    '''Check if *obj* is dict or dict-like object.'''
    if isinstance(obj, dict):
        return True
    else:
        for attr in ['__contains__', '__delitem__',
                     '__getitem__', '__iter__', '__setitem__',
                     'get', 'items', 'keys', 'pop', 'update']:
            if not hasattr(obj, attr):
                return False
        return True


def inherit_docstring(parents, func, template=None):
    '''
    Get parents' __doc__ and format template with them.

    Parameters
    ----------
    parents: tuple
        (parent objects, ...), like class, function etc.
    func: function to deal with their __doc__
        input is a list of (name, doc), return args(tuple), kwargs(dict)
    template: str
        template.format(*args, **kwargs), args, kwargs are get by func
        if no template, use object.__doc__
    '''
    parents_docstr = [(base.__name__, base.__doc__) for base in parents]
    args, kwargs = func(parents_docstr)

    def decorator(obj):
        if template:
            obj.__doc__ = template.format(*args, **kwargs)
        else:
            obj.__doc__ = obj.__doc__.format(*args, **kwargs)
        return obj

    return decorator
