#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
from mmgen.base_obj import AsyncInit
from mmgen.obj import MMGenObject,CoinAddr,TokenAddr,CoinTxID
from mmgen.util import msg
from .obj import ETHAmt

try:
	assert not g.use_internal_keccak_module
	from sha3 import keccak_256
except:
	from mmgen.keccak import keccak_256

def parse_abi(s):
	return [s[:8]] + [s[8+x*64:8+(x+1)*64] for x in range(len(s[8:])//64)]

def create_method_id(sig):
	return keccak_256(sig.encode()).hexdigest()[:8]

class TokenBase(MMGenObject): # ERC20

	def transferdata2sendaddr(self,data): # online
		return CoinAddr(self.proto,parse_abi(data)[1][-40:])

	def transferdata2amt(self,data): # online
		return ETHAmt(int(parse_abi(data)[-1],16) * self.base_unit)

	async def do_call(self,method_sig,method_args='',toUnit=False):
		data = create_method_id(method_sig) + method_args
		if g.debug:
			msg('ETH_CALL {}:  {}'.format(
				method_sig,
				'\n  '.join(parse_abi(data)) ))
		ret = await self.rpc.call('eth_call',{ 'to': '0x'+self.addr, 'data': '0x'+data },'pending')
		if self.proto.network == 'regtest' and g.daemon_id == 'erigon': # ERIGON
			import asyncio
			await asyncio.sleep(5)
		if toUnit:
			return int(ret,16) * self.base_unit
		else:
			return ret

	async def get_balance(self,acct_addr):
		return ETHAmt(await self.do_call('balanceOf(address)',acct_addr.rjust(64,'0'),toUnit=True))

	def strip(self,s):
		return ''.join([chr(b) for b in s if 32 <= b <= 127]).strip()

	async def get_name(self):
		return self.strip(bytes.fromhex((await self.do_call('name()'))[2:]))

	async def get_symbol(self):
		return self.strip(bytes.fromhex((await self.do_call('symbol()'))[2:]))

	async def get_decimals(self):
		ret = await self.do_call('decimals()')
		try:
			assert ret[:2] == '0x'
			return int(ret,16)
		except:
			msg(f'RPC call to decimals() failed (returned {ret!r})')
			return None

	async def get_total_supply(self):
		return await self.do_call('totalSupply()',toUnit=True)

	async def info(self):
		return ('{:15}{}\n' * 5).format(
			'token address:', self.addr,
			'token symbol:',  await self.get_symbol(),
			'token name:',    await self.get_name(),
			'decimals:',      self.decimals,
			'total supply:',  await self.get_total_supply() )

	async def code(self):
		return (await self.rpc.call('eth_getCode','0x'+self.addr))[2:]

	def create_data(self,to_addr,amt,method_sig='transfer(address,uint256)',from_addr=None):
		from_arg = from_addr.rjust(64,'0') if from_addr else ''
		to_arg = to_addr.rjust(64,'0')
		amt_arg = '{:064x}'.format( int(amt / self.base_unit) )
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

	async def txsign(self,tx_in,key,from_addr,chain_id=None):

		from .pyethereum.transactions import Transaction

		if chain_id is None:
			res = await self.rpc.call('eth_chainId')
			chain_id = None if res == None else int(res,16)

		tx = Transaction(**tx_in).sign(key,chain_id)
		hex_tx = rlp.encode(tx).hex()
		coin_txid = CoinTxID(tx.hash.hex())
		if tx.sender.hex() != from_addr:
			die(3,f'Sender address {from_addr!r} does not match address of key {tx.sender.hex()!r}!')
		if g.debug:
			msg('TOKEN DATA:')
			pp_msg(tx.to_dict())
			msg('PARSED ABI DATA:\n  {}'.format(
				'\n  '.join(parse_abi(tx.data.hex())) ))
		return hex_tx,coin_txid

# The following are used for token deployment only:

	async def txsend(self,hex_tx):
		return (await self.rpc.call('eth_sendRawTransaction','0x'+hex_tx)).replace('0x','',1)

	async def transfer(   self,from_addr,to_addr,amt,key,start_gas,gasPrice,
					method_sig='transfer(address,uint256)',
					from_addr2=None,
					return_data=False):
		tx_in = self.make_tx_in(
					from_addr,to_addr,amt,
					start_gas,gasPrice,
					nonce = int(await self.rpc.call('eth_getTransactionCount','0x'+from_addr,'pending'),16),
					method_sig = method_sig,
					from_addr2 = from_addr2 )
		(hex_tx,coin_txid) = await self.txsign(tx_in,key,from_addr)
		return await self.txsend(hex_tx)

class Token(TokenBase):

	def __init__(self,proto,addr,decimals,rpc=None):
		self.proto = proto
		self.addr = TokenAddr(proto,addr)
		assert isinstance(decimals,int),f'decimals param must be int instance, not {type(decimals)}'
		self.decimals = decimals
		self.base_unit = Decimal('10') ** -self.decimals
		self.rpc = rpc

class TokenResolve(TokenBase,metaclass=AsyncInit):

	async def __init__(self,proto,rpc,addr):
		self.proto = proto
		self.rpc = rpc
		self.addr = TokenAddr(proto,addr)
		decimals = await self.get_decimals() # requires self.addr!
		if not decimals:
			raise TokenNotInBlockchain(f'Token {addr!r} not in blockchain')
		Token.__init__(self,proto,addr,decimals,rpc)
