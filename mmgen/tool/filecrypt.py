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
tool.filecrypt: File encryption/decryption routines for the 'mmgen-tool' utility
"""

import os

from .common import tool_cmd_base
from ..crypto import Crypto
from ..fileutil import get_data_from_file, write_data_to_file

class tool_cmd(tool_cmd_base):
	"""
	file encryption and decryption

	MMGen encryption suite:
	* Key: Scrypt (user-configurable hash parameters, 32-byte salt)
	* Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
	* The encrypted file is indistinguishable from random data
	"""
	def encrypt(self, infile: str, outfile='', hash_preset=''):
		"encrypt a file"
		data = get_data_from_file(self.cfg, infile, 'data for encryption', binary=True)
		enc_d = Crypto(self.cfg).mmgen_encrypt(data, 'data', hash_preset)
		if not outfile:
			outfile = f'{os.path.basename(infile)}.{Crypto.mmenc_ext}'
		write_data_to_file(self.cfg, outfile, enc_d, 'encrypted data', binary=True)
		return True

	def decrypt(self, infile: str, outfile='', hash_preset=''):
		"decrypt a file"
		enc_d = get_data_from_file(self.cfg, infile, 'encrypted data', binary=True)
		while True:
			dec_d = Crypto(self.cfg).mmgen_decrypt(enc_d, 'data', hash_preset)
			if dec_d:
				break
			from ..util import msg
			msg('Trying again...')
		if not outfile:
			from ..util import remove_extension
			o = os.path.basename(infile)
			outfile = remove_extension(o, Crypto.mmenc_ext)
			if outfile == o:
				outfile += '.dec'
		write_data_to_file(self.cfg, outfile, dec_d, 'decrypted data', binary=True)
		return True
