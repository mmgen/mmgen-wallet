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
tx.online: online signed transaction class
"""

from .signed import Signed, AutomountSigned

class OnlineSigned(Signed):

	@property
	def status(self):
		from . import _base_proto_subclass
		return _base_proto_subclass('Status', 'status', self.proto)(self)

	def check_swap_expiry(self):
		import time
		from ..util import msg, make_timestr
		from ..util2 import format_elapsed_hr
		from ..color import pink, yellow
		expiry = self.swap_quote_expiry
		now = int(time.time())
		t_rem = expiry - now
		clr = yellow if t_rem < 0 else pink
		msg('Swap quote {a} {b} [{c}]'.format(
			a = clr('expired' if t_rem < 0 else 'expires'),
			b = clr(format_elapsed_hr(expiry, now=now, future_msg='from now')),
			c = make_timestr(expiry)))
		return t_rem >= 0

	def confirm_send(self):
		from ..util import msg
		from ..ui import confirm_or_raise
		confirm_or_raise(
			cfg     = self.cfg,
			message = '' if self.cfg.quiet else 'Once this transaction is sent, there’s no taking it back!',
			action  = f'broadcast this transaction to the {self.proto.coin} {self.proto.network.upper()} network',
			expect  = 'YES' if self.cfg.quiet or self.cfg.yes else 'YES, I REALLY WANT TO DO THIS')
		msg('Sending transaction')

	async def post_send(self, asi):
		from . import SentTX
		tx2 = await SentTX(cfg=self.cfg, data=self.__dict__, automount=bool(asi))
		tx2.add_sent_timestamp()
		tx2.add_blockcount()
		tx2.file.write(
			outdir        = asi.txauto_dir if asi else None,
			ask_overwrite = False,
			ask_write     = False)
		tx2.post_write()

	async def send(self, cfg, asi):

		if not (cfg.receipt or cfg.dump_hex or cfg.test):
			self.confirm_send()

		sent_status = None

		for idx in ('', '2'):
			if coin_txid := getattr(self, f'coin_txid{idx}', None):
				txhex = getattr(self, f'serialized{idx}')
				if cfg.receipt:
					import sys
					sys.exit(await self.status.display(print_receipt=True, idx=idx))
				elif cfg.dump_hex:
					from ..fileutil import write_data_to_file
					write_data_to_file(
							cfg,
							cfg.dump_hex + idx,
							txhex + '\n',
							desc = 'serialized transaction hex data',
							ask_overwrite = False,
							ask_tty = False)
				elif cfg.tx_proxy:
					from .tx_proxy import send_tx
					if ret := send_tx(cfg, txhex):
						if ret != coin_txid:
							from ..util import ymsg
							ymsg(f'Warning: txid mismatch (after sending) ({ret} != {coin_txid})')
						sent_status = 'confirm_post_send'
				elif cfg.test:
					await self.test_sendable(txhex)
				else: # node send
					if not cfg.bogus_send:
						ret = await self.send_with_node(txhex)
						assert ret == coin_txid, f'txid mismatch (after sending) ({ret} != {coin_txid})'
					desc = 'BOGUS transaction NOT' if cfg.bogus_send else 'Transaction'
					from ..util import msg
					msg(desc + ' sent: ' + coin_txid.hl())
					sent_status = 'no_confirm_post_send'

		if sent_status:
			from ..ui import keypress_confirm
			if sent_status == 'no_confirm_post_send' or not asi or keypress_confirm(
					cfg, 'Mark transaction as sent on removable device?'):
				await self.post_send(asi)

class AutomountOnlineSigned(AutomountSigned, OnlineSigned):
	pass

class Sent(OnlineSigned):
	desc = 'sent transaction'
	ext = 'subtx'

class AutomountSent(AutomountOnlineSigned):
	desc = 'sent automount transaction'
	ext = 'asubtx'
