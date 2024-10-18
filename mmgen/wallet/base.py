#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
wallet.base: wallet base class
"""

import os

from ..util import msg, die
from ..color import orange
from ..objmethods import MMGenObject
from . import wallet_data, get_wallet_cls

class WalletMeta(type):

	def __init__(cls, name, bases, namespace):
		t = cls.__module__.rsplit('.', maxsplit=1)[-1]
		if t in wallet_data:
			for k, v in wallet_data[t]._asdict().items():
				setattr(cls, k, v)

class wallet(MMGenObject, metaclass=WalletMeta):

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
		passwd_file   = None):

		self.passwd_file = None if passwd_file is False else (passwd_file or self.cfg.passwd_file)
		self.ssdata = self.WalletData()
		self.msg = {}
		self.in_data = in_data

		for c in reversed(self.__class__.__mro__):
			if hasattr(c, '_msg'):
				self.msg.update(c._msg)

		if hasattr(self, 'seed'):
			self._encrypt()
			return
		elif hasattr(self, 'infile') or self.in_data or not self.cfg.stdin_tty:
			self._deformat_once()
			self._decrypt_retry()
		else:
			if not self.stdin_ok:
				die(1, f'Reading from standard input not supported for {self.desc} format')
			self._deformat_retry()
			self._decrypt_retry()

		self.cfg._util.qmsg('Valid {a} for Seed ID {b}{c}{d}'.format(
			a = self.desc,
			b = self.seed.sid.hl(),
			c = f' (seed length {self.seed.bitlen})' if self.seed.bitlen != 256 else '',
			d = '' if not hasattr(self, 'mnemonic') or self.mnemonic.has_chksum else
				orange(' [mnemonic format has no checksum]')
		))

	def _get_data(self):
		if hasattr(self, 'infile'):
			from ..fileutil import get_data_from_file
			self.fmt_data = get_data_from_file(
				self.cfg,
				self.infile.name,
				self.desc,
				binary = self.file_mode=='binary')
		elif self.in_data:
			self.fmt_data = self.in_data
		else:
			self.fmt_data = self._get_data_from_user(self.desc)

	def _get_data_from_user(self, desc):
		from ..ui import get_data_from_user
		return get_data_from_user(self.cfg, desc)

	def _deformat_once(self):
		self._get_data()
		if not self._deformat():
			die(2, 'Invalid format for input data')

	def _deformat_retry(self):
		while True:
			self._get_data()
			if self._deformat():
				break
			msg('Trying again...')

	@staticmethod
	def ext_to_cls(ext, proto):
		return get_wallet_cls(ext=ext)

	def get_fmt_data(self):
		self._format()
		return self.fmt_data

	def write_to_file(self, outdir='', desc=''):
		self._format()
		kwargs = {
			'desc':     desc or self.desc,
			'ask_tty':  self.ask_tty,
			'no_tty':   self.no_tty,
			'binary':   self.file_mode == 'binary'
		}

		if outdir:
			# write_data_to_file(): outfile with absolute path overrides self.cfg.outdir
			of = os.path.abspath(os.path.join(outdir, self._filename()))

		from ..fileutil import write_data_to_file
		write_data_to_file(
			self.cfg,
			of if outdir else self._filename(),
			self.fmt_data,
			**kwargs)

	def check_usr_seed_len(self, bitlen=None):
		chk = bitlen or self.seed.bitlen
		if self.cfg.seed_len and self.cfg.seed_len != chk:
			die(1, f'ERROR: requested seed length ({self.cfg.seed_len}) doesn’t match seed length of source ({chk})')
