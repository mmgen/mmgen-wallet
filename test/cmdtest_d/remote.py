#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.remote: THORChain remote RPC tests for the cmdtest.py test suite
"""

from .base import CmdTestBase
from .swap import CmdTestSwapMethods
from .rune import CmdTestRuneMethods

class CmdTestRemote(CmdTestBase, CmdTestSwapMethods, CmdTestRuneMethods):
	'fetching data from remote JSON-RPC server'

	networks = ('btc',)
	tmpdir_nums = [37]
	thornode_servers = ('rpc', 'midgard')

	cmd_group = (
		('ping',                'pinging remote REST server'),
		('health',              'checking health of THORChain network'),
		('inbounds',            'getting inbound addresses (all coins)'),
		('inbound_ltc',         'getting inbound address for LTC'),
		('inbound_ltc_log',     'getting inbound addresses (all coins, logging to file)'),
		('inbound_ltc_log_chk', 'checking log file'),
		('lastblock',           'getting lastblock info'),
		('lastblock_btc',       'getting lastblock info for BTC'),
		('actions_addr',        'getting actions for address'),
		('actions_txid',        'getting actions for txid'),
		('actions_addr_txid',   'getting actions for txid and addr'),
		('stop_thornode_servers','stopping the Thornode RPC and Midgard servers'))

	def __init__(self, cfg, trunner, cfgs, spawn):
		super().__init__(cfg, trunner, cfgs, spawn)
		if trunner is None:
			return
		self.start_thornode_servers()

	def ping(self):
		return self._rune_remote('ping')

	def health(self):
		return self._rune_remote('health')

	def inbounds(self):
		return self._rune_remote('inbound_addrs')

	def inbound_ltc(self):
		return self._rune_remote('inbound_addrs', ['coin=ltc'])

	def inbound_ltc_log(self):
		return self._rune_remote('inbound_addrs', ['coin=ltc'], add_opts=['--log'])

	def inbound_ltc_log_chk(self):
		import json
		self.spawn(msg_only=True)
		json.loads(self.read_from_tmpfile('mmgen-remote-RUNE-inbound-addrs-coin=ltc.json'))
		return 'ok'

	def lastblock(self):
		return self._rune_remote('lastblock')

	def lastblock_btc(self):
		return self._rune_remote('lastblock', ['coin=btc'])

	def actions_addr(self):
		return self._rune_remote('actions', ['addr=thor1abcdefg'])

	def actions_txid(self):
		return self._rune_remote('actions', ['txid=deadbeef'])

	def actions_addr_txid(self):
		return self._rune_remote('actions', ['addr=thor1abcdefg', 'txid=deadbeef'])

	def stop_servers(self):
		self.stop_thornode_servers(['rpc','midgard'])
