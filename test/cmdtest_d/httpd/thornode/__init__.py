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

import time

from mmgen.cfg import Config

from .. import HTTPD

day = int(time.time() // (24 * 60 * 60))
cfg = Config()

def make_inbound_addr(coin):
	from mmgen.protocol import init_proto
	from mmgen.tool.coin import tool_cmd
	proto = init_proto(cfg, coin, network='regtest', need_amt=True)
	n = (day + int('beadcafe' * 8, 16)) % (2 ** 256) # address changes every 24 hours
	ret = tool_cmd(
		cfg     = cfg,
		cmdname = 'privhex2addr',
		proto   = proto,
		mmtype  = proto.preferred_mmtypes[0]).privhex2addr(f'{n:064x}')
	return ('0x' + ret) if coin.upper() == 'ETH' else ret.views[0]

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
