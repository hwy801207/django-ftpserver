import time
import os
from collections import namedtuple

from six import text_type
from pyftpdlib.filesystems import AbstractedFS

from django.core.files.storage import (
    get_storage_class as _get_storage_class
)

PseudoStat = namedtuple(
    'PseudoStat',
    [
        'st_size', 'st_mtime', 'st_nlink', 'st_mode', 'st_uid', 'st_gid',
        'st_dev', 'st_ino'
    ])


class StorageFS(AbstractedFS):
    """FileSystem for bridge to Django storage.
    """
    storage_class = None

    def __init__(self, root, cmd_channel):
        super(StorageFS, self).__init__(root, cmd_channel)
        self.storage = self.get_storage()

    def get_storage_class(self):
        if self.storage_class is None:
            return _get_storage_class()
        return self.storage_class

    def get_storage(self):
        storage_class = self.get_storage_class()
        return storage_class()

    def open(self, filename, mode):
        path = os.path.join(self._cwd, filename)
        return self.storage.open(path, mode)

    def mkstemp(self, suffix='', prefix='', dir=None, mode='wb'):
        raise NotImplementedError

    def chdir(self, path):
        assert isinstance(path, text_type), path
        self._cwd = self.fs2ftp(path)

    def mkdir(self, path):
        # TODO: resolve directory operation
        raise NotImplementedError

    def listdir(self, path):
        assert isinstance(path, text_type), path
        if path == '/':
            path = ''
        directories, files = self.storage.listdir(path)
        return [name + '/' for name in directories] + files

    def rmdir(self, path):
        # TODO: resolve directory operation
        raise NotImplementedError

    def remove(self, path):
        assert isinstance(path, text_type), path
        self.storage.remove(path)

    def chmod(self, path, mode):
        raise NotImplementedError

    def stat(self, path):
        if self.isdir(path):
            # directory
            st_mode = 0o0040770
        else:
            st_mode = 0o0100770
        return PseudoStat(
            st_size=self.getsize(path),
            st_mtime=int(self.getmtime(path)),
            st_nlink=1,
            st_mode=st_mode,
            st_uid=1000,
            st_gid=1000,
            st_dev=0,
            st_ino=0,
        )

    lstat = stat

    def _exists(self, path):
        if path == '/':
            return self.storage.exists("")
        return self.storage.exists(path)

    def isfile(self, path):
        return self._exists(path) and not path.endswith('/')

    def islink(self, path):
        return False

    def isdir(self, path):
        if path == '':
            return True
        elif path.endswith('/'):
            return self._exists(path)
        return self._exists(path + '/')

    def getsize(self, path):
        return self.storage.size(path)

    def getmtime(self, path):
        return time.mktime(self.storage.get_created_time(path).timetuple())

    def realpath(self, path):
        return path

    def lexists(self, path):
        return self._exists(path)

    def get_user_by_uid(self, uid):
        return "owner"

    def get_group_by_gid(self, gid):
        return "group"