# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import sys

if __name__ == "__main__":
    print('I: Current working directory is %s' % os.getcwd())
    print('I: Command line argumentsis %s' % sys.argv)

    # get cmd by prog name
    # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#gnulinux
    # 1. staticx fully-static bundled version, prog is .staticx.prog
    # 2. PyInstaller version, prog can be gdpy3-app or a link
    prog = os.path.basename(sys.argv[0])
    cmd = 'gdpy3-gui'  # use gui as default
    if prog == '.staticx.prog':
        use_default = True
        Files = ['CLI', 'GUI', 'IPY', 'RUN']
        for File in Files:
            if os.path.isfile(os.path.join(os.getcwd(), File)):
                print('I: Find file %s in current working directory.' % File)
                cmd = 'gdpy3-%s' % File.lower()
                use_default = False
                break
        if use_default:
            print('I: This is a fully-static bundled version, you can '
                  'touch file named %s in current working directory '
                  'to use different cmd!' % Files)
        print('I: %s fully-static, use cmd %s.' % (prog, cmd))
    else:
        if os.path.islink(sys.argv[0]):
            cmd = prog
        print('I: %s not fully static, use cmd %s.' % (prog, cmd))

    if cmd == 'gdpy3-cli':
        import gdpy3.cli
        gdpy3.cli.cli_script()
    elif cmd == 'gdpy3-gui':
        import gdpy3.GUI
        gdpy3.GUI.gui_script()
    elif cmd == 'gdpy3-ipy':
        from IPython import start_ipython
        start_ipython()
    elif cmd == 'gdpy3-run':
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
                print("E: %s is not a file!" % path)
        else:
            print("Usage: %s [path/to/job.py]" % cmd)
    else:
        links = ['gdpy3-%s' % c for c in ['cli', 'gui', 'ipy', 'run']]
        print("I: Create symbolic links %s to me!" % links)
