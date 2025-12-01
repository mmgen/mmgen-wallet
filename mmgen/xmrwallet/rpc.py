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
xmrwallet.rpc: Monero wallet RPC methods for the MMGen Suite
"""

from collections import namedtuple

from ..obj import CoinTxID
from ..color import red, cyan, pink
from ..util import msg, msg_r, gmsg, gmsg_r, die
from ..addr import CoinAddr

from .include import gen_acct_addr_info, XMRWalletAddrSpec
from .file.tx import MoneroMMGenTX as mtx

class MoneroWalletRPC:

	def __init__(self, parent, d):
		self.parent = parent
		self.cfg = parent.cfg
		self.proto = parent.proto
		self.c = parent.c
		self.d = d
		self.fn = parent.get_wallet_fn(d)
		self.new_tx_cls = (
			mtx.NewUnsignedCompat if self.parent.compat_call else
			mtx.NewUnsigned if self.cfg.watch_only else
			mtx.NewSigned)

	def open_wallet(self, desc=None, *, refresh=True):
		add_desc = desc + ' ' if desc else self.parent.add_wallet_desc
		gmsg_r(f'\n  Opening {add_desc}wallet...')
		self.c.call( # returns {}
			'open_wallet',
			filename = self.fn.name,
			password = self.d.wallet_passwd)
		gmsg('done')

		if refresh:
			gmsg_r(f'  Refreshing {add_desc}wallet...')
			ret = self.c.call('refresh')
			gmsg('done')
			if ret['received_money']:
				msg('  Wallet has received funds')

	def close_wallet(self, desc):
		gmsg_r(f'\n  Closing {desc} wallet...')
		self.c.call('close_wallet')
		gmsg_r('done')

	async def stop_wallet(self, desc):
		msg(f'Stopping {self.c.daemon.desc} on port {self.c.daemon.bind_port}')
		gmsg_r(f'\n  Stopping {desc} wallet...')
		await self.c.stop_daemon(quiet=True) # closes wallet
		gmsg_r('done')

	def gen_accts_info(self, accts_data, addrs_data, *, indent='    ', skip_empty_ok=False):
		from .ops import addr_width
		fs = indent + '  {I:<3} {A} {N} {B} {L}'
		yield indent + f'Accounts of wallet {self.fn.name}:'
		yield fs.format(
			I = '',
			A = 'Base Address'.ljust(addr_width),
			N = 'nAddrs',
			B = '  Unlocked Balance',
			L = 'Label')
		for i, e in enumerate(accts_data['subaddress_accounts']):
			if skip_empty_ok and self.cfg.skip_empty_accounts and not e['unlocked_balance']:
				continue
			ca = CoinAddr(self.proto, e['base_address'])
			from .ops import fmt_amt
			yield fs.format(
				I = str(e['account_index']),
				A = ca.hl(0) if self.cfg.full_address else ca.fmt(0, addr_width, color=True),
				N = red(str(len(addrs_data[i]['addresses'])).ljust(6)),
				B = fmt_amt(e['unlocked_balance']),
				L = pink(e['label']))

	def get_wallet_data(self, *, print=True, skip_empty_ok=False):
		accts_data = self.c.call('get_accounts')
		addrs_data = [
			self.c.call('get_address', account_index=i)
				for i in range(len(accts_data['subaddress_accounts']))]
		if print and not self.parent.compat_call:
			msg('\n' + '\n'.join(self.gen_accts_info(
				accts_data,
				addrs_data,
				skip_empty_ok = skip_empty_ok)))
		bals_data = self.c.call('get_balance', all_accounts=True)
		return namedtuple('wallet_data', ['accts_data', 'addrs_data', 'bals_data'])(
			accts_data, addrs_data, bals_data)

	def create_acct(self, label=None):
		msg('\n    Creating new account...')
		ret = self.c.call('create_account', label=label)
		msg('      Index:   {}'.format(pink(str(ret['account_index']))))
		msg('      Address: {}'.format(cyan(ret['address'])))
		return (ret['account_index'], ret['address'])

	def get_last_acct(self, accts_data):
		msg('\n    Getting last account...')
		ret = accts_data['subaddress_accounts'][-1]
		msg('      Index:   {}'.format(pink(str(ret['account_index']))))
		msg('      Address: {}'.format(cyan(ret['base_address'])))
		return (ret['account_index'], ret['base_address'])

	def print_acct_addrs(self, wallet_data, account, silent=False):
		if not (self.parent.compat_call or silent):
			msg('\n      Addresses of account #{} ({}):'.format(
				account,
				wallet_data.accts_data['subaddress_accounts'][account]['label']))
			msg('\n'.join(gen_acct_addr_info(self, wallet_data, account, indent='        ')))
		return wallet_data.addrs_data[account]['addresses']

	def create_new_addr(self, account, label):
		msg_r('\n    Creating new address: ')
		ret = self.c.call('create_address', account_index=account, label=label or '')
		msg(cyan(ret['address']))
		return ret['address']

	def get_last_addr(self, account, wallet_data, *, display=True):
		if display:
			msg('\n    Getting last address:')
		acct_addrs = wallet_data.addrs_data[account]['addresses']
		addr = acct_addrs[-1]['address']
		if display:
			msg('      ' + cyan(addr))
		return (addr, len(acct_addrs) - 1)

	def set_label(self, account, address_idx, label):
		return self.c.call(
			'label_address',
			index = {'major': account, 'minor': address_idx},
			label = label)

	def make_transfer_tx(self, account, addr, amt):
		res = self.c.call(
			'transfer',
			account_index = account,
			destinations = [{
				'amount':  amt.to_unit('atomic'),
				'address': addr}],
			priority = self.cfg.priority or None,
			do_not_relay = True,
			get_tx_hex = True,
			get_tx_metadata = True)
		return self.new_tx_cls(
			cfg            = self.cfg,
			op             = self.parent.name,
			network        = self.proto.network,
			seed_id        = self.parent.kal.al_id.sid,
			source         = XMRWalletAddrSpec(self.parent.source.idx, self.parent.account, None),
			dest           = None,
			dest_address   = addr,
			txid           = res['tx_hash'],
			amount         = self.proto.coin_amt(res['amount'], from_unit='atomic'),
			fee            = self.proto.coin_amt(res['fee'], from_unit='atomic'),
			blob           = res['tx_blob'],
			metadata       = res['tx_metadata'],
			unsigned_txset = res['unsigned_txset'] if self.cfg.watch_only else None)

	def make_sweep_tx(self, account, dest_acct, dest_addr_idx, addr, addrs_data):
		res = self.c.call(
			'sweep_all',
			address = addr,
			account_index = account,
			subaddr_indices = list(range(len(addrs_data[account]['addresses'])))
				if self.parent.name == 'sweep_all' else [],
			priority = self.cfg.priority or None,
			do_not_relay = True,
			get_tx_hex = True,
			get_tx_metadata = True)

		if len(res['tx_hash_list']) > 1:
			die(3, 'More than one TX required.  Cannot perform this sweep')

		return self.new_tx_cls(
			cfg            = self.cfg,
			op             = self.parent.name,
			network        = self.proto.network,
			seed_id        = self.parent.kal.al_id.sid,
			source         = XMRWalletAddrSpec(self.parent.source.idx, self.parent.account, None),
			dest           = XMRWalletAddrSpec(
								(self.parent.dest or self.parent.source).idx,
								dest_acct,
								dest_addr_idx),
			dest_address   = addr,
			txid           = res['tx_hash_list'][0],
			amount         = self.proto.coin_amt(res['amount_list'][0], from_unit='atomic'),
			fee            = self.proto.coin_amt(res['fee_list'][0], from_unit='atomic'),
			blob           = res['tx_blob_list'][0],
			metadata       = res['tx_metadata_list'][0],
			unsigned_txset = res['unsigned_txset'] if self.cfg.watch_only else None)

	def relay_tx(self, tx_hex):
		ret = self.c.call('relay_tx', hex=tx_hex)
		try:
			msg('\n    Relayed {}'.format(CoinTxID(ret['tx_hash']).hl()))
		except:
			msg(f'\n   Server returned: {ret!s}')
