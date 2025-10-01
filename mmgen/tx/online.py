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

import sys, time, asyncio

from ..util import msg, Msg, gmsg, ymsg, make_timestr, die
from ..color import pink, yellow

from .signed import Signed, AutomountSigned

class OnlineSigned(Signed):

	@property
	def status(self):
		from . import _base_proto_subclass
		return _base_proto_subclass('Status', 'status', {'proto': self.proto})(self)

	def check_swap_expiry(self):
		from ..util2 import format_elapsed_hr
		expiry = self.swap_quote_expiry
		now = int(time.time())
		t_rem = expiry - now
		clr = yellow if t_rem < 0 else pink
		msg('Swap quote {a} {b} [{c}]'.format(
			a = clr('expired' if t_rem < 0 else 'expires'),
			b = clr(format_elapsed_hr(expiry, now=now, future_msg='from now')),
			c = make_timestr(expiry)))
		return t_rem >= 0

	def confirm_send(self, idxs):
		from ..ui import confirm_or_raise
		confirm_or_raise(
			cfg     = self.cfg,
			message = '' if self.cfg.quiet else 'Once this transaction is sent, there’s no taking it back!',
			action  = f'broadcast this transaction to the {self.proto.coin} {self.proto.network.upper()} network',
			expect  = 'YES' if self.cfg.quiet or self.cfg.yes else 'YES, I REALLY WANT TO DO THIS')
		msg('Sending transaction')
		if len(idxs) > 1 and getattr(self, 'coin_txid2', None) and self.is_swap:
			ymsg('Warning: two transactions (approval and router) will be broadcast to the network')

	async def post_send(self, asi):
		from . import SentTX
		tx2 = await SentTX(cfg=self.cfg, data=self.__dict__, automount=bool(asi))
		tx2.add_sent_timestamp()
		tx2.add_blockcount()
		tx2.file.write(
			outdir        = asi.txauto_dir if asi else None,
			ask_overwrite = False,
			ask_write     = False)

	async def send(self, cfg, asi):

		status_exitval = None
		sent_status = None
		all_ok = True
		idxs = ['', '2']

		if cfg.txhex_idx:
			if getattr(self, 'coin_txid2', None):
				if cfg.txhex_idx in ('1', '2'):
					idxs = ['' if cfg.txhex_idx == '1' else cfg.txhex_idx]
				else:
					die(1, f'{cfg.txhex_idx}: invalid parameter for --txhex-idx (must be 1 or 2)')
			else:
				die(1, 'Transaction has only one part, so --txhex-idx makes no sense')

		if not (cfg.status or cfg.receipt or cfg.dump_hex or cfg.test):
			self.confirm_send(idxs)

		for idx in idxs:
			if coin_txid := getattr(self, f'coin_txid{idx}', None):
				txhex = getattr(self, f'serialized{idx}')
				if cfg.status:
					cfg._util.qmsg(f'{self.proto.coin} txid: {coin_txid.hl()}')
					if cfg.verbose:
						await self.post_network_send(coin_txid)
					status_exitval = await self.status.display(idx=idx)
				elif cfg.receipt:
					if res := await self.get_receipt(coin_txid, receipt_only=True):
						import json
						Msg(json.dumps(res, indent=4))
					else:
						msg(f'Unable to get receipt for TX {coin_txid.hl()}')
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
					if idx != '' and not cfg.test_suite:
						await asyncio.sleep(2)
					from .tx_proxy import send_tx
					msg('{} TX: {}'.format('Testing' if cfg.test else 'Sending', coin_txid.hl()))
					if ret := send_tx(cfg, txhex):
						if ret != coin_txid:
							ymsg(f'Warning: txid mismatch (after sending) ({ret} != {coin_txid})')
						sent_status = 'confirm_post_send'
					if cfg.test:
						break
				elif cfg.test:
					if await self.test_sendable(txhex):
						gmsg('Transaction can be sent')
					else:
						ymsg('Transaction cannot be sent')
				else: # node send
					msg(f'Sending TX: {coin_txid.hl()}')
					if cfg.bogus_send:
						msg(f'BOGUS transaction NOT sent: {coin_txid.hl()}')
					else:
						if idx != '':
							await asyncio.sleep(1)
						ret = await self.send_with_node(txhex)
						msg(f'Transaction sent: {coin_txid.hl()}')
						if ret != coin_txid:
							die('TxIDMismatch', f'txid mismatch (after sending) ({ret} != {coin_txid})')
					sent_status = 'no_confirm_post_send'

				if cfg.wait and sent_status:
					res = await self.post_network_send(coin_txid)
					if all_ok:
						all_ok = res

		if not cfg.txhex_idx and sent_status and all_ok:
			from ..ui import keypress_confirm
			if sent_status == 'no_confirm_post_send' or not asi or keypress_confirm(
					cfg, 'Mark transaction as sent on removable device?'):
				await self.post_send(asi)

		if status_exitval is not None:
			if cfg.verbose:
				self.info.view_with_prompt('View transaction details?', pause=False)
			sys.exit(status_exitval)

class AutomountOnlineSigned(AutomountSigned, OnlineSigned):
	pass

class Sent(OnlineSigned):
	desc = 'sent transaction'
	ext = 'subtx'

class AutomountSent(AutomountOnlineSigned):
	desc = 'sent automount transaction'
	ext = 'asubtx'
