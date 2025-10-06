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
proto.eth.params: Ethereum protocol
"""

from ...protocol import CoinProtocol, _nw, decoded_addr
from ...addr import CoinAddr
from ...util import is_hex_str_lc, Msg

class mainnet(CoinProtocol.DummyWIF, CoinProtocol.Secp256k1):

	network_names = _nw('mainnet', 'testnet', 'devnet')
	addr_len      = 20
	mmtypes       = ('E',)
	preferred_mmtypes  = ('E',)
	dfl_mmtype    = 'E'
	mod_clsname   = 'Ethereum'
	pubkey_type   = 'std' # required by DummyWIF

	coin_amt      = 'ETHAmt'
	max_tx_fee    = 0.005
	chain_names   = ['ethereum', 'foundation']
	sign_mode     = 'standalone'
	caps          = ('token',)
	mmcaps        = ('rpc', 'rpc_init', 'tw', 'msg')
	base_proto    = 'Ethereum'
	base_proto_coin = 'ETH'
	base_coin     = 'ETH'
	avg_bdi       = 15
	decimal_prec  = 36
	address_reuse_ok = True
	is_vm = True
	is_evm = True

	# https://www.chainid.dev
	chain_ids = {
		1:    'ethereum',         # ethereum mainnet
		2:    'morden',           # morden testnet (deprecated)
		3:    'ropsten',          # ropsten testnet
		4:    'rinkeby',          # rinkeby testnet
		5:    'goerli',           # goerli testnet
		42:   'kovan',            # kovan testnet
		61:   'classic',          # ethereum classic mainnet
		62:   'morden',           # ethereum classic testnet
		17:   'developmentchain', # parity dev chain
		1337: 'developmentchain', # geth dev chain
		711:  'ethereum',         # geth mainnet (empty chain)
		17000: 'holesky'}         # proof-of-stake testnet

	coin_cfg_opts = (
		'daemon_id',
		'ignore_daemon_version',
		'rpc_host',
		'rpc_port',
		'max_tx_fee')

	proto_cfg_opts = (
		'chain_names')

	@property
	def dcoin(self):
		return self.tokensym or self.coin

	def decode_addr(self, addr):
		if is_hex_str_lc(addr) and len(addr) == self.addr_len * 2:
			return decoded_addr(bytes.fromhex(addr), None, 'p2pkh')
		if self.cfg.debug:
			Msg(f'Invalid address: {addr}')
		return False

	def checksummed_addr(self, addr):
		h = self.keccak_256(addr.encode()).digest().hex()
		return ''.join(addr[i].upper() if int(h[i], 16) > 7 else addr[i] for i in range(len(addr)))

	def pubhash2addr(self, pubhash, addr_type):
		assert len(pubhash) == 20, f'{len(pubhash)}: invalid length for {self.name} pubkey hash'
		assert addr_type == 'p2pkh', (
				f'{addr_type}: bad addr type - {self.name} protocol supports P2PKH address format only')
		return CoinAddr(self, pubhash.hex())

class testnet(mainnet):
	chain_names = ['kovan', 'goerli', 'rinkeby']

class regtest(testnet):
	chain_names = ['developmentchain']
