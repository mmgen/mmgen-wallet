#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
wallet.base: wallet base class
"""

import os

from ..globalvars import g
from ..opts import opt
from ..util import msg,qmsg,die
from ..objmethods import MMGenObject
from . import Wallet,wallet_data,get_wallet_cls

class WalletMeta(type):

	def __init__(cls,name,bases,namespace):
		t = cls.__module__.split('.')[-1]
		if t in wallet_data:
			for k,v in wallet_data[t]._asdict().items():
				setattr(cls,k,v)

class wallet(MMGenObject,metaclass=WalletMeta):

	desc = 'MMGen seed source'
	file_mode = 'text'
	filename_api = True
	stdin_ok = False
	ask_tty = True
	no_tty  = False
	op = None

	class WalletData(MMGenObject):
		pass

	def __init__(self,
		in_data       = None,
		passwd_file   = None ):

		self.passwd_file = passwd_file or opt.passwd_file
		self.ssdata = self.WalletData()
		self.msg = {}
		self.in_data = in_data

		for c in reversed(self.__class__.__mro__):
			if hasattr(c,'_msg'):
				self.msg.update(c._msg)

		if hasattr(self,'seed'):
			self._encrypt()
			return
		elif hasattr(self,'infile') or self.in_data or not g.stdin_tty:
			self._deformat_once()
			self._decrypt_retry()
		else:
			if not self.stdin_ok:
				die(1,f'Reading from standard input not supported for {self.desc} format')
			self._deformat_retry()
			self._decrypt_retry()

		qmsg('Valid {} for Seed ID {}{}'.format(
			self.desc,
			self.seed.sid.hl(),
			(f', seed length {self.seed.bitlen}' if self.seed.bitlen != 256 else '')
		))

	def _get_data(self):
		if hasattr(self,'infile'):
			from ..fileutil import get_data_from_file
			self.fmt_data = get_data_from_file(self.infile.name,self.desc,binary=self.file_mode=='binary')
		elif self.in_data:
			self.fmt_data = self.in_data
		else:
			self.fmt_data = self._get_data_from_user(self.desc)

	def _get_data_from_user(self,desc):
		from ..ui import get_data_from_user
		return get_data_from_user(desc)

	def _deformat_once(self):
		self._get_data()
		if not self._deformat():
			die(2,'Invalid format for input data')

	def _deformat_retry(self):
		while True:
			self._get_data()
			if self._deformat():
				break
			msg('Trying again...')

	@classmethod
	def ext_to_cls(cls,ext,proto):
		return get_wallet_cls(ext=ext)

	def get_fmt_data(self):
		self._format()
		return self.fmt_data

	def write_to_file(self,outdir='',desc=''):
		self._format()
		kwargs = {
			'desc':     desc or self.desc,
			'ask_tty':  self.ask_tty,
			'no_tty':   self.no_tty,
			'binary':   self.file_mode == 'binary'
		}

		if outdir:
			# write_data_to_file(): outfile with absolute path overrides opt.outdir
			of = os.path.abspath(os.path.join(outdir,self._filename()))

		from ..fileutil import write_data_to_file
		write_data_to_file(
			of if outdir else self._filename(),
			self.fmt_data,
			**kwargs )

	def check_usr_seed_len(self,bitlen=None):
		chk = bitlen or self.seed.bitlen
		if opt.seed_len and opt.seed_len != chk:
			die(1,f'ERROR: requested seed length ({opt.seed_len}) doesn’t match seed length of source ({chk})')
