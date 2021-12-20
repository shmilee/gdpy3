# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

from distutils.spawn import find_executable
from PyInstaller.depend.bindepend import findSystemLibrary
from PyInstaller.utils.hooks import collect_submodules, exec_statement

hiddenimports = collect_submodules('gdpy3')

data_dir = exec_statement(
    "import gdpy3.__about__; print(gdpy3.__about__.__data_path__)")
datas = [(data_dir, "gdpy3-data")]

binaries = []

# libsixel
img2sixel = find_executable('img2sixel')
libsixel_so = findSystemLibrary('libsixel.so')
if img2sixel:
    binaries += [(img2sixel, '.')]
if libsixel_so:
    binaries += [(libsixel_so, '.')]
    hiddenimports += ['libsixel']
