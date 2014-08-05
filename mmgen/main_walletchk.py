#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
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
mmgen-walletchk: Check integrity of an MMGen deterministic wallet, display
                 information about it and export it to various formats
"""

import sys
import mmgen.config as g
from mmgen.Opts import *
from mmgen.util import *
from mmgen.crypto import get_seed_from_wallet,wallet_to_incog_data

help_data = {
	'prog_name': g.prog_name,
	'desc':  """Check integrity of an {} deterministic wallet, display
                    its information, and export seed and mnemonic data.
             """.format(g.proj_name),
	'usage':   "[opts] [filename]",
	'options': """
-h, --help             Print this help message
-d, --outdir=       d  Specify an alternate directory 'd' for output
-e, --echo-passphrase  Print passphrase to screen when typing it
-P, --passwd-file=  f  Get passphrase from file 'f'
-q, --quiet            Suppress warnings; overwrite files without prompting
-r, --usr-randchars= n Get 'n' characters of additional randomness from
                       user (min={g.min_urandchars}, max={g.max_urandchars})
-S, --stdout           Print seed or mnemonic data to standard output
-v, --verbose          Produce more verbose output
-g, --export-incog     Export wallet to incognito format
-X, --export-incog-hex Export wallet to incognito hexadecimal format
-G, --export-incog-hidden=f,o  Hide incognito data in existing file 'f'
                       at offset 'o' (comma-separated)
-m, --export-mnemonic  Export the wallet's mnemonic to file
-s, --export-seed      Export the wallet's seed to file
""".format(g=g),
	'notes': """

Since good randomness is particularly important for incognito wallets,
the '--usr-randchars' option is turned on by default to gather additional
entropy from the user when one of the '--export-incog*' options is
selected.  If you fully trust your OS's random number generator and wish
to disable this option, then specify '-r0' on the command line.
"""
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if 'export_incog_hidden' in opts or 'export_incog_hex' in opts:
	opts['export_incog'] = True

if len(cmd_args) != 1: usage(help_data)

check_infile(cmd_args[0])

if 'export_mnemonic' in opts:
	qmsg("Exporting mnemonic data to file by user request")
elif 'export_seed' in opts:
	qmsg("Exporting seed data to file by user request")
elif 'export_incog' in opts:
	if opts['usr_randchars'] == -1: opts['usr_randchars'] = g.usr_randchars_dfl
	qmsg("Exporting wallet to incognito format by user request")
	incog_enc,seed_id,key_id,iv_id,preset = \
		wallet_to_incog_data(cmd_args[0],opts)

	if "export_incog_hidden" in opts:
		export_to_hidden_incog(incog_enc,opts)
	else:
		seed_len = (len(incog_enc)-g.salt_len-g.aesctr_iv_len)*8
		fn = "%s-%s-%s[%s,%s].%s" % (
			seed_id, key_id, iv_id, seed_len, preset,
			g.incog_hex_ext if "export_incog_hex" in opts else g.incog_ext
		)
		data = pretty_hexdump(incog_enc,2,8,line_nums=False) \
					if "export_incog_hex" in opts else incog_enc
		export_to_file(fn, data, opts, "incognito wallet data")

	sys.exit()

seed = get_seed_from_wallet(cmd_args[0], opts)
if seed: qmsg("Wallet is OK")
else:
	msg("Error opening wallet")
	sys.exit(2)

if 'export_mnemonic' in opts:
	wl = get_default_wordlist()
	from mmgen.mnemonic import get_mnemonic_from_seed
	p = True if g.debug else False
	mn = get_mnemonic_from_seed(seed, wl, g.default_wl, print_info=p)
	fn = "%s.%s" % (make_chksum_8(seed).upper(), g.mn_ext)
	export_to_file(fn, " ".join(mn)+"\n", opts, "mnemonic data")

elif 'export_seed' in opts:
	from mmgen.bitcoin import b58encode_pad
	data = col4(b58encode_pad(seed))
	chk = make_chksum_6(b58encode_pad(seed))
	fn = "%s.%s" % (make_chksum_8(seed).upper(), g.seed_ext)
	export_to_file(fn, "%s %s\n" % (chk,data), opts, "seed data")
