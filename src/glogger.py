# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Gdpy3's logger module.

* [G]dp: gdpy3
* [L]oad: loaders
* [S]ave: savers
* [C]ore: processors
* [E]xport: exporters
* [P]lot: plotters
'''

import os
import tempfile
import getpass
import time
import logging
import logging.config

logfile = os.path.join(
    tempfile.gettempdir(),
    'gdpy3-%s-%s.log' % (getpass.getuser(), time.strftime('%Y')))

logger_common_config = {
    'level': 'DEBUG',
    'handlers': ['console', 'file'],
    'propagate': False,
}

gloggerConfig = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s - %(name)s:%(module)s:%(lineno)d:%(levelname)s - %(message)s',
            'datefmt': '%m-%d %H:%M:%S',
        },
        'simple': {
            'class': 'logging.Formatter',
            'format': '[%(name)s]%(levelname)-7s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': logfile,
            'maxBytes': 3 * 1024 * 1024,
            'backupCount': 9,
        },
    },
    'loggers': {
        'G': logger_common_config,  # gdpy3
        'L': logger_common_config,  # gdpy3.loaders
        'S': logger_common_config,  # gdpy3.savers
        'C': logger_common_config,  # gdpy3.cores.converter
        'D': logger_common_config,  # gdpy3.cores.digger
        'E': logger_common_config,  # gdpy3.cores.exporter
        # gdpy3.processors
        'P': logger_common_config,  # gdpy3.plotters
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


def getGLogger(name):
    if name not in gloggerConfig['loggers']:
        raise KeyError("'%s' not found in supported loggers!" % name)
    return logging.getLogger(name)


logging.setLoggerClass(GLogger)
logging.config.dictConfig(gloggerConfig)
