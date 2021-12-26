# -*- coding: utf-8 -*-

# Copyright (c) 2021 shmilee

import os
import multiprocessing
from .mod import MultiProcessor
print('HERE-init:', os.getpid())


def get_proc():
    print('HERE-init-def:', os.getpid())
    manager = multiprocessing.Manager()
    suite = {'dict0': manager.dict(), 'list0': manager.list()}
    return MultiProcessor(suite)
