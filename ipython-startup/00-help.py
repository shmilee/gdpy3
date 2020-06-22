# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

print()

import sys
# pyinstaller frozen check
if getattr(sys, 'frozen', None):
    try:
        from pydoc import help
        print("[pre-import] pydoc.Helper instance 'help'")
    except Exception:
        pass
del sys
