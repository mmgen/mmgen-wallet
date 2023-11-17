#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.params: Ethereum protocol
"""

from ...protocol import CoinProtocol,_nw,decoded_addr
from ...util import is_hex_str_lc,Msg

class mainnet(CoinProtocol.DummyWIF,CoinProtocol.Secp256k1):

	network_names = _nw('mainnet','testnet','devnet')
	addr_len      = 20
	mmtypes       = ('E',)
	dfl_mmtype    = 'E'
	mod_clsname   = 'Ethereum'
	pubkey_type   = 'std' # required by DummyWIF

	coin_amt      = 'ETHAmt'
	max_tx_fee    = '0.005'
	chain_names   = ['ethereum','foundation']
	sign_mode     = 'standalone'
	caps          = ('token',)
	mmcaps        = ('key','addr','rpc_init','tx')
	base_proto    = 'Ethereum'
	base_proto_coin = 'ETH'
	base_coin     = 'ETH'
	avg_bdi       = 15
	ignore_daemon_version = False

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
	}

	@property
	def dcoin(self):
		return self.tokensym or self.coin

	def decode_addr(self,addr):
		if is_hex_str_lc(addr) and len(addr) == self.addr_len * 2:
			return decoded_addr( bytes.fromhex(addr), None, 'ethereum' )
		if self.cfg.debug:
			Msg(f'Invalid address: {addr}')
		return False

	def checksummed_addr(self,addr):
		h = self.keccak_256(addr.encode()).digest().hex()
		return ''.join(addr[i].upper() if int(h[i],16) > 7 else addr[i] for i in range(len(addr)))

	def pubhash2addr(self,pubhash,p2sh):
		assert len(pubhash) == 20, f'{len(pubhash)}: invalid length for {self.name} pubkey hash'
		assert not p2sh, f'{self.name} protocol has no P2SH address format'
		return pubhash.hex()

class testnet(mainnet):
	chain_names = ['kovan','goerli','rinkeby']

class regtest(testnet):
	chain_names = ['developmentchain']
