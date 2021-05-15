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
    - [build app on the oldest version of Linux to support](https://pythonhosted.org/PyInstaller/usage.html#making-linux-apps-forward-compatible)
      example, build app in centos7 docker container

* Error staticx: Library 'libc.so.6' already exists in archive`
    - ignore: https://github.com/JonathonReinhart/staticx/issues/92

### Usage

Staticx fully-static bundled version, need to set environment
variable 'GDPY3_IFACE' in entry_iface_candidates or touch a file
named **uppercase** entry_iface_candidates in current working
directory(CWD) to run different cmds.

```shell
entry_iface_candidates=(cli gui run ipy)
GDPY3_IFACE=cli ./gdpy3-app [args]
touch CLI # GUI, RUN, IPY
./gdpy3-app [args]
```

PyInstaller version, besides 'GDPY3_IFACE' and special file name in CWD,
we can also create links named entry_iface_candidates to run different cmds.

```shell
for lk in ${entry_iface_candidates[@]}; do
    ln -s gdpy3-app ./dist/gdpy3-app/gdpy3-$lk
done

./dist/gdpy3-app/gdpy3-cli [args]
./dist/gdpy3-app/gdpy3-gui [args]
./dist/gdpy3-app/gdpy3-run [./script.py] # run ./script.py
./dist/gdpy3-app/gdpy3-ipy # run into ipython
```


centos7
-------

1. run a new docker container

```bash
docker build --rm -t gdpy3/centos7:$(date +%y%m%d) -f centos7.Dockerfile .
cd ..
python setup.py bdist_wheel
cp ./dist/gdpy3-*-any.whl pyinstaller/
docker run --rm -i -t -v $PWD/pyinstaller:/gdpy3-pyinstaller \
    gdpy3/centos7:$(date +%y%m%d) bash
```

2. install and freeze gdpy3 in container

```bash
cd /gdpy3-pyinstaller
pip3 install ./gdpy3-*-any.whl
pyinstaller --onefile gdpy3-app.spec
entry_iface_candidates=(cli gui run ipy)
for lk in ${entry_iface_candidates[@]}; do
    ln -s gdpy3-app ./dist/gdpy3-app/gdpy3-$lk
done
cd dist/
gver=$(sed 's|\(v.*\)-\(.\)-g.*|\1.r\2|' gdpy3-app/gdpy3-data/git-version)
tar czvf gdpy3-app-$gver-$(uname -m).pkg.tar.gz  gdpy3-app/
```

3. decompress in cluster and create shell wrappers

```bash
tar zxvf gdpy3-app-pkg-$(uname -m).tar.gz -C ~/.local/lib/
for lk in ${entry_iface_candidates[@]}; do
    echo '#!/bin/bash' > ~/.local/bin/gdpy3-$lk
    echo "exec ~/.local/lib/gdpy3-app/gdpy3-$lk \"\$@\"" >> ~/.local/bin/gdpy3-$lk
    chmod +x ~/.local/bin/gdpy3-$lk
done
```

Keep an eye on [exe outside dir](https://github.com/pyinstaller/pyinstaller/issues/1048)


arm64v8-debian9
---------------

1. prepare [Docker Buildx](https://docs.docker.com/buildx/working-with-buildx/)
   * Docker > 19.03
   * Install qemu, qemu-arch-extra
   * Register Arm executables
     ```bash
     docker run --rm --privileged docker/binfmt:820fdd95a9972a5308930a2bdfb8573dd4447ad3
     cat /proc/sys/fs/binfmt_misc/qemu-aarch64
     ```
2. run a new docker container

```bash
docker buildx build --rm --network host \
    -t gdpy3/arm64v8-debian9:$(date +%y%m%d) \
    -f arm64v8-debian9.Dockerfile \
    --platform linux/arm64 .
cd ..
python setup.py bdist_wheel
cp ./dist/gdpy3-*-any.whl pyinstaller/
docker run --rm -i -t -v $PWD/pyinstaller:/gdpy3-pyinstaller \
    gdpy3/arm64v8-debian9:$(date +%y%m%d) bash
```

3. install and freeze gdpy3 in container

```bash
cd /gdpy3-pyinstaller
pip3 install ./gdpy3-*-any.whl
pyinstaller --onefile gdpy3-app.spec
entry_iface_candidates=(cli gui run ipy)
for lk in ${entry_iface_candidates[@]}; do
    ln -s gdpy3-app ./dist/gdpy3-app/gdpy3-$lk
done
cp -v /lib/aarch64-linux-gnu/{libc.so.6,libresolv.so.2} ./dist/gdpy3-app/
cp -v /usr/lib/aarch64-linux-gnu/libxcb.so.1 ./dist/gdpy3-app/
cp -v /lib/aarch64-linux-gnu/libpthread.so.0 ./dist/gdpy3-app/
cd dist/
gver=$(sed 's|\(v.*\)-\(.\)-g.*|\1.r\2|' gdpy3-app/gdpy3-data/git-version)
tar czvf gdpy3-app-$gver-$(uname -m).pkg.tar.gz  gdpy3-app/
```

4. decompress in cluster and create shell wrappers

```bash
TDIR=$HOME/.local
tar zxvf gdpy3-app-pkg-$(uname -m).tar.gz -C $TDIR/lib/
MATPLOTLIBDATA=$TDIR/lib/gdpy3-app/matplotlib/mpl-data
for lk in ${entry_iface_candidates[@]}; do
    echo '#!/bin/bash' > $TDIR/bin/gdpy3-$lk
    echo "export MATPLOTLIBDATA=$MATPLOTLIBDATA" >> $TDIR/bin/gdpy3-$lk
    echo "exec $TDIR/lib/gdpy3-app/gdpy3-$lk \"\$@\"" >> $TDIR/bin/gdpy3-$lk
    chmod +x $TDIR/bin/gdpy3-$lk
done
```


macos
-----

test


reference
=========

* https://pythonhosted.org/PyInstaller/spec-files.html
* https://github.com/pyinstaller/pyinstaller/wiki/FAQ#gnulinux
* https://github.com/JonathonReinhart/staticx/issues/94
