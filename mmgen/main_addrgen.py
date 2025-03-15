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
mmgen-addrgen: Generate a series or range of addresses from an MMGen
               deterministic wallet
"""

from . import addrlist
from .cfg import gc, Config
from .addr import MMGenAddrType
from .wallet import Wallet

if gc.prog_name == 'mmgen-keygen':
	gen_what = 'keys'
	gen_clsname = 'KeyAddrList'
	gen_desc = 'secret keys'
	filter_codes = ['-', 'k']
	note_addrkey = 'By default, both addresses and secret keys are generated.\n\n'
else:
	gen_what = 'addresses'
	gen_clsname = 'AddrList'
	gen_desc = 'addresses'
	filter_codes = ['-']
	note_addrkey = ''

opts_data = {
	'filter_codes': filter_codes,
	'sets': [('print_checksum', True, 'quiet', True)],
	'text': {
		'desc': f"""
                 Generate a range or list of {gen_desc} from an {gc.proj_name} wallet,
                 mnemonic, seed or brainwallet
			  """,
		'usage':'[opts] [seed source] <index list or range(s)>',
		'options': """
			-- -h, --help            Print this help message
			-- --, --longhelp        Print help message for long (global) options
			-k -A, --no-addresses    Print only secret keys, no addresses
			-- -c, --print-checksum  Print address list checksum and exit
			-- -d, --outdir=      d  Output files to directory 'd' instead of working dir
			-- -e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
			-- -i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
			-- -H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
			+                        'f' at offset 'o' (comma-separated)
			-- -O, --old-incog-fmt   Specify old-format incognito input
			-- -k, --use-internal-keccak-module Force use of the internal keccak module
			-- -K, --keygen-backend=n Use backend 'n' for public key generation.  Options
			+                        for {coin_id}: {kgs}
			-- -l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
			+                        is required only for brainwallet and incognito inputs
			+                        with non-standard (< {dsl}-bit) seed lengths.
			-- -p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
			+                        for password hashing (default: '{gc.dfl_hash_preset}')
			-- -z, --show-hash-presets Show information on available hash presets
			-- -P, --passwd-file= f  Get wallet passphrase from file 'f'
			-- -q, --quiet           Produce quieter output; suppress some warnings
			-- -r, --usr-randchars=n Get 'n' characters of additional randomness from user
			+                        (min={cfg.min_urandchars}, max={cfg.max_urandchars}, default={cfg.usr_randchars})
			-- -S, --stdout          Print {what} to stdout
			-- -t, --type=t          Choose address type. Options: see ADDRESS TYPES below
			+                        (default: {dmat})
			-- -U, --subwallet=   U  Generate {what} for subwallet 'U' (see SUBWALLETS
			+                        below)
			-k -V, --viewkeys        Print viewkeys, omitting secret keys
			-- -v, --verbose         Produce more verbose output
			-k -x, --b16             Print secret keys in hexadecimal too
		""",
		'notes': """

                           NOTES FOR THIS COMMAND

Address indexes are given as a comma-separated list and/or hyphen-separated
range(s).

{n_addrkey}If available, the libsecp256k1 library will be used for address generation.


                      NOTES FOR ALL GENERATOR COMMANDS

{n_sw}{n_pw}{n_bw}

{n_at}

{n_fmt}
"""
	},
	'code': {
		'options': lambda proto, help_notes, cfg, s: s.format(
			dmat      = help_notes('dfl_mmtype'),
			kgs       = help_notes('keygen_backends'),
			coin_id   = help_notes('coin_id'),
			dsl       = help_notes('dfl_seed_len'),
			pnm       = gc.proj_name,
			what      = gen_what,
			cfg       = cfg,
			gc        = gc,
		),
		'notes': lambda help_mod, help_notes, s: s.format(
			n_addrkey = note_addrkey,
			n_sw      = help_mod('subwallet')+'\n\n',
			n_pw      = help_notes('passwd')+'\n\n',
			n_bw      = help_notes('brainwallet'),
			n_fmt     = help_notes('fmt_codes'),
			n_at      = help_notes('address_types'),
		)
	}
}

cfg = Config(opts_data=opts_data, need_amt=False)

proto = cfg._proto

addr_type = MMGenAddrType(
	proto = proto,
	id_str = cfg.type or proto.dfl_mmtype,
	errmsg = f'{cfg.type!r}: invalid parameter for --type option')

if len(cfg._args) < 1:
	cfg._usage()

if cfg.keygen_backend:
	from .keygen import check_backend
	check_backend(cfg, proto, cfg.keygen_backend, cfg.type)

idxs = addrlist.AddrIdxList(fmt_str=cfg._args.pop())

from .fileutil import get_seed_file
sf = get_seed_file(cfg, nargs=1)

from .ui import do_license_msg
do_license_msg(cfg)

ss = Wallet(cfg, fn=sf)

ss_seed = ss.seed if cfg.subwallet is None else ss.seed.subseed(cfg.subwallet, print_msg=True)

if cfg.no_addresses:
	gen_clsname = 'KeyList'
elif cfg.viewkeys:
	gen_clsname = 'ViewKeyAddrList'

al = getattr(addrlist, gen_clsname)(
	cfg       = cfg,
	proto     = proto,
	seed      = ss_seed,
	addr_idxs = idxs,
	mmtype    = addr_type)

af = al.file

af.format()

if al.gen_addrs and cfg.print_checksum:
	from .util import Die
	Die(0, al.checksum)

from .ui import keypress_confirm
if al.gen_keys and keypress_confirm(cfg, 'Encrypt key list?'):
	af.encrypt()
	af.write(
		binary = True,
		desc = f'encrypted {af.desc}')
else:
	af.write()
