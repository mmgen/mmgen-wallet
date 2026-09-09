#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.completed: completed transaction class
"""

from ..cfg import gc
from ..util import msg, ymsg, die
from .base import Base

class Completed(Base):
	"""
	signed or unsigned transaction with associated file
	"""
	filename_api = True
	txfile_version = 4

	def __init__(self, cfg, *args, filename=None, data=None, quiet_open=False, **kwargs):

		assert (filename or data) and not (filename and data), 'CompletedTX_chk1'

		super().__init__(*args, cfg=cfg, **kwargs)

		if data:
			self.__dict__ = data | {'twctl': self.twctl}
			self.name = type(self).__name__
		else:
			from .file import MMGenTxFile
			try:
				MMGenTxFile(self).parse(str(filename), quiet_open=quiet_open)
				self.check_serialized_integrity()
			except Exception:
				from ..color import orange
				msg(orange(
					f'Something is wrong with transaction file ‘{filename}’\n'
					'To fix this problem, please move or delete the file'))
				raise

			# repeat with sign and send, because coin daemon could be restarted
			self.check_correct_chain()

			if self.check_sigs() != self.signed:
				die(1, 'Transaction is {}signed!'.format('not ' if self.signed else ''))

			self.infile = filename

	@property
	def file(self):
		from .file import MMGenTxFile
		return MMGenTxFile(self)

	@staticmethod
	def ext_to_cls(ext, proto):
		"""
		see twctl:import_token()
		"""
		from .unsigned import Unsigned, AutomountUnsigned
		from .online import Sent, AutomountSent
		for cls in (Unsigned, AutomountUnsigned, Sent, AutomountSent):
			if ext == cls.ext:
				return cls

		if proto.tokensym:
			from .online import OnlineSigned as Signed
			from .online import AutomountOnlineSigned as AutomountSigned
		else:
			from .signed import Signed, AutomountSigned
		for cls in (Signed, AutomountSigned):
			if ext == cls.ext:
				return cls

	def check_swap_memo(self):
		if memo_bytes := self.get_swap_memo_maybe():
			from ..swap.proto.thorchain import Memo
			if Memo.is_partial_memo(memo_bytes):
				from ..protocol import init_proto
				text = memo_bytes.decode('ascii')
				p = Memo.parse(text)
				r = self.recv_asset
				assert p.function == 'SWAP', f'‘{p.function}’: unsupported function in swap memo ‘{text}’'
				assert p.asset.name == r.name, f'invalid memo: {p.asset.name} != {r.name}'
				proto = init_proto(
						self.cfg,
						r.coin,
						network = self.cfg.network,
						tokensym = r.tokensym,
						need_amt = True)
				if mmid := getattr(self, 'swap_recv_addr_mmid', None):
					pass
				elif self.cfg.allow_non_wallet_swap:
					ymsg('Warning: allowing swap to non-wallet address (--allow-non-wallet-swap)')
				else:
					raise ValueError('Swap to non-wallet address forbidden (override with --allow-non-wallet-swap)')
				return self.Output(proto, addr=p.address, mmid=mmid, amt=proto.coin_amt('0'))

		if self.is_swap:
			raise ValueError('missing or invalid memo in swap transaction')

	def die_on_version_error(self, errmsg): # overridden by test.overlay.fakemods
		die('TxFileVersionError', errmsg)

	def legacy_fmt_chk(self, desc):
		if 'sign' in gc.prog_name:
			a, b = ('sign', 'Has your online installation been compromised?')
		elif 'send' in gc.prog_name:
			a, b = ('send', 'Is your offline installation out of date?')
		else:
			return
		fs = f'Request to {{}} legacy-format transaction ({desc}). {{}}'
		self.die_on_version_error(fs.format(a, b))

	def txfile_version_chk(self, f_ver, s_ver):
		if 'sign' in gc.prog_name:
			a = 'sign'
			b = 'Is your {} installation out of date?'.format('offline' if f_ver > s_ver else 'online')
		elif 'send' in gc.prog_name:
			a = 'send'
			b = 'Is your {} installation out of date?'.format('offline' if f_ver < s_ver else 'online')
		else:
			return
		fs = (
			f'Request to {{}} transaction with version {f_ver}, which is {{}} '
			f'than version {s_ver} current with installed software. {{}}')
		self.die_on_version_error(fs.format(a, ('greater' if f_ver > s_ver else 'less'), b))

class DummyCompleted: # required by MMGenTxFile.get_proto()

	desc = 'dummy transaction'

	def __init__(self, cfg):
		self.cfg = cfg

	die_on_version_error = Completed.die_on_version_error
	legacy_fmt_chk = Completed.legacy_fmt_chk
