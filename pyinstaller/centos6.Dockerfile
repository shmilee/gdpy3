# centos6.10
# https://hub.docker.com/_/centos?tab=tags
#
# tianhe NeoKylin release 3.2 (Carambola)
# 2.6.32-358.11.1.2.ky3.1.x86_64 -> kernel-2.6.32-358.el6
# GLIBC_2.12
# without python3


FROM centos:centos6.10

LABEL maintainer="shmilee.zju@gmail.com" \
      release.version="6.10" \
      description="centos6 with gdpy3 run prerequisites"

ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    OS_RELEASE=6.10 \
    PIP_INDEX_URL=https://mirrors.bfsu.edu.cn/pypi/web/simple

RUN sed -e "s|^mirrorlist=|#mirrorlist=|g" \
        -e "s|^#baseurl=http://mirror.centos.org/centos/\$releasever|baseurl=https://mirrors.tuna.tsinghua.edu.cn/centos-vault/${OS_RELEASE}|g" \
        -i.bak \
        /etc/yum.repos.d/CentOS-*.repo \
    && yum -y install openssl bzip2 xz tkinter tcl tk sqlite \
    && yum -y install gcc make openssl-devel bzip2-devel xz-devel tkinter tcl-devel tk-devel sqlite-devel \
    && yum clean all \
    && curl -fLC - --retry 3 --retry-delay 3 -o /tmp/Python-3.6.9.tgz https://www.python.org/ftp/python/3.6.9/Python-3.6.9.tgz \
    && tar zxvf /tmp//Python-3.6.9.tgz -C /tmp/ \
    && cd /tmp/Python-3.6.9/ \
    && ./configure --prefix=/usr/local \
        --enable-shared \
        --with-computed-gotos \
        --enable-optimizations \
    && make \
    && make install \
    && echo '/usr/local/lib' > /etc/ld.so.conf.d/usrlocal.conf \
    && ldconfig \
    && echo "==> clean python3 ..." \
    && find /usr/local/lib/python3* \
       	\( -type d -a -name test -o -name tests \) \
       	-exec rm -rf '{}' + ; \
       rm -rf /usr/share/man/ /usr/share/doc/ /root /tmp \
    && install -d -m1777 /tmp \
    && install -d -m0700 /root \
    && yum -y history undo last \
    && yum clean all

RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} numpy scipy matplotlib==3.0.3

RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} h5py cryptography==2.9.2 paramiko==2.8.0 screeninfo jedi==0.17.2 ipython
#RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} notebook ipywidgets

ADD 0002-libsixel-loader-gcc44.patch /
RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} pillow==7.1.2 \
    && yum -y install libcurl libpng \
    && yum clean all
RUN curl -fLC - --retry 3 --retry-delay 3 -o /tmp/libsixel-1.8.6.tar.gz https://github.com/saitoha/libsixel/archive/v1.8.6.tar.gz \
    && yum -y install gcc make patch libcurl-devel libpng-devel \
    && tar zxvf /tmp/libsixel-1.8.6.tar.gz -C /tmp/ \
    && cd /tmp/libsixel-1.8.6/ \
    && patch ./src/loader.c -i /0002-libsixel-loader-gcc44.patch \
    && ./configure --disable-python --prefix=/usr/local \
    && make \
    && make install \
    && ldconfig \
    && cd python/ \
    && python3 setup.py install \
    && rm -rf /tmp/libsixel-1.8.6/ /tmp/libsixel-1.8.6.tar.gz \
    && yum -y history undo last \
    && yum clean all

RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} pyinstaller==4.3 \
    && pip3 freeze > /py3-requirements.txt

ADD 0001-FIX-protect-shared_memory-server-from-SIGINT.patch /
RUN yum -y install patch && yum clean all \
    && patch /usr/local/lib/python3.6/multiprocessing/managers.py -i /0001-FIX-protect-shared_memory-server-from-SIGINT.patch \
    && yum -y history undo last

CMD ["/bin/bash"]
