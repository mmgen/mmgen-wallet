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
test.tooltest2_d.xmr: XMR test vectors for the ‘mmgen-tool’ utility
"""

from .coin import kafile_opts, privhex1, privhex2, privhex3, privhex4, privhex5, privhex6

pubhex1 = '1ed49357e217e79dab3c5503822f2bdb561e302e24476ee6ff33242c7551d4e78944790c0cfa9998c2f196061be89b2b8387f9d397db20ea8e049899cdc947d1'

addr1 = '42nsXK8WbVGTNayQ6Kjw5UdgqbQY5KCCufdxdCgF7NgTfjC69Mna7DJSYyie77hZTQ8H92G2HwgFhgEUYnDzrnLnQdF28r3'
addr2 = '49voQEbjouUQSDikRWKUt1PGbS47TBde4hiGyftN46CvTDd8LXCaimjHRGtofCJwY5Ed5QhYwc12P15AH5w7SxUAMCz1nr1'
addr3 = '45Ee1yJSjXBKuf8aaihf6KgSRGtMBN6NNDtkd9fLJzHiK4ar4NyNxDk6afc7MTRoruAsg6J6792tCJazHqs1sjbv7LuEsLx'
addr4 = '43aZyywWW4MYt2Az32XioQYirxyT8xeRBP84EBNA7Cra5SqQNmca6iD9pM487pcR9JAEiKrnw2QwvA5uWiFNokEzLJ5coZ9'
addr5 = '4AeR1owefiJGbrAdSKCbVL73ME4FGv2cpczjV2peqqkxagm5D4gBqAHJta6NpbtxyuRe3ywaTj6QCHD59savvPW69wfW9my'
addr6 = '41i7saPWA53EoHenmJVRt34dubPxsXwoWMnw8AdMyx4mTD1svf7qYzcVjxxRfteLNdYrAxWUMmiPegFW9EfoNgXx7vDMExv'

tests = {
	'Coin': {
		'privhex2addr': {
			'xmr_mainnet': [
				([privhex1], addr1),
				([privhex2], addr2),
				([privhex3], addr3),
				([privhex4], addr4),
				([privhex5], addr5),
				([privhex6], addr6),
			],
		},
		'privhex2pubhex': {
			'xmr_mainnet': [
				([privhex1], pubhex1),
			],
		},
		'pubhex2addr': {
			'xmr_mainnet': [
				([pubhex1], addr1),
			],
		},
		'wif2addr': {
			'xmr_mainnet': [
				([privhex1], addr1),
				(['1c95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f'], addr2),
				(['2c94988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f'], addr3),
				(['1d95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0e'], addr4),
				([privhex5], addr5),
				(['e8164dda6d42bd1e261a3406b2038dcbddadbeefdeadbeefdeadbeefdeadbe0f'], addr6),
			],
		},
	},
	'File': {
		'addrfile_chksum': {
			'xmr_mainnet': [
				(['test/ref/monero/98831F3A-XMR-M[1,31-33,500-501,1010-1011].addrs'], '4369 0253 AC2C 0E38'),],
		},
		'viewkeyaddrfile_chksum': {
			'xmr_mainnet': [
				(['test/ref/monero/98831F3A-XMR-M[1-3].vkeys'], '40C9 0E61 B743 229C'),
			],
		},
		'keyaddrfile_chksum': {
			'xmr_mainnet': [
				(
					['test/ref/monero/98831F3A-XMR-M[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'E0D7 9612 3D67 404A', kafile_opts
				),
			],
		},
	},
}
