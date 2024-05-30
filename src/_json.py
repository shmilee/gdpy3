#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 shmilee

'''
For jsonlines & json zipfile.
'''

import os
import re
import json
import base64
import numpy as np
import gzip
import tempfile
from typing import Union, Dict, List
from .glogger import getGLogger
from ._zipfile import zipfile_factory, zipfile_copy, ZIP_DEFLATED

__all__ = ['JsonEncoder', 'JsonLines', 'JsonZip']
log = getGLogger('G')
KeyType = Union[str, int]
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


def dumps(obj, *, indent=None, indent_limit=None, cls=JsonEncoder, **kw):
    '''
    Call `json.dumps`. Add kwargs `indent_limit`.
    Use class `JsonEncoder` which supports numpy.

    Printed indent of object members will be eliminated,
    if their indent level bigger than `indent_limit`.

    ref: https://stackoverflow.com/a/72611442
    '''
    res = json.dumps(obj, indent=indent, cls=cls, **kw)
    if indent and indent_limit:
        # fr https://stackoverflow.com/questions/58302531
        pat = re.compile(fr'\n(\s){{{indent_limit}}}((\s)+|(?=(}}|])))')
        return pat.sub('', res)
    else:
        return res


def dump(obj, fp, *, indent=None, indent_limit=None, cls=JsonEncoder, **kw):
    ''' Call :func:`dumps`, then save stream to ``fp`` (file-like object). '''
    res = dumps(obj, indent=indent, indent_limit=indent_limit, cls=cls, **kw)
    fp.write(res)


def test_path_writable(path, overwrite):
    if os.path.exists(path):
        if not overwrite:
            log.error('%s exists! Set overwrite to overwrite it!' % path)
            return False
        if not os.access(path, os.R_OK):
            log.error('%s exists! But not writable!' % path)
            return False
    else:
        if not os.access(os.path.dirname(path), os.R_OK):
            log.error('Dirname of %s is not writable!' % path)
            return False
    return True


class JsonLines(object):
    '''
    Read and write jsonlines format file (xxxx.jsonl)
    or just read compressed file (xxxx.jsonl.gz or xxxx.jsonl-gz).

    Attributes
    ----------
    path: str
        path of '.jsonl' file or gzip-compressed '.jsonl.gz' (.jsonl-gz) file
    isgzip: bool
        is a gzip file or not
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
    seek_step: int
        set seek step for searching index line. default 0, auto-setting

    Notes
    --------
    1. Every record can be any JSON types.
    2. Input 'index key' can be string or int.
       But all 'index key' in jsonl will be converted to string.
    3. https://jsonlines.org
    4. Gzip-compressed file is not writable, cannot call :meth:`update`.
       Reading big gzip-compressed file may be very slow.

    .. code:
        {1st record}
        {2nd record}
        ......
        {last record}
        {index key: (absolute position, line number), ..., __RecordCount__: N}
    '''

    def __init__(self, path: str, sort_keys: bool = False,
                 compact: bool = True, cache_on: bool = False,
                 seek_step: int = 0) -> None:
        self.path = path
        self.isgzip = False
        if os.path.exists(path):
            if path.endswith('.jsonl.gz') or path.endswith('.jsonl-gz'):
                with open(path, 'rb') as f:
                    # ref https://stackoverflow.com/questions/3703276
                    if f.read(2) == b'\x1f\x8b':
                        self.isgzip = True
            open_fun = gzip.open if self.isgzip else open
            # ref: https://stackoverflow.com/questions/46258499
            # seek(-2) read(1) too slow for a long index line
            # seek(-1024**6) gzip: No OSError, return pos: 0
            with open_fun(path, 'rb') as f:
                try:
                    offset = f.seek(0, os.SEEK_END)
                    seek_step = abs(seek_step)
                    step = seek_step or min(max(128, offset//1024), 4096*8)
                    # import time #TIME
                    # start = time.time() #TIME
                    offset = f.seek(-step-1, os.SEEK_END)
                    # While not found & pos>0
                    while f.read(step).find(b'\n') == -1 and offset > 0:
                        offset = f.seek(-step*2, os.SEEK_CUR)
                    f.seek(offset, os.SEEK_SET)
                except OSError:
                    # catch OSError in case: one line text or too large step
                    f.seek(0)
                last_line = f.readlines()[-1]
                # cost = time.time() - start #TIME
                # print(f'index({len(last_line)}) cost {cost:.6f}s') #TIME
                # indexpos for :meth:`update`, disable for gzip, not needed
                if self.isgzip:
                    self.indexpos = None
                else:
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
        # str keys
        return [k for k in self.index if k != '__RecordCount__']

    @staticmethod
    def _not_backup_key(key):
        karr = key.split('-')
        if len(karr) >= 3 and karr[-2] == 'backup':
            return False
        return True

    def keys_without_backup(self):
        # skip backup keys
        return list(filter(self._not_backup_key, self.keys()))

    def update(self, records: Dict[KeyType, RecordType]) -> None:
        '''
        records: dict, like {key: record, ...}
        duplicate key backup: key-backup-0, key-backup-1, etc.
        '''
        if self.isgzip:
            log.error('Not support to record in compressed %s!' % self.path)
            return
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
                if type(key) == int:
                    key = str(key)
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

    def _get_raw_records(self, keys: List[str]) -> List[str]:
        open_fun = gzip.open if self.isgzip else open
        res = []
        with open_fun(self.path, 'rt', encoding='utf-8') as f:
            for key in keys:
                f.seek(self.index[key][0])
                res.append(f.readline())
            return res

    def get_records(self, *keys: List[KeyType]) -> List[RecordType]:
        result, keys_todo = [], []
        for i, key in enumerate(keys):
            if type(key) == int:
                key = str(key)
            if key in self.index:
                if key in self.read_cache:
                    result.append(self.read_cache[key])
                else:
                    result.append(None)
                    keys_todo.extend((i, key))
            else:
                result.append(None)
        if keys_todo:
            records = self._get_raw_records(keys_todo[1::2])
            for i, k, rc in zip(keys_todo[::2], keys_todo[1::2], records):
                result[i] = guess_json_strbytes(json.loads(rc))
                if self.cache_on:
                    self.read_cache[k] = result[i]
        return result

    def get_record(self, key: KeyType) -> RecordType:
        return self.get_records(key)[0]

    def slim(self, outpath: str, overwrite: bool = False,
             recompact: bool = False) -> None:
        '''
        Remove backup lines, save to xxx.jsonl or xxx.jsonl.gz (xxx.jsonl-gz).
        '''
        if not test_path_writable(outpath, overwrite):
            return
        if recompact:
            dump_kws = dict(ensure_ascii=False, sort_keys=self.sort_keys,
                            separators=(",", ":"))
            recompact_dumps = JsonEncoder(**dump_kws).encode
        if outpath.endswith('.jsonl.gz') or outpath.endswith('.jsonl-gz'):
            fun_open_out = gzip.open
        else:
            fun_open_out = open
        fun_open_in = gzip.open if self.isgzip else open
        with fun_open_out(outpath, 'wt', encoding='utf-8') as out, \
                fun_open_in(self.path, 'rt', encoding='utf-8') as f:
            new_index, offset, RecordCount = {}, 0, 0
            for key in self.keys_without_backup():
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

    def finalize(self, outpath: str, overwrite: bool = False) -> None:
        '''
        Call :meth:`slim`, save to gzip file (xxx.jsonl.gz xxx.jsonl-gz).
        '''
        old = outpath
        name, ext = os.path.splitext(outpath)
        if ext == '.gz':
            name, ext = os.path.splitext(name)
            if ext != '.json':
                outpath = name + '.jsonl.gz'
        elif ext == '.jsonl-gz':
            pass
        else:
            outpath = name + '.jsonl.gz'
        if old != outpath:
            log.warning("Change extension: '%s' -> '%s'!" % (old, outpath))
        self.slim(outpath, overwrite=overwrite, recompact=True)

    def clear_cache(self) -> None:
        self.read_cache = {}


class JsonZip(object):
    '''
    Read and write json records in zipfile (xxx.jsonz).
    Each record is saved to a json file named by key (key.json).    

    Attributes
    ----------
    path: str
        path of '.jsonz' file
    record_keys: list
        all records' keys (without extension '.json')
    cache_on: bool
        read cache enabled or not

    Parameters
    ----------
    path: str
    sort_keys: bool
        whether to sort object keys
    cache_on: bool
        whether to enable read cache

    Notes
    -----
    1. :meth:`update_from_jsonl` with compression=ZIP_LZMA runs very slow.
       Example, convert 'xx.converted.jsonl'(6.2G) to 'xx.converted.jsonz'.
       With compression=ZIP_DEFLATED, `2.2G`, `12min`.
       With compression=ZIP_LZMA, `1.7G`, `1h35min`.
    2. Writting with compression=ZIP_LZMA is slow, but reading not affected!
    3. Input record keys can be string or int. But keys in jsonz are string.
    '''

    def __init__(self, path: str, sort_keys: bool = False,
                 cache_on: bool = False) -> None:
        self.path = path
        if os.path.exists(path):
            with zipfile_factory(self.path, mode="r") as z:
                nl = set(n[:-5] for n in z.namelist() if n.endswith('.json'))
            self.record_keys = list(nl)
        else:
            with zipfile_factory(path, mode="w") as z:
                pass
            self.record_keys = []
        dump_kws = dict(ensure_ascii=False, sort_keys=sort_keys,
                        separators=(",", ":"))
        self._dumps = JsonEncoder(**dump_kws).encode
        self.cache_on = cache_on
        self.read_cache = {}

    def keys(self):
        return self.record_keys

    def update(self, records: Dict[KeyType, RecordType],
               compression: int = ZIP_DEFLATED) -> None:
        '''
        records: dict, like {key: record, ...}
        Duplicate keys point to the last record.
        With compression=ZIP_LZMA, writting may be very slow.
        '''
        with zipfile_factory(self.path, mode='a',
                             compression=compression) as z:
            for key in records:
                rc = records[key]
                if type(key) == int:
                    key = str(key)
                try:
                    rc = self._dumps(rc).encode('utf-8')
                    z.writestr(key + '.json', rc)
                except Exception as e:
                    log.error("Failed to record %s: %s!" % (
                        key, rc), exc_info=1)
                else:
                    if key not in self.record_keys:
                        self.record_keys.append(key)

    def update_from_jsonl(self, jsonl: str, redump: bool = False,
                          compression: int = ZIP_DEFLATED) -> None:
        '''
        Update by records get from jsonl file, and ignore backup records.
        '''
        jl = JsonLines(jsonl)
        with zipfile_factory(self.path, mode='a',
                             compression=compression) as z:
            keys = jl.keys_without_backup()
            n = max(len(keys)//100, 10)
            keys = [keys[i:i + n] for i in range(0, len(keys), n)]
            for subkeys in keys:
                # log.info("--- Record %d keys ---" % n)
                try:
                    rcs = jl._get_raw_records(subkeys)
                    # log.info("--- Get raw Done ---")
                    if redump:
                        rcs = [self._dumps(json.loads(rc)) for rc in rcs]
                        # log.info("--- Re-dump Done ---Slow---")
                    for k, rc in zip(subkeys, rcs):
                        z.writestr(k + '.json', rc.encode('utf-8'))
                        if k not in self.record_keys:
                            self.record_keys.append(k)
                    # log.info("--- Write Done ---Slow---")
                except Exception as e:
                    log.error("Failed to record %s in %s!" % (
                        subkeys, jl.path), exc_info=1)

    def get_records(self, *keys: List[KeyType]) -> List[RecordType]:
        result, keys_todo = [], []
        for i, key in enumerate(keys):
            if type(key) == int:
                key = str(key)
            if key.endswith('.json'):
                key = key[:-5]
            if key in self.record_keys:
                if key in self.read_cache:
                    result.append(self.read_cache[key])
                else:
                    result.append(None)
                    keys_todo.extend((i, key))
            else:
                result.append(None)
        if keys_todo:
            with zipfile_factory(self.path, mode="r") as z:
                for i, key in zip(keys_todo[::2], keys_todo[1::2]):
                    rc = z.read(key + '.json').decode('utf-8')
                    result[i] = guess_json_strbytes(json.loads(rc))
                    if self.cache_on:
                        self.read_cache[k] = result[i]
        return result

    def get_record(self, key: KeyType) -> RecordType:
        ''' key or typo key.json '''
        return self.get_records(key)[0]

    def slim(self, outpath: str, overwrite: bool = False) -> None:
        ''' Remove duplicate keys, save to new outpath (xxx.jsonz). '''
        if not test_path_writable(outpath, overwrite):
            return
        if not outpath.endswith('.jsonz'):
            log.warning("Recommand using '.jsonz' as file extension!")
        zipfile_copy(self.path, outpath, remove_duplicate=True)

    finalize = slim

    def clear_cache(self) -> None:
        self.read_cache = {}
