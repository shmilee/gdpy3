# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Gdpy3's logger module.

* [G]dp: gdpy3
* [L]oad: loaders
* [S]ave: savers
* [C]onvert: converters
* [D]ig: diggers
* [E]xport: exporters
* [P]rocess: processors
* [V]isualize, plot: visplters
'''

import os
import tempfile
import getpass
import time
import logging
import logging.config
import contextlib
import multiprocessing


def get_glogger_config(c, logfile=None, queue=None):
    '''
    Parameters
    ----------
    c: str
        main, for main process
        listen, for listener main process, add processName in format
        work, for worker child process
    logfile: str
        needed when c is 'main' or 'listen'
    queue: Queue
        needed when c is 'work'
    '''
    if c in ['main', 'listen']:
        pn = '{%(processName)s}' if c == 'listen' else ''
        msg = '%s %%(message)s' % pn
        detailed_fmt = '%(asctime)s - %(name)s:%(module)s:%(lineno)d:%(levelname)s - ' + msg
        simple_fmt = '[%(name)s]%(levelname)-7s - ' + msg
        formatters = {
            'detailed': {
                'class': 'logging.Formatter',
                'format': detailed_fmt,
                'datefmt': '%m-%d %H:%M:%S',
            },
            'simple': {
                'class': 'logging.Formatter',
                'format': simple_fmt,
            },
        }
        handlers = {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stderr',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': logfile,
                'maxBytes': 3 * 1024 * 1024,
                'backupCount': 9,
            },
        }
    else:
        formatters = {}
        handlers = {
            'queue': {
                'class': 'logging.handlers.QueueHandler',
                'queue': queue,
            },
        }
    _common_logger_config = {
        'level': 'DEBUG',
        'handlers': list(handlers.keys()),
        'propagate': False,
    }
    return {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': {
            'G': _common_logger_config,  # gdpy3 # gdpy3.GUI
            'L': _common_logger_config,  # gdpy3.loaders
            'S': _common_logger_config,  # gdpy3.savers
            'C': _common_logger_config,  # gdpy3.cores.converter
            'D': _common_logger_config,  # gdpy3.cores.digger
            'E': _common_logger_config,  # gdpy3.cores.exporter
            'P': _common_logger_config,  # gdpy3.processors
            'V': _common_logger_config,  # gdpy3.visplters
        },
    }


class GLogger(logging.Logger):
    '''
    Modify the logging.Logger class for gdpy3.
    '''

    def parm(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO'.
        Add 'Parameter,' before the *msg*.
        """
        msg = '%s, %s' % ('Parameter', msg)
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, msg, args, **kwargs)


logfile = os.path.join(
    tempfile.gettempdir(),
    'gdpy3-%s-%s.log' % (getpass.getuser(), time.strftime('%Y')))
glogger_config_main = get_glogger_config('main', logfile=logfile)
glogger_config_listen = get_glogger_config('listen', logfile=logfile)


def getGLogger(name):
    '''
    Support name: G, L etc. and G.x.y, L.m.n etc.
    '''
    if name.split('.')[0] not in glogger_config_main['loggers']:
        raise KeyError("Logger '%s' not supported!" % name)
    return logging.getLogger(name)


logging.setLoggerClass(GLogger)
logging.config.dictConfig(glogger_config_main)


@contextlib.contextmanager
def get_glogger_work_initializer():
    # listener in MainProcess
    logqueue = multiprocessing.Manager().Queue(-1)
    logging.config.dictConfig(glogger_config_listen)
    queue_listener = logging.handlers.QueueListener(
        logqueue,
        *logging.getLogger('G').handlers,
        respect_handler_level=True)
    queue_listener.start()
    try:
        def initializer():
            glogger_config_work = get_glogger_config('work', queue=logqueue)
            logging.config.dictConfig(glogger_config_work)
        yield initializer
    finally:
        queue_listener.stop()
        logging.config.dictConfig(glogger_config_main)


# multiprocessing logging ref:
# https://docs.python.org/3/howto/logging-cookbook.html#a-more-elaborate-multiprocessing-example
# https://gist.github.com/schlamar/7003737
# https://github.com/jruere/multiprocessing-logging
