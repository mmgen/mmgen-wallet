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
tool/util.py: Utility commands for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base

class tool_cmd(tool_cmd_base):
	"general string conversion and hashing utilities"

	def bytespec(self,dd_style_byte_specifier:str):
		"convert a byte specifier such as '1GB' into an integer"
		from ..util import parse_bytespec
		return parse_bytespec(dd_style_byte_specifier)

	def to_bytespec(self,
			n: int,
			dd_style_byte_specifier: str,
			fmt = '0.2',
			print_sym = True ):
		"convert an integer to a byte specifier such as '1GB'"
		from ..util import int2bytespec
		return int2bytespec( n, dd_style_byte_specifier, fmt, print_sym )

	def randhex(self,nbytes='32'):
		"print 'n' bytes (default 32) of random data in hex format"
		from ..crypto import get_random
		return get_random( int(nbytes) ).hex()

	def hexreverse(self,hexstr:'sstr'):
		"reverse bytes of a hexadecimal string"
		return bytes.fromhex( hexstr.strip() )[::-1].hex()

	def hexlify(self,infile:str):
		"convert bytes in file to hexadecimal (use '-' for stdin)"
		from ..fileutil import get_data_from_file
		data = get_data_from_file( infile, dash=True, quiet=True, binary=True )
		return data.hex()

	def unhexlify(self,hexstr:'sstr'):
		"convert hexadecimal value to bytes (warning: outputs binary data)"
		return bytes.fromhex(hexstr)

	def hexdump(self,infile:str,cols=8,line_nums='hex'):
		"create hexdump of data from file (use '-' for stdin)"
		from ..fileutil import get_data_from_file
		from ..util import pretty_hexdump
		data = get_data_from_file( infile, dash=True, quiet=True, binary=True )
		return pretty_hexdump( data, cols=cols, line_nums=line_nums ).rstrip()

	def unhexdump(self,infile:str):
		"decode hexdump from file (use '-' for stdin) (warning: outputs binary data)"
		from ..globalvars import g
		if g.platform == 'win':
			import msvcrt
			msvcrt.setmode( sys.stdout.fileno(), os.O_BINARY )
		from ..fileutil import get_data_from_file
		from ..util import decode_pretty_hexdump
		hexdata = get_data_from_file( infile, dash=True, quiet=True )
		return decode_pretty_hexdump(hexdata)

	def hash160(self,hexstr:'sstr'):
		"compute ripemd160(sha256(data)) (convert hex pubkey to hex addr)"
		from ..proto.common import hash160
		return hash160( bytes.fromhex(hexstr) ).hex()

	def hash256(self,string_or_bytes:str,file_input=False,hex_input=False): # TODO: handle stdin
		"compute sha256(sha256(data)) (double sha256)"
		from hashlib import sha256
		if file_input:
			from ..fileutil import get_data_from_file
			b = get_data_from_file( string_or_bytes, binary=True )
		elif hex_input:
			from ..util import decode_pretty_hexdump
			b = decode_pretty_hexdump(string_or_bytes)
		else:
			b = string_or_bytes
		return sha256(sha256(b.encode()).digest()).hexdigest()

	def id6(self,infile:str):
		"generate 6-character MMGen ID for a file (use '-' for stdin)"
		from ..util import make_chksum_6
		from ..fileutil import get_data_from_file
		return make_chksum_6(
			get_data_from_file( infile, dash=True, quiet=True, binary=True ))

	def str2id6(self,string:'sstr'): # retain ignoring of space for backwards compat
		"generate 6-character MMGen ID for a string, ignoring spaces"
		from ..util import make_chksum_6
		return make_chksum_6( ''.join(string.split()) )

	def id8(self,infile:str):
		"generate 8-character MMGen ID for a file (use '-' for stdin)"
		from ..util import make_chksum_8
		from ..fileutil import get_data_from_file
		return make_chksum_8(
			get_data_from_file( infile, dash=True, quiet=True, binary=True ))

	def randb58(self,nbytes=32,pad=0):
		"generate random data (default: 32 bytes) and convert it to base 58"
		from ..crypto import get_random
		from ..baseconv import baseconv
		return baseconv('b58').frombytes( get_random(nbytes), pad=pad, tostr=True )

	def bytestob58(self,infile:str,pad=0):
		"convert bytes to base 58 (supply data via STDIN)"
		from ..fileutil import get_data_from_file
		from ..baseconv import baseconv
		data = get_data_from_file( infile, dash=True, quiet=True, binary=True )
		return baseconv('b58').frombytes( data, pad=pad, tostr=True )

	def b58tobytes(self,b58num:'sstr',pad=0):
		"convert a base 58 number to bytes (warning: outputs binary data)"
		from ..baseconv import baseconv
		return baseconv('b58').tobytes( b58num, pad=pad )

	def hextob58(self,hexstr:'sstr',pad=0):
		"convert a hexadecimal number to base 58"
		from ..baseconv import baseconv
		return baseconv('b58').fromhex( hexstr, pad=pad, tostr=True )

	def b58tohex(self,b58num:'sstr',pad=0):
		"convert a base 58 number to hexadecimal"
		from ..baseconv import baseconv
		return baseconv('b58').tohex( b58num, pad=pad )

	def hextob58chk(self,hexstr:'sstr'):
		"convert a hexadecimal number to base58-check encoding"
		from ..proto.common import b58chk_encode
		return b58chk_encode( bytes.fromhex(hexstr) )

	def b58chktohex(self,b58chk_num:'sstr'):
		"convert a base58-check encoded number to hexadecimal"
		from ..proto.common import b58chk_decode
		return b58chk_decode(b58chk_num).hex()

	def hextob32(self,hexstr:'sstr',pad=0):
		"convert a hexadecimal number to MMGen's flavor of base 32"
		from ..baseconv import baseconv
		return baseconv('b32').fromhex( hexstr, pad, tostr=True )

	def b32tohex(self,b32num:'sstr',pad=0):
		"convert an MMGen-flavor base 32 number to hexadecimal"
		from ..baseconv import baseconv
		return baseconv('b32').tohex( b32num.upper(), pad )

	def hextob6d(self,hexstr:'sstr',pad=0,add_spaces=True):
		"convert a hexadecimal number to die roll base6 (base6d)"
		from ..baseconv import baseconv
		from ..util import block_format
		ret = baseconv('b6d').fromhex(hexstr,pad,tostr=True)
		return block_format( ret, gw=5, cols=None ).strip() if add_spaces else ret

	def b6dtohex(self,b6d_num:'sstr',pad=0):
		"convert a die roll base6 (base6d) number to hexadecimal"
		from ..baseconv import baseconv
		from ..util import remove_whitespace
		return baseconv('b6d').tohex( remove_whitespace(b6d_num), pad )
