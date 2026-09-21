# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.overlay.fakemods.mmgen.daemon: test suite overlay for daemon module
"""

from .daemon_orig import *
from .daemon_orig import _dd, _nw # noqa

class overlay_fake_Daemon:
	"""
	Port shift bits:

	test_suite
	| test_user
	| | | reserved
	| | | . . . . .
	7 6 5 4 3 2 1 0
	"""

	@property
	def port_shift(self):

		udata = {
			'':      0,
			'miner': 1,
			'bob':   2,
			'alice': 3}

		if os.getenv('MMGEN_TEST_SUITE_ENABLE_USER_PORT_SHIFT'):
			return 1 << 7 | udata[self.test_user or self.cfg.test_user] << 5
		else:
			return 1 << 7

Daemon.port_shift = overlay_fake_Daemon.port_shift
