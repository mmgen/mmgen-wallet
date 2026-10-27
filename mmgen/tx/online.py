# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.online: online signed transaction class
"""

import time, asyncio

from ..obj import MMGenRange
from ..util import msg, Msg, gmsg, ymsg, make_timestr, die
from ..color import pink, yellow

from .signed import Signed, AutomountSigned

def test_txid(txid, txid_chk):
	if txid == txid_chk:
		return 0
	else:
		ymsg(f'Warning: txid mismatch (after sending) ({txid} != {txid_chk})')
		return 1

class SentTXRange(MMGenRange):
	min_idx = 0
	max_idx = 1_000_000

class CreatedTXRange(SentTXRange):
	pass

class OnlineSigned(Signed):
	"""
	send_op_*() methods return an integer exit value to the system
	"""

	@property
	def status(self):
		from . import _base_proto_subclass
		return _base_proto_subclass('Status', 'status', proto=self.proto)(self)

	async def check_memoless_presend(self, *, amt=None):
		data = self.swap_proto_rpc.do_validate_amt(self.send_asset, amt or self.vault_output.amt)
		if data['reference'] != self.refnum:
			die(3, f'registered reference number ({data["reference"]}) does not match ours ({self.refnum})')
		if not data['available']:
			die(3, f'reference number {self.refnum} is not available')
		self.memoless_memo = data['memo']
		await self.parse_network_memo(
			data = data,
			recv_asset_spec = self.swap_recv_asset_spec,
			recv_twmmid = self.swap_recv_addr_mmid)

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
			cfg = self.cfg,
			message = '' if self.cfg.quiet else
				'Once this transaction is sent, there’s no taking it back!',
			action = 'broadcast this transaction to the {} {} network'.format(
				self.proto.coin,
				self.proto.network.upper()),
			expect = 'YES')
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

	async def send_op_status(self, cfg, idx, txid, txhex, op_val):
		if cfg.verbose:
			await self.post_network_send(txid)
		else:
			cfg._util.qmsg(f'{self.proto.coin} TxID: {txid.hl()}')
		return await self.status.display(idx=idx)

	async def send_op_receipt(self, cfg, idx, txid, txhex, op_val):
		if res := await self.get_receipt(txid, receipt_only=True):
			import json
			Msg(json.dumps(res, indent=4))
			return 0
		else:
			msg(f'Unable to get receipt for TX {txid.hl()}')
			return 1

	async def send_op_dump_hex(self, cfg, idx, txid, txhex, op_val):
		from ..fileutil import write_data_to_file
		sfx = idx + 1 if idx else ''
		write_data_to_file(
			cfg,
			('-' if op_val == '-' else f'{op_val}{sfx}'),
			txhex + '\n',
			desc = 'serialized transaction hex data',
			ask_overwrite = False,
			ask_tty = False)
		return 0

	async def send_op_rpc_send(self, cfg, idx, txid, txhex, op_val):
		msg(f'Sending TX: {txid.hl()}')
		if cfg.test_suite_bogus_send:
			msg(f'BOGUS transaction NOT sent: {txid.hl()}')
			return 0
		else:
			if idx:
				await asyncio.sleep(1)
			ret = await self.rpc_send(txhex)
			msg(f'Transaction sent: {txid.hl()}')
			return test_txid(ret, txid)

	async def send_op_rpc_test(self, cfg, idx, txid, txhex, op_val):
		if await self.test_sendable(txhex):
			gmsg('Transaction can be sent')
			return 0
		else:
			ymsg('Transaction cannot be sent')
			return 1

	async def send_op_proxy_send(self, cfg, idx, txid, txhex, op_val, *, test=False):
		if idx and not cfg.test_suite:
			await asyncio.sleep(2)
		from .tx_proxy import send_tx
		msg('{} TX: {}'.format('Testing' if test else 'Sending', txid.hl()))
		ret = send_tx(cfg, txhex, test=test)
		return 0 if test else test_txid(ret, txid)

	async def send_op_proxy_test(self, cfg, idx, txid, txhex, op_val):
		return await self.send_op_proxy_send(cfg, idx, txid, txhex, op_val, test=True)

	async def send(self, cfg, op, op_val, asi, batch=False):
		"""
		returns an integer exit value to the system
		"""

		sending = op in ('rpc_send', 'proxy_send')
		idxs = (
			[int(cfg.txhex_idx) - 1] if cfg.txhex_idx else
			[0, 1] if getattr(self, 'coin_txid2', None) else
			[0])
		ret = []
		post_network_ret = []

		if sending:
			self.confirm_send(idxs)

		for idx in idxs:
			sfx = idx + 1 if idx else ''
			txid = getattr(self, f'coin_txid{sfx}')
			txhex = getattr(self, f'serialized{sfx}')
			ret.append(await getattr(self, f'send_op_{op}')(cfg, idx, txid, txhex, op_val))
			if op == 'proxy_send' and cfg.test:
				continue
			if sending and cfg.wait:
				post_network_ret.append(await self.post_network_send(txid))

		if sending and all(post_network_ret) and not cfg.txhex_idx:
			from ..ui import keypress_confirm
			if op == 'rpc_send' or not asi or keypress_confirm(
					cfg, 'Mark transaction as sent on removable device?'):
				await self.post_send(asi)

		if op == 'status' and cfg.verbose:
			if batch:
				self.info.view(pause=False, terse=True)
			else:
				self.info.view_with_prompt('View transaction details?', pause=False)

		return max(ret)

class AutomountOnlineSigned(AutomountSigned, OnlineSigned):
	pass

class Sent(OnlineSigned):
	desc = 'sent transaction'
	ext = 'subtx'

class AutomountSent(AutomountOnlineSigned):
	desc = 'sent automount transaction'
	ext = 'asubtx'
