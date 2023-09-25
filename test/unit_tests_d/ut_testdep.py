#!/usr/bin/env python3

"""
test.unit_tests_d.ut_testdep: test dependency unit tests for the MMGen suite
"""

from mmgen.common import *
from subprocess import run,PIPE

sec = 'deadbeef' * 8

class unit_tests:

	altcoin_deps = ('pycoin','monero_python','keyconv','zcash_mini','ethkey','ssh_socks_proxy')
	win_skip = ('losetup','zcash_mini')

	def core_repo(self,name,ut):
		crr = os.getenv('CORE_REPO_ROOT')
		if not crr or not os.path.exists(os.path.join(crr,'src/test/data/tx_valid.json')):
			ymsg('CORE_REPO_ROOT not set, or does not point to Bitcoin Core repository')
			return False
		return True

	def losetup(self,name,ut):
		os.stat('/dev/loop0')
		run(['/sbin/losetup','-f'],check=True,stdout=PIPE)
		return True

	def pycoin(self,name,ut):
		from pycoin.networks.registry import network_for_netcode as nfnc
		network = nfnc('btc')
		key = network.keys.private(secret_exponent=int(sec,16),is_compressed=True)
		hash160_c = key.hash160(is_compressed=True)
		addr = network.address.for_p2pkh_wit(hash160_c)
		return True

	def monero_python(self,name,ut):
		from monero.seed import Seed
		res = Seed('deadbeef' * 8).public_address()
		return True

	def keyconv(self,name,ut):
		res = run(['keyconv','-G','ltc'],stdout=PIPE,stderr=PIPE,check=True)
		return True

	def zcash_mini(self,name,ut):
		res = run(['zcash-mini'],stdout=PIPE,check=True)
		return True

	def ethkey(self,name,ut):
		if gc.platform == 'linux' and os.uname().machine != 'x86_64':
			distro = [l for l in open('/etc/os-release').read().split('\n') if l.startswith('ID=')][0][3:]
			if distro != 'archarm':
				ut.skip_msg('distro {!r} on architecture {!r}'.format( distro, os.uname().machine ))
				return True
		from test.include.common import get_ethkey
		get_ethkey()
		return True

	def ssh_socks_proxy(self,name,ut):
		from test.test_py_d.ts_xmrwallet import TestSuiteXMRWallet
		return TestSuiteXMRWallet.init_proxy(external_call=True)
