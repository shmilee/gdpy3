#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 shmilee

'''
For jsonlines.
'''

import os
import json
import base64
import numpy as np
from typing import Union, Dict
from .glogger import getGLogger

__all__ = ['JsonEncoder', 'JsonLines']
log = getGLogger('G')
RecordType = Union[dict, list, str, int, float, bool, bytes, None,
                   np.integer, np.floating, np.ndarray]


class JsonEncoder(json.JSONEncoder):
    ''' Support numpy int, float, array and bytes. '''

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return 'base64(%s)64b' % base64.b64encode(obj).decode('utf8')
            # return 'base85(%s)' % base64.b85encode(obj).decode('utf8')
        else:
            return super(JsonEncoder, self).default(obj)


def guess_json_strbytes(s):
    ''' Get bytes from string 'base64(%s)64b'. '''
    if type(s) == str and s.startswith('base64(') and s.endswith(')64b'):
        return base64.b64decode(s[7:-4])
    else:
        return s


class JsonLines(object):
    '''
    Read and write jsonlines format file(xxxx.jsonl).

    Attributes
    ----------
    path: str
        path of the jsonl file
    index: dict
        index dict for all records
    sort_keys: bool
        sort object keys enabled or not
    cache_on: bool
        read cache enabled or not

    Parameters
    ----------
    path: str
    sort_keys: bool
        whether to sort object keys
    compact: bool
        whether to eliminate whitespace to get compact JSON representation
    cache_on: bool
        whether to enable read cache

    Data
    --------
    1. Every record can be any JSON types.
    2. 'index key' should be string or int.
    3. https://jsonlines.org

    .. code:
        {1st record}
        {2nd record}
        ......
        {last record}
        {index key: (absolute position, line number), ..., __RecordCount__: N}
    '''

    def __init__(self, path: str, sort_keys: bool = False,
                 compact: bool = True, cache_on: bool = False) -> None:
        self.path = path
        if os.path.exists(path):
            # ref https://stackoverflow.com/questions/46258499
            with open(path, 'rb') as f:
                try:  # catch OSError in case of a one line file
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                except OSError:
                    f.seek(0)
                last_line = f.readline()
                # len(bytes) -> offset
                self.indexpos = f.seek(-len(last_line), os.SEEK_END)
                self.index = json.loads(last_line.decode('utf-8'))
        else:
            self.indexpos = 0
            self.index = {'__RecordCount__': 0}
        # ref https://github.com/wbolster/jsonlines
        dump_kws = dict(ensure_ascii=False, sort_keys=sort_keys,  # UTF-8
                        separators=(",", ":") if compact else None)
        self.sort_keys = sort_keys
        self._dumps = JsonEncoder(**dump_kws).encode
        self.cache_on = cache_on
        self.read_cache = {}

    def keys(self):
        return [k for k in self.index if k != '__RecordCount__']

    def update(self, records: Dict[Union[str, int], RecordType]) -> None:
        '''
        records: dict, like {key: record, ...}
        duplicate key backup: key-backup-0, key-backup-1, etc.
        '''
        with open(self.path, 'a+', encoding='utf-8') as f:
            # truncate index
            f.seek(self.indexpos)
            f.truncate()
            # add new records
            offset = self.indexpos
            for key in records:
                try:
                    line = self._dumps(records[key]) + '\n'
                except Exception as e:
                    log.error("Failed to record %s: %s!" % (
                        key, records[key]), exc_info=1)
                    continue
                f.write(line)
                if key in self.index:
                    for i in range(999):
                        backkey = '%s-backup-%d' % (key, i)
                        if backkey not in self.index:
                            break
                    log.debug('Backup record: %s -> %s' % (key, backkey))
                    self.index[backkey] = self.index[key]
                self.index['__RecordCount__'] += 1
                # set (absolute position, line number)
                self.index[key] = (offset, self.index['__RecordCount__'])
                offset += len(line.encode('utf-8'))
            # add new index line
            self.indexpos = offset
            line = self._dumps(self.index) + '\n'
            f.write(line)

    def get_record(self, key: Union[str, int]) -> RecordType:
        if key in self.index:
            if key in self.read_cache:
                return self.read_cache[key]
            else:
                with open(self.path, 'r', encoding='utf-8') as f:
                    f.seek(self.index[key][0])
                    rc = json.loads(f.readline())
                    rc = guess_json_strbytes(rc)
                    if self.cache_on:
                        self.read_cache[key] = rc
                    return rc
        else:
            return None

    def slim_jsonl(self, outpath: str, overwrite: bool = False,
                   recompact: bool = False) -> None:
        ''' Remove backup lines, save to new output file. '''
        if os.path.exists(outpath) and not overwrite:
            log.error('%s exists! Set overwrite to overwrite it!' % outpath)
            return
        if recompact:
            dump_kws = dict(ensure_ascii=False, sort_keys=self.sort_keys,
                            separators=(",", ":"))
            recompact_dumps = JsonEncoder(**dump_kws).encode
        with open(outpath, 'w', encoding='utf-8') as out, \
                open(self.path, 'r', encoding='utf-8') as f:
            new_index, offset, RecordCount = {}, 0, 0
            for key in [k for k in self.index if k != '__RecordCount__']:
                karr = key.split('-')
                if len(karr) >= 3 and karr[-2] == 'backup':
                    continue  # skip backup lines
                f.seek(self.index[key][0])
                line = f.readline()  # contains '\n'
                if recompact:
                    rc = json.loads(line)
                    line = recompact_dumps(rc) + '\n'
                out.write(line)
                RecordCount += 1
                new_index[key] = (offset, RecordCount)
                offset += len(line.encode('utf-8'))
            new_index['__RecordCount__'] = RecordCount
            line = self._dumps(new_index) + '\n'
            out.write(line)

    def clear_cache(self) -> None:
        self.read_cache = {}
