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
mmgen-passgen: Generate a series or range of passwords from an MMGen
               deterministic wallet
"""

import sys, time

from .cfg import gc, Config
from .addrlist import AddrIdxList
from .passwdlist import PasswordList
from .wallet import Wallet
from .obj import MMGenPWIDString
from .ui import keypress_confirm

pwi = PasswordList.pw_info

opts_data = {
	'sets': [('print_checksum', True, 'quiet', True)],
	'text': {
		'desc': f"""
                 Generate a range or list of passwords from an {gc.proj_name} wallet,
                 mnemonic, seed or brainwallet for the given ID string
		 """,
		'usage':'[opts] [seed source] <ID string> <index list or range(s)>',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long (global) options
-d, --outdir=      d  Output files to directory 'd' instead of working dir
-e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
-f, --passwd-fmt=  f  Generate passwords of format 'f'.  Default: {pl.dfl_pw_fmt}.
                      See PASSWORD FORMATS below
-i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-O, --old-incog-fmt   Specify old-format incognito input
-L, --passwd-len=  l  Specify length of generated passwords.  For defaults,
                      see PASSWORD FORMATS below.  An argument of 'h' will
                      generate passwords of half the default length.
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {dsl}-bit) seed lengths.
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{gc.dfl_hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={cfg.min_urandchars}, max={cfg.max_urandchars}, default={cfg.usr_randchars})
-S, --stdout          Print passwords to stdout
-v, --verbose         Produce more verbose output
""",
	'notes': """

                           NOTES FOR THIS COMMAND

ID string must be a valid UTF-8 string not longer than {ml} characters and
not containing the symbols '{fs}'.

Password indexes are given as a comma-separated list and/or hyphen-separated
range(s).

Changing either the password format (base32,base58) or length alters the seed
and thus generates a completely new set of passwords.

PASSWORD FORMATS:

  {pfi}

EXAMPLES:

  Generate ten base58 passwords of length {i58.dfl_len} for Alice's email account:
  {gc.prog_name} alice@nowhere.com 1-10

  Generate ten base58 passwords of length 16 for Alice's email account:
  {gc.prog_name} --passwd-len=16 alice@nowhere.com 1-10

  Generate ten base32 passwords of length {i32.dfl_len} for Alice's email account:
  {gc.prog_name} --passwd-fmt=b32 alice@nowhere.com 1-10

  Generate three BIP39 mnemonic seed phrases of length {i39.dfl_len} for Alice's
  Trezor device:
  {gc.prog_name} --passwd-fmt=bip39 mytrezor 1-3

  All passwords are cryptographically unlinkable with each other, including
  passwords with the same format but different length, so Alice needn't worry
  about inadvertent reuse of private data.


                      NOTES FOR ALL GENERATOR COMMANDS

{n_pw}

{n_bw}

{n_fmt}
"""
	},
	'code': {
		'options': lambda cfg, help_notes, s: s.format(
			cfg   = cfg,
			dsl   = help_notes('dfl_seed_len'),
			pl    = PasswordList,
			gc    = gc,
		),
		'notes': lambda cfg, help_notes, s: s.format(
			cfg   = cfg,
			i58   = pwi['b58'],
			i32   = pwi['b32'],
			i39   = pwi['bip39'],
			ml    = MMGenPWIDString.max_len,
			fs    = '", "'.join(MMGenPWIDString.forbidden),
			n_pw  = help_notes('passwd'),
			n_bw  = help_notes('brainwallet'),
			pfi   = help_notes('password_formats'),
			n_fmt = help_notes('fmt_codes'),
			gc    = gc,
		)
	}
}

cfg = Config(opts_data=opts_data)

if len(cfg._args) < 2:
	cfg._usage()

pw_idxs = AddrIdxList(fmt_str=cfg._args.pop())

pw_id_str = cfg._args.pop()

from .fileutil import get_seed_file
sf = get_seed_file(cfg, nargs=1)

pw_fmt = cfg.passwd_fmt or PasswordList.dfl_pw_fmt
pw_len = pwi[pw_fmt].dfl_len // 2 if cfg.passwd_len in ('h', 'H') else cfg.passwd_len

from .protocol import init_proto
proto = init_proto(cfg, 'btc') # TODO: get rid of dummy proto

PasswordList(
	cfg             = cfg,
	proto           = proto,
	pw_id_str       = pw_id_str,
	pw_len          = pw_len,
	pw_fmt          = pw_fmt,
	chk_params_only = True)

from .ui import do_license_msg
do_license_msg(cfg)

ss = Wallet(cfg, fn=sf)

al = PasswordList(
	cfg       = cfg,
	proto     = proto,
	seed      = ss.seed,
	pw_idxs   = pw_idxs,
	pw_id_str = pw_id_str,
	pw_len    = pw_len,
	pw_fmt    = pw_fmt)

af = al.file

af.format()

if keypress_confirm(cfg, 'Encrypt password list?'):
	af.encrypt()
	af.write(binary=True, desc='encrypted password list')
else:
	if cfg.test_suite_popen_spawn and sys.platform == 'win32':
		time.sleep(0.1)
	af.write(desc='password list')
