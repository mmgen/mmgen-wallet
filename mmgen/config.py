#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013 by philemon <mmgen-py@yandex.com>
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
config.py:  Constants and configuration options for the mmgen suite
"""
quiet,verbose = False,False
min_screen_width = 80

from decimal import Decimal
tx_fee        = Decimal("0.001")
max_tx_fee    = Decimal("0.1")

proj_name     = "mmgen"
proj_name_cap = "MMGen"

wallet_ext    = "mmdat"
seed_ext      = "mmseed"
mn_ext        = "mmwords"
brain_ext     = "mmbrain"
incog_ext     = "mmincog"

seedfile_exts = wallet_ext, seed_ext, mn_ext, brain_ext, incog_ext

addrfile_ext = "addrs"
keyfile_ext  = "keys"

default_wl    = "electrum"
#default_wl    = "tirosh"

cl_override_vars = 'seed_len','hash_preset','usr_randlen'

seed_lens = 128,192,256
seed_len  = 256

mnemonic_lens = [i / 32 * 3 for i in seed_lens]

http_timeout = 30

keyconv_exec = "keyconv"

from os import getenv
debug      = True if getenv("MMGEN_DEBUG") else False
no_license = True if getenv("MMGEN_NOLICENSE") else False

mins_per_block = 8.5
passwd_max_tries = 5
max_randlen,min_randlen = 80,5
usr_randlen = 20
salt_len    = 16
aesctr_iv_len  = 16

hash_preset = '3'
hash_presets = {
#   Scrypt params:
#   ID    N   p  r
# N is a power of two
	'1': [12, 8, 1],
	'2': [13, 8, 4],
	'3': [14, 8, 8],
	'4': [15, 8, 12],
	'5': [16, 8, 16],
	'6': [17, 8, 20],
	'7': [18, 8, 24],
}

mmgen_idx_max_digits = 7

from string import ascii_letters, digits

addr_label_symbols = tuple([chr(i) for i in range(0x20,0x7f)])
max_addr_label_len = 32

wallet_label_symbols = addr_label_symbols
max_wallet_label_len = 32

#addr_label_punc = ".","_",",","-"," ","(",")"
#addr_label_symbols = tuple(ascii_letters + digits) + addr_label_punc
#wallet_label_punc = addr_label_punc
