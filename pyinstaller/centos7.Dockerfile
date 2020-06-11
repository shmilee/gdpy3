# centos7.4.1708
# https://hub.docker.com/_/centos?tab=tags

FROM centos:centos7.4.1708

LABEL maintainer="shmilee.zju@gmail.com" \
      release.version="7.4.1708" \
      description="centos7 with gdpy3 run prerequisites"

ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    PIP_INDEX_URL=https://mirrors.bfsu.edu.cn/pypi/web/simple

RUN yum -y install python3-pip python3-tkinter glibc \
    && yum clean all
RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} numpy matplotlib==3.0.3

RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} h5py paramiko scipy screeninfo ipython
#RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} notebook ipywidgets

RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} pillow \
    && yum -y install libcurl libjpeg-turbo libpng \
    && yum clean all
RUN yum -y install gcc make python3-devel libcurl-devel libjpeg-turbo-devel libpng-devel \
    && yum clean all \
    && curl -fLC - --retry 3 --retry-delay 3 -o /tmp/libsixel-1.8.6.tar.gz https://github.com/saitoha/libsixel/archive/v1.8.6.tar.gz \
    && tar zxvf /tmp/libsixel-1.8.6.tar.gz -C /tmp/ \
    && cd /tmp/libsixel-1.8.6/ \
    && ./configure --disable-python --prefix=/usr/local \
    && make \
    && make install \
    && echo '/usr/local/lib' > /etc/ld.so.conf.d/usrlocal.conf \
    && ldconfig \
    && cd python/ \
    && python3 setup.py install \
    && rm -rf /tmp/libsixel-1.8.6/ /tmp/libsixel-1.8.6.tar.gz \
    && yum -y history undo last \
    && yum clean all

RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} pyinstaller

ADD 0001-FIX-protect-shared_memory-server-from-SIGINT.patch /
RUN yum -y install patch && yum clean all \
    && patch /usr/lib64/python3.6/multiprocessing/managers.py -i /0001-FIX-protect-shared_memory-server-from-SIGINT.patch \
    && yum -y history undo last

CMD ["/bin/bash"]
