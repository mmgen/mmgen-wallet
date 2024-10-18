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
altcointest.py - Test constants for Bitcoin-derived altcoins
"""

import sys

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from mmgen.cfg import gc, Config
from mmgen.util import msg
from mmgen.altcoin.params import CoinInfo

def test_equal(desc, a, b, *cdata):
	if type(a) is int:
		a = hex(a)
		b = hex(b)
	(network, coin, _, b_desc, verbose) = cdata
	if verbose:
		msg(f'  {desc:20}: {a!r}')
	if a != b:
		raise ValueError(
			f'{desc.capitalize()}s for {coin.upper()} {network} do not match:\n  CoinInfo: {a}\n  {b_desc}: {b}')

class TestCoinInfo(CoinInfo):

	# Sources (see CoinInfo) that are in agreement for these coins
	# No check for segwit, p2sh check skipped if source doesn't support it
	cross_checks = {
		'2GIVE':  ['wn'],
		'42':     ['vg', 'wn'],
		'611':    ['wn'],
		'AC':     ['lb', 'vg'],
		'ACOIN':  ['wn'],
		'ALF':    ['wn'],
		'ANC':    ['vg', 'wn'],
		'APEX':   ['wn'],
		'ARCO':   ['wn'],
		'ARG':    ['pc'],
		'AUR':    ['vg', 'wn'],
		'BCH':    ['wn'],
		'BLK':    ['lb', 'vg', 'wn'],
		'BQC':    ['vg', 'wn'],
		'BSTY':   ['wn'],
		'BTC':    ['lb', 'vg', 'wn'],
		'BTCD':   ['lb', 'vg', 'wn'],
		'BUCKS':  ['wn'],
		'CASH':   ['wn'],
		'CBX':    ['wn'],
		'CCN':    ['lb', 'vg', 'wn'],
		'CDN':    ['lb', 'vg', 'wn'],
		'CHC':    ['wn'],
		'CLAM':   ['lb', 'vg'],
		'CON':    ['vg', 'wn'],
		'CPC':    ['wn'],
		'DASH':   ['lb', 'pc', 'vg', 'wn'],
		'DCR':    ['pc'],
		'DFC':    ['pc'],
		'DGB':    ['lb', 'vg'],
		'DGC':    ['lb', 'vg', 'wn'],
		'DOGE':   ['lb', 'pc', 'vg', 'wn'],
		'DOGED':  ['lb', 'vg', 'wn'],
		'DOPE':   ['lb', 'vg'],
		'DVC':    ['vg', 'wn'],
		'EFL':    ['lb', 'vg', 'wn'],
		'EMC':    ['vg'],
		'EMD':    ['wn'],
		'ESP':    ['wn'],
		'FAI':    ['pc'],
		'FC2':    ['wn'],
		'FIBRE':  ['wn'],
		'FJC':    ['wn'],
		'FLO':    ['wn'],
		'FLT':    ['wn'],
		'FST':    ['wn'],
		'FTC':    ['lb', 'pc', 'vg', 'wn'],
		'GCR':    ['lb', 'vg'],
		'GOOD':   ['wn'],
		'GRC':    ['vg', 'wn'],
		'GUN':    ['vg', 'wn'],
		'HAM':    ['vg', 'wn'],
		'HTML5':  ['wn'],
		'HYP':    ['wn'],
		'ICASH':  ['wn'],
		'INFX':   ['wn'],
		'IPC':    ['wn'],
		'JBS':    ['lb', 'pc', 'vg', 'wn'],
		'JUDGE':  ['wn'],
		'LANA':   ['wn'],
		'LAT':    ['wn'],
		'LDOGE':  ['wn'],
		'LMC':    ['wn'],
		'LTC':    ['lb', 'vg', 'wn'],
		'MARS':   ['wn'],
		'MEC':    ['pc', 'wn'],
		'MINT':   ['wn'],
		'MOBI':   ['wn'],
		'MONA':   ['lb', 'vg'],
		'MOON':   ['wn'],
		'MUE':    ['lb', 'vg'],
		'MXT':    ['wn'],
		'MYR':    ['pc'],
		'MYRIAD': ['vg', 'wn'],
		'MZC':    ['lb', 'pc', 'vg', 'wn'],
		'NEOS':   ['lb', 'vg'],
		'NEVA':   ['wn'],
		'NKA':    ['wn'],
		'NLG':    ['vg', 'wn'],
		'NMC':    ['lb', 'vg'],
		'NVC':    ['lb', 'vg', 'wn'],
		'OK':     ['lb', 'vg'],
		'OMC':    ['vg', 'wn'],
		'ONION':  ['vg', 'wn'],
		'PART':   ['wn'],
		'PINK':   ['vg', 'wn'],
		'PIVX':   ['wn'],
		'PKB':    ['lb', 'vg', 'wn'],
		'PND':    ['lb', 'vg', 'wn'],
		'POT':    ['lb', 'vg', 'wn'],
		'PPC':    ['lb', 'vg', 'wn'],
		'PTC':    ['vg', 'wn'],
		'PXC':    ['wn'],
		'QRK':    ['wn'],
		'RAIN':   ['wn'],
		'RBT':    ['wn'],
		'RBY':    ['lb', 'vg'],
		'RDD':    ['vg', 'wn'],
		'RIC':    ['pc', 'vg', 'wn'],
		'SDC':    ['lb', 'vg'],
		'SIB':    ['wn'],
		'SMLY':   ['wn'],
		'SONG':   ['wn'],
		'SPR':    ['vg', 'wn'],
		'START':  ['lb', 'vg'],
		'SYS':    ['wn'],
		'TAJ':    ['wn'],
		'TIT':    ['wn'],
		'TPC':    ['lb', 'vg'],
		'TRC':    ['wn'],
		'TTC':    ['wn'],
		'TX':     ['wn'],
		'UNO':    ['pc', 'vg', 'wn'],
		'VIA':    ['lb', 'pc', 'vg', 'wn'],
		'VPN':    ['lb', 'vg'],
		'VTC':    ['lb', 'vg', 'wn'],
		'WDC':    ['vg', 'wn'],
		'WISC':   ['wn'],
		'WKC':    ['vg', 'wn'],
		'WSX':    ['wn'],
		'XCN':    ['wn'],
		'XGB':    ['wn'],
		'XPM':    ['lb', 'vg', 'wn'],
		'XST':    ['wn'],
		'XVC':    ['wn'],
		'ZET':    ['wn'],
		'ZOOM':   ['lb', 'vg'],
		'ZRC':    ['lb', 'vg']
	}

	@classmethod
	def verify_leading_symbols(cls, quiet=False, verbose=False):

		for network in ('mainnet', 'testnet'):
			for coin in [e.symbol for e in cls.coin_constants[network]]:
				e = cls.get_entry(coin, network)
				cdata = (network, coin, e, 'Computed value', verbose)

				if not quiet:
					msg(f'{coin} {network}')

				vn_info = e.p2pkh_info
				ret = cls.find_addr_leading_symbol(vn_info[0])
				test_equal('P2PKH leading symbol', vn_info[1], ret, *cdata)

				vn_info = e.p2sh_info
				if vn_info:
					ret = cls.find_addr_leading_symbol(vn_info[0])
					test_equal('P2SH leading symbol', vn_info[1], ret, *cdata)

	@classmethod
	def verify_core_coin_data(cls, cfg, quiet=False, verbose=False):
		from mmgen.protocol import CoinProtocol, init_proto

		for network in ('mainnet', 'testnet'):
			for coin in gc.core_coins:
				e = cls.get_entry(coin, network)
				if e:
					proto = init_proto(cfg, coin, network=network)
					cdata = (network, coin, e, type(proto).__name__, verbose)
					if not quiet:
						msg(f'Verifying {coin.upper()} {network}')

					if coin != 'bch': # TODO
						test_equal('coin name', e.name, proto.name, *cdata)

					if e.trust_level != -1:
						test_equal('Trust level', e.trust_level, CoinProtocol.coins[coin].trust_level, *cdata)

					test_equal(
						'WIF version number',
						e.wif_ver_num,
						int.from_bytes(proto.wif_ver_bytes['std'], 'big'),
						*cdata)

					test_equal(
						'P2PKH version number',
						e.p2pkh_info[0],
						int.from_bytes(proto.addr_fmt_to_ver_bytes['p2pkh'], 'big'),
						*cdata)

					test_equal(
						'P2SH version number',
						e.p2sh_info[0],
						int.from_bytes(proto.addr_fmt_to_ver_bytes['p2sh'], 'big'),
						*cdata)

	# Data is one of the coin_constants lists above.  Normalize ints to hex of correct width, add
	# missing leading letters, set trust level from external_tests.
	# Insert a coin entry from outside source, set version info leading letters to '?' and trust level
	# to 0, then run TestCoinInfo.fix_table(data).  'has_segwit' field is updated manually for now.
	@classmethod
	def fix_table(cls, data):
		import re

		def myhex(n):
			return '0x{:0{}x}'.format(n, 2 if n < 256 else 4)

		def fix_ver_info(e, k):
			e[k] = list(e[k])
			e[k][0] = myhex(e[k][0])
			s1 = cls.find_addr_leading_symbol(int(e[k][0][2:], 16))
			m = f'Fixing leading address letter for coin {e["symbol"]} ({e[k][1]!r} --> {s1})'
			if e[k][1] != '?':
				assert s1 == e[k][1], f'First letters do not match! {m}'
			else:
				msg(m)
				e[k][1] = s1
			e[k] = tuple(e[k])

		old_sym = None
		for sym in sorted([e.symbol for e in data]):
			if sym == old_sym:
				msg(f'{sym!r}: duplicate coin symbol in data!')
				sys.exit(2)
			old_sym = sym

		tt = cls.create_trust_table()

		name_w = max(len(e.name) for e in data)
		fs = '\t({:%s} {:10} {:7} {:17} {:17} {:6} {}),' % (name_w+3)
		for e in data:
			e = e._asdict()
			e['wif_ver_num'] = myhex(e['wif_ver_num'])
			sym, trust = e['symbol'], e['trust_level']

			fix_ver_info(e, 'p2pkh_info')
			if isinstance(e['p2sh_info'], tuple):
				fix_ver_info(e, 'p2sh_info')

			for k in e.keys():
				e[k] = repr(e[k])
				e[k] = re.sub(r"'0x(..)'", r'0x\1', e[k])
				e[k] = re.sub(r"'0x(....)'", r'0x\1', e[k])
				e[k] = re.sub(r' ', r'', e[k]) + ('', ',')[k != 'trust_level']

			if trust != -1:
				if sym in tt:
					src = tt[sym]
					if src != trust:
						msg(f'Updating trust for coin {sym!r}: {trust} -> {src}')
						e['trust_level'] = src
				else:
					if trust != 0:
						msg(f'Downgrading trust for coin {sym!r}: {trust} -> 0')
						e['trust_level'] = 0

				if sym in cls.cross_checks:
					if int(e['trust_level']) == 0 and len(cls.cross_checks[sym]) > 1:
						msg(f'Upgrading trust for coin {sym!r}: {e["trust_level"]} -> 1')
						e['trust_level'] = 1

			print(fs.format(*e.values()))
		msg(f'Processed {len(data)} entries')

	@classmethod
	def find_addr_leading_symbol(cls, ver_num, verbose=False):

		if ver_num == 0:
			return '1'

		def phash2addr(ver_num, pk_hash):
			from mmgen.proto.btc.common import b58chk_encode
			bl = ver_num.bit_length()
			ver_bytes = int.to_bytes(ver_num, bl//8 + bool(bl%8), 'big')
			return b58chk_encode(ver_bytes + pk_hash)

		low = phash2addr(ver_num, b'\x00'*20)
		high = phash2addr(ver_num, b'\xff'*20)

		if verbose:
			print('low address:  ' + low)
			print('high address: ' + high)

		l1, h1 = low[0], high[0]
		return (l1, h1) if l1 != h1 else l1

	@classmethod
	def print_symbols(cls, include_names=False, reverse=False):
		for e in cls.coin_constants['mainnet']:
			if reverse:
				print(f'{e.symbol:6} {e.name}')
			else:
				name_w = max(len(e.name) for e in cls.coin_constants['mainnet'])
				print((f'{e.name:{name_w}} ' if include_names else '') + e.symbol)

	@classmethod
	def create_trust_table(cls):
		tt = {}
		mn = cls.external_tests['mainnet']
		for ext_prog in mn:
			assert len(set(mn[ext_prog])) == len(mn[ext_prog]), f'Duplicate entry in {ext_prog!r}!'
			for coin in mn[ext_prog]:
				if coin in tt:
					tt[coin] += 1
				else:
					tt[coin] = 1
		for k in cls.trust_override:
			tt[k] = cls.trust_override[k]
		return tt

	trust_override = {'BTC':3, 'BCH':3, 'LTC':3, 'DASH':1, 'EMC':2}

	@classmethod
	def get_test_support(cls, coin, addr_type, network, toolname=None, verbose=False):
		"""
		If requested tool supports coin/addr_type/network triplet, return tool name.
		If 'tool' is None, return tool that supports coin/addr_type/network triplet.
		Return None on failure.
		"""
		all_tools = [toolname] if toolname else list(cls.external_tests[network].keys())
		coin = coin.upper()

		for tool in all_tools:
			if coin in cls.external_tests[network][tool]:
				break
		else:
			if verbose:
				m1 = 'Requested tool {t!r} does not support coin {c} on network {n}'
				m2 = 'No test tool found for coin {c} on network {n}'
				msg((m1 if toolname else m2).format(t=tool, c=coin, n=network))
			return None

		if addr_type == 'zcash_z':
			if toolname in (None, 'zcash-mini'):
				return 'zcash-mini'
			else:
				if verbose:
					msg(f"Address type {addr_type!r} supported only by tool 'zcash-mini'")
				return None

		try:
			bl = cls.external_tests_blacklist[addr_type][tool]
		except:
			pass
		else:
			if bl is True or coin in bl:
				if verbose:
					msg(f'Tool {tool!r} blacklisted for coin {coin}, addr_type {addr_type!r}')
				return None

		if toolname: # skip whitelists
			return tool

		if addr_type in ('segwit', 'bech32'):
			st = cls.external_tests_segwit_whitelist
			if addr_type in st and coin in st[addr_type]:
				return tool
			else:
				if verbose:
					m1 = 'Requested tool {t!r} does not support coin {c}, addr_type {a!r}, on network {n}'
					m2 = 'No test tool found supporting coin {c}, addr_type {a!r}, on network {n}'
					msg((m1 if toolname else m2).format(t=tool, c=coin, n=network, a=addr_type))
				return None

		return tool

	external_tests = {
		'mainnet': {
			# List in order of preference.
			# If 'tool' is not specified, the first tool supporting the coin will be selected.
			'pycoin': (
				'DASH', # only compressed
				'BCH',
				'BTC', 'LTC', 'VIA', 'FTC', 'DOGE', 'MEC',
				'JBS', 'MZC', 'RIC', 'DFC', 'FAI', 'ARG', 'ZEC', 'DCR'),
			'keyconv': ( # broken: PIVX
				'BCH', '42', 'AC', 'AIB', 'ANC', 'ARS', 'ATMOS', 'AUR', 'BLK', 'BQC', 'BTC', 'TEST',
				'BTCD', 'CCC', 'CCN', 'CDN', 'CLAM', 'CNC', 'CNOTE', 'CON', 'CRW', 'DEEPONION', 'DGB',
				'DGC', 'DMD', 'DOGED', 'DOGE', 'DOPE', 'DVC', 'EFL', 'EMC', 'EXCL', 'FAIR', 'FLOZ', 'FTC',
				'GAME', 'GAP', 'GCR', 'GRC', 'GRS', 'GUN', 'HAM', 'HODL', 'IXC', 'JBS', 'LBRY', 'LEAF',
				'LTC', 'MMC', 'MONA', 'MUE', 'MYRIAD', 'MZC', 'NEOS', 'NLG', 'NMC', 'NVC', 'NYAN', 'OK',
				'OMC', 'PIGGY', 'PINK', 'PKB', 'PND', 'POT', 'PPC', 'PTC', 'PTS', 'QTUM', 'RBY', 'RDD',
				'RIC', 'SCA', 'SDC', 'SKC', 'SPR', 'START', 'SXC', 'TPC', 'UIS', 'UNO', 'VIA', 'VPN',
				'VTC', 'WDC', 'WKC', 'WUBS', 'XC', 'XPM', 'YAC', 'ZOOM', 'ZRC'),
			'ethkey': ('ETH', 'ETC'),
			'zcash-mini': ('ZEC',),
			'monero-python': ('XMR',),
		},
		'testnet': {
			'pycoin': {
				'DASH':'tDASH', # only compressed
				'BCH':'XTN',
				'BTC':'XTN', 'LTC':'XLT', 'VIA':'TVI', 'FTC':'FTX', 'DOGE':'XDT', 'DCR':'DCRT'
				},
			'ethkey': {},
			'keyconv': {}
		}
	}
	external_tests_segwit_whitelist = {
		# Whitelists apply to the *first* tool in cls.external_tests supporting the given coin/addr_type.
		# They're ignored if specific tool is requested.
		'segwit': ('BTC',), # LTC Segwit broken on pycoin: uses old fmt
		'bech32': ('BTC', 'LTC'),
		'compressed': (
			'BTC', 'LTC', 'VIA', 'FTC', 'DOGE', 'DASH', 'MEC', 'MYR', 'UNO',
			'JBS', 'MZC', 'RIC', 'DFC', 'FAI', 'ARG', 'ZEC', 'DCR', 'ZEC'
		),
	}
	external_tests_blacklist = {
		# Unconditionally block testing of the given coin/addr_type with given tool, or all coins if True
		'legacy': {},
		'segwit': {'keyconv': True},
		'bech32': {'keyconv': True},
	}

if __name__ == '__main__':

	opts_data = {
		'text': {
			'desc': 'Check altcoin data',
			'usage':'[opts]',
			'options': '-q, --quiet    Be quieter\n-v, --verbose  Be more verbose'
		}
	}

	cfg = Config(opts_data=opts_data, need_amt=False)

	msg('Checking CoinInfo WIF/P2PKH/P2SH version numbers and trust levels against protocol.py')
	TestCoinInfo.verify_core_coin_data(cfg, cfg.quiet, cfg.verbose)

	msg('Checking CoinInfo address leading symbols')
	TestCoinInfo.verify_leading_symbols(cfg.quiet, cfg.verbose)
