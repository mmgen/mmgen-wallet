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
tool/coin.py: Cryptocoin routines for the 'mmgen-tool' utility
"""

from collections import namedtuple
generator_data = namedtuple('generator_data',['kg','ag'])

from .common import tool_cmd_base

from ..protocol import init_proto,init_genonly_altcoins,hash160
from ..key import PrivKey
from ..addr import KeyGenerator,AddrGenerator,MMGenAddrType,CoinAddr

class tool_cmd(tool_cmd_base):
	"""
	cryptocoin key/address utilities

		May require use of the '--coin', '--type' and/or '--testnet' options

		Examples:
			mmgen-tool --coin=ltc --type=bech32 wif2addr <wif key>
			mmgen-tool --coin=zec --type=zcash_z randpair
	"""

	def __init__(self,proto=None,mmtype=None):

		if proto:
			self.proto = proto
		else:
			from ..protocol import init_proto_from_opts
			self.proto = init_proto_from_opts()

		from ..opts import opt
		self.mmtype = MMGenAddrType(
			self.proto,
			mmtype or opt.type or self.proto.dfl_mmtype )

		from ..globalvars import g
		if g.token:
			self.proto.tokensym = g.token.upper()

	def _init_generators(self,arg=None):
		return generator_data(
			kg = KeyGenerator( self.proto, self.mmtype.pubkey_type ),
			ag = AddrGenerator( self.proto, self.mmtype ),
		)

	def randwif(self):
		"generate a random private key in WIF format"
		from ..crypto import get_random
		return PrivKey(
			self.proto,
			get_random(32),
			pubkey_type = self.mmtype.pubkey_type,
			compressed  = self.mmtype.compressed ).wif

	def randpair(self):
		"generate a random private key/address pair"
		gd = self._init_generators()
		from ..crypto import get_random
		privkey = PrivKey(
			self.proto,
			get_random(32),
			pubkey_type = self.mmtype.pubkey_type,
			compressed  = self.mmtype.compressed )
		return (
			privkey.wif,
			gd.ag.to_addr( gd.kg.gen_data(privkey) ))

	def wif2hex(self,wifkey:'sstr'):
		"convert a private key from WIF to hex format"
		return PrivKey(
			self.proto,
			wif = wifkey ).hex()

	def hex2wif(self,privhex:'sstr'):
		"convert a private key from hex to WIF format"
		return PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			pubkey_type = self.mmtype.pubkey_type,
			compressed  = self.mmtype.compressed ).wif

	def wif2addr(self,wifkey:'sstr'):
		"generate a coin address from a key in WIF format"
		gd = self._init_generators()
		privkey = PrivKey(
			self.proto,
			wif = wifkey )
		return gd.ag.to_addr( gd.kg.gen_data(privkey) )

	def wif2redeem_script(self,wifkey:'sstr'): # new
		"convert a WIF private key to a Segwit P2SH-P2WPKH redeem script"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		gd = self._init_generators()
		privkey = PrivKey(
			self.proto,
			wif = wifkey )
		return gd.ag.to_segwit_redeem_script( gd.kg.gen_data(privkey) )

	def wif2segwit_pair(self,wifkey:'sstr'):
		"generate both a Segwit P2SH-P2WPKH redeem script and address from WIF"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		gd = self._init_generators()
		data = gd.kg.gen_data(PrivKey(
			self.proto,
			wif = wifkey ))
		return (
			gd.ag.to_segwit_redeem_script(data),
			gd.ag.to_addr(data) )

	def privhex2addr(self,privhex:'sstr',output_pubhex=False):
		"generate coin address from raw private key data in hexadecimal format"
		gd = self._init_generators()
		pk = PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			compressed  = self.mmtype.compressed,
			pubkey_type = self.mmtype.pubkey_type )
		data = gd.kg.gen_data(pk)
		return data.pubkey.hex() if output_pubhex else gd.ag.to_addr(data)

	def privhex2pubhex(self,privhex:'sstr'): # new
		"generate a hex public key from a hex private key"
		return self.privhex2addr(privhex,output_pubhex=True)

	def pubhex2addr(self,pubkeyhex:'sstr'):
		"convert a hex pubkey to an address"
		pubkey = bytes.fromhex(pubkeyhex)
		if self.mmtype.name == 'segwit':
			return self.proto.pubkey2segwitaddr( pubkey )
		else:
			return self.pubhash2addr( hash160(pubkey).hex() )

	def pubhex2redeem_script(self,pubkeyhex:'sstr'): # new
		"convert a hex pubkey to a Segwit P2SH-P2WPKH redeem script"
		assert self.mmtype.name == 'segwit','This command is meaningful only for --type=segwit'
		return self.proto.pubkey2redeem_script( bytes.fromhex(pubkeyhex) ).hex()

	def redeem_script2addr(self,redeem_scripthex:'sstr'): # new
		"convert a Segwit P2SH-P2WPKH redeem script to an address"
		assert self.mmtype.name == 'segwit', 'This command is meaningful only for --type=segwit'
		assert redeem_scripthex[:4] == '0014', f'{redeem_scripthex!r}: invalid redeem script'
		assert len(redeem_scripthex) == 44, f'{len(redeem_scripthex)//2} bytes: invalid redeem script length'
		return self.pubhash2addr( hash160(bytes.fromhex(redeem_scripthex)).hex() )

	def pubhash2addr(self,pubhashhex:'sstr'):
		"convert public key hash to address"
		pubhash = bytes.fromhex(pubhashhex)
		if self.mmtype.name == 'bech32':
			return self.proto.pubhash2bech32addr( pubhash )
		else:
			return self.proto.pubhash2addr( pubhash, self.mmtype.addr_fmt=='p2sh' )

	def addr2pubhash(self,addr:'sstr'):
		"convert coin address to public key hash"
		from ..tx import addr2pubhash
		return addr2pubhash( self.proto, CoinAddr(self.proto,addr) )

	def addr2scriptpubkey(self,addr:'sstr'):
		"convert coin address to scriptPubKey"
		from ..tx import addr2scriptPubKey
		return addr2scriptPubKey( self.proto, CoinAddr(self.proto,addr) )

	def scriptpubkey2addr(self,hexstr:'sstr'):
		"convert scriptPubKey to coin address"
		from ..tx import scriptPubKey2addr
		return scriptPubKey2addr( self.proto, hexstr )[0]
