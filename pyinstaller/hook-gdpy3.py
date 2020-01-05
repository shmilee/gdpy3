# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

from PyInstaller.utils.hooks import collect_submodules, exec_statement

hiddenimports = collect_submodules('gdpy3')

data_dir = exec_statement(
    "import gdpy3.__about__; print(gdpy3.__about__.__data_path__)")
datas = [(data_dir, "gdpy3-data")]
