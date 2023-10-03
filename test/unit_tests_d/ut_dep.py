#!/usr/bin/env python3

"""
test.unit_tests_d.ut_dep: dependency unit tests for the MMGen suite

  Test whether dependencies are installed and functional.
  No data verification is performed.
"""

from subprocess import run,PIPE

from mmgen.cfg import gc
from mmgen.util import msg,ymsg,gmsg
from mmgen.exception import NoLEDSupport

from ..include.common import cfg,vmsg,check_solc_ver

class unit_tests:

	altcoin_deps = ('pysha3','py_ecc','solc','pycryptodomex')
	win_skip = ('pysha3','led')

	def led(self,name,ut):
		from mmgen.led import LEDControl
		try:
			LEDControl(enabled=True)
		except NoLEDSupport:
			ymsg('Warning: no LED support on this platform')
		else:
			gmsg('LED support found!')
		return True

	def pysha3(self,name,ut): # ETH,XMR
		from mmgen.pyversion import python_version
		if python_version >= '3.11':
			ut.skip_msg(f'Python version {python_version}')
		else:
			from sha3 import keccak_256
		return True

	def pycryptodomex(self,name,ut): # ETH,XMR
		from mmgen.pyversion import python_version
		if python_version >= '3.11' or gc.platform == 'win':
			try:
				from mmgen.util import load_cryptodomex
			except Exception as e:
				msg(str(e))
				ymsg('Please install the ‘pycryptodome’ or ‘pycryptodomex’ package on your system')
				return False
		elif gc.platform != 'win':
			ut.skip_msg(f'platform {gc.platform!r}')
		else:
			ut.skip_msg(f'Python version {python_version}')
		return True

	def py_ecc(self,name,ut): # ETH
		from py_ecc.secp256k1 import privtopub
		return True

	def pysocks(self,name,ut):
		import requests,urllib3
		urllib3.disable_warnings()
		session = requests.Session()
		session.trust_env = False
		session.proxies.update({'https':'socks5h://127.243.172.8:20677'})
		try:
			session.get('https://127.188.29.17')
		except Exception as e:
			if type(e).__name__ == 'ConnectionError':
				return True
			else:
				print(e)
		return False

	def secp256k1(self,name,ut):
		from mmgen.proto.secp256k1.secp256k1 import priv2pub
		priv2pub(bytes.fromhex('deadbeef'*8),1)
		return True

	def cryptography(self,name,ut):
		from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
		from cryptography.hazmat.backends import default_backend
		c = Cipher(algorithms.AES(b'deadbeef'*4),modes.CTR(b'deadbeef'*2),backend=default_backend())
		encryptor = c.encryptor()
		enc_data = encryptor.update(b'foo') + encryptor.finalize()
		return True

	def ecdsa(self,name,ut):
		import ecdsa
		pko = ecdsa.SigningKey.from_secret_exponent(12345678901234,curve=ecdsa.SECP256k1)
		pubkey = pko.get_verifying_key().to_string().hex()
		return True

	def ripemd160(self,name,ut):
		import hashlib
		if hashlib.new.__name__ == 'hashlib_new_wrapper':
			ymsg('Warning: RIPEMD160 missing in hashlib, falling back on pure-Python implementation')
		hashlib.new('ripemd160')
		return True

	def gmpy(self,name,ut):
		from gmpy2 import context,set_context,sqrt,cbrt
		# context() parameters are platform-dependent!
		set_context(context(precision=75,round=1)) # OK for gmp 6.1.2 / gmpy 2.1.0
		return True

	def aiohttp(self,name,ut):
		import asyncio,aiohttp
		async def do():
			async with aiohttp.ClientSession(
				headers = { 'Content-Type': 'application/json' },
				connector = aiohttp.TCPConnector(),
			) as session:
				pass
		asyncio.run(do())
		return True

	def pexpect(self,name,ut):
		import pexpect
		from pexpect.popen_spawn import PopenSpawn
		return True

	def scrypt(self,name,ut):
		passwd,salt = b'foo',b'bar'
		N,r,p = 4,8,16
		buflen = 64

		vmsg('Testing builtin scrypt module (hashlib)')
		from hashlib import scrypt # max N == 14!!
		scrypt(password=passwd,salt=salt,n=2**N,r=r,p=p,maxmem=0,dklen=buflen)

		vmsg('Testing standalone scrypt module')
		import scrypt
		scrypt.hash(passwd, salt, N=2**N, r=r, p=p, buflen=buflen)

		return True

	def solc(self,name,ut):
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
				init_proto( cfg, 'eth' ).checksummed_addr('deadbeef'*5),
			]
			cp = run(cmd,stdout=PIPE,stderr=PIPE)
			vmsg(cp.stderr.decode())
			if cp.returncode:
				msg(cp.stderr.decode())
				return False
		return True
