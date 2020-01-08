make application
================

Use [PyInstaller](https://github.com/pyinstaller/pyinstaller) and [staticx](https://github.com/JonathonReinhart/staticx).

```shell
pyinstaller --onefile gdpy3-app.spec
rm -rf dist/gdpy3-app/share/icons/
staticx dist/gdpy3-app/gdpy3-app \
    -l dist/gdpy3-app/ \
    -l /usr/lib/libm.so.6 \
    -l /lib64/libpthread.so.0 \
    gdpy3-app
```

reference
---------

* https://pythonhosted.org/PyInstaller/spec-files.html
* https://github.com/pyinstaller/pyinstaller/wiki/FAQ#gnulinux
* https://github.com/JonathonReinhart/staticx/issues/94
