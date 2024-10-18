#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.include: Monero wallet shared data for the MMGen Suite
"""

import re

from ..objmethods import MMGenObject, HiliteStr, InitErrors
from ..color import red, green, pink
from ..addr import CoinAddr, AddrIdx
from ..util import die

def gen_acct_addr_info(self, wallet_data, account, indent=''):
	fs = indent + '{I:<3} {A} {U} {B} {L}'
	addrs_data = wallet_data.addrs_data[account]['addresses']

	for d in addrs_data:
		d['unlocked_balance'] = 0

	if 'per_subaddress' in wallet_data.bals_data:
		for d in wallet_data.bals_data['per_subaddress']:
			if d['account_index'] == account:
				addrs_data[d['address_index']]['unlocked_balance'] = d['unlocked_balance']

	from .ops import addr_width
	yield fs.format(
		I = '',
		A = 'Address'.ljust(addr_width),
		U = 'Used'.ljust(5),
		B = '  Unlocked Balance',
		L = 'Label')

	for addr in addrs_data:
		ca = CoinAddr(self.proto, addr['address'])
		bal = addr['unlocked_balance']
		if self.cfg.skip_empty_addresses and addr['used'] and not bal:
			continue
		from .ops import fmt_amt
		yield fs.format(
			I = addr['address_index'],
			A = ca.hl(0) if self.cfg.full_address else ca.fmt(0, color=True, width=addr_width),
			U = (red('True ') if addr['used'] else green('False')),
			B = fmt_amt(bal),
			L = pink(addr['label']))

class XMRWalletAddrSpec(HiliteStr, InitErrors, MMGenObject):
	color = 'cyan'
	width = 0
	trunc_ok = False
	min_len = 5  # 1:0:0
	max_len = 14 # 9999:9999:9999
	def __new__(cls, arg1, arg2=None, arg3=None):
		if isinstance(arg1, cls):
			return arg1

		try:
			if isinstance(arg1, str):
				me = str.__new__(cls, arg1)
				m = re.fullmatch('({n}):({n}):({n}|None)'.format(n=r'[0-9]{1,4}'), arg1)
				assert m is not None, f'{arg1!r}: invalid XMRWalletAddrSpec'
				for e in m.groups():
					if len(e) != 1 and e[0] == '0':
						die(2, f'{e}: leading zeroes not permitted in XMRWalletAddrSpec element')
				me.wallet = AddrIdx(m[1])
				me.account = int(m[2])
				me.account_address = None if m[3] == 'None' else int(m[3])
			else:
				me = str.__new__(cls, f'{arg1}:{arg2}:{arg3}')
				for arg in [arg1, arg2] + ([] if arg3 is None else [arg3]):
					assert isinstance(arg, int), f'{arg}: XMRWalletAddrSpec component not of type int'
					assert arg is None or arg <= 9999, f'{arg}: XMRWalletAddrSpec component greater than 9999'
				me.wallet = AddrIdx(arg1)
				me.account = arg2
				me.account_address = arg3
			return me
		except Exception as e:
			return cls.init_fail(e, me)
