#!/usr/bin/env python3

"""
test.modtest_d.ut_xmrseed: Monero mnemonic unit test for the MMGen suite
"""

altcoin_dep = True

from mmgen.util import ymsg
from mmgen.xmrseed import xmrseed
from ..include.common import cfg, vmsg

class unit_tests:

	vectors = ( # private keys are reduced
		(
			'148d78d2aba7dbca5cd8f6abcfb0b3c009ffbdbea1ff373d50ed94d78286640e', # Monero repo
			'velvet lymph giddy number token physics poetry unquoted nibs useful sabotage limits benches ' +
			'lifestyle eden nitrogen anvil fewest avoid batch vials washing fences goat unquoted',
		), (
			'e8164dda6d42bd1e261a3406b2038dcbddadbeefdeadbeefdeadbeefdeadbe0f',
			'viewpoint donuts ardent template unveil agile meant unafraid urgent athlete rustled mime azure ' +
			'jaded hawk baby jagged haystack baby jagged haystack ramped oncoming point template'
		), (
			'6900dea9753f5c7ced87b53bdcfb109a8417bca6a2797a708194157b227fb60b',
			'criminal bamboo scamper gnaw limits womanly wrong tuition birth mundane donuts square cohesive ' +
			'dolphin titans narrate fuel saved wrap aloof magically mirror together update wrap'
		), (
			'0000000000000000000000000000000000000000000000000000000000000001',
			'abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey abbey ' +
			'abbey abbey abbey abbey abbey bamboo jaws jerseys abbey'
		), (
			'1c95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f',
			'powder directed sayings enmity bacon vapidly entrance bumper noodles iguana sleepless nasty flying ' +
			'soil software foamy solved soggy foamy solved soggy jury yawning ankle solved'
		), (
			'2c94988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f',
			'memoir apart olive enmity bacon vapidly entrance bumper noodles iguana sleepless nasty flying soil ' +
			'software foamy solved soggy foamy solved soggy jury yawning ankle foamy'
		), (
			'4bb0288c9673b69fa68c2174851884abbaaedce6af48a03bbfd25e8cd0364102',
			'rated bicycle pheasants dejected pouch fizzle shipped rash citadel queen avatar sample muzzle mews ' +
			'jagged origin yeti dunes obtains godfather unbending pastry vortex washing citadel'
		), (
			'4bb0288c9673b69fa68c2174851884abbaaedce6af48a03bbfd25e8cd0364100',
			'rated bicycle pheasants dejected pouch fizzle shipped rash citadel queen avatar sample muzzle mews ' +
			'jagged origin yeti dunes obtains godfather unbending kangaroo auctions audio citadel'
		), (
			'1d95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0e',
			'pram distance scamper enmity bacon vapidly entrance bumper noodles iguana sleepless nasty flying ' +
			'soil software foamy solved soggy foamy solved soggy hashing mullet onboard solved'
		), (
			'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0f',
			'foamy solved soggy foamy solved soggy foamy solved soggy foamy solved soggy foamy solved soggy ' +
			'foamy solved soggy foamy solved soggy jury yawning ankle soggy'
		),
	)

	@property
	def _use_monero_python(self):
		if not hasattr(self, '_use_monero_python_'):
			try:
				from monero.wordlists.english import English
				self.wl = English()
			except ImportError:
				self._use_monero_python_ = False
				ymsg('Warning: unable to import monero-python, skipping external library checks')
			else:
				self._use_monero_python_ = True
		return self._use_monero_python_

	def wordlist(self, name, ut, desc='Monero wordlist'):
		xmrseed().check_wordlist(cfg)
		return True

	def fromhex(self, name, ut, desc='fromhex() method'):
		b = xmrseed()
		vmsg('Checking seed to mnemonic conversion:')
		for privhex, chk in self.vectors:
			vmsg(f'    {chk}')
			chk = tuple(chk.split())
			res = b.fromhex(privhex)
			if self._use_monero_python:
				mp_chk = tuple(self.wl.encode(privhex).split())
				assert res == mp_chk, f'check failed:\nres: {res}\nchk: {chk}'
			assert res == chk, f'check failed:\nres: {res}\nchk: {chk}'
		return True

	def tohex(self, name, ut, desc='tohex() method'):
		b = xmrseed()
		vmsg('Checking mnemonic to seed conversion:')
		for chk, words in self.vectors:
			vmsg(f'    {chk}')
			res = b.tohex(words.split())
			if self._use_monero_python:
				mp_chk = self.wl.decode(words)
				assert res == mp_chk, f'check failed:\nres: {res}\nchk: {mp_chk}'
			assert res == chk, f'check failed:\nres: {res}\nchk: {chk}'
		return True

	def errors(self, name, ut, desc='error handling'):

		bad_chksum_mn = ('abbey ' * 21 + 'bamboo jaws jerseys donuts').split()
		bad_word_mn = "admire zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo".split()
		bad_seed = 'deadbeef'
		good_mn = self.vectors[0][1].split()
		good_hex = self.vectors[0][0]
		bad_len_mn = good_mn[:22]

		b = xmrseed()
		th = b.tohex
		fh = b.fromhex

		hse = 'HexadecimalStringError'
		sle = 'SeedLengthError'
		ase = 'AssertionError'
		mne = 'MnemonicError'

		ut.process_bad_data((
			('hex',               hse, 'not a hexadecimal',     lambda: fh('xx')),
			('seed len',          sle, 'invalid seed byte len', lambda: fh(bad_seed)),
			('mnemonic type',     ase, 'must be list',          lambda: th('string')),
			('pad arg (fromhex)', ase, "invalid 'pad' arg",     lambda: fh(good_hex, pad=23)),
			('pad arg (tohex)',   ase, "invalid 'pad' arg",     lambda: th(good_mn, pad=23)),
			('word',              mne, "not in Monero",         lambda: th(bad_word_mn)),
			('checksum',          mne, "checksum",              lambda: th(bad_chksum_mn)),
			('seed phrase len',   mne, "phrase len",            lambda: th(bad_len_mn)),
		))

		return True
