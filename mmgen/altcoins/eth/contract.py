#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
altcoins.eth.contract: Ethereum contract and token classes for the MMGen suite
"""

from decimal import Decimal
from . import rlp

from mmgen.globalvars import g
from mmgen.common import *
from mmgen.obj import MMGenObject,CoinAddr,TokenAddr,CoinTxID,ETHAmt
from mmgen.util import msg

try:
	assert not g.use_internal_keccak_module
	from sha3 import keccak_256
except:
	from mmgen.keccak import keccak_256

def parse_abi(s):
	return [s[:8]] + [s[8+x*64:8+(x+1)*64] for x in range(len(s[8:])//64)]

def create_method_id(sig): return keccak_256(sig.encode()).hexdigest()[:8]

class Token(MMGenObject): # ERC20

	_decimals = None

	# Test that token is in the blockchain by calling constructor w/o decimals arg
	def __init__(self,addr,decimals=None):
		self.addr = TokenAddr(addr)
		if decimals:
			self._decimals = decimals
		else:
			rpc_init()
			self.decimals()
		if not self._decimals:
			raise TokenNotInBlockchain("Token '{}' not in blockchain".format(addr))
		self.base_unit = Decimal('10') ** -self._decimals

	@staticmethod
	def transferdata2sendaddr(data): # online
		return CoinAddr(parse_abi(data)[1][-40:])

	def transferdata2amt(self,data): # online
		return ETHAmt(int(parse_abi(data)[-1],16) * self.base_unit)

	def do_call(self,method_sig,method_args='',toUnit=False):
		data = create_method_id(method_sig) + method_args
		if g.debug:
			msg('ETH_CALL {}:  {}'.format(method_sig,'\n  '.join(parse_abi(data))))
		ret = g.rpch.eth_call({ 'to': '0x'+self.addr, 'data': '0x'+data })
		return int(ret,16) * self.base_unit if toUnit else ret

	def balance(self,acct_addr):
		return ETHAmt(self.do_call('balanceOf(address)',acct_addr.rjust(64,'0'),toUnit=True))

	def strip(self,s):
		return ''.join([chr(b) for b in s if 32 <= b <= 127]).strip()

	# TODO: make these properties
	def decimals(self):
		if self._decimals == None:
			res = self.do_call('decimals()')
			try:
				assert res[:2] == '0x'
				self._decimals = int(res[2:],16)
			except:
				msg("RPC call to decimals() failed (returned '{}')".format(res))
				return None
		return self._decimals

	def name(self):
		return self.strip(bytes.fromhex(self.do_call('name()')[2:]))

	def symbol(self):
		return self.strip(bytes.fromhex(self.do_call('symbol()')[2:]))

	def total_supply(self):
		return self.do_call('totalSupply()',toUnit=True)

	def info(self):
		fs = '{:15}{}\n' * 5
		return fs.format('token address:',self.addr,
						'token symbol:',self.symbol(),
						'token name:',self.name(),
						'decimals:',self.decimals(),
						'total supply:',self.total_supply())

	def code(self):
		return g.rpch.eth_getCode('0x'+self.addr)[2:]

	def create_data(self,to_addr,amt,method_sig='transfer(address,uint256)',from_addr=None):
		from_arg = from_addr.rjust(64,'0') if from_addr else ''
		to_arg = to_addr.rjust(64,'0')
		amt_arg = '{:064x}'.format(int(amt//self.base_unit))
		return create_method_id(method_sig) + from_arg + to_arg + amt_arg

	def make_tx_in( self,from_addr,to_addr,amt,start_gas,gasPrice,nonce,
					method_sig='transfer(address,uint256)',from_addr2=None):
		data = self.create_data(to_addr,amt,method_sig=method_sig,from_addr=from_addr2)
		return {'to':       bytes.fromhex(self.addr),
				'startgas': start_gas.toWei(),
				'gasprice': gasPrice.toWei(),
				'value':    0,
				'nonce':    nonce,
				'data':     bytes.fromhex(data) }

	def txsign(self,tx_in,key,from_addr,chain_id=None):

		from .pyethereum.transactions import Transaction

		if chain_id is None:
			chain_id_method = ('parity_chainId','eth_chainId')['eth_chainId' in g.rpch.caps]
			chain_id = int(g.rpch.request(chain_id_method),16)
		tx = Transaction(**tx_in).sign(key,chain_id)
		hex_tx = rlp.encode(tx).hex()
		coin_txid = CoinTxID(tx.hash.hex())
		if tx.sender.hex() != from_addr:
			m = "Sender address '{}' does not match address of key '{}'!"
			die(3,m.format(from_addr,tx.sender.hex()))
		if g.debug:
			msg('TOKEN DATA:')
			pmsg(tx.to_dict())
			msg('PARSED ABI DATA:\n  {}'.format('\n  '.join(parse_abi(tx.data.hex()))))
		return hex_tx,coin_txid

# The following are used for token deployment only:

	def txsend(self,hex_tx):
		return g.rpch.eth_sendRawTransaction('0x'+hex_tx).replace('0x','',1)

	def transfer(   self,from_addr,to_addr,amt,key,start_gas,gasPrice,
					method_sig='transfer(address,uint256)',
					from_addr2=None,
					return_data=False):
		tx_in = self.make_tx_in(
					from_addr,to_addr,amt,
					start_gas,gasPrice,
					nonce = int(g.rpch.parity_nextNonce('0x'+from_addr),16),
					method_sig = method_sig,
					from_addr2 = from_addr2 )
		(hex_tx,coin_txid) = self.txsign(tx_in,key,from_addr)
		return self.txsend(hex_tx)
