# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import sys

VERSION = (0, 7, 0)

__description__ = "Gyrokinetic Toroidal Code Data Processing tools written in python3"
__url__ = "https://github.com/shmilee/gdpy3.git"
__version__ = '.'.join(map(str, VERSION))
__status__ = "alpha"
__author__ = "shmilee"
__email__ = "shmilee.zju@gmail.com"
__license__ = "MIT"
__copyright__ = 'Copyright (c) 2020 shmilee'


def _get_beside_path(name):
    '''
    Check directory or file *name* beside __about__.py or not.
    Return abspath or ''
    '''
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    if os.path.exists(path):
        return path
    else:
        return ''


def _get_data_path(name):
    '''Get the path to *name*.'''

    path = _get_beside_path(name)
    if os.path.isdir(path):
        return path

    # pyinstaller frozen check
    if getattr(sys, 'frozen', None):
        path = os.path.join(sys._MEIPASS, name)
        if os.path.isdir(path):
            return path

        path = os.path.join(os.path.dirname(sys.executable), name)
        if os.path.isdir(path):
            return path

        path = os.path.join(sys.path[0], name)
        if os.path.isdir(path):
            return path

    raise RuntimeError("Can't find the %s files!" % name)


__data_path__ = _get_data_path('gdpy3-data')
__icon_name__ = 'gdpy3_128'
__icon_path__ = os.path.join(__data_path__, 'icon', '%s.png' % __icon_name__)


# see: sysconfig._getuserbase()
def _get_userbase():
    env_base = os.getenv("GDPY3_USERBASE", None)
    if env_base:
        return env_base

    def joinuser(*args):
        return os.path.expanduser(os.path.join(*args))

    if os.name == "nt":
        base = os.environ.get("APPDATA") or "~"
        return joinuser(base, "Gdpy3")
    if sys.platform == "darwin" and sys._framework:
        return joinuser("~", "Library", "Gdpy3")
    return joinuser("~", ".Gdpy3")


__ENABLE_USERBASE__ = True
__userbase__ = _get_userbase()
if __ENABLE_USERBASE__:
    if not os.path.exists(__userbase__):
        os.mkdir(__userbase__)
    if __userbase__ not in sys.path:
        sys.path.append(__userbase__)


def _git_versionstr_read(vfile):
    '''read versionstr, v{X}.{Y}.{Z}-{N}-g{commit}'''
    if os.path.isfile(vfile):
        with open(vfile, 'r', encoding='utf-8') as f:
            return f.readline()
    else:
        upath = _get_beside_path('utils.py')
        if os.path.isfile(upath):
            import importlib.util
            spec = importlib.util.spec_from_file_location('utils.py', upath)
            utils = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(utils)
            run_child_cmd = getattr(utils, 'run_child_cmd')

            git = 'git.exe' if os.name == 'nt' else 'git'
            code, stdout, stderr = run_child_cmd(
                [git, 'describe', '--tags', '--abbrev=40'],
                cwd=os.path.dirname(upath))
            if code == 0:
                # example, v0.6.1-21-gbed56cc...
                return stdout
    # fallback
    return ''


def _git_versionstr_write(vfile):
    '''write versionstr'''
    vstr = _git_versionstr_read('vfile-not-exists')
    if os.path.isfile(vfile) and vstr == '':
        # no need to write
        return
    with open(vfile, 'w', encoding='utf-8') as f:
        f.write(vstr)


def _git_versionstr_fmt(vfile):
    '''
    1. v{X}.{Y}.{Z}-{N}-g{commit} --> (X, Y, Z, N, commit)
    2. '' --> (X, Y, Z, 0, None)
    '''
    import re
    vstr = _git_versionstr_read(vfile)
    if vstr:
        m = re.match('v(\d+).(\d+).(\d+)-(\d+)-g(.*)', vstr)
        if m:
            return m.groups()
    # fallback
    return (*VERSION, 0, None)


_git_versionstr_file = 'git-version'
GITVERSION = _git_versionstr_fmt(
    os.path.join(__data_path__, _git_versionstr_file))
if GITVERSION[4]:
    __gversion__ = "%s.r%s" % (__version__, GITVERSION[3])
else:
    __gversion__ = __version__
