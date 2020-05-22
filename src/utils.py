# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee
'''
Utils.
'''

import subprocess

__all__ = [
    'is_dict_like',
    'inherit_docstring', 'simple_parse_doc',
    'run_child_cmd',
]


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


def simple_parse_doc(doc, sections, strip=None):
    '''
    Extract the docstring text from the ordered sections.
    Return a dict of sections.

    Parameters
    ----------
    doc: str, docstring
    sections: tuple of ordered sections
    strip: str or None.
        If strip is None, remove leading and trailing whitespace in sections.
        Else, remove characters in strip instead.

    Example
    -------
    .. code:: python

        doc = ('\\n    summary\\n\\n    ABC\\n    ---\\n    abcdefg\\n'
               '\\n    HIJ\\n    ---\\n    hijklmn\\n    ')
        sections = ('ABC', 'HIJ')
        return_doc_sections = {
            'ABC': '---\\n    abcdefg',
            'HIJ': '---\\n    hijklmn'
        }
    '''
    idxs = []
    start = 0
    for sect in sections:
        idx = doc.find(sect + '\n', start)
        if idx == -1:
            idxs.append(None)
        else:
            start = idx + len(sect) + 1
            idxs.append((idx, start))
    doc_sections = {}
    zip_sections = [(sections[i], *idxs[i])
                    for i in range(len(sections)) if idxs[i] is not None]
    for i, zip_sect in enumerate(zip_sections):
        sect, idx, start = zip_sect
        if i == len(zip_sections) - 1:
            doc_sect = doc[start:]
        else:
            idx_next = zip_sections[i+1][1]
            doc_sect = doc[start:idx_next]
        doc_sections[sect] = doc_sect.strip(strip)
    return doc_sections


def run_child_cmd(args, **kwargs):
    '''
    Execute a child program *args*, return returncode, stdout, stderr.

    Parameters
    ----------
    args: A string, or a sequence of program arguments.
    kwargs: kwargs pass to subprocess.Popen
    '''
    d_kwargs = dict(close_fds=True,
                    universal_newlines=True, text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
    d_kwargs.update(kwargs)
    try:
        pipe = subprocess.Popen(args, **d_kwargs)
        stdout, stderr = pipe.communicate()
    except FileNotFoundError:
        return 127, '', 'command not found'
    else:
        return pipe.returncode, stdout, stderr
