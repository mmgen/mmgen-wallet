#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.rpc: Ethereum base protocol RPC client class
"""

import re

from ...base_obj import AsyncInit
from ...obj import Int
from ...util import die, fmt, oneshot_warning_group
from ...rpc import RPCClient

class daemon_warning(oneshot_warning_group):

	class geth:
		color = 'yellow'
		message = 'Geth has not been tested on mainnet. You may experience problems.'

	class erigon:
		color = 'red'
		message = 'Erigon support is EXPERIMENTAL. Use at your own risk!!!'

class CallSigs:
	pass

class EthereumRPCClient(RPCClient, metaclass=AsyncInit):

	async def __init__(
			self,
			cfg,
			proto,
			daemon,
			backend,
			ignore_wallet):

		self.proto = proto
		self.daemon = daemon
		self.call_sigs = getattr(CallSigs, daemon.id, None)

		super().__init__(
			cfg  = cfg,
			host = 'localhost' if cfg.test_suite else (cfg.rpc_host or 'localhost'),
			port = daemon.rpc_port)

		await self.set_backend_async(backend)

		vi, bh, ci = await self.gathered_call(None, (
				('web3_clientVersion', ()),
				('eth_getBlockByNumber', ('latest', False)),
				('eth_chainId', ()),
			))

		vip = re.match(self.daemon.version_pat, vi, re.ASCII)
		if not vip:
			die(2, fmt(f"""
			Aborting on daemon mismatch:
			  Requested daemon: {self.daemon.id}
			  Running daemon:   {vi}
			""", strip_char='\t').rstrip())

		self.daemon_version = int('{:d}{:03d}{:03d}'.format(*[int(e) for e in vip.groups()]))
		self.daemon_version_str = '{}.{}.{}'.format(*vip.groups())
		self.daemon_version_info = vi

		self.blockcount = int(bh['number'], 16)
		self.cur_date = int(bh['timestamp'], 16)

		self.caps = ()
		if self.daemon.id in ('parity', 'openethereum'):
			if (await self.call('parity_nodeKind'))['capability'] == 'full':
				self.caps += ('full_node',)
			self.chainID = None if ci is None else Int(ci, 16) # parity/oe return chainID only for dev chain
			self.chain = (await self.call('parity_chain')).replace(' ', '_').replace('_testnet', '')
		elif self.daemon.id in ('geth', 'erigon'):
			if self.daemon.network == 'mainnet':
				daemon_warning(self.daemon.id)
			self.caps += ('full_node',)
			self.chainID = Int(ci, 16)
			self.chain = self.proto.chain_ids[self.chainID]

	def make_host_path(self, wallet):
		return ''

	rpcmethods = (
		'eth_blockNumber',
		'eth_call',
		# Returns the EIP155 chain ID used for transaction signing at the current best block.
		# Parity: Null is returned if not available, ID not required in transactions
		# Erigon: always returns ID, requires ID in transactions
		'eth_chainId',
		'eth_gasPrice',
		'eth_getBalance',
		'eth_getCode',
		'eth_getTransactionCount',
		'eth_getTransactionReceipt',
		'eth_sendRawTransaction',
		'parity_chain',
		'parity_nodeKind',
		'parity_pendingTransactions',
		'txpool_content',
	)
