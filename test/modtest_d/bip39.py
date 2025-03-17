#!/usr/bin/env python3

"""
test.modtest_d.bip39: BIP39 unit test for the MMGen suite
"""

from mmgen.color import blue, orange, purple
from mmgen.bip39 import bip39

from ..include.common import cfg, qmsg, vmsg

class unit_tests:

	vectors = (
		(
			"00000000000000000000000000000000",
			"abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
		), (
			"7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
			"legal winner thank year wave sausage worth useful legal winner thank yellow"
		), (
			"80808080808080808080808080808080",
			"letter advice cage absurd amount doctor acoustic avoid letter advice cage above"
		), (
			"ffffffffffffffffffffffffffffffff",
			"zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong"
		), (
			"000000000000000000000000000000000000000000000000",
			"abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon "
			"abandon abandon abandon abandon abandon agent"
		), (
			"7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
			"legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth "
			"useful legal will"
		), (
			"808080808080808080808080808080808080808080808080",
			"letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor "
			"acoustic avoid letter always"
		), (
			"ffffffffffffffffffffffffffffffffffffffffffffffff",
			"zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when"
		), (
			"0000000000000000000000000000000000000000000000000000000000000000",
			"abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon "
			"abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
		), (
			"7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
			"legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth "
			"useful legal winner thank year wave sausage worth title"
		), (
			"8080808080808080808080808080808080808080808080808080808080808080",
			"letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor "
			"acoustic avoid letter advice cage absurd amount doctor acoustic bless"
		), (
			"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
			"zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote"
		), (
			"9e885d952ad362caeb4efe34a8e91bd2",
			"ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic"
		), (
			"6610b25967cdcca9d59875f5cb50b0ea75433311869e930b",
			"gravity machine north sort system female filter attitude volume fold club stay feature office "
			"ecology stable narrow fog"
		), (
			"68a79eaca2324873eacc50cb9c6eca8cc68ea5d936f98787c60c7ebc74e6ce7c",
			"hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy "
			"gospel tennis maple dilemma loan word shrug inflict delay length"
		), (
			"c0ba5a8e914111210f2bd131f3d5e08d",
			"scheme spot photo card baby mountain device kick cradle pact join borrow"
		), (
			"6d9be1ee6ebd27a258115aad99b7317b9c8d28b6d76431c3",
			"horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle "
			"crack brave"
		), (
			"9f6a2878b2520799a44ef18bc7df394e7061a224d2c33cd015b157d746869863",
			"panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed "
			"nation flash devote level hobby quick inner drive ghost inside"
		), (
			"23db8160a31d3e0dca3688ed941adbf3",
			"cat swing flag economy stadium alone churn speed unique patch report train"
		), (
			"8197a4a47f0425faeaa69deebc05ca29c0a5b5cc76ceacc0",
			"light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain "
			"crack supply proud access"
		), (
			"066dca1a2bb7e8a1db2832148ce9933eea0f3ac9548d793112d9a95c9407efad",
			"all hour make first leader extend hole alien behind guard gospel lava path output census museum "
			"junior mass reopen famous sing advance salt reform"
		), (
			"f30f8c1da665478f49b001d94c5fc452",
			"vessel ladder alter error federal sibling chat ability sun glass valve picture"
		), (
			"c10ec20dc3cd9f652c7fac2f1230f7a3c828389a14392f05",
			"scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk "
			"hair mango congress clump"
		), (
			"f585c11aec520db57dd353c69554b21a89b20fb0650966fa0a9d6f74fd989d8f",
			"void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen "
			"patrol group space point ten exist slush involve unfold"
		)
	)

	def conversion(self, name, ut):

		vmsg('')
		qmsg(blue('Testing BIP39 conversion routines'))

		b = bip39()
		b.check_wordlist(cfg)

		vmsg('')
		qmsg('Checking seed to mnemonic conversion:')
		for v in self.vectors:
			chk = tuple(v[1].split())
			vmsg('    '+v[1])
			res = b.fromhex(v[0])
			assert res == chk, f'mismatch:\nres: {res}\nchk: {chk}'

		vmsg('')
		qmsg('Checking mnemonic to seed conversion:')
		for v in self.vectors:
			chk = v[0]
			vmsg('    '+chk)
			res = b.tohex(v[1].split())
			assert res == chk, f'mismatch:\nres: {res}\nchk: {chk}'

		qmsg('OK')
		vmsg('')

		return True

	def errors(self, name, ut):

		vmsg('')
		qmsg(blue('Testing error handling'))

		good_mn = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong".split()
		bad_len_mn = "zoo zoo zoo".split()
		bad_chksum_mn = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo".split()
		bad_word_mn = "admire zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo".split()
		bad_seed = 'deadbeef'
		good_seed = 'deadbeef' * 4

		b = bip39()
		th = b.tohex
		fh = b.fromhex
		bad_data = (
			('hex',               'AssertionError', 'not a hexadecimal', lambda: fh('xx')),
			('seed len',          'AssertionError', 'invalid seed bit',  lambda: fh(bad_seed)),
			('mnemonic type',     'AssertionError', 'must be list',      lambda: th('string')),
			('arg (tostr=True)',  'AssertionError', "'tostr' must be",   lambda: fh(good_seed, tostr=True)),
			('pad len (fromhex)', 'AssertionError', "invalid 'pad' arg", lambda: fh(good_seed, pad=23)),
			('pad len (tohex)',   'AssertionError', "invalid 'pad' arg", lambda: th(good_mn, pad=23)),
			('word',              'MnemonicError',  "not in the BIP39",  lambda: th(bad_word_mn)),
			('checksum',          'MnemonicError',  "checksum",          lambda: th(bad_chksum_mn)),
			('seed phrase len',   'MnemonicError',  "phrase len",        lambda: th(bad_len_mn)),
		)

		ut.process_bad_data(bad_data)

		qmsg('OK')
		vmsg('')

		return True

	def genseed(self, name, ut):

		vmsg('')
		qmsg(blue('Testing seed generation with password'))
		fn = 'test/ref/98831F3A.bip39'

		vmsg(f'Seed source: {purple(fn)}')
		vmsg('KDF: PBKDF2-SHA512, 2048 rounds')
		with open(fn) as fh:
			mnemonic = fh.read().strip()

		seed_hex = bip39().generate_seed(mnemonic.split()).hex()
		vmsg(f'  Password: {orange("(null)")}\n    {seed_hex}')
		assert seed_hex == '3c30b98d3d9a713cf5a7a42f5dd27b3bf7f4d792d2b9225f6f519a0da978e13c6f36989ef2123b12a96d6ad5a443a95d61022ffaa9fbce8f946da7b67f75d339'

		passwd = 'passw0rd'
		seed_hex = bip39().generate_seed(mnemonic.split(), passwd=passwd).hex()
		vmsg(f'  Password: {orange(passwd)}\n    {seed_hex}')
		assert seed_hex == '7eb773bf60f1a5071f96736b6ddbe5c544a7b7740182a80493e29577e58b7cde011d4e38d26f65dab6c9fdebe5594e523447a1427ffd60746e6d04b4daa42eb1'

		qmsg('OK')
		vmsg('')

		return True
