#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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

from mmgen.common import *
from mmgen.crypto import *
from mmgen.addr import PasswordList,AddrIdxList
from mmgen.seed import SeedSource
from mmgen.obj import MMGenPWIDString

dfl_len = {
	'b58': PasswordList.pw_info['b58']['dfl_len'],
	'b32': PasswordList.pw_info['b32']['dfl_len'],
	'hex': PasswordList.pw_info['hex']['dfl_len']
}

opts_data = lambda: {
	'sets': [('print_checksum',True,'quiet',True)],
	'desc': """Generate a range or list of passwords from an {pnm} wallet,
                  mnemonic, seed or brainwallet for the given ID string""".format(pnm=g.proj_name),
	'usage':'[opts] [seed source] <ID string> <index list or range(s)>',
	'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-b, --base32          Generate passwords in Base32 format instead of Base58
-x, --hex             Generate passwords in raw hex format instead of Base58
-d, --outdir=      d  Output files to directory 'd' instead of working dir
-e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
-i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-O, --old-incog-fmt   Specify old-format incognito input
-L, --passwd-len=  l  Specify length of generated passwords
                      (default: {d58} chars [base58], {d32} chars [base32],
                      {dhex} chars [hex]).  An argument of 'h' will generate
                      passwords of half the default length.
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {g.seed_len}-bit) seed lengths
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={g.min_urandchars}, max={g.max_urandchars}, default={g.usr_randchars})
-S, --stdout          Print passwords to stdout
-v, --verbose         Produce more verbose output
""".format(
	seed_lens=', '.join(map(str,g.seed_lens)),
	g=g,pnm=g.proj_name,d58=dfl_len['b58'],d32=dfl_len['b32'],dhex=dfl_len['hex'],
	kgs=' '.join(['{}:{}'.format(n,k) for n,k in enumerate(g.key_generators,1)])
),
	'notes': u"""

                           NOTES FOR THIS COMMAND

ID string must be a valid UTF-8 string not longer than {ml} characters and
not containing the symbols '{fs}'.

Password indexes are given as a comma-separated list and/or hyphen-separated
range(s).

Changing either the password format (base32,base58) or length alters the seed
and thus generates a completely new set of passwords.

EXAMPLE:
  Generate ten base58 passwords of length {d58} for Alice's email account:
  {g.prog_name} alice@nowhere.com 1-10

  Generate ten base58 passwords of length 16 for Alice's email account:
  {g.prog_name} -L16 alice@nowhere.com 1-10

  Generate ten base32 passwords of length {d32} for Alice's email account:
  {g.prog_name} -b alice@nowhere.com 1-10

  The three sets of passwords are completely unrelated to each other, so
  Alice doesn't need to worry about password reuse.


                      NOTES FOR ALL GENERATOR COMMANDS

{n_pw}

{n_bw}

FMT CODES:
  {n_fmt}
""".format(
		o=opts,g=g,d58=dfl_len['b58'],d32=dfl_len['b32'],
		ml=MMGenPWIDString.max_len,
		fs="', '".join(MMGenPWIDString.forbidden),
		n_pw=help_notes('passwd'),
		n_bw=help_notes('brainwallet'),
		n_fmt='\n  '.join(SeedSource.format_fmt_codes().splitlines())
	)
}

cmd_args = opts.init(opts_data,add_opts=['b16'])

if len(cmd_args) < 2: opts.usage()

pw_idxs = AddrIdxList(fmt_str=cmd_args.pop())

pw_id_str = cmd_args.pop()

sf = get_seed_file(cmd_args,1)

pw_fmt = ('b58','b32','hex')[bool(opt.base32)+2*bool(opt.hex)]

pw_len = (opt.passwd_len,dfl_len[pw_fmt]/2)[opt.passwd_len in ('h','H')]

PasswordList(pw_id_str=pw_id_str,pw_len=pw_len,pw_fmt=pw_fmt,chk_params_only=True)
do_license_msg()

ss = SeedSource(sf)

al = PasswordList(seed=ss.seed,pw_idxs=pw_idxs,pw_id_str=pw_id_str,pw_len=pw_len,pw_fmt=pw_fmt)

al.format()

if keypress_confirm('Encrypt password list?'):
	al.encrypt(desc='password list')
	al.write_to_file(binary=True,desc='encrypted password list')
else:
	al.write_to_file(desc='password list')
