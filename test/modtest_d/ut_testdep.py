#!/usr/bin/env python3

"""
test.modtest_d.ut_testdep: test dependency unit tests for the MMGen suite
"""

import sys, os
from subprocess import run, DEVNULL

from mmgen.util import ymsg, bmsg
from ..include.common import cfg

sec = 'deadbeef' * 8

class unit_tests:

	altcoin_deps = ('pycoin', 'monero_python', 'keyconv', 'zcash_mini', 'ethkey', 'ssh_socks_proxy')
	win_skip = ('losetup', 'zcash_mini', 'sudo')
	mac_skip = ('losetup',)

	def pylint(self, name, ut):
		try:
			return run(['pylint', '--version'], stdout=None if cfg.verbose else DEVNULL).returncode == 0
		except OSError as e:
			ymsg('  ' + str(e))
			bmsg("  Install pylint with 'python3 -m pip install pylint'")
			return False

	def core_repo(self, name, ut):
		crr = os.getenv('CORE_REPO_ROOT')
		if not crr or not os.path.exists(os.path.join(crr, 'src/test/data/tx_valid.json')):
			ymsg('CORE_REPO_ROOT not set, or does not point to Bitcoin Core repository')
			return False
		return True

	def losetup(self, name, ut):
		os.stat('/dev/loop0')
		run(['/sbin/losetup', '-f'], check=True, stdout=DEVNULL)
		return True

	def pycoin(self, name, ut):
		from pycoin.networks.registry import network_for_netcode as nfnc
		network = nfnc('btc')
		key = network.keys.private(secret_exponent=int(sec, 16), is_compressed=True)
		hash160_c = key.hash160(is_compressed=True)
		network.address.for_p2pkh_wit(hash160_c)
		return True

	def monero_python(self, name, ut):
		from mmgen.util2 import load_cryptodomex
		load_cryptodomex()
		from monero.seed import Seed
		Seed('deadbeef' * 8).public_address()
		return True

	def keyconv(self, name, ut):
		run(['keyconv', '-G', 'ltc'], stdout=DEVNULL, stderr=DEVNULL, check=True)
		return True

	def zcash_mini(self, name, ut):
		run(['zcash-mini'], stdout=DEVNULL, check=True)
		return True

	def ethkey(self, name, ut):
		if sys.platform == 'linux' and os.uname().machine != 'x86_64':
			distro = [l for l in open('/etc/os-release').read().split('\n') if l.startswith('ID=')][0][3:]
			if distro != 'archarm':
				ut.skip_msg(f'distro {distro!r} on architecture {os.uname().machine!r}')
				return True
		from test.include.common import get_ethkey
		get_ethkey()
		return True

	def ssh_socks_proxy(self, name, ut):
		from test.cmdtest_d.ct_xmrwallet import CmdTestXMRWallet
		return CmdTestXMRWallet.init_proxy(external_call=True)

	def sudo(self, name, ut):
		from mmgen.util import have_sudo
		if have_sudo():
			return True
		else:
			ymsg(f'To run the test suite, please enable sudo without password for user ‘{os.getenv("USER")}’')
			return False
