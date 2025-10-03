#!/usr/bin/env python3

"""
test.modtest_d.dep: dependency unit tests for the MMGen suite

  Test whether dependencies are installed and functional.
  No data verification is performed.
"""

import sys

from subprocess import run, PIPE

from mmgen.util import msg, rmsg, ymsg, gmsg
from mmgen.exception import NoLEDSupport

from ..include.common import cfg, vmsg, check_solc_ver

class unit_tests:

	altcoin_deps = ('solc', 'keccak', 'pysocks', 'semantic_version')
	win_skip = ('led', 'semantic_version')

	def secp256k1(self, name, ut):
		try:
			from mmgen.proto.secp256k1.secp256k1 import pubkey_gen
			pubkey_gen(bytes.fromhex('deadbeef'*8), 1)
			return True
		except ModuleNotFoundError as e:
			ymsg(f'{type(e).__name__}: {e}')
			msg('Installing secp256k1 module locally...')
			run(['python3', './setup.py', 'build_ext', '--inplace'], stdout=PIPE, stderr=PIPE, check=True)
			ymsg('The module has been installed.  Try re-running the test')
			sys.exit(1)
		return False

	def led(self, name, ut):
		from mmgen.led import LEDControl
		try:
			LEDControl(enabled=True)
		except NoLEDSupport:
			ymsg('Warning: no LED support on this platform')
		else:
			gmsg('LED support found!')
		return True

	def keccak(self, name, ut): # used by ETH, ETC, XMR
		from mmgen.util2 import get_keccak, get_hashlib_keccak
		if not (keccak_256 := get_hashlib_keccak()):
			ymsg('Hashlib keccak_256() not available, falling back on cryptodome(x) package')
			try:
				keccak_256 = get_keccak()
			except Exception as e:
				rmsg(str(e))
				return False

		chk = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
		assert keccak_256(b'').hexdigest() == chk, 'hash mismatch!'
		return True

	def pysocks(self, name, ut):
		import requests, urllib3
		urllib3.disable_warnings()
		session = requests.Session()
		session.trust_env = False
		session.proxies.update({'https':'socks5h://127.243.172.8:20677'})
		try:
			session.get('https://127.188.29.17', timeout=1)
		except Exception as e:
			if type(e).__name__ in ('ConnectionError', 'ConnectTimeout'):
				return True
			else:
				ymsg('{}: {}'.format(type(e).__name__, e))
				msg('Is the ‘pysocks’ package installed?')
		return False

	def cryptography(self, name, ut):
		from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
		from cryptography.hazmat.backends import default_backend
		c = Cipher(algorithms.AES(b'deadbeef'*4), modes.CTR(b'deadbeef'*2), backend=default_backend())
		encryptor = c.encryptor()
		encryptor.update(b'foo') + encryptor.finalize()
		return True

	def ecdsa(self, name, ut):
		import ecdsa
		pko = ecdsa.SigningKey.from_secret_exponent(12345678901234, curve=ecdsa.SECP256k1)
		pko.get_verifying_key().to_string().hex()
		return True

	def ripemd160(self, name, ut):
		import hashlib
		if hashlib.new.__name__ == 'hashlib_new_wrapper':
			ymsg('Warning: RIPEMD160 missing in hashlib, falling back on pure-Python implementation')
		hashlib.new('ripemd160')
		return True

	def gmpy(self, name, ut):
		from gmpy2 import context, set_context, sqrt, cbrt
		# context() parameters are platform-dependent!
		set_context(context(precision=75, round=1)) # OK for gmp 6.1.2 / gmpy 2.1.0
		return True

	def aiohttp(self, name, ut):
		import asyncio, aiohttp
		async def do():
			async with aiohttp.ClientSession(
				headers = {'Content-Type': 'application/json'},
				connector = aiohttp.TCPConnector(),
			):
				pass
		asyncio.run(do())
		return True

	def pexpect(self, name, ut):
		import pexpect
		from pexpect.popen_spawn import PopenSpawn
		return True

	def scrypt(self, name, ut):
		passwd, salt = b'foo', b'bar'
		N, r, p = 4, 8, 16
		buflen = 64

		vmsg('Testing builtin scrypt module (hashlib)')
		from hashlib import scrypt # max N == 14!!
		scrypt(password=passwd, salt=salt, n=2**N, r=r, p=p, maxmem=0, dklen=buflen)

		vmsg('Testing standalone scrypt module')
		import scrypt
		scrypt.hash(passwd, salt, N=2**N, r=r, p=p, buflen=buflen)

		return True

	def semantic_version(self, name, ut):
		from semantic_version import Version, NpmSpec
		return True

	def solc(self, name, ut):
		from mmgen.protocol import init_proto
		solc_ok = check_solc_ver()
		if solc_ok:
			cmd = [
				'python3',
				'scripts/create-token.py',
				'--coin=ETH',
				'--name=My Fake Token',
				'--symbol=FAKE',
				'--supply=100000000000000000000000000',
				'--decimals=18',
				'--stdout',
				init_proto(cfg, 'eth').checksummed_addr('deadbeef'*5),
			]
			cp = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
			vmsg(cp.stderr)
			if cp.returncode:
				msg(cp.stderr)
				return False
		return True
