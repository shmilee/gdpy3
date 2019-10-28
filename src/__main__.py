# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

if __name__ == "__main__":
    iface = 'cli'
    if iface == 'gui':
        from .GUI import gui_script as i_script
    else:
        from .cli import cli_script as i_script
    i_script()
