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
proj_name     = "mmgen"
seed_ext      = "mmseed"
default_wl    = "electrum"
#default_wl    = "tirosh"

seed_lens = 128,192,256
seed_len  = 256

mnemonic_lens = [i / 32 * 3 for i in seed_lens]

from os import getenv
debug = True if getenv("MMGEN_DEBUG") else False

mins_per_block = 9
passwd_max_tries = 5
max_randlen,min_randlen = 80,5
usr_randlen = 20
salt_len    = 16

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
}
