#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
mmgen-addrgen: Generate a series or range of addresses from an MMGen
               deterministic wallet
"""

from mmgen.common import *
from mmgen.crypto import *
from mmgen.addr import *
from mmgen.seed import Wallet

if g.prog_name == 'mmgen-keygen':
	gen_what = 'keys'
	gen_desc = 'secret keys'
	opt_filter = None
	note_addrkey = 'By default, both addresses and secret keys are generated.\n\n'
else:
	gen_what = 'addresses'
	gen_desc = 'addresses'
	opt_filter = 'hbcdeEiHOkKlpzPqrStUv-'
	note_addrkey = ''

opts_data = {
	'sets': [('print_checksum',True,'quiet',True)],
	'text': {
		'desc': """
                 Generate a range or list of {desc} from an {pnm} wallet,
                 mnemonic, seed or brainwallet
			  """.format(desc=gen_desc,pnm=g.proj_name),
		'usage':'[opts] [seed source] <index list or range(s)>',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-A, --no-addresses    Print only secret keys, no addresses
-c, --print-checksum  Print address list checksum and exit
-d, --outdir=      d  Output files to directory 'd' instead of working dir
-e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
-E, --use-old-ed25519 Use original (and slow) ed25519 module for Monero
                      address generation instead of ed25519ll_djbec
-i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-O, --old-incog-fmt   Specify old-format incognito input
-k, --use-internal-keccak-module Force use of the internal keccak module
-K, --key-generator=m Use method 'm' for public key generation
                      Options: {kgs} (default: {kg})
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
-S, --stdout          Print {what} to stdout
-t, --type=t          Choose address type. Options: see ADDRESS TYPES below
                      (default: {dmat})
-U, --subwallet=   U  Generate {what} for subwallet 'U' (see SUBWALLETS
                      below)
-v, --verbose         Produce more verbose output
-x, --b16             Print secret keys in hexadecimal too
""",
	'notes': """

                           NOTES FOR THIS COMMAND

Address indexes are given as a comma-separated list and/or hyphen-separated
range(s).

{n_addrkey}If available, the libsecp256k1 library will be used for address generation.

ADDRESS TYPES:
  {n_at}


                      NOTES FOR ALL GENERATOR COMMANDS

{n_sw}{n_pw}{n_bw}

FMT CODES:

  {n_fmt}
"""
	},
	'code': {
		'options': lambda s: s.format(
			seed_lens=', '.join(map(str,g.seed_lens)),
			dmat="'{}' or '{}'".format(g.proto.dfl_mmtype,MMGenAddrType.mmtypes[g.proto.dfl_mmtype].name),
			kgs=' '.join(['{}:{}'.format(n,k) for n,k in enumerate(g.key_generators,1)]),
			kg=g.key_generator,
			pnm=g.proj_name,
			what=gen_what,
			g=g,
		),
		'notes': lambda s: s.format(
			n_addrkey=note_addrkey,
			n_sw=help_notes('subwallet')+'\n\n',
			n_pw=help_notes('passwd')+'\n\n',
			n_bw=help_notes('brainwallet'),
			n_fmt='\n  '.join(Wallet.format_fmt_codes().splitlines()),
			n_at='\n  '.join(["'{}','{:<12} - {}".format(
				k,v.name+"'",v.desc) for k,v in MMGenAddrType.mmtypes.items()])
		)
	}
}

cmd_args = opts.init(opts_data,add_opts=['b16'],opt_filter=opt_filter)

errmsg = "'{}': invalid parameter for --type option".format(opt.type)
addr_type = MMGenAddrType(opt.type or g.proto.dfl_mmtype,errmsg=errmsg)

if len(cmd_args) < 1: opts.usage()

if opt.use_old_ed25519:
	msg('Using old (slow) ed25519 module by user request')

idxs = AddrIdxList(fmt_str=cmd_args.pop())

sf = get_seed_file(cmd_args,1)

do_license_msg()

ss = Wallet(sf)

ss_seed = ss.seed if opt.subwallet is None else ss.seed.subseed(opt.subwallet,print_msg=True)

i = (gen_what=='addresses') or bool(opt.no_addresses)*2
al = (KeyAddrList,AddrList,KeyList)[i](seed=ss_seed,addr_idxs=idxs,mmtype=addr_type)
al.format()

if al.gen_addrs and opt.print_checksum:
	Die(0,al.checksum)

if al.gen_keys and keypress_confirm('Encrypt key list?'):
	al.encrypt()
	al.write_to_file(binary=True,desc='encrypted '+al.file_desc)
else:
	al.write_to_file()
