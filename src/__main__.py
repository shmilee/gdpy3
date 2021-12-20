# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import sys
from .glogger import getGLogger

log = getGLogger('G')


def entry_iface(candidates=('cli', 'gui'), default='gui'):
    '''
    Get and enter first valid iface in candidates.

    There are 3 ways to set entry iface: program name, environment
    variable 'GDPY3_IFACE' and special file name in current working
    directory (CWD). First, check if program name without 'gdpy3-'
    in candidates; then if value of 'GDPY3_IFACE' in candidates;
    finally check if a file named of uppercase candidates in CWD.
    After all check failed, use default iface.

    Parameters
    ----------
    candidates: tuple
        choose candidates from available interfaces,
        'cli', 'gui', 'run', 'ipy', etc.
    default: str
        default interface in candidates
    '''
    log.debug('Current working directory (CWD) is %s' % os.getcwd())
    log.debug('Entry interface argumentsis %s' % sys.argv)
    # first, 'gdpy3-cli' -> 'cli'
    prog = os.path.basename(sys.argv[0])
    iface = prog.split('-')[-1]
    if iface in candidates:
        log.debug('Get iface %s from program name %s.' % (iface, prog))
    else:
        # then, env
        iface = os.getenv('GDPY3_IFACE', default=None)
        if iface in candidates:
            log.debug('Get iface %s from env GDPY3_IFACE.' % iface)
        else:
            # finally, file in CWD
            iface = None
            for f in candidates:
                if os.path.isfile(os.path.join(os.getcwd(), f.upper())):
                    iface = f
                    log.debug('Get iface %s from file name in CWD.' % iface)
                    break
            if not iface:
                # all failed, use default
                iface = default
                log.debug('Get iface %s from default setting.' % iface)
                note = entry_iface.__doc__.split('\n\n')[1]
                print("Note:\n%s" % note.replace(' '*4, ' '*2))
    # enter
    log.info("Using iface '%s' in candidates %s ..." % (iface, candidates))
    if iface == 'cli':
        from .cli import cli_script
        cli_script()
    elif iface == 'gui':
        from .GUI import gui_script
        gui_script()
    elif iface == 'run':
        if len(sys.argv) > 1:
            path = sys.argv[1]
            if os.path.isfile(path):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    os.path.basename(path), path)
                foo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(foo)
                run = getattr(foo, 'run', None)
                if callable(run):
                    run()
            else:
                log.error("%s is not a file!" % path)
        else:
            print("Usage: gdpy3-%s [path/to/job.py]" % iface)
    elif iface == 'ipy':
        from IPython import start_ipython
        start_ipython()
    else:
        log.error('Invalid iface %s!' % iface)


if __name__ == "__main__":
    entry_iface()
