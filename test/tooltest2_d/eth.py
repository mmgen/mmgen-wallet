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
test.tooltest2_d.eth: ETH test vectors for the ‘mmgen-tool’ utility
"""

from .coin import kafile_opts, privhex1, privhex2, privhex3, privhex4, privhex5, privhex6

addr1 = '7e5f4552091a69125d5dfcb7b8c2659029395bdf'
addr2 = 'b92702b3eefb3c2049aeb845b0335b283e11e9c6'
addr3 = 'ad30adc7451c1dace34c5d1f328f8a74a4947534'
addr4 = '5044a80bd3eff58302e638018534bbda8896c48a'
addr5 = '8b10f977e27611516f186980d8161b25f8adca5e'
addr6 = 'c96aaa54e2d44c299564da76e1cd3184a2386b8d'

pubhex1 = '0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8' # Bitcoin-style '04'-prefixed pubkey
pubhex2 = '9166c289b9f905e55f9e3df9f69d7f356b4a22095f894f4715714aa4b56606aff181eb966be4acb5cff9e16b66d809be94e214f06c93fd091099af98499255e7'   # raw pubkey

tests = {
	'Coin': {
		'eth_checksummed_addr': {
			'eth_mainnet': [
				(['00a329c0648769a73afac7f9381e08fb43dbea72'], '00a329c0648769A73afAc7F9381E08FB43dBEA72'),
				(['deadbeef'*5], 'DeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF'),
				(['ffffffff'*5], 'FFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF'),
				(['0'*39 + '1'], '0'*39 + '1'),
			],
		},
		'privhex2addr': {
			'eth_mainnet': [
				([privhex1], addr1),
				([privhex2], addr2),
				([privhex3], addr3),
				([privhex4], addr4),
				([privhex5], addr5),
				([privhex6], addr6),
			],
		},
		'privhex2pubhex': {
			'eth_mainnet': [
				([privhex1], pubhex1),
			],
		},
		'pubhex2addr': {
			'eth_mainnet': [
				([pubhex1], addr1),
				([pubhex2], addr2),
			],
		},
		'wif2addr': {
			'eth_mainnet': [
				([privhex1], addr1),
				(['000000000000000000000000000000014551231950b75fc4402da1732fc9bebe'], addr2),
				([privhex3], addr3),
				([privhex4], addr4),
				(['000000000000000000000000000000014551231950b75fc4402da1732fc9bdce'], addr5),
				([privhex6], addr6),
			],
		},
	},
	'File': {
		'addrfile_chksum': {
			'eth_mainnet': [
				(['test/ref/ethereum/98831F3A-ETH[1,31-33,500-501,1010-1011].addrs'],'E554 076E 7AF6 66A3'),],
		},
		'keyaddrfile_chksum': {
			'eth_mainnet': [
				(
					['test/ref/ethereum/98831F3A-ETH[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'E400 70D9 0AE3 C7C2', kafile_opts
				),
			],
		},
		'txview': {
			'eth_mainnet': [(['test/ref/ethereum/88FEFD-ETH[23.45495,40000].rawtx'], None),],
			'eth_testnet': [([
				'test/ref/ethereum/76CF8C-ETH[99.99895,50000].regtest.rawtx',
				'test/ref/ethereum/76CF8C-ETH[99.99895,50000].regtest.sigtx'
				], None),],
			'mm1_mainnet': [(['test/ref/ethereum/5881D2-MM1[1.23456,50000].rawtx'], None),],
			'mm1_testnet': [(['test/ref/ethereum/6BDB25-MM1[1.23456,50000].testnet.rawtx'], None),],
		},
	},
}
