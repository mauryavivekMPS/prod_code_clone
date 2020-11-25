#!/usr/bin/env python

import logging
import os
import paramiko
import uuid

from email.utils import quote


def dquote(s):
	"""
	return a double quoted copy of s with any inner backslashes
	or double quotes escaped by a backslash
	"""
	if isinstance(s, str):
		s = '"' + quote(s) + '"'
	return s


class IVSFTPFileSystemServer(paramiko.SFTPServerInterface):

	def __init__(self, server, *args, **kwargs):
		"""Initialize a new IVSFTPFileSystemServer

		An IVSFTPFileSystemServer implements a basic
		SFTP server on top of a local filesystem.

		Parameters:

		server - instance of paramiko.ServerInterface associated with the request

			The following attributes must be available on the server:

			home_dir - path to the client user's ``home`` directory
			on the filesystem, which will act as the root of the
			client's filesystem operations

			user - user object associated with the client

			publishers - list of publisher objects associated with the client

		*args - list with the following items:
			args[0] Namespace object with the following fields:
				name - name of the service
				log - general Logger instance
				access_log - access log Logger instance

		**kwargs - ignored
		"""
		self.server = server
		self.args = args[0]

		self.access_log = self.args.access_log
		self.log = logging.getLogger(self.args.name)

		if not hasattr(self.server, 'home_dir'):
			raise Exception('server missing required attribte: home_dir')
		if not hasattr(self.server, 'user'):
			raise Exception('server missing required attribte: user')
		if not hasattr(self.server, 'publishers'):
			raise Exception('server missing required attribte: publishers')

	def session_started(self):
		self.session_id = str(uuid.uuid1())
		self.access_log.info("[%s] session_started %s %s <%s>",
			self.session_id, self.server.user.user_id,
			dquote(self.server.user.display_name), self.server.user.email)

	def session_ended(self):
		self.access_log.info("[%s] session_ended",
			self.session_id)

	def fspath(self, path):
		"""
		Return normalized ``path`` under ``self.server.home_dir``
		"""
		if path is None:
			path = "/"

		canonical = []

		parts = os.path.normpath(path).split(os.path.sep)
		for i in range(len(parts)):
			if parts[i] == "" or parts[i] == ".":
				continue
			if parts[i] == "..":
				if len(canonical) > 0:
					canonical = canonical[0:-1]
				continue
			canonical.append(parts[i])

		fspath = os.path.join(self.server.home_dir, *canonical)
		self.log.debug("IVSFTPFileSystemServer.fspath(%s):  %s", path, fspath)
		return fspath

	def open(self, path, flags, attr):
		"""
		Open a file on the server and create a handle for
		future operations.  On success a new object subclassed
		from SFTPHandle is returned.  On failure an error code
		such as SFTP_PERMISSION_DENIED should be returned.
		"""
		self.log.debug("IVSFTPFileSystemServer.open(%s, %s, %s)", path, flags, attr)
		path = self.fspath(path)
		try:
			binary_flag = getattr(os, 'O_BINARY', 0)
			flags |= binary_flag
			mode = getattr(attr, 'st_mode', None)
			if mode is not None:
				fd = os.open(path, flags, mode)
			else:
				fd = os.open(path, flags, 0o666)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)

		if (flags & os.O_CREAT) and (attr is not None):
			attr._flags &= ~attr.FLAG_PERMISSIONS
			paramiko.SFTPServer.set_file_attr(path, attr)
		if flags & os.O_WRONLY:
			if flags & os.O_APPEND:
				fstr = 'ab'
			else:
				fstr = 'wb'
		elif flags & os.O_RDWR:
			if flags & os.O_APPEND:
				fstr = 'a+b'
			else:
				fstr = 'r+b'
		else:
			fstr = 'rb'

		try:
			f = os.fdopen(fd, fstr)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)

		fobj = IVSFTPFileHandle(flags)
		fobj.session_id = self.session_id
		fobj.access_log = self.args.access_log
		fobj.filename = path
		fobj.readfile = f
		fobj.writefile = f
		return fobj

	def list_folder(self, path):
		"""
		Return a list of files writhin a given folder.  The ``path``
		will use posix notation (``"/"`` separates folder names) and
		may be an absolute or relative path.

		The returned list will consist of SFTPAttribute objects.

		In the case of an error one of the SFTP_* error codes, such
		as SFTP_PERMISSION_DENIED will be returned.
		"""
		self.log.debug("IVSFTPFileSystemServer.list_folder(%s)", path)
		path = self.fspath(path)
		try:
			folder = []
			listing = os.listdir(path)
			for name in listing:
				attr = paramiko.SFTPAttributes.from_stat(os.stat(os.path.join(path, name)))
				attr.filename = name
				folder.append(attr)
			return folder
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] list_folder %s",
				self.session_id, dquote(path))

	def stat(self, path):
		"""
		Return an SFTPAttributes object for a given path, or
		return an error code.   This version follows symbolic
		links.
		"""
		self.log.debug("IVSFTPFileSystemServer.stat(%s)", path)
		path = self.fspath(path)
		try:
			return paramiko.SFTPAttributes.from_stat(os.stat(path))
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] stat %s",
				self.session_id, dquote(path))

	def lstat(self, path):
		"""
		Return an SFTPAttributes object for a path on the server,
		or an error code.  This version does not follow symbolic
		links.
		"""
		self.log.debug("IVSFTPFileSystemServer.lstat(%s)", path)
		path = self.fspath(path)
		try:
			return paramiko.SFTPAttributes.from_stat(os.lstat(path))
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] lstat %s",
				self.session_id, dquote(path))

	def remove(self, path):
		"""
		Delete a file, if possible, or return an error code.
		"""
		self.log.debug("IVSFTPFileSystemServer.remove(%s)", path)
		path = self.fspath(path)
		try:
			os.remove(path)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] remove %s",
				self.session_id, dquote(path))
		return paramiko.SFTP_OK

	def rename(self, oldpath, newpath):
		"""
		Rename a file if the newpath does not already exist
		The operation will be denied if the newpath exists
		or if the oldpath is a directory
		"""
		self.log.debug("IVSFTPFileSystemServer.rename(%s, %s)", oldpath, newpath)
		oldpath = self.fspath(oldpath)
		newpath = self.fspath(newpath)
		try:
			if os.path.exists(newpath):
				return paramiko.SFTP_PERMISSION_DENIED
			if os.path.isdir(oldpath):
				return paramiko.SFTP_PERMISSION_DENIED
			os.rename(oldpath, newpath)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] rename %s %s",
				self.session_id, dquote(oldpath), dquote(newpath))
		return paramiko.SFTP_OK

	def posix_rename(self, oldpath, newpath):
		"""
		Rename a file
		"""
		self.log.debug("IVSFTPFileSystemServer.posix_rename(%s, %s)", oldpath, newpath)
		oldpath = self.fspath(oldpath)
		newpath = self.fspath(newpath)
		try:
			os.rename(oldpath, newpath)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] posix_rename %s %s",
				self.session_id, dquote(oldpath), dquote(newpath))
		return paramiko.SFTP_OK

	def mkdir(self, path, attr):
		"""
		Create a new directory with the given attributes
		This operation is automatically denied
		"""
		return paramiko.SFTP_PERMISSION_DENIED

	def rmdir(self, path):
		"""
		Remove an empty directory if it exists
		This operation is automatically denied
		"""
		return paramiko.SFTP_PERMISSION_DENIED

	def chattr(self, path, attr):
		"""
		Change the attributes of a file
		"""
		self.log.debug("IVSFTPFileSystemServer.chattr(%s, %s)", path, attr)
		path = self.fspath(path)
		try:
			paramiko.SFTPServer.set_file_attr(path, attr)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] chattr %s (%s)",
				self.session_id, dquote(path), attr)
		return paramiko.SFTP_OK

	def symlink(self, target_path, path):
		"""
		Create a symbolic link on the server, as new pathname ``path``,
		with ``target_path`` as the target of the ink
		This operation is automatically denied
		"""
		return paramiko.SFTP_PERMISSION_DENIED

	def readlink(self, path):
		"""
		Return the target of a symbolic link on the server.  If the
		specified path doesn't refer to a symbolic link then
		paramiko.SFTP_OP_UNSUPPORTED is returned
		"""
		path = self.fspath(path)

		try:
			target = os.readlink(path)
			if (len(target) > 0) and (target[0] == '/'):
				n = len(os.path.commonprefix([target, path]))
				target = os.path.relpath(target[n:], start=os.dirname(path[n:]))
			return target
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		finally:
			self.access_log.info("[%s] readlink %s",
				self.session_id, dquote(path))


class IVSFTPFileHandle(paramiko.SFTPHandle):

	def __init__(self, flags=0):
		self.n_read = 0
		self.n_write = 0
		super().__init__(flags)

	def chattr(self, attr):
		try:
			paramiko.SFTPServer.set_file_attr(self.filename, attr)
			return paramiko.SFTP_OK
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)

	def close(self):
		try:
			super().close()
		finally:
			if self.n_read:
				self.access_log.info("[%s] read %s (%d)",
					self.session_id, dquote(self.filename), self.n_read)
			if self.n_write:
				self.access_log.info("[%s] write %s (%d)",
					self.session_id, dquote(self.filename), self.n_write)

	def read(self, offset, length):
		data = super().read(offset, length)
		if not isinstance(data, str):
			self.n_read += len(data)
		return data

	def stat(self):
		try:
			return paramiko.SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)

	def write(self, offset, data):
		rc = super(IVSFTPFileHandle, self).write(offset, data)
		if rc == paramiko.SFTP_OK:
			self.n_write += len(data)
		return rc
