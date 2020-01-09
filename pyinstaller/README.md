Make application
================

Use [PyInstaller](https://github.com/pyinstaller/pyinstaller) and [staticx](https://github.com/JonathonReinhart/staticx).


archlinux
---------

```shell
pyinstaller --onefile gdpy3-app.spec
~/.local/bin/staticx dist/gdpy3-app/gdpy3-app \
    -l dist/gdpy3-app/ \
    -l /usr/lib/libm.so.6 -l /lib64/libpthread.so.0 \
    gdpy3-app
#~/.local/bin/staticx dist/gdpy3-app/gdpy3-app \
#    -l dist/gdpy3-app/ \
#    -l /usr/lib/libm.so.6 -l /lib64/libpthread.so.0 \
#    -l /lib64/libc.so.6 \
#    -l /lib64/ld-linux-x86-64.so.2 \
#    gdpy3-app
```

* Including additional library files according to error information.

* Error `loading Python lib '/tmp/staticx-pJJpKL/libpython3.8.so.1.0'`
    - `-l dist/gdpy3-app/`

* Error `loading Python lib '/tmp/staticx-DMMKEc/libpython3.8.so.1.0': dlopen: /lib64/libm.so.6: /lib64/libpthread.so.0:`
    - `-l /usr/lib/libm.so.6 -l /lib64/libpthread.so.0`

* Error `fc-list: relocation error: /tmp/staticx-nlLmnE/libc.so.6: symbol _dl_exception_create, version GLIBC_PRIVATE not defined in file ld-linux-x86-64.so.2 with link time reference`
    - glibc, python3, matplotlib too new, disable matplotlib
    - TODO: [build app on the oldest version of Linux to support](https://pythonhosted.org/PyInstaller/usage.html#making-linux-apps-forward-compatible)

* Error staticx: Library 'libc.so.6' already exists in archive`
    - ignore: https://github.com/JonathonReinhart/staticx/issues/92

### Usage

PyInstaller version, first create symbolic links, then run links.

```shell
for lk in cli gui ipy run; do
    ln -s gdpy3-app ./dist/gdpy3-app/gdpy3-$lk
done

./dist/gdpy3-app/gdpy3-cli [args]
./dist/gdpy3-app/gdpy3-gui [args]
./dist/gdpy3-app/gdpy3-ipy # run into ipython
./dist/gdpy3-app/gdpy3-run [./script.py] # run ./script.py
```

Staticx fully-static bundled version, need to touch a file
named 'CLI', 'GUI', 'IPY' or 'RUN' in current working directory
to run as cmd: 'gdpy3-cli', 'gdpy3-gui', 'gdpy3-ipy' or 'gdpy3-run'.

```shell
touch CLI # GUI, IPY, RUN
./gdpy3-app [args]
```


macos
-----

test


reference
=========

* https://pythonhosted.org/PyInstaller/spec-files.html
* https://github.com/pyinstaller/pyinstaller/wiki/FAQ#gnulinux
* https://github.com/JonathonReinhart/staticx/issues/94
