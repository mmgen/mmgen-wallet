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
test.tooltest2_d.zec: ZEC test vectors for the ‘mmgen-tool’ utility
"""

from .coin import kafile_opts, privhex1, privhex2, privhex3, privhex4, privhex5, privhex6

addr1 = 'zceQDpyNwek7dKqF5ZuFGj7YrNVxh7X1aPkrVxDLVxWSiZAFDEuy5C7XNV8VhyZ3ghTPQ61xjCGiyLT3wqpiN1Yi6mdmaCq'
addr2 = 'zcY1hqJ3P5ifjnWk1BcXpjrLG5XeJZUSPCiiVTF9LXrejxBzAsFWcNyr6PudwQHm8DnQpD8HEaM3dh8sB6cf91ciAa53YQ1'
addr4 = 'zcck12KgVY34LJwVEDLN8sXhL787zmjKqPsP1uBYRHs75bL9sQu4P7wcc5ZJTjKsL376zaSpsYqGxK94JbiYcNoH8DkeGbN'
addr5 = 'zcJ9hEezG1Jeye5dciqiMDh6SXtYbUsircGmpVyhHWyzyxDVRRDs5Q8M7hG3c7nDcvd5Pw4u4wV9RAQmq5RCBZq5wVyMQV8'
addr6 = 'zchFELwBxqsAubsLQ8yZgPCDDGukjXJssgCbiTPwFNmFwn9haLnDatzfhLdZzJT4PcU4o2yr92B52UFirUzEdF6ZYM2gBkM'

pubhex1 = 'e6a4edbff547f21bcc2a825b6cf70f06e266a452d2da9d6dc5c1da3d99d7e996f488704dcdfe8d92cafe47772b3f692a98d59de1e99e00ff815f64ae59910f0c'

tests = {
	'Coin': {
		'privhex2addr': {
			'zec_mainnet': [
				([privhex1], addr1, ['--type=zcash_z'], 'zcash_z'),
				([privhex2], addr2, ['--type=zcash_z'], 'zcash_z'),
				([privhex3], addr2, ['--type=zcash_z'], 'zcash_z'),
				([privhex4], addr4, ['--type=zcash_z'], 'zcash_z'),
				([privhex5], addr5, ['--type=zcash_z'], 'zcash_z'),
				([privhex6], addr6, ['--type=zcash_z'], 'zcash_z'),
			],
		},
		'privhex2pubhex': {
			'zec_mainnet': [
				([privhex1], pubhex1, ['--type=zcash_z'], 'zcash_z'),
			],
		},
		'pubhex2addr': {
			'zec_mainnet': [
				([pubhex1], addr1, ['--type=zcash_z'], 'zcash_z'),
			],
		},
		'wif2addr': {
			'zec_mainnet': [
				(
					['SKxny894fJe2rmZjeuoE6GVfNkWoXfPp8337VrLLNWG56FjqVUYR'],
					addr1, ['--type=zcash_z'], 'zcash_z'
				), (
					['SKxv1peuQvMT4TvqPLqKy1px3oqLm98Evi948VU8N8VKcf7C2umc'],
					addr2, ['--type=zcash_z'], 'zcash_z'
				), (
					['SKxny894fJe2rmZjeuoE6GVfNkWoXfPp8337VrLLNWG56kQw4qjm'],
					addr4, ['--type=zcash_z'], 'zcash_z'
				), (
					['SKxv1peuQvMT4TvqPLqKy1px3oqLm98Evi948VU8N8VKcBwrLwiu'],
					addr5, ['--type=zcash_z'], 'zcash_z'
				), (
					['SKxuS56e99jpCeD9mMQ5o63zoGPakNdM9HCvt4Vt2cypvRjCdvGJ'],
					addr6, ['--type=zcash_z'], 'zcash_z'
				),
			],
		},
	},
	'File': {
		'addrfile_chksum': {
			'zec_mainnet': [
				(['test/ref/zcash/98831F3A-ZEC-C[1,31-33,500-501,1010-1011].addrs'], '903E 7225 DD86 6E01'),
				(
					['test/ref/zcash/98831F3A-ZEC-Z[1,31-33,500-501,1010-1011].addrs'],
					'9C7A 72DC 3D4A B3AF', ['--type=zcash_z'], 'zcash_z'
				),
			],
		},
		'keyaddrfile_chksum': {
			'zec_mainnet': [
				(
					['test/ref/zcash/98831F3A-ZEC-C[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'F05A 5A5C 0C8E 2617', kafile_opts
				), (
					['test/ref/zcash/98831F3A-ZEC-Z[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'6B87 9B2D 0D8D 8D1E', kafile_opts + ['--type=zcash_z'], 'zcash_z'
				),
			],
		},
	},
}
