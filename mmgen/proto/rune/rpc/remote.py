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

# throws exception on error:
def process_response(json_response, errmsg):
	data = json.loads(json_response)
	if data['result'] is None:
		from ....util import die
		die('RPCFailure', errmsg)
	return data['result']

# HTTP POST, JSON-RPC response:
class ThornodeRemoteRPCClient(HTTPClient):

	timeout = 30

	def __init__(self, cfg, proto, *, network_proto=None, host=None):
		for k, v in proto.rpc_remote_rpc_params.items():
			setattr(self, k, v)
		super().__init__(cfg, network_proto=network_proto, host=host)

# HTTP GET, params in query string, JSON-RPC response:
class ThornodeRemoteRESTClient(HTTPClient):

	http_hdrs = {'Content-Type': 'application/json'}
	timeout = 5

	def __init__(self, cfg, proto, *, network_proto=None, host=None):
		for k, v in proto.rpc_remote_rest_params.items():
			setattr(self, k, v)
		super().__init__(cfg, network_proto=network_proto, host=host)

class THORChainRemoteRPCClient(RemoteRPCClient):
	server_proto = 'THORChain'

	def __init__(self, cfg, proto):
		for k, v in proto.rpc_remote_params.items():
			setattr(self, k, v)
		super().__init__(cfg, proto)
		self.caps = ('lbl_id',)
		self.rest_api = ThornodeRemoteRESTClient(cfg, proto)
		self.rpc_api = ThornodeRemoteRPCClient(cfg, proto)

	def get_balance(self, addr, *, block=None):
		res = process_response(
			self.rest_api.get(path=f'/bank/balances/{addr}'),
			errmsg =  f'address ‘{addr}’ not found in blockchain')
		rune_res = [d for d in res if d['denom'] == 'rune']
		assert len(rune_res) == 1, f'{rune_res}: result length is not one!'
		return self.proto.coin_amt(int(rune_res[0]['amount']), from_unit='satoshi')

	def get_account_info(self, addr, *, block=None):
		return process_response(
			self.rest_api.get(path=f'/auth/accounts/{addr}'),
			errmsg =  f'address ‘{addr}’ not found in blockchain')['value']

	def get_tx_info(self, txid):
		return process_response(
			self.rpc_api.post(
				path = '/tx',
				data = {'hash': '0x' + txid}),
			errmsg = f'get info for transaction {txid} failed')

	def tx_op(self, txhex, op=None):
		assert isinstance(txhex, str)
		assert op in ('check_tx', 'broadcast_tx_sync', 'broadcast_tx_async')
		return process_response(
			self.rpc_api.post(
				path = '/' + op,
				data = {'tx': '0x' + txhex}),
			errmsg = f'transaction operation ‘{op}’ failed')
