# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.httpd.thornode: Thornode WSGI HTTP server
"""

from .. import HTTPD

class ThornodeServer(HTTPD):
	name = 'thornode server'
	content_type = 'application/json'

	var_actions = {}
	chain_var_actions = {}

	def get_idx(self, key, coin):
		return next(n for n, e in enumerate(getattr(self, key)) if e['chain'] == coin)

	def set_var(self, key, name, val):
		getattr(self, key)[name] = val

	def set_chain_var(self, key, chain, name, val):
		getattr(self, key)[self.get_idx(key, chain)][name] = val

	def setvar(self, name, val):
		if name in self.var_actions:
			self.set_var(*self.var_actions[name], val)
		elif name in self.chain_var_actions:
			self.set_chain_var(*self.chain_var_actions[name], val)
		else:
			raise ValueError(f'{name!r}: unrecognized action')
