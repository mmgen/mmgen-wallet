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
tx.new_swap: new swap transaction class
"""

from collections import namedtuple
from ..cfg import gc

from .new import New
from ..amt import UniAmt

class NewSwap(New):
	desc = 'swap transaction'

	def __init__(self, *args, **kwargs):
		import importlib
		self.is_swap = True
		self.swap_proto = kwargs['cfg'].swap_proto
		self.swap_proto_mod = importlib.import_module(f'mmgen.swap.proto.{self.swap_proto}')
		New.__init__(self, *args, **kwargs)

	def check_addr_is_wallet_addr(self, output, *, message):
		if not output.mmid:
			self._non_wallet_addr_confirm(message)

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
			send_amt  = None # optional: Omit to skip change addr and send value of all inputs minus fees
							 #           to vault
			chg_spec  = None # optional: change address spec, e.g. ‘B’ ‘DEADBEEF:B’ ‘DEADBEEF:B:1’ or coin
							 #           address.  Omit for autoselected change address. Use of non-wallet
							 #           change address will emit warning and prompt user for confirmation
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

			from ..amt import is_coin_amt
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

		from ..protocol import init_proto
		sp = self.swap_proto_mod
		args_in = list(cmd_args)
		args = CmdlineArgs()
		parse()

		chg_output = (
			await self.get_swap_output(self.send_proto, args.chg_spec, addrfiles, 'change address')
			if args.send_amt else None)

		if chg_output:
			self.check_addr_is_wallet_addr(
				chg_output,
				message = 'Change address is not an MMGen wallet address!')

		recv_output = await self.get_swap_output(self.recv_proto, args.recv_spec, addrfiles, 'destination address')

		self.check_addr_is_wallet_addr(
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

	def process_swap_options(self):
		if s := self.cfg.trade_limit:
			self.usr_trade_limit = (
				1 - float(s[:-1]) / 100 if s.endswith('%') else
				UniAmt(self.cfg.trade_limit))
		else:
			self.usr_trade_limit = None

	def update_vault_output(self, amt, *, deduct_est_fee=False):
		sp = self.swap_proto_mod
		c = sp.rpc_client(self, amt)

		from ..util import msg
		from ..term import get_char

		def get_trade_limit():
			if type(self.usr_trade_limit) is UniAmt:
				return self.usr_trade_limit
			elif type(self.usr_trade_limit) is float:
				return (
					UniAmt(int(c.data['expected_amount_out']), from_unit='satoshi')
					* self.usr_trade_limit)

		while True:
			self.cfg._util.qmsg(f'Retrieving data from {c.rpc.host}...')
			c.get_quote()
			trade_limit = get_trade_limit()
			self.cfg._util.qmsg('OK')
			msg(c.format_quote(trade_limit, self.usr_trade_limit, deduct_est_fee=deduct_est_fee))
			ch = get_char('Press ‘r’ to refresh quote, any other key to continue: ')
			msg('')
			if ch not in 'Rr':
				break

		self.swap_quote_expiry = c.data['expiry']
		self.update_vault_addr(c.inbound_address)
		self.update_data_output(trade_limit)
		return c.rel_fee_hint
