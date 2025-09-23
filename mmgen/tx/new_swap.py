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

from .new import New
from ..amt import UniAmt

def get_swap_proto_mod(swap_proto_name):
	import importlib
	return importlib.import_module(f'mmgen.swap.proto.{swap_proto_name}')

def init_swap_proto(cfg, asset):
	from ..protocol import init_proto
	return init_proto(
		cfg,
		asset.coin,
		network = cfg._proto.network,
		tokensym = asset.tokensym,
		need_amt = True)

def get_send_proto(cfg):
	try:
		arg = cfg._args.pop(0)
	except:
		cfg._usage()
	return init_swap_proto(cfg, get_swap_proto_mod(cfg.swap_proto).SwapAsset(arg, 'send'))

class NewSwap(New):
	desc = 'swap transaction'
	swap_quote_refresh_timeout = 30

	def __init__(self, *args, **kwargs):
		self.is_swap = True
		self.swap_proto = kwargs['cfg'].swap_proto
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
				await TwAddrData(self.cfg, proto))
			if pa.addr:
				await self.warn_addr_used(proto, pa, desc)
				return ret(proto.coin, proto.network, pa.addr, pa.mmid)

		full_desc = f'{desc} on the {proto.coin} {proto.network} network'
		res = await self.get_autochg_addr(proto, arg, exclude=[], desc=full_desc, all_addrtypes=not arg)
		self.confirm_autoselected_addr(res.twmmid, full_desc)
		return ret(proto.coin, proto.network, res.addr, res.twmmid)

	async def get_chg_output(self, arg, addrfiles):
		chg_output = await self.get_swap_output(self.proto, arg, addrfiles, 'change address')
		self.check_addr_is_wallet_addr(
			chg_output,
			message = 'Change address is not an MMGen wallet address!')
		return chg_output

	async def process_swap_cmdline_args(self, cmd_args, addrfiles):

		class CmdlineArgs: # listed in command-line order
			# send_coin       # required: uppercase coin symbol
			send_amt  = None  # optional: Omit to skip change addr and send value of all inputs minus fees
							  #           to vault
			# chg_spec = None # optional: change address spec, e.g. ‘B’ ‘DEADBEEF:B’ ‘DEADBEEF:B:1’ or
							  #           coin address.  Omit for autoselected change address.  Use of
							  #           non-wallet change address will emit warning and prompt user
							  #           for confirmation
			# recv_coin       # required: uppercase coin symbol
			recv_spec = None  # optional: destination address spec. Same rules as for chg_spec

		def get_arg():
			try:
				return args_in.pop(0)
			except:
				self.cfg._usage()

		async def parse():

			# arg 1: send_coin - already popped and parsed by get_send_proto()

			from ..amt import is_coin_amt
			arg = get_arg()

			# arg 2: amt
			if is_coin_amt(self.proto, arg):
				UniAmt(arg) # throw exception on decimal overflow
				args.send_amt = self.proto.coin_amt(arg)
				arg = get_arg()

			# arg 3: chg_spec (change address spec)
			if args.send_amt and not (self.proto.is_vm or arg in sa.recv): # is change arg
				nonlocal chg_output
				chg_output = await self.get_chg_output(arg, addrfiles)
				arg = get_arg()

			# arg 4: recv_coin
			self.swap_recv_asset_spec = arg # this goes into the transaction file
			self.recv_proto = init_swap_proto(self.cfg, self.recv_asset)

			# arg 5: recv_spec (receive address spec)
			if args_in:
				args.recv_spec = get_arg()

			if args_in: # done parsing, all args consumed
				self.cfg._usage()

		sp = self.swap_proto_mod
		sa = sp.SwapAsset('BTC', 'send')
		args_in = list(cmd_args)
		args = CmdlineArgs()
		chg_output = None

		await parse()

		for a in (self.send_asset, self.recv_asset):
			if a.name not in sa.tested:
				from ..util import msg, ymsg
				from ..term import get_char
				ymsg(f'Warning: {a.direction} asset {a.name} is untested by the MMGen Project')
				get_char('Press any key to continue: ')
				msg('')

		if args.send_amt and not (chg_output or self.proto.is_vm):
			chg_output = await self.get_chg_output(None, addrfiles)

		recv_output = await self.get_swap_output(
			self.recv_proto,
			args.recv_spec,
			addrfiles,
			'destination address')

		self.check_addr_is_wallet_addr(
			recv_output,
			message = (
				'Swap destination address is not an MMGen wallet address!\n'
				'To sign this transaction, autosign or txsign must be invoked'
				' with --allow-non-wallet-swap'))

		sc = self.swap_cfg = self.swap_proto_mod.SwapCfg(self.cfg)

		memo = sp.Memo(
			self.swap_cfg,
			self.recv_proto,
			self.recv_asset,
			recv_output.addr,
			# sc.trade_limit could be a float:
			trade_limit = sc.trade_limit if isinstance(sc.trade_limit, UniAmt) else None)

		# this goes into the transaction file:
		self.swap_recv_addr_mmid = recv_output.mmid

		return (
			[f'vault,{args.send_amt}', f'data:{memo}'] if args.send_amt and self.proto.is_vm else
			[f'vault,{args.send_amt}', chg_output.mmid, f'data:{memo}'] if args.send_amt else
			['vault', f'data:{memo}'])

	def update_vault_addr(self, c, *, addr='inbound_address'):
		vault_idx = self.vault_idx
		assert vault_idx == 0, f'{vault_idx}: vault index is not zero!'
		o = self.outputs[vault_idx]._asdict()
		o['addr'] = getattr(c, addr)
		self.outputs[vault_idx] = self.Output(self.proto, **o)

	async def update_vault_output(self, amt, *, deduct_est_fee=False):
		c = self.swap_proto_mod.rpc_client(self, amt)

		import time
		from ..util import msg
		from ..term import get_char

		def get_trade_limit():
			match self.swap_cfg.trade_limit:
				case UniAmt(): # can’t use positional arg here (not supported by Decimal)
					return self.swap_cfg.trade_limit
				case float(x):
					return UniAmt(int(c.data['expected_amount_out']), from_unit='satoshi') * x

		while True:
			self.cfg._util.qmsg(f'Retrieving data from {c.rpc.host}...')
			c.get_quote(self.swap_cfg)
			self.cfg._util.qmsg('OK')
			self.swap_quote_refresh_time = time.time()
			await self.set_gas(to_addr=c.router if self.is_token else None)
			trade_limit = get_trade_limit()
			msg(await c.format_quote(trade_limit, deduct_est_fee=deduct_est_fee))
			ch = get_char('Press ‘r’ to refresh quote, any other key to continue: ')
			msg('')
			if ch not in 'Rr':
				break

		self.swap_quote_expiry = c.data['expiry']
		self.update_vault_addr(c)
		self.update_data_output(trade_limit)
		self.quote_data = c
		return c.rel_fee_hint
