#!/usr/bin/env python

import logging
import os
import paramiko


class IVSFTPFileSystemServer(paramiko.SFTPServerInterface):

	def __init__(self, server, *args, **kwargs):
		"""Initialize a new IVSFTPFileSystemServer

		An IVSFTPFileSystemServer implements a basic
		SFTP server on top of a local filesystem.

		Parameters:

		server - instance of parimiko.ServerInterface associated with the request

			The following attributes must be available on the server:

			home_dir - path to the client user's ``home`` directory
			on the filesystem, which will act as the root of the
			client's filesystem operations

			user - user object associated with the client

			publishers - list of publisher objects associated with the client

		*args - list with the following items:
			args[0] Namespace object with the following fields:
				log - Logger instance

		**kwargs - ignored
		"""
		self.server = server
		self.args = args[0]
		self.log = logging.getLogger(self.args.name)

		if not hasattr(self.server, 'home_dir'):
			raise Exception('server missing required attribte: home_dir')
		if not hasattr(self.server, 'user'):
			raise Exception('server missing required attribte: user')
		if not hasattr(self.server, 'publishers'):
			raise Exception('server missing required attribte: publishers')

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
		fobj.user_id = self.server.user.user_id
		fobj.user_email= self.server.user.email
		fobj.access = self.args.access
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
		return paramiko.SFTP_OK

	def rename(self, oldpath, newpath):
		"""
		Rename a file if the newpath does not already exist
		"""
		self.log.debug("IVSFTPFileSystemServer.rename(%s, %s)", oldpath, newpath)
		oldpath = self.fspath(oldpath)
		newpath = self.fspath(newpath)
		try:
			if os.path.exists(newpath):
				return paramiko.SFTP_PERMISSION_DENIED
			os.rename(oldpath, newpath)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
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
		return paramiko.SFTP_OK

	def mkdir(self, path, attr):
		"""
		Create a new directory with the given attributes
		"""
		self.log.debug("IVSFTPFileSystemServer.mkdir(%s, %s)", path, attr)
		path = self.fspath(path)
		try:
			os.mkdir(path)
			if attr is not None:
				paramiko.SFTPServer.set_file_attr(path, attr)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		return paramiko.SFTP_OK

	def rmdir(self, path):
		"""
		Remove an empty directory if it exists
		"""
		self.log.debug("IVSFTPFileSystemServer.rmdir(%s)", path)
		path = self.fspath(path)
		try:
			if os.path.isdir(path):
				os.rmdir(path)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		return paramiko.SFTP_OK

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
		return paramiko.SFTP_OK

	def symlink(self, target_path, path):
		"""
		Create a symbolic link on the server, as new pathname ``path``,
		with ``target_path`` as the target of the ink
		"""
		self.log.debug("IVSFTPFileSystemServer.symlink(%s, %s)", target_path, path)

		# if target_path is relative place it under the same dir as path
		if (len(target_path) > 0) and (target_path[0] != '/'):
			target_path = os.path.join(os.path.dirname(path), target_path)

		target_path = self.fspath(target_path)
		path = self.fspath(path)

		if os.path.exists(path):
			return paramiko.SFTP_PERMISSION_DENIED

		n = len(os.path.commonprefix([target_path, path]))
		target = os.path.relpath(target_path[n:], start=os.path.dirname(path[n:]))
		try:
			os.symlink(target, path)
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)
		return paramiko.SFTP_OK

	def readlink(self, path):
		"""
		Return the target of a symbolic link on the server.  If the
		specified path doesn't refer to a symbolic link then
		paramiko.SFTP_OP_UNSUPPORTED is returned
		"""
		self.log.debug("IVSFTPFileSystemServer.readlink(%s)", path)
		path = self.fspath(path)

		try:
			target = os.readlink(path)
			if (len(target) > 0) and (target[0] == '/'):
				n = len(os.path.commonprefix([target, path]))
				target = os.path.relpath(target[n:], start=os.dirname(path[n:]))
			return target
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)


class IVSFTPFileHandle(paramiko.SFTPHandle):

	def read(self, offset, length):
		n = 0
		try:
			super().read(offset, length)
			n = length
		finally:
			self.n_read += n

	def write(self, offset, data):
		n = 0
		try:
			super().write(offset, data)
			n = len(data)
		finally:
			self.n_write += n

	def stat(self):
		try:
			return paramiko.SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
		except OSError as e:
			return paramiko.SFTPServer.convert_errno(e.errno)

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
			if self.bytes_read:
				self.access("%s:%s:READ:%s:%d".format(self.user_id, self.user_email, self.filename))
			if self.bytes_write:
				self.access("%s:%s:WRITE:%s:%d".format(self.user_id, self.user_email, self.filename))
