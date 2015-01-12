#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
config.py:  Constants and configuration options for the MMGen suite
"""

import sys, os

# Variables - these might be altered at runtime:

user_entropy   = ""
hash_preset    = '3'
usr_randchars  = 30
use_urandchars = False

# returns None if env var unset
debug                = os.getenv("MMGEN_DEBUG")
no_license           = os.getenv("MMGEN_NOLICENSE")
bogus_wallet_data    = os.getenv("MMGEN_BOGUS_WALLET_DATA")
disable_hold_protect = os.getenv("MMGEN_DISABLE_HOLD_PROTECT")

from decimal import Decimal
tx_fee        = Decimal("0.00005")
max_tx_fee    = Decimal("0.01")

seed_len     = 256
http_timeout = 30

# Constants - these don't change at runtime

proj_name = "MMGen"
prog_name = os.path.basename(sys.argv[0])
author    = "Philemon"
email     = "<mmgen-py@yandex.com>"
Cdates    = '2013-2015'
version   = '0.7.9'

required_opts = [ # list must contain "usr_randchars"
	"quiet","verbose","debug","outdir","echo_passphrase","passwd_file","usr_randchars"
]
min_screen_width = 80
max_tx_comment_len = 72

wallet_ext    = "mmdat"
seed_ext      = "mmseed"
mn_ext        = "mmwords"
brain_ext     = "mmbrain"
incog_ext     = "mmincog"
incog_hex_ext = "mmincox"

seedfile_exts = wallet_ext, seed_ext, mn_ext, brain_ext, incog_ext

rawtx_ext           = "raw"
sigtx_ext           = "sig"
addrfile_ext        = "addrs"
addrfile_chksum_ext = "chk"
keyfile_ext         = "keys"
keyaddrfile_ext     = "akeys"
mmenc_ext           = "mmenc"

default_wl    = "electrum"
#default_wl    = "tirosh"

# Global value sets user opt
dfl_vars = "seed_len","hash_preset","usr_randchars","debug"

seed_lens = 128,192,256

mn_lens = [i / 32 * 3 for i in seed_lens]

keyconv_exec = "keyconv"

mins_per_block   = 8.5
passwd_max_tries = 5

max_urandchars,min_urandchars = 80,10

salt_len      = 16
aesctr_iv_len = 16

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
max_wallet_label_len = 48

#addr_label_punc = ".","_",",","-"," ","(",")"
#addr_label_symbols = tuple(ascii_letters + digits) + addr_label_punc
#wallet_label_punc = addr_label_punc
