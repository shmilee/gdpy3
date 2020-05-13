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
RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} h5py paramiko scipy screeninfo
RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} ipython notebook ipywidgets
RUN pip3 --no-cache-dir install -i ${PIP_INDEX_URL} pyinstaller

CMD ["/bin/bash"]
