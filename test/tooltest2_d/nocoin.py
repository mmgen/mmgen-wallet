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
test.tooltest2_d.nocoin: Non-coin-specific test vectors for the ‘mmgen-tool’ utility
"""

from decimal import Decimal

from mmgen.cfg import gc

from mmgen.util import is_hex_str

from mmgen.bip39 import is_bip39_mnemonic
from mmgen.baseconv import is_mmgen_mnemonic, is_b58_str
from mmgen.xmrseed import is_xmrseed

from ..modtest_d.baseconv import unit_test as baseconv
from ..modtest_d.bip39 import unit_tests as bip39
from ..modtest_d.xmrseed import unit_tests as xmrseed

from ..include.common import cfg, sample_text
proto = cfg._proto

def is_str(s):
	return isinstance(s, str)

def md5_hash(s):
	from hashlib import md5
	return md5(s.encode()).hexdigest()

def md5_hash_strip(s):
	import re
	s = re.sub('\x1b' + r'\[[;0-9]+?m', '', s) # strip ANSI color sequences
	s = s.replace(NL, '\n')             # fix DOS newlines
	return md5_hash(s.strip())

NL = ('\n', '\r\n')[gc.platform=='win32']

sample_text_hexdump = (
	'000000: 5468 6520 5469 6d65 7320 3033 2f4a 616e{n}' +
	'000010: 2f32 3030 3920 4368 616e 6365 6c6c 6f72{n}' +
	'000020: 206f 6e20 6272 696e 6b20 6f66 2073 6563{n}' +
	'000030: 6f6e 6420 6261 696c 6f75 7420 666f 7220{n}' +
	'000040: 6261 6e6b 73').format(n=NL)

tests = {
	'Mnemonic': {
		'hex2mn': (
			[([a[0]], b) for a, b in baseconv.vectors['mmgen']] +
			[([a, 'fmt=bip39'], b) for a, b in bip39.vectors] +
			[([a, 'fmt=xmrseed'], b) for a, b in xmrseed.vectors]
		),
		'mn2hex': (
			[([b, 'fmt=mmgen'], a[0]) for a, b in baseconv.vectors['mmgen']] +
			[([b, 'fmt=bip39'], a) for a, b in bip39.vectors] +
			[([b, 'fmt=xmrseed'], a) for a, b in xmrseed.vectors]
		),
		'mn_rand128': [
			([], is_mmgen_mnemonic, ['-r0']),
			(['fmt=mmgen'], is_mmgen_mnemonic, ['-r0']),
			(['fmt=bip39'], is_bip39_mnemonic, ['-r0']),
		],
		'mn_rand192': [
			(['fmt=mmgen'], is_mmgen_mnemonic, ['-r0']),
			(['fmt=bip39'], is_bip39_mnemonic, ['-r0']),
		],
		'mn_rand256': [
			(['fmt=mmgen'], is_mmgen_mnemonic, ['-r0']),
			(['fmt=bip39'], is_bip39_mnemonic, ['-r0']),
			(['fmt=xmrseed'], is_xmrseed, ['-r0']),
		],
		'mn_stats': [
			([], is_str),
			(['fmt=mmgen'], is_str),
			(['fmt=bip39'], is_str),
			(['fmt=xmrseed'], is_str),
		],
		'mn_printlist': [
			([], is_str),
			(['fmt=mmgen'], is_str),
			(['fmt=bip39'], is_str),
			(['fmt=xmrseed', 'enum=true'], is_str),
		],
	},
	'Util': {
		'hextob32': [
			(['deadbeef'], 'DPK3PXP'),
			(['deadbeefdeadbeef'], 'N5LN657PK3PXP'),
			(['ffffffffffffffff'], 'P777777777777'),
			(['0000000000000000'], 'A'),
			(['0000000000000000', 'pad=10'], 'AAAAAAAAAA'),
			(['ff', 'pad=10'], 'AAAAAAAAH7'),
		],
		'b32tohex': [
			(['DPK3PXP'], 'deadbeef'),
			(['N5LN657PK3PXP'], 'deadbeefdeadbeef'),
			(['P777777777777'], 'ffffffffffffffff'),
			(['A', 'pad=16'], '0000000000000000'),
			(['AAAAAAAAAA', 'pad=16'], '0000000000000000'),
			(['AAAAAAAAH7', 'pad=2'], 'ff'),
		],
		'hextob6d': [
			(['deadbeef'], '25255 24636 426'),
			(['deadbeefdeadbeef'], '43263 51255 35545 36422 42642'),
			(['ffffffffffffffff'], '46316 33121 21321 15553 55534'),
			(['0000000000000000'], '1'),
			(['0000000000000000', 'pad=10'], '11111 11111'),
			(['ff', 'pad=10'], '11111 12214'),
			(
				['ff'*16],
				'34164 46464 12666 61652 46515 46546 53354 43666 45555 21414'
			), (
				['ff'*24],
				'24611 14114 33323 36422 24655 66552 32465 25661 21541 62342 '
				'61351 63525 45161 35543 13654'
			), (
				['ff'*32],
				'21325 21653 31261 31341 45131 42346 54146 36252 11413 12253 '
				'24246 31114 16424 56513 41632 24121 46151 43214 22425 65134'
			),
		],
		'b6dtohex': [
			(['25255 24636 426'], 'deadbeef'),
			(['43263 51255 35545 36422 42642'], 'deadbeefdeadbeef'),
			(['46316 33121 21321 15553 55534'], 'ffffffffffffffff'),
			(['1', 'pad=16'], '0000000000000000'),
			(['11111 11111', 'pad=16'], '0000000000000000'),
			(['11111 12214', 'pad=2'], 'ff'),
			(['22222 22222'], 'b88733'),
			(['66666 66666'], '039aa3ff'),
			(['6'*50], {
				'len': 34,
				'value':'0260154fc36cbf42778f23ffffffffffff' # 130 bits
				}),
			(['6'*75], {
				'len': 50,
				'value':'03a92ef1c3432e71a7679561bb6817d7ffffffffffffffffff' # 194 bits
				}),
			(['6'*100], {
				'len': 66,
				'value':'05a4653ca673768565b41f775d6947d55cf3813d0fffffffffffffffffffffffff' # 259 bits
				}),
		],
		'hextob58chk': [
			(['deadbeef'], 'eFGDJPketnz'),
			(['deadbeefdeadbeef'], '5CizhNNRPYpBjrbYX'),
			(['ffffffffffffffff'], '5qCHTcgbQwprzjWrb'),
			(['0000000000000000'], '111111114FCKVB'),
			(['00'], '1Wh4bh'),
			(['000000000000000000000000000000000000000000'], '1111111111111111111114oLvT2'),
		],
		'b58chktohex': [
			(['eFGDJPketnz'], 'deadbeef'),
			(['5CizhNNRPYpBjrbYX'], 'deadbeefdeadbeef'),
			(['5qCHTcgbQwprzjWrb'], 'ffffffffffffffff'),
			(['111111114FCKVB'], '0000000000000000'),
			(['3QJmnh'], ''),
			(['1111111111111111111114oLvT2'], '000000000000000000000000000000000000000000'),
		],
		'bytestob58': [
			([b'\xde\xad\xbe\xef'], '6h8cQN'),
			([b'\xde\xad\xbe\xef\xde\xad\xbe\xef'], 'eFGDJURJykA'),
			([b'\xff\xff\xff\xff\xff\xff\xff\xff'], 'jpXCZedGfVQ'),
			([b'\x00\x00\x00\x00\x00\x00\x00\x00'], '1'),
			([b'\x00\x00\x00\x00\x00\x00\x00\x00', 'pad=10'], '1111111111'),
			([b'\xff', 'pad=10'], '111111115Q'),
		],
		'b58tobytes': [
			(['6h8cQN'], b'\xde\xad\xbe\xef'),
			(['eFGDJURJykA'], b'\xde\xad\xbe\xef\xde\xad\xbe\xef'),
			(['jpXCZedGfVQ'], b'\xff\xff\xff\xff\xff\xff\xff\xff'),
			(['1', 'pad=8'], b'\x00\x00\x00\x00\x00\x00\x00\x00'),
			(['1111111111', 'pad=8'], b'\x00\x00\x00\x00\x00\x00\x00\x00'),
			(['111111115Q', 'pad=1'], b'\xff'),
		],
		'hextob58': [
			(['deadbeef'], '6h8cQN'),
			(['deadbeefdeadbeef'], 'eFGDJURJykA'),
			(['ffffffffffffffff'], 'jpXCZedGfVQ'),
			(['0000000000000000'], '1'),
			(['0000000000000000', 'pad=10'], '1111111111'),
			(['ff', 'pad=10'], '111111115Q'),
		],
		'b58tohex': [
			(['6h8cQN'], 'deadbeef'),
			(['eFGDJURJykA'], 'deadbeefdeadbeef'),
			(['jpXCZedGfVQ'], 'ffffffffffffffff'),
			(['1', 'pad=16'], '0000000000000000'),
			(['1111111111', 'pad=16'], '0000000000000000'),
			(['111111115Q', 'pad=2'], 'ff'),
		],
		'bytespec': [
			(['1G'],        str(1024*1024*1024)),
			(['1GB'],       str(1000*1000*1000)),
			(['1234GB'],    str(1234*1000*1000*1000)),
			(['1234G'],     str(1234*1024*1024*1024)),
			(['1234TB'],    str(1234*1000*1000*1000*1000)),
			(['1234T'],     str(1234*1024*1024*1024*1024)),
			(['1234PB'],    str(1234*1000*1000*1000*1000*1000)),
			(['1234P'],     str(1234*1024*1024*1024*1024*1024)),
			(['1234EB'],    str(1234*1000*1000*1000*1000*1000*1000)),
			(['1234E'],     str(1234*1024*1024*1024*1024*1024*1024)),
			(['1.234MB'],   str(1234*1000)),
			(['1.234567M'], str(int(Decimal('1.234567')*1024*1024))),
			(['1234'],      str(1234)),
		],
		'to_bytespec': [
			([str(1024*1024*1024), 'G'],                                '1.00G'),
			([str(1024*1024*1024), 'G', 'fmt=0.0'],                     '1G'),
			([str(1024*1024*1024), 'G', 'fmt=08.5'],                    '01.00000G'),
			([str(1234*1000*1000*1000), 'GB'],                          '1234.00GB'),
			([str(1234*1000*1000*1000), 'GB', 'strip=True'],            '1234.0GB'),
			([str(1234*1000*1000*1000), 'GB', 'add_space=True'],        '1234.00 GB'),
			([str(1234*1024*1024*1024), 'G'],                           '1234.00G',),
			([str(1000*1000*1000*1000*1000), 'PB'],                     '1.00PB'),
			([str(1024*1024*1024*1024*1024), 'P'],                      '1.00P'),
			([str(1024*1024*1024*1024*1024*1024), 'E'],                 '1.00E'),
			([str(int(Decimal('1.234567')*1024*1024)), 'M', 'fmt=0.6'], '1.234567M'),
			(['1234', 'c', 'fmt=0.0', 'print_sym=false'],               '1234'),
		],
		'hash160': [ # TODO: check that hextob58chk(hash160) = pubhex2addr
			(['deadbeef'], 'f04df4c4b30d2b7ac6e1ed2445aeb12a9cb4d2ec'),
			(['000000000000000000000000000000000000000000'], '2db95e704e2d9b0474acf76182f3f985b7064a8a'),
			([''], 'b472a266d0bd89c13706a4132ccfb16f7c3b9fcb'),
			(['ffffffffffffffff'], 'f86221f5a1fca059a865c0b7d374dfa9d5f3aeb4'),
		],
		'hash256': [
			(['deadbeef'], 'e107944e77a688feae4c2d4db5951923812dd0f72026a11168104ee1b248f8a9'),
			(
				['000000000000000000000000000000000000000000'],
				'fd5181fcd097a334ab340569e5edcd09f702fef7994abab01f4b66e86b32ebbe'
			),
			([''], '5df6e0e2761359d30a8275058e299fcc0381534545f55cf43e41983f5d4c9456'),
			(['ffffffffffffffff'], '57b2d2c3455e0f76c61c5237ff04fc9fc0f3fe691e587ea9c951949e1a5e0fed'),
		],
		'hexdump': [
			([sample_text.encode()], sample_text_hexdump),
		],
		'unhexdump': [
			([sample_text_hexdump.encode()], sample_text.encode()),
		],
		'hexlify': [
			([b'foobar'], '666f6f626172'),
		],
		'unhexlify': [
			(['666f6f626172'], 'foobar'),
		],
		'hexreverse': [
			(['deadbeefcafe'], 'fecaefbeadde'),
		],
		'id6': [
			([sample_text.encode()], 'a6d72b'),
		],
		'id8': [
			([sample_text.encode()], '687C09C2'),
		],
		'str2id6': [
			(['74ev zjeq Zw2g DspF RKpE 7H'], '70413d'), # checked
		],
		'randhex': [
			([], {'boolfunc':is_hex_str, 'len':64}, ['-r0']),
			(['nbytes=16'], {'boolfunc':is_hex_str, 'len':32}, ['-r0']),
			(['nbytes=6'], {'boolfunc':is_hex_str, 'len':12}, ['-r0']),
		],
		'randb58': [
			([], {'boolfunc':is_b58_str}, ['-r0']),
			(['nbytes=16'], {'boolfunc':is_b58_str}, ['-r0']),
			(['nbytes=12', 'pad=0'], is_b58_str, ['-r0']),
		],
	},
	'Wallet': {
		'gen_key': [
			(
				['98831F3A:11', 'wallet=test/ref/98831F3A.mmwords'],
				'5JKLcdYbhP6QQ4BXc9HtjfqJ79FFRXP2SZTKUyEuyXJo9QSFUkv'
			), (
				['98831F3A:C:11', 'wallet=test/ref/98831F3A.mmwords'],
				'L2LwXv94XTU2HjCbJPXCFuaHjrjucGipWPWUi1hkM5EykgektyqR'
			), (
				['98831F3A:B:11', 'wallet=test/ref/98831F3A.mmwords'],
				'L2K4Y9MWb5oUfKKZtwdgCm6FLZdUiWJDHjh9BYxpEvtfcXt4iM5g'
			), (
				['98831F3A:S:11', 'wallet=test/ref/98831F3A.mmwords'],
				'KwmkkfC9GghnJhnKoRXRn5KwGCgXrCmDw6Uv83NzE4kJS5axCR9A'
			),
		],
		'get_subseed': [
			(['3s', 'wallet=test/ref/98831F3A.mmwords'], '4018EB17'),
			(['200', 'wallet=test/ref/98831F3A.mmwords'], '2B05AE73'),
		],
		'get_subseed_by_seed_id': [
			(['4018EB17', 'wallet=test/ref/98831F3A.mmwords'], '3S'),
			(['2B05AE73', 'wallet=test/ref/98831F3A.mmwords'], None),
			(['2B05AE73', 'wallet=test/ref/98831F3A.mmwords', 'last_idx=200'], '200L'),
		],
		'list_subseeds': [
			(
				['1-5', 'wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip, '996c047e8543d5dde6f82efc3214a6a1')
			),
		],
		'list_shares': [
			(
				['3', 'wallet=test/ref/98831F3A.bip39'],
				(md5_hash_strip, '84e8bdaebf9c816a8a3bd2ebec5a2e12')
			), (
				['3', 'id_str=default', 'wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip, '84e8bdaebf9c816a8a3bd2ebec5a2e12')
			), (
				['3', 'id_str=foo', 'wallet=test/ref/98831F3A.bip39'],
				(md5_hash_strip, 'd2ac20823c4ea26f15234b5ca8df5d6f')
			), (
				['3', 'id_str=foo', 'master_share=0', 'wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip, 'd2ac20823c4ea26f15234b5ca8df5d6f')
			), (
				['3', 'id_str=foo', 'master_share=5', 'wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip, 'c4feedce40bb5959011ee4a996710832')
			), (
				['3', 'id_str=βαρ', 'master_share=5', 'wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip, 'f7d254798fe2e34b94b5f4ff312998db')
			), (
				['4', 'id_str=βαρ', 'master_share=5', 'wallet=test/ref/98831F3A.bip39'],
				(md5_hash_strip, 'd3e479f55792181372a9f32a569c04e5')
			),
		],
	},
}
