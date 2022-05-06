#!/usr/bin/env python3
"""
test.unit_tests_d.ut_testdep: test dependency unit tests for the MMGen suite
"""

from mmgen.common import *
from subprocess import run,PIPE

sec = 'deadbeef' * 8

class unit_tests:

	altcoin_deps = ('pycoin','moneropy','keyconv','zcash_mini','ethkey','ssh_socks_proxy')
	win_skip = ('losetup','moneropy','zcash_mini')
	arm_skip = ('zcash_mini','ethkey')

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

	def moneropy(self,name,ut):
		from moneropy import account
		res = account.account_from_spend_key(sec)
		return True

	def keyconv(self,name,ut):
		res = run(['keyconv','-G','ltc'],stdout=PIPE,stderr=PIPE)
		return True

	def zcash_mini(self,name,ut):
		res = run(['zcash-mini'],stdout=PIPE)
		return True

	def ethkey(self,name,ut):
		res = run(['ethkey','generate','random'],stdout=PIPE)
		return True

	def ssh_socks_proxy(self,name,ut):
		from test.test_py_d.ts_xmrwallet import TestSuiteXMRWallet
		return TestSuiteXMRWallet.init_proxy(external_call=True)
