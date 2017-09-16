# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Gdpy3's logger module.
'''

import os
import tempfile
import logging
import logging.config

# levels
PARAMETER = 25
VERBOSE = 15
DDEBUG = 5

_levelToName = {
    PARAMETER: 'PARAMETER',
    VERBOSE: 'VERBOSE',
    DDEBUG: 'DDEBUG',
}

for _k, _v in _levelToName.items():
    logging.addLevelName(_k, _v)

gloggerConfig = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            #'format': '[%(asctime)s] [%(name)s] [%(module)-9s %(lineno)-3d] %(levelname)-7s %(message)s',
            'format': '[%(asctime)s] [%(name)s] [%(module)-9s] %(levelname)-7s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
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
            'level': 'DDEBUG',
            'formatter': 'detailed',
            'filename': os.path.join(tempfile.gettempdir(), 'gdpy3.log'),
            'maxBytes': 3 * 1024 * 1024,
            'backupCount': 2,
        },
    },
    'loggers': {
        # gdpy3
        'G': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        # gdpy3.convert
        'C': {
            'level': 'VERBOSE',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        # gdpy3.plot
        'P': {
            'level': 'DDEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
}


class GLogger(logging.Logger):
    '''
    Modify the logging.Logger class for gdpy3.
    '''

    def parameter(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'PARAMETER'.
        """
        if self.isEnabledFor(PARAMETER):
            self._log(PARAMETER, msg, args, **kwargs)

    parm = parameter

    def verbose(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'VERBOSE'.
        """
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kwargs)

    vrbs = verbose

    def ddebug(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'DDEBUG'.
        """
        if self.isEnabledFor(DDEBUG):
            self._log(DDEBUG, msg, args, **kwargs)

    ddbg = ddebug

    def warn(self, msg, *args, **kwargs):
        self.warning(msg, *args, **kwargs)


def getGLogger(name):
    if name not in gloggerConfig['loggers']:
        raise KeyError("'%s' not found in supported loggers!" % name)
    return logging.getLogger(name)


logging.setLoggerClass(GLogger)
logging.config.dictConfig(gloggerConfig)
