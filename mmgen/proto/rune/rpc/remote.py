# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.rune.rpc.remote: THORChain base protocol remote RPC client for the MMGen Project
"""

import json

from ....http import RemoteJSONClient
from ....rpc.remote import RemoteRPCClient

# throws exception on error:
def process_response(json_response, errmsg):
	data = json.loads(json_response)
	if isinstance(data, dict) and 'result' in data:
		if data['result'] is None:
			from ....util import die
			die('RPCFailure', errmsg)
		return data['result']
	return data

def data_for_coin(ret, coin):
	return next(iter([e for e in ret if e['chain'] == coin.upper()] or [None])) if coin else ret

# HTTP POST, JSON-RPC response:
class ThornodeRemoteRPCClient(RemoteJSONClient):
	params = 'rpc_remote_rpc_params'
	timeout = 30

# HTTP GET, params in query string, JSON-RPC response:
class ThornodeRemoteRESTClient(RemoteJSONClient):
	params = 'rpc_remote_rest_params'
	timeout = 15

class ThornodeRemoteMidgardClient(RemoteJSONClient):
	params = 'rpc_remote_midgard_params'
	timeout = 30

class THORChainRemoteRPCClient(RemoteRPCClient):
	"retrieve data from a remote THORChain JSON-RPC endpoint"

	server_proto = 'THORChain'
	mods = {
		'get': (
			'ping',
			'health',
			'pools',
			'lastblock',
			'mimir',
			'actions',
			'inbound_addrs',
			'acct_info',
			'balance',
			'tx_info')}

	def __init__(self, cfg, proto):
		for k, v in proto.rpc_remote_params.items():
			setattr(self, k, v)
		super().__init__(cfg, proto)
		self.caps = ('lbl_id',)
		self.rest_api = ThornodeRemoteRESTClient(cfg, proto)
		self.rpc_api = ThornodeRemoteRPCClient(cfg, proto)
		self.midgard_api = ThornodeRemoteMidgardClient(cfg, proto)

	def ping(self):
		"ping the remote REST endpoint"
		return process_response(
			self.rest_api.get(path='/thorchain/ping'),
			errmsg = f'pinging remote endpoint {self.rest_api.host} failed')

	def health(self):
		"check the health of the THORChain network"
		return process_response(
			self.midgard_api.get(path='/v2/health'),
			errmsg = f'getting health status from {self.midgard_api.host} failed')

	def pools(self):
		"get available pools on the THORChain network"
		return process_response(
			self.midgard_api.get(path='/v2/pools'),
			errmsg = f'getting pools from {self.midgard_api.host} failed')

	def lastblock(self, *, coin: str=None): # noqa: RUF013
		"get last block info for all coins or a given coin"
		return data_for_coin(process_response(
			self.rest_api.get(path='/thorchain/lastblock'),
			errmsg = 'unable to retrieve lastblock data'), coin)

	def mimir(self):
		"get Mimir constants for the THORChain network"
		return process_response(
			self.rest_api.get(path='/thorchain/mimir'),
			errmsg = 'get mimir info failed')

	def actions(self, *, addr: str=None, txid: str=None): # noqa: RUF013
		"get actions for a given address or TxID"
		assert addr or txid, 'one of addr or txid must be specified'
		qs = '&'.join(f'{k}={v}' for k, v in (('address', addr), ('txid', txid)) if v)
		return process_response(
			self.midgard_api.get(path=f'/v2/actions?{qs}'),
			errmsg = 'get actions info failed')

	def inbound_addrs(self, *, coin: str=None): # noqa: RUF013
		"get current inbound (vault) addresses"
		return data_for_coin(process_response(
			self.rest_api.get(path='/thorchain/inbound_addresses'),
			errmsg = 'unable to retrieve inbound (vault) addresses'), coin)

	def acct_info(self, addr: str, *, block=None):
		"get account information for a given address"
		return process_response(
			self.rest_api.get(path=f'/auth/accounts/{addr}'),
			errmsg =  f'address ‘{addr}’ not found in blockchain')['value']

	def balance(self, addr: str, *, block=None):
		"get balance for a given address"
		res = process_response(
			self.rest_api.get(path=f'/bank/balances/{addr}'),
			errmsg =  f'address ‘{addr}’ not found in blockchain')
		rune_res = [d for d in res if d['denom'] == 'rune']
		assert len(rune_res) == 1, f'{rune_res}: result length is not one!'
		return self.proto.coin_amt(int(rune_res[0]['amount']), from_unit='satoshi')

	def tx_info(self, txid: str):
		"get information for a transaction by TxID"
		return process_response(
			self.rpc_api.post(
				path = '/tx',
				data = {'hash': '0x' + txid}),
			errmsg = f'get info for transaction {txid} failed')

	def tx_op(self, txhex: str, op=None):
		"perform a transaction operation"
		assert isinstance(txhex, str)
		assert op in ('check_tx', 'broadcast_tx_sync', 'broadcast_tx_async')
		return process_response(
			self.rpc_api.post(
				path = '/' + op,
				data = {'tx': '0x' + txhex}),
			errmsg = f'transaction operation ‘{op}’ failed')
