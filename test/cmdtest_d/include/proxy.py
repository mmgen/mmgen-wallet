#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.include.proxy: SSH SOCKS proxy runner for the cmdtest.py test suite
"""

import sys, atexit
from subprocess import run, PIPE

from mmgen.util import msg, die, fmt
from mmgen.util2 import port_in_use

from ...include.common import omsg

class TestProxy:

	port = 49237
	no_ssh_errmsg = """
		The SSH daemon must be running and listening on localhost in order to test
		XMR TX relaying via SOCKS proxy.  If sshd is not running, please start it.
		Otherwise, add the line 'ListenAddress 127.0.0.1' to your sshd_config, and
		then restart the daemon.
	"""
	bad_perm_errmsg = """
		In order to test XMR TX relaying via SOCKS proxy, it’s desirable to enable
		SSH to localhost without a password, which is not currently supported by
		your configuration.  Your possible courses of action:

		1. Continue by answering 'y' at this prompt, and enter your system password
		   at the following prompt;

		2. Exit the test here, add your user SSH public key to your user
		   'authorized_keys' file, and restart the test; or

		3. Exit the test here, start the SSH SOCKS proxy manually by entering the
		   following command, and restart the test:

			  {}
	"""
	need_start_errmsg = """
		Please start the SSH SOCKS proxy by entering the following command:

			{}

		Then restart the test.
	"""

	def kill_proxy(self, args):
		if sys.platform in ('linux', 'darwin'):
			omsg(f'Stopping SSH SOCKS server at localhost:{self.port}')
			cmd = ['pkill', '-f', ' '.join(args)]
			run(cmd)

	def __init__(self, test_group, cfg):

		if test_group and test_group.is_helper:
			return

		def start_proxy():
			run(a + b2)
			omsg(f'SSH SOCKS server started, listening at localhost:{self.port}')

		a = ['ssh', '-x', '-o', 'ExitOnForwardFailure=True', '-D', f'localhost:{self.port}']
		b0 = ['-o', 'PasswordAuthentication=False']
		b1 = ['localhost', 'true']
		b2 = ['-fN', '-E', 'txrelay-proxy.debug', 'localhost']

		if port_in_use(self.port):
			omsg(f'Port {self.port} already in use. Assuming SSH SOCKS server is running')
		else:
			cp = run(a + b0 + b1, stdout=PIPE, stderr=PIPE, text=True)
			if cp.stderr:
				omsg(cp.stderr)
			if cp.returncode == 0:
				start_proxy()
			elif 'onnection refused' in cp.stderr:
				die(2, fmt(self.no_ssh_errmsg, indent='    '))
			elif 'ermission denied' in cp.stderr:
				msg(fmt(self.bad_perm_errmsg.format(' '.join(a + b2)), indent='    ', strip_char='\t'))
				from mmgen.ui import keypress_confirm
				keypress_confirm(cfg, 'Continue?', do_exit=True)
				start_proxy()
			else:
				die(2, fmt(self.need_start_errmsg.format(' '.join(a + b2)), indent='    '))

		if test_group is None:
			self.kill_proxy(a + b2)
		elif not hasattr(test_group.tr, 'proxy_stop_registered'):
			atexit.unregister(self.kill_proxy)
			atexit.register(self.kill_proxy, a + b2)
			test_group.tr.proxy_stop_registered = True
