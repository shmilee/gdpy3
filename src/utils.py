# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee
'''
Utils.
'''

import os
import re
import sys
import types
import shutil
import importlib
import subprocess

__all__ = [
    'is_dict_like',
    'simple_parse_doc', 'simple_parse_numpydoc', 'inherit_docstring',
    'which_cmds', 'run_child_cmd',
    'find_available_module',
    'GetPasswd',
]


def is_dict_like(obj):
    '''Check if *obj* is dict or dict-like object.'''
    if isinstance(obj, dict):
        return True
    elif str(type(obj)) == "<class 'multiprocessing.managers.DictProxy'>":
        return True
    else:
        for attr in ['__contains__', '__delitem__',
                     '__getitem__', '__iter__', '__setitem__',
                     'get', 'items', 'keys', 'pop', 'update']:
            if not hasattr(obj, attr):
                return False
        return True


def simple_parse_doc(doc, sections=(), strip=None, **kwargs):
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
    kwargs: other unexpected parameters

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
    zip_sections = [(sections[i], *idxs[i])
                    for i in range(len(sections)) if idxs[i] is not None]
    doc_sections = {}
    for i, zip_sect in enumerate(zip_sections):
        sect, idx, start = zip_sect
        if i == len(zip_sections) - 1:
            doc_sect = doc[start:]
        else:
            idx_next = zip_sections[i+1][1]
            doc_sect = doc[start:idx_next]
        doc_sections[sect] = doc_sect.strip(strip)
    return doc_sections


def simple_parse_numpydoc(doc, strip=None, **kwargs):
    '''
    Extract the numpy-like docstring text by sections.
    Return a dict of sections.

    Parameters
    ----------
    doc: str, numpy-like docstring
    strip: str or None.
        If strip is None, remove leading and trailing whitespace in sections.
        Else, remove characters in strip instead.
    kwargs: other unexpected parameters

    References
    ----------
    [1] https://numpydoc.readthedocs.io/en/latest/format.html

    Example
    -------
    >>> doc = simple_parse_numpydoc.__doc__
    >>> simple_parse_numpydoc(doc)
    {'Summary': 'Extract ...',
     'Parameters': 'doc: str, ...',
     'References': '.. [1] ...',
     'Example': ">>> doc ..."}
    '''
    # search by section and ------
    msections = list(re.finditer('^\s+([\w ]+)\n\s+[-]+\n', doc, re.M))
    doc_sections, N = {}, len(msections)
    for i in range(N):
        start, end = msections[i].span()  # group=0, entire match
        name = msections[i].group(1)  # group 1 for [\w ]+
        if i == 0:  # summary section, before first found Section------
            doc_sections['Summary'] = doc[:start].strip(strip)
        if i < N-1:
            nextstart, nextend = msections[i+1].span()
            doc_sections[name] = doc[end:nextstart].strip(strip)
        elif i == N-1:
            doc_sections[name] = doc[end:].strip(strip)
    return doc_sections


def inherit_docstring(*parents, parse=None, parsekwargs=None, template=None):
    '''
    Get parents' __doc__ and format template with them.

    Parameters
    ----------
    parents: tuple
        (parent objects, ...), like class, function etc.
    parse: function
        parse their ``__doc__``, call ``parse(doc, name=name, **funckwargs)``,
        return a dict. default :func:`simple_parse_numpydoc`.
    funckwargs: dict
        some kwargs passed to function *parse*
    template: str
        ``template.format(*args, **kwargs)``, args, kwargs are get by *parse*.
        args is a tuple of parsed dict, kwargs is the first parsed dict.
        If no template, use `object.__doc__`.
    '''
    parse = parse if callable(parse) else simple_parse_numpydoc
    parsekwargs = parsekwargs if isinstance(parsekwargs, dict) else {}
    args = tuple(
        parse(
            getattr(base, '__doc__', None) or '',
            name=getattr(base, '__name__', None) or '',
            **parsekwargs)
        for base in parents)
    kwargs = args[0] if len(args) > 0 else {}

    def decorator(obj):
        if template:
            obj.__doc__ = template.format(*args, **kwargs)
        else:
            obj.__doc__ = obj.__doc__.format(*args, **kwargs)
        return obj

    return decorator


def which_cmds(*candidates):
    '''
    Return first available command in the candidates or None.

    Parameters
    ----------
    candidate: string, or a list of command arguments
    '''
    # pyinstaller frozen check
    if getattr(sys, 'frozen', None):
        path = '{}:{}{sep}bin'.format(*((sys._MEIPASS,)*2), sep=os.sep)
    else:
        path = None
    for c in candidates:
        find = None
        if isinstance(c, list) and len(c) >= 1:
            if path:
                find = shutil.which(c[0], path=path)
            if not find:
                find = shutil.which(c[0])
            if find:
                return [find] + c[1:]
        else:
            if path:
                find = shutil.which(c, path=path)
            if not find:
                find = shutil.which(c)
            if find:
                return find
    return None


def run_child_cmd(args, input=None, **kwargs):
    '''
    Execute a child program *args*.

    Returns
    -------
    A tuple: returncode, stdout, stderr
        If no input, stdout, stderr are string.
        If input is bytes, stdout, stderr are bytes too.

    Parameters
    ----------
    args: A string, or a sequence of program arguments.
    input: str or bytes
        "input" pass to subprocess.Popen.communicate
    kwargs: kwargs pass to subprocess.Popen
    '''
    d_kwargs = dict(universal_newlines=True,  # text=True, added in py 3.7
                    # close_fds=True, # default described in subprocess.Popen
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
    if isinstance(input, bytes):
        d_kwargs['stdin'] = subprocess.PIPE
        d_kwargs['universal_newlines'] = False
        # d_kwargs['text'] = False
    d_kwargs.update(kwargs)
    try:
        proc = subprocess.Popen(args, **d_kwargs)
        stdout, stderr = proc.communicate(input=input)
    except FileNotFoundError:
        if isinstance(input, bytes):
            return 127, b'', b'command not found'
        else:
            return 127, '', 'command not found'
    else:
        return proc.returncode, stdout, stderr


def find_available_module(*candidates):
    '''
    Return first available module object in the candidates or None.
    '''
    for c in candidates:
        if type(c) is types.ModuleType:
            # print('[Pass] module type %s, found!' % c)
            return c
        try:
            module = importlib.import_module(c)
            # print('[Pass] module %s, found!' % c)
            return module
        except Exception:
            # print('[Pass] module %s, not available!' % c)
            pass
    return None


class GetPasswd(object):
    '''Prompt for a password'''
    _call_func = None

    @classmethod
    def set(cls, func):
        '''Set GUI or special function to get password.'''
        cls._call_func = func if callable(func) else None

    @classmethod
    def getpasswd(cls, prompt='Password: '):
        if cls._call_func:
            return cls._call_func(prompt)
        else:
            import getpass
            return getpass.getpass(prompt)
