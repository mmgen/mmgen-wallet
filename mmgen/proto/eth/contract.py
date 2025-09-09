#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
proto.eth.contract: Ethereum contract and ERC20 token classes
"""

from decimal import Decimal
from collections import namedtuple

from . import rlp

from . import erigon_sleep
from ...util import msg, pp_msg, die
from ...base_obj import AsyncInit
from ...obj import CoinTxID
from ...addr import CoinAddr, ContractAddr

def parse_abi(s):
	return [s[:8]] + [s[8+x*64:8+(x+1)*64] for x in range(len(s[8:])//64)]

class Contract:

	def __init__(self, cfg, proto, addr, *, rpc=None):
		from ...util2 import get_keccak
		self.keccak_256 = get_keccak(cfg)
		self.cfg = cfg
		self.proto = proto
		self.addr = ContractAddr(proto, addr)
		self.rpc = rpc

	def strip(self, s):
		return ''.join([chr(b) for b in s if 32 <= b <= 127]).strip()

	def create_method_id(self, sig):
		return self.keccak_256(sig.encode()).hexdigest()[:8]

	async def code(self):
		return (await self.rpc.call('eth_getCode', '0x'+self.addr))[2:]

	async def do_call(
			self,
			method_sig  = '',
			method_args = '',
			*,
			method      = 'eth_call',
			block       = 'latest', # earliest, latest, safe, finalized, pending
			from_addr   = None,
			data        = None,
			toUnit      = False):

		data = data or (self.create_method_id(method_sig) + method_args)

		args = {
			'to': '0x' + self.addr,
			('data' if self.rpc.daemon.id == 'parity' else 'input'): '0x' + data}

		if from_addr:
			args['from'] = '0x' + from_addr

		if self.cfg.debug_evm:
			msg('{a}:\n  {b} {c}'.format(
				a = method,
				b = method_sig,
				c = '\n  '.join(parse_abi(data))))

		ret = await self.rpc.call(method, args, block)

		if self.cfg.debug_evm:
			msg('  ==> {a}{b}'.format(
				a = ret,
				b = f' [{int(ret, 16)}]' if ret.startswith('0x') and len(ret) <= 66 else ''))

		await erigon_sleep(self)

		return int(ret, 16) * self.base_unit if toUnit else ret

	def make_tx_in(self, *, gas, gasPrice, nonce, data):
		assert isinstance(gas, int), f'{type(gas)}: incorrect type for ‘gas’ (must be an int)'
		return {
			'to':       bytes.fromhex(self.addr),
			'startgas': gas,
			'gasprice': gasPrice.toWei(),
			'value':    0,
			'nonce':    nonce,
			'data':     bytes.fromhex(data)}

	async def txsign(self, tx_in, key, from_addr, *, chain_id=None):

		from .tx.transaction import Transaction

		if chain_id is None:
			res = await self.rpc.call('eth_chainId')
			chain_id = None if res is None else int(res, 16)

		etx = Transaction(**tx_in).sign(key, chain_id)

		if etx.sender.hex() != from_addr:
			die(3, f'Sender address {from_addr!r} does not match address of key {etx.sender.hex()!r}!')

		if self.cfg.debug:
			msg('TOKEN DATA:')
			pp_msg(etx.to_dict())
			msg('PARSED ABI DATA:\n  {}'.format(
				'\n  '.join(parse_abi(etx.data.hex()))))

		return namedtuple('signed_contract_transaction', ['etx', 'txhex', 'txid'])(
			etx,
			rlp.encode(etx).hex(),
			CoinTxID(etx.hash.hex()))

	async def txsend(self, txhex):
		return (await self.rpc.call('eth_sendRawTransaction', '0x'+txhex)).replace('0x', '', 1)

class Token(Contract):

	def __init__(self, cfg, proto, addr, *, rpc=None, decimals=None):
		Contract.__init__(self, cfg, proto, addr, rpc=rpc)
		if decimals:
			assert isinstance(decimals, int), f'decimals param must be int instance, not {type(decimals)}'
			self.decimals = decimals
			self.base_unit = Decimal('10') ** -self.decimals

	async def get_balance(self, acct_addr, block='latest'):
		return self.proto.coin_amt(
			await self.do_call('balanceOf(address)', acct_addr.rjust(64, '0'), toUnit=True, block=block),
			from_decimal = True)

	async def get_name(self):
		return self.strip(bytes.fromhex((await self.do_call('name()'))[2:]))

	async def get_symbol(self):
		return self.strip(bytes.fromhex((await self.do_call('symbol()'))[2:]))

	async def get_decimals(self):
		ret = await self.do_call('decimals()')
		try:
			assert ret[:2] == '0x'
			return int(ret, 16)
		except:
			msg(f'RPC call to decimals() failed (returned {ret!r})')

	async def get_total_supply(self):
		return await self.do_call('totalSupply()', toUnit=True)

	async def info(self):
		return ('{:15}{}\n' * 5).format(
			'token address:', self.addr,
			'token symbol:',  await self.get_symbol(),
			'token name:',    await self.get_name(),
			'decimals:',      self.decimals,
			'total supply:',  await self.get_total_supply())

	def transferdata2sendaddr(self, data): # online
		return CoinAddr(self.proto, parse_abi(data)[1][-40:])

	def transferdata2amt(self, data): # online
		return self.proto.coin_amt(
			int(parse_abi(data)[-1], 16) * self.base_unit,
			from_decimal = True)

	def create_transfer_data(self, to_addr, amt, *, op):
		# Method IDs: 0xa9059cbb (transfer), 0x095ea7b3 (approve)
		assert op in ('transfer', 'approve'), f'{op}: invalid operation (not ‘transfer’ or ‘approve’)'
		return (
			self.create_method_id(f'{op}(address,uint256)')
			+ to_addr.rjust(64, '0')
			+ '{:064x}'.format(int(amt / self.base_unit)))

	# used for testing only:
	async def transfer(self, *, from_addr, to_addr, amt, key, gas, gasPrice):
		nonce = await self.rpc.call('eth_getTransactionCount', '0x'+from_addr, 'pending')
		tx_in = self.make_tx_in(
			gas      = gas,
			gasPrice = gasPrice,
			nonce    = int(nonce, 16),
			data     = self.create_transfer_data(to_addr, amt, op='transfer'))
		res = await self.txsign(tx_in, key, from_addr)
		return await self.txsend(res.txhex)

class ResolvedToken(Token, metaclass=AsyncInit):

	async def __init__(self, cfg, proto, addr, *, rpc):
		Token.__init__(self, cfg, proto, addr, rpc=rpc)
		self.decimals = await self.get_decimals()
		if not self.decimals:
			die('TokenNotInBlockchain', f'Token {addr!r} not in blockchain')
		self.base_unit = Decimal('10') ** -self.decimals

# Tokens: First approve router to spend tokens from user: asset.approve(router,amount).
# Then call router.depositWithExpiry(inbound_address, asset, amount, memo, expiry).
# Asset is the token contract address. Amount should be in native asset decimals
# (eg 1e18 for most tokens). Do not swap to smart contract addresses.
class THORChainRouterContract(Token):

	def create_deposit_with_expiry_data(self, inbound_addr, asset_addr, amt, memo, expiry):
		assert isinstance(memo, bytes)
		assert isinstance(expiry, int)
		memo_chunks = len(memo) // 32 + bool(len(memo) % 32)
		return ( # Method ID: 0x44bc937b
			self.create_method_id('depositWithExpiry(address,address,uint256,string,uint256)')
			+ inbound_addr.rjust(64, '0')                   # 32 bytes
			+ asset_addr.rjust(64, '0')                     # 32 bytes
			+ '{:064x}'.format(int(amt / self.base_unit))   # 32 bytes
			+ '{:064x}'.format(32 * 5)                      # 32 bytes (memo offset)
			+ '{:064x}'.format(expiry)                      # 32 bytes
			+ '{:064x}'.format(len(memo))                   # dynamic arg
			+ memo.hex().ljust(64 * memo_chunks, '0'))
