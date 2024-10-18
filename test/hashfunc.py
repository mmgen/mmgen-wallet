#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
test/hashfunc.py: Test internal implementations of SHA256, SHA512 and Keccak256
"""

import sys

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from mmgen.util import msg, msg_r, die

def green(s):
	return '\033[32;1m' + s + '\033[0m'

class TestHashFunc:

	def test_constants(self):
		msg_r('Testing generated constants: ')
		h = self.t_cls(b'foo')
		if h.H_init != self.H_ref:
			m = 'Generated constants H[] differ from reference value:\nReference:\n{}\nGenerated:\n{}'
			die(3, m.format([hex(n) for n in self.H_ref], [hex(n) for n in h.H_init]))
		if h.K != self.K_ref:
			m = 'Generated constants K[] differ from reference value:\nReference:\n{}\nGenerated:\n{}'
			die(3, m.format([hex(n) for n in self.K_ref], [hex(n) for n in h.K]))
		msg('OK')

	def compare_hashes(self, data, chk=None):
		if chk is None:
			chk = getattr(self.hashlib, self.desc)(data).hexdigest()
		res = self.t_cls(data).hexdigest()
		if res != chk:
			m ='\nHashes do not match!\nReference {d}: {}\nMMGen {d}:     {}'
			die(3, m.format(chk, res, d=self.desc.upper()))

	def test_ref(self):
		for i, data in enumerate(self.vectors):
			msg_r(f'\rTesting reference input data: {i+1:4}/{len(self.vectors)} ')
			self.compare_hashes(data.encode(), chk=self.vectors[data])
		msg('OK')

	def test_random(self, rounds):
		if not self.hashlib:
			return
		for i in range(rounds):
			if i+1 in (1, rounds) or not (i+1) % 10:
				msg_r(f'\rTesting random input data:    {i+1:4}/{rounds} ')
			dlen = int(getrand(4).hex(), 16) >> 18
			self.compare_hashes(getrand(dlen))
		msg('OK')

class TestKeccak(TestHashFunc):
	desc = 'keccak_256'
	vectors = {
		'':                           'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470',
		'x':                          '7521d1cadbcfa91eec65aa16715b94ffc1c9654ba57ea2ef1a2127bca1127a83',
		'xa':                         'ac3f7abb3970ce4fd85fbf46ddd6c87f63e9f91deb38aa155c237c4f81a74259',
		'the':                        '58d5df6c336f348e541c83745572ac73656a0238a55c006a84123e2ace2e7aef',
		'7_chars':                    '537d95bb6222fc8d333177a4310d5549c33aae32c638a01f8ca13f8271d49a89',
		'8charmsg':                   '590d8871128ec3b84d833e2d36cc7e9e1b808b88d44aae653d6938f7e23af707',
		'9_charmsg':                  '625b2ad4132fb699ba33a8cb7c8f1a11f656054cd2fac2156ddd92585c26caac',
		'10_charmsg':                 'b24434a23e05b2f2f1a575df7647d1e6cb96e9c730190f8bc6b282aa18ff96fb',
		'8charmsg' * 8:               'b90078637f407bde1b4e44bef157810b596430a375a4f094ab3fec5258aafe8f',
		'8charmsg' * 7 + '7_chars':   'd566a70e4db4592d2649289024f6deaa1fff7138591e27c1844d172a9d16f2fe',
		'8charmsg' * 7 + '9_charmsg': '149a1620df1447401c968f9593b190dbd519ed663cde7f8606c75d6121e7c980',
		'\x00':                       'bc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a',
		'\x00\x00':                   '54a8c0ab653c15bfb48b47fd011ba2b9617af01cb45cab344acd57c924d56798',
		'\x00'*256:                   'd397b3b043d87fcd6fad1291ff0bfd16401c274896d8c63a923727f077b8e0b5',
		'\x0f':                       '3d725c5ee53025f027da36bea8d3af3b6a3e9d2d1542d47c162631de48e66c1c',
		'\x0f\x0f':                   'c5c1cadbf3ce871e667034a04649cafecd77792491ca7d75207bff6834725e5c',
		'\x0f'*256:                   '634cd5b0c7131441a789340d2ddb9158809bcee04e3389428a99094c586ab9e3',
		'\x0f\x0d':                   'ce69f143c196075c65560b98431330ed46e3bc14daeda0ed1dd7124be89f6c16',
		'\x0e\x0e'*256:               'ccd35755ad4c2bf5dd30b8867e1bb956fceebb6ec95e3684362f1ce160527481',
		'\x00'*511:                   'd28fcca01972cfdea3de8a981db12e426a4ffa25830c25f213e4823c41ab90f3',
		'\x00'*512:                   'd5c44f659751a819616c58c9efe38e80f2b84cf621036da99c019bbe4f1fb647',
		'\x00'*513:                   '8a1810ea3d9e5cc95089994be993c99382f2a7754e8c94ee14888b56ecaa05fd',
		'\x0f'*512:                   'eae2f92f9d3564b346a1937626ca25b9fafb19433a624008c0b6c0eec469aa7c',
		'\x0f'*511:                   'da69b07f366d33f62eb889e7bf05705dae4aaf8902bb8dece86346d33b540e71',
		'\x0f'*513:                   '131640bf7001195b269d652efe137afdc17f19b403b4b5f9aba09a6fb8cbecbe',
		'\x00\x0f'*512:               '330bd984f6c6361b02d7a5de6d4fc60ae8e72c7b791a511d428090b0c9af2313',
		'\x0e\x0f'*511:               '5d17f4e0f63342d3d635bfe57c416a4dddc76ccb5bb6981aacdf3227d095d244',
		'\x0a\x0d'*513:               '187c8fa19c9ac5dedbe4a3078290120eb2f5f7b3b0cb4590cdfbebcfb37bf2b3',
		'\x00\x0f'*1024:              '7aa8a949809ac159cb98fe947ddc40de05be9309aff563130d7d55afb4cc9e11',
		'\x0e\x0f'*1023:              '5c82fa38e3d35efe65a392835be500ba62d0dfc9c0de28950cdeb5bc0d96689d',
		'\x0a\x0d'*1025:              'bc99495fcaf4a987c421ff1cc5854b25786964ab863836b34c82a437a473f4c4',
	}

	def __init__(self):
		from mmgen.contrib.keccak import keccak_256
		from mmgen.util2 import get_keccak
		self.t_cls = keccak_256
		class hashlib:
			keccak_256 = get_keccak()
		self.hashlib = hashlib

	def test_constants(self):
		pass

class TestSha2(TestHashFunc):
	desc = 'sha2'

	def __init__(self):
		from mmgen.sha2 import Sha256, Sha512
		import hashlib
		self.t_cls = {'sha256':Sha256, 'sha512':Sha512}[self.desc]
		self.hashlib = hashlib
		self.vectors = {k:None for k in TestKeccak.vectors}

class TestSha256(TestSha2):
	desc = 'sha256'
	H_ref = (
		0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19)
	K_ref = (
		0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
		0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
		0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
		0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
		0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
		0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
		0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
		0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2)

class TestSha512(TestSha2):
	desc = 'sha512'
	H_ref = (
		0x6a09e667f3bcc908, 0xbb67ae8584caa73b, 0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,
		0x510e527fade682d1, 0x9b05688c2b3e6c1f, 0x1f83d9abfb41bd6b, 0x5be0cd19137e2179)
	K_ref = (
		0x428a2f98d728ae22, 0x7137449123ef65cd, 0xb5c0fbcfec4d3b2f, 0xe9b5dba58189dbbc, 0x3956c25bf348b538,
		0x59f111f1b605d019, 0x923f82a4af194f9b, 0xab1c5ed5da6d8118, 0xd807aa98a3030242, 0x12835b0145706fbe,
		0x243185be4ee4b28c, 0x550c7dc3d5ffb4e2, 0x72be5d74f27b896f, 0x80deb1fe3b1696b1, 0x9bdc06a725c71235,
		0xc19bf174cf692694, 0xe49b69c19ef14ad2, 0xefbe4786384f25e3, 0x0fc19dc68b8cd5b5, 0x240ca1cc77ac9c65,
		0x2de92c6f592b0275, 0x4a7484aa6ea6e483, 0x5cb0a9dcbd41fbd4, 0x76f988da831153b5, 0x983e5152ee66dfab,
		0xa831c66d2db43210, 0xb00327c898fb213f, 0xbf597fc7beef0ee4, 0xc6e00bf33da88fc2, 0xd5a79147930aa725,
		0x06ca6351e003826f, 0x142929670a0e6e70, 0x27b70a8546d22ffc, 0x2e1b21385c26c926, 0x4d2c6dfc5ac42aed,
		0x53380d139d95b3df, 0x650a73548baf63de, 0x766a0abb3c77b2a8, 0x81c2c92e47edaee6, 0x92722c851482353b,
		0xa2bfe8a14cf10364, 0xa81a664bbc423001, 0xc24b8b70d0f89791, 0xc76c51a30654be30, 0xd192e819d6ef5218,
		0xd69906245565a910, 0xf40e35855771202a, 0x106aa07032bbd1b8, 0x19a4c116b8d2d0c8, 0x1e376c085141ab53,
		0x2748774cdf8eeb99, 0x34b0bcb5e19b48a8, 0x391c0cb3c5c95a63, 0x4ed8aa4ae3418acb, 0x5b9cca4f7763e373,
		0x682e6ff3d6b2b8a3, 0x748f82ee5defb2fc, 0x78a5636f43172f60, 0x84c87814a1f0ab72, 0x8cc702081a6439ec,
		0x90befffa23631e28, 0xa4506cebde82bde9, 0xbef9a3f7b2c67915, 0xc67178f2e372532b, 0xca273eceea26619c,
		0xd186b8c721c0c207, 0xeada7dd6cde0eb1e, 0xf57d4f7fee6ed178, 0x06f067aa72176fba, 0x0a637dc5a2c898a6,
		0x113f9804bef90dae, 0x1b710b35131c471b, 0x28db77f523047d84, 0x32caab7b40c72493, 0x3c9ebe0a15c9bebc,
		0x431d67c49c100d4c, 0x4cc5d4becb3e42b6, 0x597f299cfc657e2a, 0x5fcb6fab3ad6faec, 0x6c44198c4a475817)

from test.include.common import getrand, set_globals
from mmgen.cfg import Config
from mmgen.main import launch

def main():

	if len(sys.argv) not in (2, 3):
		die(1, 'Test takes 1 or 2 arguments: test name, plus optional rounds count')

	test = sys.argv[1].capitalize()

	if test not in ('Sha256', 'Sha512', 'Keccak'):
		die(1, "Valid choices for test are 'sha256', 'sha512' or 'keccak'")

	random_rounds = int(sys.argv[2]) if len(sys.argv) == 3 else 500

	set_globals(Config())
	t = globals()['Test'+test]()
	msg(f'Testing internal implementation of {t.desc}')
	t.test_constants()
	t.test_ref()
	t.test_random(random_rounds)

launch(func=main)
