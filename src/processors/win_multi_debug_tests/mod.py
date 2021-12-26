# -*- coding: utf-8 -*-

# Copyright (c) 2021 shmilee

import os
import multiprocessing
from ...glogger import LogWorkInitializer, getGLogger

log = getGLogger('P')
print('HERE-mod:', os.getpid())


class MultiProcessor(object):
    print('HERE-class:', os.getpid())

    def __init__(self, suite):
        self.a = 1
        self.results = suite['dict0']

    def _run(self, b, lock=None):
        self.a += b
        multiprocessing.current_process().name = 'Work%d' % os.getpid()
        log.info('in: %d, pid: %d, out: %d' % (b, os.getpid(), self.a))
        lock.acquire()
        self.results[b] = self.a
        lock.release()
        return self.a

    def run(self, nums=[33, 66, 99, 101, 234, 789]):
        results = []
        manager = multiprocessing.Manager()
        with LogWorkInitializer() as loginitializer:
            lock = manager.RLock()
            with multiprocessing.Pool(processes=4, initializer=loginitializer) as pool:
                async_results = [pool.apply_async(
                    self._run, (b, lock)) for b in nums]
                pool.close()
                pool.join()
            for res in async_results:
                data = res.get()
                results.append(data)
        return results
