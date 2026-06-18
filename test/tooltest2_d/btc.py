#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.tooltest2_d.btc: BTC test vectors for the ‘mmgen-tool’ utility
"""

from mmgen.key import is_wif
from mmgen.addr import is_coin_addr

from ..include.common import cfg

from .coin import kafile_opts

proto = cfg._proto

def is_wif_loc(s):
	return is_wif(proto, s)
def is_coin_addr_loc(s):
	return is_coin_addr(proto, s)

wif1 = '5HwzecKMWD82ppJK3qMKpC7ohXXAwcyAN5VgdJ9PLFaAzpBG4sX'
wif2 = 'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm'

privhex7 = '118089d66b4a5853765e94923abdd5de4616c6e5118089d66b4a5853765e9492'

pubhash1 = '118089d66b4a5853765e94923abdd5de4616c6e5'
pubhash2 = '3057f66ddd26fa6ef826b0d5ca067ec3e8f3c178'

addr1 = '1C5VPtgq9xQ6AcTgMAR3J6GDrs72HC4pS1'
addr2 = '1Kz9fVSUMshzPejpzW9D95kScgA3rY6QxF'
addr3 = '3AhjTiWHhVJAi1s5CfKMcLzYps12x3gZhg'
addr4 = 'bc1q6pqnfwwakuuejpm9w52ds342f9d5u36v0qnz7c'
addr5 = '12bYUGXS8SRArZneQDN9YEEYAtEa59Rykm'
addr6 = 'bc1qxptlvmwaymaxa7pxkr2u5pn7c0508stcncv7ms'
addr7 = '3Eevao3DRVXnYym3tdrJDqS3Wc39PQzahn'

redeem_script1 = '0014d04134b9ddb7399907657514d846aa495b4e474c'

pubhex1 = '024281a85c9ce87279e028410b851410d65136304cfbbbeaaa8e2e3931cf4e9727'
pubhex2 = '044281a85c9ce87279e028410b851410d65136304cfbbbeaaa8e2e3931cf4e972757f3254c322eeaa3cb6bf97cc5ecf8d4387b0df2c0b1e6ee18fe3a6977a7d57a'

tests = {
	'Wallet': {
		'gen_addr': [
			(['98831F3A:11', 'wallet=test/ref/98831F3A.mmwords'], addr5),
			(['98831F3A:L:11', 'wallet=test/ref/98831F3A.mmwords'], addr5),
			(
				['98831F3A:C:11', 'wallet=test/ref/98831F3A.mmwords'],
				'1MPsZ7BY9qikqfPxqmrovE8gLDX2rYArZk'
			),
			(['98831F3A:B:11', 'wallet=test/ref/98831F3A.mmwords'], addr6),
			(['98831F3A:S:11', 'wallet=test/ref/98831F3A.mmwords'], addr7),
		],
	},
	'Coin': {
		'addr2pubhash': {
			'btc_mainnet': [
				([addr5], pubhash1),
				([addr6], pubhash2),
			],
		},
		'pubhash2addr': {
			'btc_mainnet': [
				([pubhash1], addr5, None, 'legacy'),
				(['8e34586186551f6320fa3eb2d238a9c61ab8264b'], '37ZBgCBjjz9WSEzp1Zjv8sqdgmNie3Kd5s',
					['--type=segwit'], 'segwit'),
				([pubhash2], addr6, ['--type=bech32'], 'bech32'),
			],
		},
		'addr2scriptpubkey': {
			'btc_mainnet': [
				([addr5], '76a914118089d66b4a5853765e94923abdd5de4616c6e588ac'),
				([addr7], 'a9148e34586186551f6320fa3eb2d238a9c61ab8264b87'),
				([addr6], '00143057f66ddd26fa6ef826b0d5ca067ec3e8f3c178'),
			],
		},
		'scriptpubkey2addr': {
			'btc_mainnet': [
				(['76a914118089d66b4a5853765e94923abdd5de4616c6e588ac'], addr5),
				(['a9148e34586186551f6320fa3eb2d238a9c61ab8264b87'], addr7),
				(['00143057f66ddd26fa6ef826b0d5ca067ec3e8f3c178'], addr6),
			],
		},
		'hex2wif': {
			'btc_mainnet': [
				([privhex7], wif1, None, 'legacy'),
				([privhex7], wif2, ['--type=compressed'], 'compressed'),
				([privhex7], wif2, ['--type=segwit'], 'segwit'),
				([privhex7], wif2, ['--type=bech32'], 'bech32'),
			],
		},
		'privhex2pair': {
			'btc_mainnet': [
				([privhex7], [wif1, addr1], None, 'legacy'),
				([privhex7], [wif2, addr2], ['--type=compressed'], 'compressed'),
				([privhex7], [wif2, addr3], ['--type=segwit'], 'segwit'),
				([privhex7], [wif2, addr4], ['--type=bech32'], 'bech32'),
			],
		},
		'privhex2addr': {
			'btc_mainnet': [
				([privhex7], addr1, None, 'legacy'),
				([privhex7], addr2, ['--type=compressed'], 'compressed'),
				([privhex7], addr3, ['--type=segwit'], 'segwit'),
				([privhex7], addr4, ['--type=bech32'], 'bech32'),
			],
		},
		'privhex2pubhex': {
			'btc_mainnet': [
				([privhex7], pubhex2, None, 'legacy'),
				([privhex7], pubhex1, ['--type=compressed'], 'compressed'),
				([privhex7], pubhex1, ['--type=segwit'], 'segwit'),
				([privhex7], pubhex1, ['--type=bech32'], 'bech32'),
			],
		},
		'pubhex2addr': {
			'btc_mainnet': [
				([pubhex2], addr1, None, 'legacy'),
				([pubhex1], addr2, ['--type=compressed'], 'compressed'),
				([pubhex1], addr3, ['--type=segwit'], 'segwit'),
				([pubhex1], addr4, ['--type=bech32'], 'bech32'),
			],
		},
		'pubhex2redeem_script': {
			'btc_mainnet': [
				([pubhex1], redeem_script1, ['--type=segwit'], 'segwit'),
			],
		},
		'redeem_script2addr': {
			'btc_mainnet': [
				([redeem_script1], addr3, ['--type=segwit'], 'segwit'),
			],
		},
		'randpair': {
			'btc_mainnet': [([], [is_wif_loc, is_coin_addr_loc], ['-r0'])],
			'btc_testnet': [([], [is_wif_loc, is_coin_addr_loc], ['-r0'])],
		},
		'randwif': {
			'btc_mainnet': [([], is_wif_loc, ['-r0'])],
			'btc_testnet': [([], is_wif_loc, ['-r0'])],
		},
		'wif2addr': {
			'btc_mainnet': [
				([wif1], addr1, ['--type=legacy'], 'legacy'),
				([wif2], addr2, ['--type=compressed'], 'compressed'),
				([wif2], addr3, ['--type=segwit'], 'segwit'),
				([wif2], addr4, ['--type=bech32'], 'bech32'),
			],
		},
		'wif2hex': {
			'btc_mainnet': [
				([wif1], privhex7, None, 'legacy'),
				([wif2], privhex7, ['--type=compressed'], 'compressed'),
				([wif2], privhex7, ['--type=segwit'], 'segwit'),
				([wif2], privhex7, ['--type=bech32'], 'bech32'),
			],
		},
		'wif2redeem_script': {
			'btc_mainnet': [
				([wif2], redeem_script1, ['--type=segwit'], 'segwit'),
			],
		},
		'wif2segwit_pair': {
			'btc_mainnet': [
				([wif2], (redeem_script1, addr3), ['--type=segwit'], 'segwit'),
			],
		},
	},
	# TODO: compressed address files are missing
	#		'addrfile_compressed_chk':
	#			'btc': ('A33C 4FDE F515 F5BC', '6C48 AA57 2056 C8C8'),
	#			'ltc': ('3FC0 8F03 C2D6 BD19', '4C0A 49B6 2DD1 1BE0'),
	'File': {
		'addrfile_chksum': {
			'btc_mainnet': [
				(
					['test/ref/98831F3A[1,31-33,500-501,1010-1011].addrs'],
					'6FEF 6FB9 7B13 5D91'
				), (
					['test/ref/98831F3A-S[1,31-33,500-501,1010-1011].addrs'],
					'06C1 9C87 F25C 4EE6'
				), (
					['test/ref/98831F3A-B[1,31-33,500-501,1010-1011].addrs'],
					'9D2A D4B6 5117 F02E'
				),
			],
			'btc_testnet': [
				(
					['test/ref/98831F3A[1,31-33,500-501,1010-1011].testnet.addrs'],
					'424E 4326 CFFE 5F51'
				), (
					['test/ref/98831F3A-S[1,31-33,500-501,1010-1011].testnet.addrs'],
					'072C 8B07 2730 CB7A'
				), (
					['test/ref/98831F3A-B[1,31-33,500-501,1010-1011].testnet.addrs'],
					'0527 9C39 6C1B E39A'
				),
			],
		},
		'keyaddrfile_chksum': {
			'btc_mainnet': [
				(
					['test/ref/98831F3A[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'9F2D D781 1812 8BAD', kafile_opts
				),
			],
			'btc_testnet': [
				(
					['test/ref/98831F3A[1,31-33,500-501,1010-1011].testnet.akeys.mmenc'],
					'88CC 5120 9A91 22C2', kafile_opts
				),
			],
		},
		'passwdfile_chksum': {
			'btc_mainnet': [
				(
					['test/ref/98831F3A-фубар@crypto.org-b58-20[1,4,1100].pws'],
					'DDD9 44B0 CA28 183F', kafile_opts
				),
			],
		},
		'txview': {
			'btc_mainnet': [(['test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'], None),],
			'btc_testnet': [(['test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx'], None),],
		},
	},
}
