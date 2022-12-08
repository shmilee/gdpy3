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
import gzip
import shutil
import tempfile
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
    Read and write jsonlines format file(xxxx.jsonl or xxxx.jsonl-gz).

    Attributes
    ----------
    path: str
        path of '.jsonl' file or gzip-compressed '.jsonl-gz'(.jsonl.gz) file
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

    Notes
    --------
    1. Every record can be any JSON types.
    2. 'index key' should be string or int.
    3. https://jsonlines.org
    4. Gzip-compressed file is not writable, cannot call :meth:`update`.

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
        self.isgzip = False
        if os.path.exists(path):
            if path.endswith('.jsonl-gz'):
                with open(path, 'rb') as f:
                    # ref https://stackoverflow.com/questions/3703276
                    if f.read(2) == b'\x1f\x8b':
                        self.isgzip = True
            if self.isgzip:
                # seek(-2) read(1) too slow for a long index line
                # seek(-1024**6) No OSError, return pos: 0
                with gzip.open(path, 'rb') as f:
                    offset = f.seek(0, os.SEEK_END)
                    step = min(max(128, offset//1024), 4096)
                    # import time #TIME
                    # start = time.time() #TIME
                    offset = f.seek(-step-1, os.SEEK_END)
                    npos = f.read(step).rfind(b'\n')
                    while npos == -1 and offset > 0:  # not found & pos>0
                        offset = f.seek(-step*2, os.SEEK_CUR)
                        npos = f.read(step).rfind(b'\n')
                    f.seek(offset, os.SEEK_SET)
                    last_line = f.readlines()[-1]
                    # cost = time.time() - start #TIME
                    # print(f'index({len(last_line)}) cost {cost:.6f}s') #TIME
                # indexpos for :meth:`update`, disable for gzip, not needed
                self.indexpos = None
            else:
                # ref https://stackoverflow.com/questions/46258499
                with open(path, 'rb') as f:
                    try:
                        f.seek(-2, os.SEEK_END)
                        while f.read(1) != b'\n':
                            f.seek(-2, os.SEEK_CUR)
                    except OSError:  # catch OSError in case: one line file
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
                open_fun = gzip.open if self.isgzip else open
                with open_fun(self.path, 'rt', encoding='utf-8') as f:
                    f.seek(self.index[key][0])
                    rc = json.loads(f.readline())
                    rc = guess_json_strbytes(rc)
                    if self.cache_on:
                        self.read_cache[key] = rc
                    return rc
        else:
            return None

    @staticmethod
    def _test_path_writable(path, overwrite):
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

    def slim_jsonl(self, outpath: str, overwrite: bool = False,
                   recompact: bool = False) -> None:
        ''' Remove backup lines, save to new output file(xxxx.jsonl). '''
        if not self._test_path_writable(outpath, overwrite):
            return
        if recompact:
            dump_kws = dict(ensure_ascii=False, sort_keys=self.sort_keys,
                            separators=(",", ":"))
            recompact_dumps = JsonEncoder(**dump_kws).encode
        open_fun = gzip.open if self.isgzip else open
        with open(outpath, 'w', encoding='utf-8') as out, \
                open_fun(self.path, 'rt', encoding='utf-8') as f:
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

    def finalize(self, outpath: str, overwrite: bool = False,
                 slim_jsonl: bool = False) -> None:
        '''
        Call :meth:`slim_jsonl` when slim_jsonl=True,
        then save all records to gzip file(xxxx.jsonl-gz).
        '''
        if self.isgzip:
            log.error('No need to compress data in %s!' % self.path)
            return
        if not self._test_path_writable(outpath, overwrite):
            return
        if os.path.splitext(outpath)[-1] != '.jsonl-gz':
            log.warning("Recommand using '.jsonl-gz' as file extension!")
        if slim_jsonl:
            # slim to tmp file
            file_dir, file_prefix = os.path.split(outpath)
            fd, tmpfile = tempfile.mkstemp(
                prefix=file_prefix, dir=file_dir, suffix='-tmp.jsonl')
            os.close(fd)
            self.slim_jsonl(tmpfile, overwrite=True, recompact=True)
        else:
            tmpfile = self.path
        with open(tmpfile, 'rb') as f_in:
            with gzip.open(outpath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        if slim_jsonl:
            os.remove(tmpfile)

    def clear_cache(self) -> None:
        self.read_cache = {}
