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
tool.util: Utility commands for the 'mmgen-tool' utility
"""

import sys, os

from .common import tool_cmd_base

class tool_cmd(tool_cmd_base):
	"general string conversion and hashing utilities"

	# mmgen.util2.bytespec_map
	def bytespec(self, dd_style_byte_specifier: str):
		"""
		convert a byte specifier such as ‘4GB’ into an integer

		Valid specifiers:

		  c  = 1
		  w  = 2
		  b  = 512
		  kB = 1000
		  K  = 1024
		  MB = 1000000
		  M  = 1048576
		  GB = 1000000000
		  G  = 1073741824
		  TB = 1000000000000
		  T  = 1099511627776
		  PB = 1000000000000000
		  P  = 1125899906842624
		  EB = 1000000000000000000
		  E  = 1152921504606846976
		"""
		from ..util2 import parse_bytespec
		return parse_bytespec(dd_style_byte_specifier)

	# mmgen.util2.bytespec_map
	def to_bytespec(self,
			n: int,
			dd_style_byte_specifier: str,
			*,
			fmt:       'width and precision of output' = '0.2',
			print_sym: 'print the specifier after the numerical value' = True,
			strip:     'strip trailing zeroes' = False,
			add_space: 'with print_sym, add space between value and specifier' = False):
		"""
		convert an integer to a byte specifier such as ‘4GB’

		Supported specifiers:

		  c  = 1
		  w  = 2
		  b  = 512
		  kB = 1000
		  K  = 1024
		  MB = 1000000
		  M  = 1048576
		  GB = 1000000000
		  G  = 1073741824
		  TB = 1000000000000
		  T  = 1099511627776
		  PB = 1000000000000000
		  P  = 1125899906842624
		  EB = 1000000000000000000
		  E  = 1152921504606846976
		"""
		from ..util2 import int2bytespec
		return int2bytespec(
			n,
			dd_style_byte_specifier,
			fmt,
			print_sym = print_sym,
			strip     = strip,
			add_space = add_space)

	def randhex(self,
			nbytes: 'number of bytes to output' = 32):
		"print 'n' bytes (default 32) of random data in hex format"
		from ..crypto import Crypto
		return Crypto(self.cfg).get_random(nbytes).hex()

	def hexreverse(self, hexstr: 'sstr'):
		"reverse bytes of a hexadecimal string"
		return bytes.fromhex(hexstr.strip())[::-1].hex()

	def hexlify(self, infile: str):
		"convert bytes in file to hexadecimal (use '-' for stdin)"
		from ..fileutil import get_data_from_file
		data = get_data_from_file(self.cfg, infile, dash=True, quiet=True, binary=True)
		return data.hex()

	def unhexlify(self, hexstr: 'sstr'):
		"convert a hexadecimal string to bytes (warning: outputs binary data)"
		return bytes.fromhex(hexstr)

	def hexdump(self,
			infile: str,
			*,
			cols:      'number of columns in output' = 8,
			line_nums: "format for line numbers (valid choices: 'hex','dec')" = 'hex'):
		"create hexdump of data from file (use '-' for stdin)"
		from ..fileutil import get_data_from_file
		from ..util2 import pretty_hexdump
		data = get_data_from_file(self.cfg, infile, dash=True, quiet=True, binary=True)
		return pretty_hexdump(data, cols=cols, line_nums=line_nums).rstrip()

	def unhexdump(self, infile: str):
		"decode hexdump from file (use '-' for stdin) (warning: outputs binary data)"
		if sys.platform == 'win32':
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
		from ..fileutil import get_data_from_file
		from ..util2 import decode_pretty_hexdump
		hexdata = get_data_from_file(self.cfg, infile, dash=True, quiet=True)
		return decode_pretty_hexdump(hexdata)

	def hash160(self, hexstr: 'sstr'):
		"compute ripemd160(sha256(data)) (convert hex pubkey to hex addr)"
		from ..proto.btc.common import hash160
		return hash160(bytes.fromhex(hexstr)).hex()

	# TODO: handle stdin
	def hash256(self,
			data: str,
			*,
			file_input: 'first arg is the name of a file containing the data' = False,
			hex_input:  'first arg is a hexadecimal string' = False):
		"compute sha256(sha256(data)) (double sha256)"
		from hashlib import sha256
		if file_input:
			from ..fileutil import get_data_from_file
			b = get_data_from_file(self.cfg, data, binary=True)
		elif hex_input:
			from ..util2 import decode_pretty_hexdump
			b = decode_pretty_hexdump(data)
		else:
			b = data
		return sha256(sha256(b.encode()).digest()).hexdigest()

	def id6(self, infile: str):
		"generate 6-character MMGen ID for a file (use '-' for stdin)"
		from ..util import make_chksum_6
		from ..fileutil import get_data_from_file
		return make_chksum_6(
			get_data_from_file(self.cfg, infile, dash=True, quiet=True, binary=True))

	def str2id6(self, string: 'sstr'): # retain ignoring of space for backwards compat
		"generate 6-character MMGen ID for a string, ignoring spaces in string"
		from ..util import make_chksum_6
		return make_chksum_6(''.join(string.split()))

	def id8(self, infile: str):
		"generate 8-character MMGen ID for a file (use '-' for stdin)"
		from ..util import make_chksum_8
		from ..fileutil import get_data_from_file
		return make_chksum_8(
			get_data_from_file(self.cfg, infile, dash=True, quiet=True, binary=True))

	def randb58(self, *,
			nbytes: 'number of bytes to output' = 32,
			pad:    'pad output to this width' = 0):
		"generate random data (default: 32 bytes) and convert it to base 58"
		from ..baseconv import baseconv
		from ..crypto import Crypto
		return baseconv('b58').frombytes(Crypto(self.cfg).get_random(nbytes), pad=pad, tostr=True)

	def bytestob58(self, infile: str, *, pad: 'pad output to this width' = 0):
		"convert bytes to base 58 (supply data via STDIN)"
		from ..fileutil import get_data_from_file
		from ..baseconv import baseconv
		data = get_data_from_file(self.cfg, infile, dash=True, quiet=True, binary=True)
		return baseconv('b58').frombytes(data, pad=pad, tostr=True)

	def b58tobytes(self, b58_str: 'sstr', *, pad: 'pad output to this width' = 0):
		"convert a base 58 string to bytes (warning: outputs binary data)"
		from ..baseconv import baseconv
		return baseconv('b58').tobytes(b58_str, pad=pad)

	def hextob58(self, hexstr: 'sstr', *, pad: 'pad output to this width' = 0):
		"convert a hexadecimal string to base 58"
		from ..baseconv import baseconv
		return baseconv('b58').fromhex(hexstr, pad=pad, tostr=True)

	def b58tohex(self, b58_str: 'sstr', *, pad: 'pad output to this width' = 0):
		"convert a base 58 string to hexadecimal"
		from ..baseconv import baseconv
		return baseconv('b58').tohex(b58_str, pad=pad)

	def hextob58chk(self, hexstr: 'sstr'):
		"convert a hexadecimal string to base58-check encoding"
		from ..proto.btc.common import b58chk_encode
		return b58chk_encode(bytes.fromhex(hexstr))

	def b58chktohex(self, b58chk_str: 'sstr'):
		"convert a base58-check encoded string to hexadecimal"
		from ..proto.btc.common import b58chk_decode
		return b58chk_decode(b58chk_str).hex()

	def hextob32(self, hexstr: 'sstr', *, pad: 'pad output to this width' = 0):
		"convert a hexadecimal string to an MMGen-flavor base 32 string"
		from ..baseconv import baseconv
		return baseconv('b32').fromhex(hexstr, pad=pad, tostr=True)

	def b32tohex(self, b32_str: 'sstr', *, pad: 'pad output to this width' = 0):
		"convert an MMGen-flavor base 32 string to hexadecimal"
		from ..baseconv import baseconv
		return baseconv('b32').tohex(b32_str.upper(), pad=pad)

	def hextob6d(self,
			hexstr: 'sstr',
			*,
			pad: 'pad output to this width' = 0,
			add_spaces: 'add a space after every 5th character' = True):
		"convert a hexadecimal string to die roll base6 (base6d)"
		from ..baseconv import baseconv
		from ..util2 import block_format
		ret = baseconv('b6d').fromhex(hexstr, pad=pad, tostr=True)
		return block_format(ret, gw=5, cols=None).strip() if add_spaces else ret

	def b6dtohex(self, b6d_str: 'sstr', *, pad: 'pad output to this width' = 0):
		"convert a die roll base6 (base6d) string to hexadecimal"
		from ..baseconv import baseconv
		from ..util import remove_whitespace
		return baseconv('b6d').tohex(remove_whitespace(b6d_str), pad=pad)
