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
proto.btc.tx.new_swap: Bitcoin new swap transaction class
"""

from collections import namedtuple

from ....cfg import gc
from ....tx.new_swap import NewSwap as TxNewSwap
from .new import New

class NewSwap(New, TxNewSwap):
	desc = 'Bitcoin swap transaction'

	async def get_swap_output(self, proto, arg, addrfiles, desc):
		ret = namedtuple('swap_output', ['coin', 'network', 'addr', 'mmid'])
		if arg:
			from ..addrdata import TwAddrData
			pa = self.parse_cmdline_arg(
				proto,
				arg,
				self.get_addrdata_from_files(proto, addrfiles),
				await TwAddrData(self.cfg, proto, twctl=None)) # TODO: twctl required for Ethereum
			if pa.addr:
				await self.warn_addr_used(proto, pa, desc)
				return ret(proto.coin, proto.network, pa.addr, pa.mmid)

		full_desc = '{} on the {} {} network'.format(desc, proto.coin, proto.network)
		res = await self.get_autochg_addr(proto, arg, exclude=[], desc=full_desc, all_addrtypes=not arg)
		self.confirm_autoselected_addr(res.twmmid, full_desc)
		return ret(proto.coin, proto.network, res.addr, res.twmmid)

	async def process_swap_cmdline_args(self, cmd_args, addrfiles):

		class CmdlineArgs: # listed in command-line order
			# send_coin      # required: uppercase coin symbol
			send_amt  = None # optional: Omit to skip change addr and send value of all inputs minus fees to vault
			chg_spec  = None # optional: change address spec, e.g. ‘B’ ‘DEADBEEF:B’ ‘DEADBEEF:B:1’ or coin address.
							 #           Omit for autoselected change address.  Use of non-wallet change address
							 #           will emit warning and prompt user for confirmation
			# recv_coin      # required: uppercase coin symbol
			recv_spec = None # optional: destination address spec. Same rules as for chg_spec

		def check_coin_arg(coin, desc):
			if coin not in sp.params.coins[desc]:
				raise ValueError(f'{coin!r}: unsupported {desc} coin for {gc.proj_name} {sp.name} swap')
			return coin

		def get_arg():
			try:
				return args_in.pop(0)
			except:
				self.cfg._usage()

		def init_proto_from_coin(coinsym, desc):
			return init_proto(
				self.cfg,
				check_coin_arg(coinsym, desc),
				network = self.proto.network,
				need_amt = True)

		def parse():

			from ....amt import is_coin_amt
			arg = get_arg()

			# arg 1: send_coin
			self.send_proto = init_proto_from_coin(arg, 'send')
			arg = get_arg()

			# arg 2: amt
			if is_coin_amt(self.send_proto, arg):
				args.send_amt = self.send_proto.coin_amt(arg)
				arg = get_arg()

			# arg 3: chg_spec (change address spec)
			if args.send_amt:
				if not arg in sp.params.coins['receive']: # is change arg
					args.chg_spec = arg
					arg = get_arg()

			# arg 4: recv_coin
			self.recv_proto = init_proto_from_coin(arg, 'receive')

			# arg 5: recv_spec (receive address spec)
			if args_in:
				args.recv_spec = get_arg()

			if args_in: # done parsing, all args consumed
				self.cfg._usage()

		from ....protocol import init_proto
		sp = self.swap_proto_mod
		args_in = list(cmd_args)
		args = CmdlineArgs()
		parse()

		chg_output = (
			await self.get_swap_output(self.send_proto, args.chg_spec, addrfiles, 'change address')
			if args.send_amt else None)

		if chg_output:
			self.check_chg_addr_is_wallet_addr(chg_output)

		recv_output = await self.get_swap_output(self.recv_proto, args.recv_spec, addrfiles, 'destination address')

		self.check_chg_addr_is_wallet_addr(
			recv_output,
			message = (
				'Swap destination address is not an MMGen wallet address!\n'
				'To sign this transaction, autosign or txsign must be invoked with --allow-non-wallet-swap'))

		memo = sp.data(self.recv_proto, recv_output.addr)

		# this goes into the transaction file:
		self.swap_recv_addr_mmid = recv_output.mmid

		return (
			[f'vault,{args.send_amt}', chg_output.mmid, f'data:{memo}'] if args.send_amt else
			['vault', f'data:{memo}'])

	def update_data_output(self, trade_limit):
		sp = self.swap_proto_mod
		o = self.data_output._asdict()
		parsed_memo = sp.data.parse(o['data'].decode())
		memo = sp.data(
			self.recv_proto,
			self.recv_proto.coin_addr(parsed_memo.address),
			trade_limit = trade_limit)
		o['data'] = f'data:{memo}'
		self.data_output = self.Output(self.proto, **o)

	def update_vault_addr(self, addr):
		vault_idx = self.vault_idx
		assert vault_idx == 0, f'{vault_idx}: vault index is not zero!'
		o = self.outputs[vault_idx]._asdict()
		o['addr'] = addr
		self.outputs[vault_idx] = self.Output(self.proto, **o)

	@property
	def vault_idx(self):
		return self._chg_output_ops('idx', 'is_vault')

	@property
	def vault_output(self):
		return self._chg_output_ops('output', 'is_vault')
