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
proto.vm.tx.new: new transaction methods for VM chains
"""

from ....obj import MMGenTxID
from ....util import msg, is_int, is_hex_str, make_chksum_6, suf, die
from ....tw.ctl import TwCtl
from ....addr import is_mmgen_id, is_coin_addr

class New:
	desc = 'transaction'
	no_chg_msg = 'Warning: Transaction leaves account with zero balance'
	msg_insufficient_funds = 'Account balance insufficient to fund this transaction ({} {} needed)'

	# Instead of serializing tx data online as with BTC, put the data in a dict and serialize
	# offline before signing
	async def create_serialized(self, *, locktime=None):
		assert len(self.inputs) == 1, 'Transaction has more than one input!'
		o_num = len(self.outputs)
		o_ok = 0 if self.usr_contract_data else 1
		assert o_num == o_ok, f'Transaction has {o_num} output{suf(o_num)} (should have {o_ok})'
		await self.make_txobj()
		self.serialized = {k: v if v is None else str(v)
			for k, v in self.txobj.items() if k != 'token_to'}
		self.update_txid()

	def update_txid(self, data=None):
		import json
		assert not is_hex_str(self.serialized), (
			'update_txid() must be called only when self.serialized is not hex data')
		self.txid = MMGenTxID(make_chksum_6(json.dumps(data or self.serialized)).upper())

	async def process_cmdline_args(self, cmd_args, ad_f, ad_w):

		lc = len(cmd_args)

		if lc == 2 and self.is_swap:
			data_arg = cmd_args.pop()
			lc = 1
			assert data_arg.startswith('data:'), f'{data_arg}: invalid data arg (must start with "data:")'
			self.swap_memo = data_arg.removeprefix('data:')
			self.set_gas_with_data(self.swap_memo.encode())

		if lc == 0 and self.usr_contract_data and 'Token' not in self.name:
			return

		if lc != 1:
			die(1, f'{lc} output{suf(lc)} specified, but VM transactions must have exactly one')

		a = self.parse_cmdline_arg(self.proto, cmd_args[0], ad_f, ad_w)

		self.add_output(
			coinaddr = None if a.is_vault else a.addr,
			amt      = self.proto.coin_amt(a.amt or '0'),
			is_chg   = not a.amt,
			is_vault = a.is_vault)

		self.add_mmaddrs_to_outputs(ad_f, ad_w)

	def get_unspent_nums_from_user(self, unspent):
		from ....ui import line_input
		while True:
			if reply := line_input(self.cfg, 'Enter an account to spend from: ').strip():
				if not is_int(reply):
					msg('Account number must be an integer')
				elif int(reply) < 1:
					msg('Account number must be >= 1')
				elif int(reply) > len(unspent):
					msg(f'Account number must be <= {len(unspent)}')
				else:
					return [int(reply)]

	def check_chg_addr_is_wallet_addr(self):
		pass

	def check_fee(self):
		if not self.disable_fee_check:
			assert self.usr_fee <= self.proto.max_tx_fee

	@property
	def total_gas(self):
		return self.gas

	def update_change_output(self, funds_left):
		if self.outputs and self.outputs[0].is_chg:
			self.update_output_amt(0, funds_left)

	async def get_input_addrs_from_inputs_opt(self):
		ret = []
		if self.cfg.inputs:
			data_root = (await TwCtl(self.cfg, self.proto)).data_root # must create new instance here
			errmsg = 'Address {!r} not in tracking wallet'
			for addr in self.cfg.inputs.split(','):
				if is_mmgen_id(self.proto, addr):
					for waddr in data_root:
						if data_root[waddr]['mmid'] == addr:
							ret.append(waddr)
							break
					else:
						die('UserAddressNotInWallet', errmsg.format(addr))
				elif is_coin_addr(self.proto, addr):
					if not addr in data_root:
						die('UserAddressNotInWallet', errmsg.format(addr))
					ret.append(addr)
				else:
					die(1, f'{addr!r}: not an MMGen ID or coin address')
		return ret

	def final_inputs_ok_msg(self, funds_left):
		chg = self.proto.coin_amt('0') if (self.outputs and self.outputs[0].is_chg) else funds_left
		return 'Transaction leaves {} {} in the sender’s account'.format(chg.hl(), self.proto.coin)
