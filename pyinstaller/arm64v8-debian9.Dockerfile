# arm64v8/debian 9 stretch
# https://hub.docker.com/r/arm64v8/debian/

FROM arm64v8/debian:stretch

LABEL maintainer="shmilee.zju@gmail.com" \
      release.version="stretch" \
      description="stretch with gdpy3 run prerequisites"

ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    DEBIAN_CODENAME=stretch \
    DEBIAN_MIRROR=http://mirrors.163.com/debian \
    DEBIAN_SECURITY_MIRROR=http://mirrors.163.com/debian-security \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

COPY dpkg.cfg.excludes /etc/dpkg/dpkg.cfg.d/01_excludes

RUN echo "deb $DEBIAN_MIRROR $DEBIAN_CODENAME main contrib" > /etc/apt/sources.list \
    && echo "deb $DEBIAN_MIRROR $DEBIAN_CODENAME-updates main contrib" >> /etc/apt/sources.list \
    && echo "deb $DEBIAN_SECURITY_MIRROR $DEBIAN_CODENAME/updates main contrib" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y python3-pip libc6 fontconfig \
        python3-tk python3-numpy python3-scipy python3-matplotlib \
        python3-h5py python3-paramiko ipython3 python3-pillow \
    && pip3 --no-cache-dir install -i ${PIP_INDEX_URL} screeninfo==0.6.3 \
    && apt-get -y autoremove && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

#  libfreetype6 libpng16-16 pkg-config libfreetype6-dev libpng-dev \
#  pip3 --no-cache-dir install -i ${PIP_INDEX_URL} matplotlib==3.0.3

RUN apt-get update \
    && apt-get install -y curl libcurl3-gnutls libjpeg62-turbo gcc \
        make python3-dev libcurl4-gnutls-dev libjpeg62-turbo-dev libpng-dev \
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
    && apt-get remove -y \
        make python3-dev libcurl4-gnutls-dev libjpeg62-turbo-dev libpng-dev \
    && apt-get -y autoremove && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 

RUN apt-get update && apt-get install -y zlib1g-dev \
    && pip3 --no-cache-dir install -i ${PIP_INDEX_URL} pyinstaller==4.1 \
    && apt-get remove -y zlib1g-dev \
    && apt-get -y autoremove && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD 0001-FIX-protect-shared_memory-server-from-SIGINT.patch /
RUN apt-get update && apt-get install -y patch \
    && patch /usr/lib/python3.5/multiprocessing/managers.py -i /0001-FIX-protect-shared_memory-server-from-SIGINT.patch \
    && apt-get remove -y zlib1g-dev \
    && apt-get -y autoremove && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
