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
xmrwallet.ops.relay: Monero wallet ops for the MMGen Suite
"""

import time
from pathlib import Path

from ...util import msg, msg_r, gmsg, ymsg, die
from ...ui import keypress_confirm
from ...proto.xmr.rpc import MoneroRPCClient

from ..file.tx import MoneroMMGenTX

from . import OpBase

class OpRelay(OpBase):
	opts = ('tx_relay_daemon',)

	def __init__(self, cfg, uarg_tuple):

		super().__init__(cfg, uarg_tuple)

		self.mount_removable_device()

		self.tx = MoneroMMGenTX.Signed(self.cfg, Path(self.uargs.infile))

		if self.cfg.tx_relay_daemon:
			m = self.parse_tx_relay_opt()
			host, port = m[1].split(':')
			proxy = m[2]
			md = None
		else:
			from ...daemon import CoinDaemon
			md = CoinDaemon(self.cfg, network_id='xmr', test_suite=self.cfg.test_suite)
			host, port = ('localhost', md.rpc_port)
			proxy = None

		self.dc = MoneroRPCClient(
			cfg    = self.cfg,
			proto  = self.proto,
			daemon = md,
			host   = host,
			port   = int(port),
			user   = None,
			passwd = None,
			test_connection = host == 'localhost', # avoid extra connections if relay is a public node
			proxy  = proxy)

	async def main(self):
		msg('\n' + self.tx.get_info(indent='    '))

		if self.cfg.tx_relay_daemon:
			self.display_tx_relay_info(indent='    ')

		keypress_confirm(self.cfg, 'Relay transaction?', do_exit=True)

		if self.cfg.tx_relay_daemon:
			msg_r('Relaying transaction to remote daemon, please be patient...')
			t_start = time.time()

		res = self.dc.call_raw('send_raw_transaction', tx_as_hex=self.tx.data.blob)
		if res['status'] == 'OK':
			if res['not_relayed']:
				msg('not relayed')
				ymsg('Transaction not relayed')
			else:
				msg('success')
			if self.cfg.tx_relay_daemon:
				from ...util2 import format_elapsed_hr
				msg(f'Relay time: {format_elapsed_hr(t_start, rel_now=False, show_secs=True)}')
			gmsg('OK')
			return True
		else:
			die('RPCFailure', repr(res))
