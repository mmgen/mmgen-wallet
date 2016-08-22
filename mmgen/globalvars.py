#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
globalvars.py:  Constants and configuration options for the MMGen suite
"""

import sys,os

# Variables - these might be altered at runtime:

user_entropy   = ''
hash_preset    = '3'
usr_randchars  = 30
use_urandchars = False

from mmgen.obj import BTCAmt
tx_fee        = BTCAmt('0.0003')
tx_fee_adj    = 1.0
tx_confs      = 3

seed_len     = 256
http_timeout = 60

# Constants - these don't change at runtime

# os.getenv() returns None if environmental var is unset
debug                = os.getenv('MMGEN_DEBUG')
no_license           = os.getenv('MMGEN_NOLICENSE')
bogus_wallet_data    = os.getenv('MMGEN_BOGUS_WALLET_DATA')
disable_hold_protect = os.getenv('MMGEN_DISABLE_HOLD_PROTECT')
color = (False,True)[sys.stdout.isatty() and not os.getenv('MMGEN_DISABLE_COLOR')]

proj_name = 'MMGen'
prog_name = os.path.basename(sys.argv[0])
author    = 'Philemon'
email     = '<mmgen-py@yandex.com>'
Cdates    = '2013-2016'
version   = '0.8.6rc1'

required_opts = [
	'quiet','verbose','debug','outdir','echo_passphrase','passwd_file',
	'usr_randchars','stdout','show_hash_presets','label',
	'keep_passphrase','keep_hash_preset','brain_params','b16'
]
incompatible_opts = (
	('quiet','verbose'),
	('label','keep_label'),
	('tx_id', 'info'),
	('tx_id', 'terse_info'),
)

min_screen_width = 80

# Global value sets user opt
dfl_vars = 'seed_len','hash_preset','usr_randchars','debug','tx_confs','tx_fee_adj','tx_fee','key_generator'

keyconv_exec = 'keyconv'

mins_per_block   = 9
passwd_max_tries = 5

max_urandchars = 80
_x = os.getenv('MMGEN_MIN_URANDCHARS')
min_urandchars = int(_x) if _x and int(_x) else 10

seed_lens = 128,192,256
mn_lens = [i / 32 * 3 for i in seed_lens]

mmenc_ext      = 'mmenc'
salt_len       = 16
aesctr_iv_len  = 16
hincog_chk_len = 8

key_generators = 'python-ecdsa','keyconv','secp256k1'
key_generator = 3 # secp256k1 is default

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

for k in ('win','linux'):
	if sys.platform[:len(k)] == k: platform = k; break
else:
	sys.stderr.write("'%s': platform not supported by %s\n" % (sys.platform,proj_name))
	sys.exit(1)
