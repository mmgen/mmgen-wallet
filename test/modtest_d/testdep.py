#!/usr/bin/env python3

"""
test.modtest_d.testdep: test dependency unit tests for the MMGen suite
"""

import os
from subprocess import run, DEVNULL

from mmgen.util import ymsg, bmsg
from ..include.common import cfg, get_ethkey

sec = 'deadbeef' * 8

class unit_tests:

	altcoin_deps = ('pycoin', 'monero_python', 'keyconv', 'zcash_mini', 'eth_keys', 'ssh_socks_proxy')
	win_skip = ('losetup', 'zcash_mini', 'sudo')
	mac_skip = ('losetup',)

	def sudo(self, name, ut):
		from mmgen.util import have_sudo
		if have_sudo():
			return True
		else:
			ymsg(f'To run the test suite, please enable sudo without password for user ‘{os.getenv("USER")}’')
			return False

	def losetup(self, name, ut):
		os.stat('/dev/loop0')
		for cmd in ('/sbin/losetup', '/usr/sbin/losetup', 'losetup'):
			try:
				run([cmd, '-f'], check=True, stdout=DEVNULL)
				break
			except:
				if cmd == 'losetup':
					raise
		return True

	def pycoin(self, name, ut):
		from pycoin.networks.registry import network_for_netcode as nfnc
		network = nfnc('btc')
		key = network.keys.private(secret_exponent=int(sec, 16), is_compressed=True)
		hash160_c = key.hash160(is_compressed=True)
		network.address.for_p2pkh_wit(hash160_c)
		return True

	def monero_python(self, name, ut):
		from mmgen.util2 import load_cryptodome
		load_cryptodome()
		from monero.seed import Seed
		Seed('deadbeef' * 8).public_address()
		return True

	def keyconv(self, name, ut):
		run(['keyconv', '-G', 'ltc'], stdout=DEVNULL, stderr=DEVNULL, check=True)
		return True

	def zcash_mini(self, name, ut):
		run(['zcash-mini'], stdout=DEVNULL, check=True)
		return True

	def eth_keys(self, name, ut):
		try:
			from eth_keys import keys
			return True
		except ImportError:
			if get_ethkey():
				return True
		ymsg('Neither the ‘eth-keys’ package nor the Parity ‘ethkey’ executable '
			'could be found on the system!')

	def ssh_socks_proxy(self, name, ut):
		from test.cmdtest_d.include.proxy import TestProxy
		return TestProxy(None, cfg)
