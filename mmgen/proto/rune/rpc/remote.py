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
proto.rune.rpc.remote: THORChain base protocol remote RPC client for the MMGen Project
"""

import json

from ....http import HTTPClient
from ....rpc.remote import RemoteRPCClient

class ThornodeRemoteRESTClient(HTTPClient):

	http_hdrs = {'Content-Type': 'application/json'}
	timeout = 5

	def __init__(self, cfg, *, proto=None, host=None):
		for k, v in cfg._proto.rpc_remote_rest_params.items():
			setattr(self, k, v)
		super().__init__(cfg, proto=proto, host=host)

class THORChainRemoteRPCClient(RemoteRPCClient):
	server_proto = 'THORChain'

	def __init__(self, cfg, proto):
		for k, v in proto.rpc_remote_params.items():
			setattr(self, k, v)
		super().__init__(cfg, proto)
		self.caps = ('lbl_id',)
		self.rest_api = ThornodeRemoteRESTClient(cfg)

	# throws exception on error
	def get_balance(self, addr, *, block):
		http_res = self.rest_api.get(path=f'/bank/balances/{addr}')
		data = json.loads(http_res)
		if data['result'] is None:
			from ....util import die
			die('RPCFailure', f'address ‘{addr}’ not found in blockchain')
		else:
			rune_res = [d for d in data['result'] if d['denom'] == 'rune']
			assert len(rune_res) == 1, f'{rune_res}: result length is not one!'
			return self.proto.coin_amt(int(rune_res[0]['amount']), from_unit='satoshi')
