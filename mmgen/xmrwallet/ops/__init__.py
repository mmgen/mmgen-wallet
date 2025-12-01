#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.ops.__init__: Monero wallet ops for the MMGen Suite
"""

import re, atexit

from ...color import blue
from ...util import msg, die, fmt
from ...protocol import init_proto
from ...tx.util import get_autosign_obj

from ... import xmrwallet

from .. import uarg_info

class OpBase:

	opts = ('wallet_dir',)
	trust_monerod = False
	do_umount = True
	name = None
	return_data = False

	def __init__(self, cfg, uarg_tuple):

		def gen_classes():
			for cls in type(self).__mro__:
				if not cls.__name__.startswith('OpMixin'):
					yield cls
				if cls.__name__ == 'OpBase':
					break

		self.cfg = cfg
		self.uargs = uarg_tuple
		self.compat_call = self.uargs.compat_call
		self.tx_dir = 'txauto_dir' if self.compat_call else 'xmr_tx_dir'

		classes = tuple(gen_classes())
		self.opts = tuple(set(opt for cls in classes for opt in xmrwallet.opts))

		if not hasattr(self, 'stem'):
			self.stem = self.name

		global fmt_amt, hl_amt, addr_width

		def fmt_amt(amt):
			return self.proto.coin_amt(amt, from_unit='atomic').fmt(5, prec=12, color=True)
		def hl_amt(amt):
			return self.proto.coin_amt(amt, from_unit='atomic').hl()

		addr_width = 95 if self.cfg.full_address else 24

		self.proto = init_proto(cfg, 'xmr', network=self.cfg.network, need_amt=True)

		id_cur = None
		for cls in classes:
			if id(cls.check_uopts) != id_cur:
				cls.check_uopts(self)
				id_cur = id(cls.check_uopts)

		id_cur = None
		for cls in classes:
			if id(cls.pre_init_action) != id_cur:
				cls.pre_init_action(self)
				id_cur = id(cls.pre_init_action)

		if cfg.autosign:
			self.asi = get_autosign_obj(cfg)

	def check_uopts(self):

		def check_pat_opt(name):
			val = getattr(self.cfg, name)
			if not re.fullmatch(uarg_info[name].pat, val, re.ASCII):
				die(1, '{!r}: invalid value for --{}: it must have format {!r}'.format(
					val,
					name.replace('_', '-'),
					uarg_info[name].annot))

		for attr in self.cfg.__dict__:
			if attr in xmrwallet.opts and not attr in self.opts:
				die(1, 'Option --{} not supported for {!r} operation'.format(
					attr.replace('_', '-'),
					self.name))

		for opt in xmrwallet.pat_opts:
			if getattr(self.cfg, opt, None):
				check_pat_opt(opt)

	def parse_tx_relay_opt(self):
		return re.fullmatch(
			uarg_info['tx_relay_daemon'].pat,
			self.cfg.tx_relay_daemon,
			re.ASCII)

	def get_tx_cls(self, clsname):
		from ..file.tx import MoneroMMGenTX
		return getattr(MoneroMMGenTX, clsname + ('Compat' if self.compat_call else ''))

	def display_tx_relay_info(self, *, indent=''):
		m = self.parse_tx_relay_opt()
		msg(fmt(f"""
			TX relay info:
			  Host:  {blue(m[1])}
			  Proxy: {blue(m[2] or 'None')}
			""", strip_char='\t', indent=indent))

	def mount_removable_device(self, registered=[]):
		if self.cfg.autosign:
			if not self.asi.device_inserted:
				die(1, 'Removable device not present!')
			if self.do_umount and not registered:
				atexit.register(lambda: self.asi.do_umount())
				registered.append(None)
			self.asi.do_mount()
			self.post_mount_action()

	def pre_init_action(self):
		pass

	def post_main_success(self):
		pass

	def post_main_failure(self):
		pass

	async def stop_wallet_daemon(self):
		pass

	def post_mount_action(self):
		pass
