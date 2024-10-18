#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
tool.mnemonic: Mnemonic routines for the 'mmgen-tool' utility
"""

from collections import namedtuple

from .common import tool_cmd_base, options_annot_str

from ..baseconv import baseconv
from ..xmrseed import xmrseed
from ..bip39 import bip39

dfl_mnemonic_fmt = 'mmgen'
mft = namedtuple('mnemonic_format', ['fmt', 'pad', 'conv_cls'])
mnemonic_fmts = {
	'mmgen':   mft('words',  'seed', baseconv),
	'bip39':   mft('bip39',   None,  bip39),
	'xmrseed': mft('xmrseed', None,  xmrseed),
}
mn_opts_disp = 'seed phrase format ' + options_annot_str(mnemonic_fmts)

class tool_cmd(tool_cmd_base):
	"""
	seed phrase utilities

	Supported seed phrase formats: 'mmgen' (default), 'bip39', 'xmrseed'

	IMPORTANT NOTE: MMGen Wallet’s default seed phrase format uses the
	Electrum wordlist, however seed phrases are computed using a different
	algorithm and are NOT Electrum-compatible!

	BIP39 support is fully compatible with the standard, allowing users to
	import and export seed entropy from BIP39-compatible wallets.  However,
	users should be aware that BIP39 support does not imply BIP32 support!
	MMGen uses its own key derivation scheme differing from the one described
	by the BIP32 protocol.

	For Monero (‘xmrseed’) seed phrases, input data is reduced to a spendkey
	before conversion so that a canonical seed phrase is produced.  This is
	required because Monero seeds, unlike ordinary wallet seeds, are tied
	to a concrete key/address pair.  To manually generate a Monero spendkey,
	use the ‘hex2wif’ command.
	"""

	def _xmr_reduce(self, bytestr):
		from ..protocol import init_proto
		proto = init_proto(self.cfg, 'xmr')
		if len(bytestr) != proto.privkey_len:
			from ..util import die
			die(1, '{!r}: invalid bit length for Monero private key (must be {})'.format(
				len(bytestr*8),
				proto.privkey_len*8))
		return proto.preprocess_key(bytestr, None)

	def _do_random_mn(self, nbytes: int, fmt: str):
		assert nbytes in (16, 24, 32), 'nbytes must be 16, 24 or 32'
		from ..crypto import Crypto
		randbytes = Crypto(self.cfg).get_random(nbytes)
		if fmt == 'xmrseed':
			randbytes = self._xmr_reduce(randbytes)
		if self.cfg.verbose:
			from ..util import msg
			msg(f'Seed: {randbytes.hex()}')
		return self.hex2mn(randbytes.hex(), fmt=fmt)

	def mn_rand128(self, fmt:mn_opts_disp = dfl_mnemonic_fmt):
		"generate a random 128-bit mnemonic seed phrase"
		return self._do_random_mn(16, fmt)

	def mn_rand192(self, fmt:mn_opts_disp = dfl_mnemonic_fmt):
		"generate a random 192-bit mnemonic seed phrase"
		return self._do_random_mn(24, fmt)

	def mn_rand256(self, fmt:mn_opts_disp = dfl_mnemonic_fmt):
		"generate a random 256-bit mnemonic seed phrase"
		return self._do_random_mn(32, fmt)

	def hex2mn(self, hexstr: 'sstr', fmt:mn_opts_disp = dfl_mnemonic_fmt):
		"convert a 16, 24 or 32-byte hexadecimal string to a mnemonic seed phrase"
		if fmt == 'xmrseed':
			hexstr = self._xmr_reduce(bytes.fromhex(hexstr)).hex()
		f = mnemonic_fmts[fmt]
		return ' '.join(f.conv_cls(fmt).fromhex(hexstr, f.pad))

	def mn2hex(self, seed_mnemonic: 'sstr', fmt:mn_opts_disp = dfl_mnemonic_fmt):
		"convert a mnemonic seed phrase to a hexadecimal string"
		f = mnemonic_fmts[fmt]
		return f.conv_cls(fmt).tohex(seed_mnemonic.split(), f.pad)

	def mn2hex_interactive(self,
			fmt: mn_opts_disp = dfl_mnemonic_fmt,
			mn_len: 'length of seed phrase in words' = 24,
			print_mn: 'print the seed phrase after entry' = False):
		"convert an interactively supplied mnemonic seed phrase to a hexadecimal string"
		from ..mn_entry import mn_entry
		mn = mn_entry(self.cfg, fmt).get_mnemonic_from_user(25 if fmt == 'xmrseed' else mn_len, validate=False)
		if print_mn:
			from ..util import msg
			msg(mn)
		return self.mn2hex(seed_mnemonic=mn, fmt=fmt)

	def mn_stats(self, fmt:mn_opts_disp = dfl_mnemonic_fmt):
		"show stats for a mnemonic wordlist"
		return mnemonic_fmts[fmt].conv_cls(fmt).check_wordlist(self.cfg)

	def mn_printlist(self,
			fmt: mn_opts_disp = dfl_mnemonic_fmt,
			enum: 'enumerate the list' = False,
			pager: 'send output to pager' = False):
		"print a mnemonic wordlist"
		ret = mnemonic_fmts[fmt].conv_cls(fmt).get_wordlist()
		if enum:
			ret = [f'{n:>4} {e}' for n, e in enumerate(ret)]
		return '\n'.join(ret)
