# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.new_swap: new swap transaction class
"""

import sys, time
from collections import namedtuple

from ..addr import CoinAddr
from ..amt import UniAmt
from ..util import msg, ymsg, is_int, die
from ..swap.util import get_swap_asset, init_swap_proto

from .base_swap import BaseSwapMethods
from .new import New

def get_send_proto(cfg):
	try:
		arg = cfg._args.pop(0)
	except:
		cfg._usage()
	return init_swap_proto(cfg, get_swap_asset(cfg, arg, direction='send'))

class NewSwap(BaseSwapMethods, New):
	desc = 'swap transaction'
	swap_quote_refresh_timeout = 30
	memoless_tx_fee = '0.2' # RUNE
	_output = namedtuple('swap_output', ['coin', 'network', 'addr', 'mmid'])

	def __init__(self, *, cfg, is_memoless=False, **kwargs):
		assert is_int(cfg.refnum) or cfg.refnum is None, '--refnum must be an integer'
		self.refnum = int(cfg.refnum) if is_int(cfg.refnum) else None
		self.swap_proto = cfg.swap_proto
		self.is_swap = True
		self.is_memoless = bool(is_memoless)
		self.is_refreq = self.is_memoless and not self.refnum
		super().__init__(cfg=cfg, **kwargs)

	def check_addr_is_wallet_addr(self, output, *, message):
		if not output.mmid:
			self._non_wallet_addr_confirm(message)

	async def get_swap_output(self, proto, arg, addrfiles, desc):
		if arg:
			from ..addrdata import TwAddrData
			pa = self.parse_cmdline_arg(
				proto,
				arg,
				self.get_addrdata_from_files(proto, addrfiles),
				await TwAddrData(self.cfg, proto))
			if pa.addr:
				await self.warn_addr_used(proto, pa, f'{desc} address')
				return self._output(proto.coin, proto.network, pa.addr, pa.mmid)

		full_desc = f'{desc} address on the {proto.coin} {proto.network} network'
		res = await self.get_autochg_addr(proto, arg, exclude=[], desc=full_desc)
		if not (self.refnum and desc == 'destination'):
			self.confirm_autoselected_addr(res.twmmid, res.comment, full_desc)
		return self._output(proto.coin, proto.network, res.addr, res.twmmid)

	async def get_chg_output(self, arg, addrfiles):
		chg_output = await self.get_swap_output(self.proto, arg, addrfiles, 'change')
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

			# arg 2: optional amt
			if is_coin_amt(self.proto, arg):
				UniAmt(arg) # throw exception on decimal overflow
				args.send_amt = self.proto.coin_amt(arg)
				arg = get_arg()

			# arg 3: optional chg_spec (change address spec, requires amt)
			if self.proto.has_chg and args.send_amt and not arg in sa.recv: # is change arg
				nonlocal chg_output
				if not self.cfg.quote:
					chg_output = await self.get_chg_output(arg, addrfiles)
				arg = get_arg()

			# arg 4: recv_coin
			# this goes into the transaction file:
			self.swap_recv_asset_spec = sp.SwapAsset(arg, 'recv').name # used by ‘recv_asset’ property
			self.recv_proto = init_swap_proto(self.cfg, self.recv_asset)

			# arg 5: optional recv_spec (receive address spec)
			if args_in:
				if self.refnum:
					die(1, 'destination address must be omitted with --refnum')
				args.recv_spec = get_arg()

			if args_in: # done parsing, all args consumed
				self.cfg._usage()

		sp = self.swap_proto_mod
		sa = sp.SwapAsset('BTC', 'send')
		args_in = list(cmd_args)
		args = CmdlineArgs()
		chg_output = None

		await parse()

		self.swap_cfg = self.swap_proto_mod.SwapCfg(self.cfg)

		if self.cfg.quote:
			if not args.send_amt:
				die(1, 'With --quote, you must supply a send amount')
			await self.display_quote(
				self.swap_proto_mod.quote_client(self, args.send_amt),
				skip_est_fee = True)
			sys.exit(0)

		self.check_swap_network()

		for asset in (self.send_asset, self.recv_asset):
			if asset.name not in sa.tested:
				from ..term import get_char
				ymsg(f'Warning: {asset.direction} asset {asset.name} is untested by the MMGen Project')
				get_char('Press any key to continue: ')
				msg('')

		if self.proto.has_chg and args.send_amt and not chg_output:
			chg_output = await self.get_chg_output(None, addrfiles)

		if self.refnum:
			pm, resolved_addr = await self.parse_network_memo(
				data = self.swap_proto_rpc.validate_refnum(self.proto.coin, self.refnum),
				recv_asset_spec = self.swap_recv_asset_spec)
			if pm.trade_limit:
				self.swap_cfg.trade_limit = UniAmt(pm.trade_limit, from_unit='satoshi')
			recv_output = self._output(
				self.recv_proto.coin,
				self.recv_proto.network,
				CoinAddr(self.recv_proto, pm.address),
				resolved_addr.twmmid)
		else:
			recv_output = await self.get_swap_output(
				self.recv_proto,
				args.recv_spec,
				addrfiles,
				'destination')

		self.check_addr_is_wallet_addr(
			recv_output,
			message = (
				'Swap destination address is not an MMGen wallet address!\n'
				'To sign this transaction, autosign or txsign must be invoked'
				' with --allow-non-wallet-swap'))

		memo = sp.Memo(
			self.swap_cfg,
			self.recv_proto,
			self.recv_asset,
			recv_output.addr,
			# self.swap_cfg.trade_limit could be a float:
			trade_limit = (
				self.swap_cfg.trade_limit if isinstance(self.swap_cfg.trade_limit, UniAmt)
				else None))

		if self.is_memoless:
			self.memoless_memo = str(memo)

		# this goes into the transaction file:
		self.swap_recv_addr_mmid = recv_output.mmid

		if self.is_refreq:
			if memo.trade_limit:
				ymsg(
					'Warning: setting a trade limit on a memoless transaction is dangerous!\n'
					'On the second pass, both amount and trade limit must remain unchanged!')
			from ..rpc import rpc_init
			if not args.send_amt:
				die(1, 'With --memoless (reference request transaction), you must supply a send amount')
			self.rpc = await rpc_init(self.cfg, self.proto)
			qd = self.swap_proto_mod.quote_client(self, args.send_amt)
			await self.display_quote_loop(qd, deduct_est_fee=False)
			self.reference_memo = self.swap_proto_mod.reference_memo(
				self.send_asset,
				str(self.update_memo(self.memoless_memo, qd.trade_limit)))
			return None

		return tuple((
			[f'vault,{args.send_amt}', chg_output.mmid] if chg_output else
			[f'vault,{args.send_amt}'] if args.send_amt else
			['vault']) + ([] if self.is_memoless else [f'data:{memo}']))

	async def display_quote_loop(self, qd, *, deduct_est_fee=False):
		from ..term import get_char
		while True:
			await self.display_quote(qd, deduct_est_fee=deduct_est_fee)
			ch = get_char('Press ‘r’ to refresh quote, any other key to continue: ')
			msg('')
			if ch not in 'Rr':
				break

	async def display_quote(self, qd, *, deduct_est_fee=False, skip_est_fee=False):
		self.cfg._util.qmsg(f'Retrieving data from {qd.rpc.swap_api.host}...')
		qd.get_quote(self.swap_cfg)
		self.cfg._util.qmsg('OK')
		self.swap_quote_refresh_time = time.time()
		if not skip_est_fee:
			await self.set_gas(to_addr=qd.router if self.is_token else None)
		msg(await qd.format_quote(deduct_est_fee=deduct_est_fee, skip_est_fee=skip_est_fee))

	def update_vault_memoless_amt(self, round_down=False):
		self.update_output_amt(
			self.vault_idx,
			self.swap_proto_mod.memoless_amt(
				self.outputs[self.vault_idx].amt,
				self.refnum,
				round_down = round_down).amt)

	def update_vault_addr(self, qd, *, addr='inbound_address'):
		vault_idx = self.vault_idx
		assert vault_idx == 0, f'{vault_idx}: vault index is not zero!'
		o = self.outputs[vault_idx]._asdict()
		o['addr'] = getattr(qd, addr)
		self.outputs[vault_idx] = self.Output(self.proto, **o)

	def update_memo(self, memo, trade_limit):
		return self.swap_proto_mod.Memo(
			self.swap_cfg,
			self.recv_proto,
			self.recv_asset,
			self.recv_proto.coin_addr(self.swap_proto_mod.Memo.parse(memo).address),
			trade_limit = trade_limit)

	async def update_vault_output(self, amt, *, deduct_est_fee=False):
		qd = self.swap_proto_mod.quote_client(self, amt)
		await self.display_quote_loop(qd, deduct_est_fee=deduct_est_fee)
		self.swap_quote_expiry = qd.data['expiry']
		self.update_vault_addr(qd)
		if self.is_memoless:
			if not self.is_bump:
				self.memoless_memo = str(self.update_memo(self.memoless_memo, qd.trade_limit))
		else:
			self.update_data_output(qd.trade_limit)
		self.quote_data = qd
		return qd.rel_fee_hint
