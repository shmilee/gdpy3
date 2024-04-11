# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
Contains SFTP directory raw loader class.
'''

import io
import os
import stat
import tempfile
import urllib.parse
try:
    import paramiko
except ImportError as exc:
    raise ImportError(
        'SftpRawLoader requires paramiko. But %s' % exc) from None

from ..glogger import getGLogger
from ..utils import inherit_docstring, GetPasswd
from .base import BaseRawLoader, _raw_copydoc_func

__all__ = ['SftpRawLoader']
log = getGLogger('L')


@inherit_docstring((BaseRawLoader,), _raw_copydoc_func, template=None)
class SftpRawLoader(BaseRawLoader):
    '''
    Load raw data from a directory in remote SSH server.
    Return a dictionary-like object.

    Attributes
    {Attributes}

    Parameters
    {Parameters}

    Notes
    {Notes}
    3. Directory tree maxdepth is 2.
    4. path format: 'sftp://username@host[:port]##remote/path'
       example: 'sftp://Bob@192.168.1.10:2233##test/case/'
    '''
    __slots__ = ['user', '__passwd', 'host', 'port', 'rmt_path', 'transport']
    _sep = '/'  # unix sep
    loader_type = 'sftp.directory'

    def _check_path_access(self, path):
        '''Check for access to remote *path*.'''
        tpath = path.split('##')
        if (len(tpath) != 2 or not isinstance(tpath[0], str)
                or not tpath[0].startswith('sftp://')
                or not isinstance(tpath[1], str)):
            log.error("Wrong format of sftp path: %s" % path)
            return False
        u = urllib.parse.urlparse(tpath[0])
        self.user = u.username
        self.host = u.hostname
        self.port = u.port or 22
        self.rmt_path = tpath[1]
        self.__passwd = GetPasswd.getpasswd(
            prompt='Password for "%s@%s": ' % (self.user, self.host))
        try:
            self.transport = paramiko.Transport((self.host, self.port))
            self.transport.connect(username=self.user, password=self.__passwd)
            sftp = paramiko.SFTPClient.from_transport(self.transport)
            sftp.listdir(self.rmt_path)
            sftp.close()
            return True
        except Exception as e:
            log.error("Sftp transport error: %s" % e)
            try:
                self.transport.close()
            except:
                pass
            return False

    def _special_check_path(self):
        if self.transport.is_alive():
            return True
        else:
            log.error("Sftp transport of '%s' is not alive!" % self.path)
            return False

    def _special_open(self):
        if not self.transport.is_alive():
            log.warning("Sftp transport not alive, reconnect '%s'!"
                        % self.path)
            try:
                self.transport.close()
                self.transport = paramiko.Transport((self.host, self.port))
                self.transport.connect(
                    username=self.user, password=self.__passwd)
            except Exception:
                try:
                    self.transport.close()
                except:
                    pass
                raise
        return paramiko.SFTPClient.from_transport(self.transport)

    def _special_close(self, pathobj):
        pathobj.close()

    def _special_getkeys(self, pathobj):
        filenames = []
        for p1 in pathobj.listdir_attr(self.rmt_path):
            if stat.S_ISDIR(p1.st_mode):
                if not self.exclude_match(p1.filename, dirname=True):
                    _dir = self._sep.join([self.rmt_path, p1.filename])
                    for p2 in pathobj.listdir_attr(_dir):
                        if not stat.S_ISDIR(p2.st_mode):
                            if not self.exclude_match(p2.filename):
                                filenames.append(
                                    self._sep.join([p1.filename, p2.filename]))
            else:
                if not self.exclude_match(p1.filename):
                    filenames.append(p1.filename)
        return sorted(filenames)

    def _special_get(self, pathobj, key):
        # paramiko.SFTP.open, SSH treats all files as binary
        return io.TextIOWrapper(
            pathobj.open(self._sep.join([self.rmt_path, key]), 'r'))

    def beside_path(self, name):
        return os.path.join(tempfile.tempdir, '%s-%s' % (
            self.rmt_path.replace('/', '-'), name))
