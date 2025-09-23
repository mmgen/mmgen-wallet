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
tool.coin: Cryptocoin routines for the 'mmgen-tool' utility
"""

from collections import namedtuple
generator_data = namedtuple('generator_data', ['kg', 'ag'])

from .common import tool_cmd_base

from ..key import PrivKey
from ..addr import CoinAddr, MMGenAddrType
from ..addrgen import KeyGenerator, AddrGenerator

class tool_cmd(tool_cmd_base):
	"""
	cryptocoin key/address utilities

	May require use of the '--coin', '--type' and/or '--testnet' options

	Examples:
	  mmgen-tool --coin=ltc --type=bech32 wif2addr <wif key>
	  mmgen-tool --coin=zec --type=zcash_z randpair
	"""

	need_proto = True
	need_addrtype = True

	def _init_generators(self):
		return generator_data(
			kg = KeyGenerator(self.cfg, self.proto, self.mmtype.pubkey_type),
			ag = AddrGenerator(self.cfg, self.proto, self.mmtype),
		)

	def randwif(self):
		"generate a random private key in WIF format"
		from ..crypto import Crypto
		return PrivKey(
			self.proto,
			Crypto(self.cfg).get_random(32),
			pubkey_type = self.mmtype.pubkey_type,
			compressed  = self.mmtype.compressed).wif

	def privhex2pair(self, privhex: 'sstr'):
		"generate a wifkey/address pair from the provided hexadecimal key"
		gd = self._init_generators()
		privkey = PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			pubkey_type = self.mmtype.pubkey_type,
			compressed  = self.mmtype.compressed)
		return (
			privkey.wif,
			gd.ag.to_addr(gd.kg.gen_data(privkey)))

	def randpair(self):
		"generate a random wifkey/address pair"
		from ..crypto import Crypto
		return self.privhex2pair(Crypto(self.cfg).get_random(32).hex())

	def wif2hex(self, wifkey: 'sstr'):
		"convert a private key from WIF to hexadecimal format"
		return PrivKey(
			self.proto,
			wif = wifkey).hex()

	def hex2wif(self, privhex: 'sstr'):
		"convert a private key from hexadecimal to WIF format"
		return PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			pubkey_type = self.mmtype.pubkey_type,
			compressed  = self.mmtype.compressed).wif

	def wif2addr(self, wifkey: 'sstr'):
		"generate a coin address from a key in WIF format"
		gd = self._init_generators()
		privkey = PrivKey(
			self.proto,
			wif = wifkey)
		return gd.ag.to_addr(gd.kg.gen_data(privkey))

	def wif2redeem_script(self, wifkey: 'sstr'): # new
		"convert a WIF private key to a Segwit P2SH-P2WPKH redeem script"
		assert self.mmtype.name == 'segwit', 'This command is meaningful only for --type=segwit'
		gd = self._init_generators()
		privkey = PrivKey(
			self.proto,
			wif = wifkey)
		return gd.ag.to_segwit_redeem_script(gd.kg.gen_data(privkey))

	def wif2segwit_pair(self, wifkey: 'sstr'):
		"generate a Segwit P2SH-P2WPKH redeem script and address from a WIF private key"
		assert self.mmtype.name == 'segwit', 'This command is meaningful only for --type=segwit'
		gd = self._init_generators()
		data = gd.kg.gen_data(PrivKey(
			self.proto,
			wif = wifkey))
		return (
			gd.ag.to_segwit_redeem_script(data),
			gd.ag.to_addr(data))

	def _privhex2out(self, privhex: 'sstr', *, output_pubhex=False):
		gd = self._init_generators()
		pk = PrivKey(
			self.proto,
			bytes.fromhex(privhex),
			compressed  = self.mmtype.compressed,
			pubkey_type = self.mmtype.pubkey_type)
		data = gd.kg.gen_data(pk)
		return data.pubkey.hex() if output_pubhex else gd.ag.to_addr(data)

	def privhex2addr(self, privhex: 'sstr'):
		"generate a coin address from raw hexadecimal private key data"
		return self._privhex2out(privhex)

	def privhex2pubhex(self, privhex: 'sstr'): # new
		"generate a hexadecimal public key from raw hexadecimal private key data"
		return self._privhex2out(privhex, output_pubhex=True)

	def pubhex2addr(self, pubkeyhex: 'sstr'):
		"convert a hexadecimal pubkey to an address"
		if self.proto.base_proto == 'Ethereum' and len(pubkeyhex) == 128: # support raw ETH pubkeys
			pubkeyhex = '04' + pubkeyhex
		from ..keygen import keygen_public_data
		ag = AddrGenerator(self.cfg, self.proto, self.mmtype)
		return ag.to_addr(keygen_public_data(
			pubkey        = bytes.fromhex(pubkeyhex),
			viewkey_bytes = None,
			pubkey_type   = self.mmtype.pubkey_type,
			compressed    = self.mmtype.compressed,
		))

	def pubhex2redeem_script(self, pubkeyhex: 'sstr'): # new
		"convert a hexadecimal pubkey to a Segwit P2SH-P2WPKH redeem script"
		assert self.mmtype.name == 'segwit', 'This command is meaningful only for --type=segwit'
		from ..proto.btc.common import hash160
		return self.proto.pubhash2redeem_script(hash160(bytes.fromhex(pubkeyhex))).hex()

	def redeem_script2addr(self, redeem_script_hex: 'sstr'): # new
		"convert a Segwit P2SH-P2WPKH redeem script to an address"
		assert self.mmtype.name == 'segwit', 'This command is meaningful only for --type=segwit'
		assert redeem_script_hex[:4] == '0014', f'{redeem_script_hex!r}: invalid redeem script'
		assert len(redeem_script_hex) == 44, f'{len(redeem_script_hex)//2} bytes: invalid redeem script length'
		from ..proto.btc.common import hash160
		return self.proto.pubhash2addr(hash160(bytes.fromhex(redeem_script_hex)), 'p2sh')

	def pubhash2addr(self, pubhashhex: 'sstr'):
		"convert public key hash to address"
		pubhash = bytes.fromhex(pubhashhex)
		match self.mmtype.name:
			case 'segwit':
				return self.proto.pubhash2segwitaddr(pubhash)
			case 'bech32':
				return self.proto.pubhash2bech32addr(pubhash)
			case 'bech32x':
				return self.proto.encode_addr_bech32x(pubhash)
			case _:
				return self.proto.pubhash2addr(pubhash, self.mmtype.addr_fmt)

	def addr2pubhash(self, addr: 'sstr'):
		"convert coin address to public key hash"
		ap = self.proto.decode_addr(addr)
		assert ap, f'coin address {addr!r} could not be parsed'
		if ap.fmt not in MMGenAddrType.pkh_fmts:
			from ..util import die
			die(2, f'{ap.fmt} addresses cannot be converted to pubhash')
		return ap.bytes.hex()

	def addr2scriptpubkey(self, addr: 'sstr'):
		"convert coin address to scriptPubKey"
		from ..proto.btc.tx.base import addr2scriptPubKey
		return addr2scriptPubKey(self.proto, CoinAddr(self.proto, addr))

	def scriptpubkey2addr(self, hexstr: 'sstr'):
		"convert scriptPubKey to coin address"
		from ..proto.btc.tx.base import decodeScriptPubKey
		return decodeScriptPubKey(self.proto, hexstr).addr

	def eth_checksummed_addr(self, addr: 'sstr'):
		"create a checksummed Ethereum address"
		from ..protocol import init_proto
		return init_proto(self.cfg, 'eth').checksummed_addr(addr)
