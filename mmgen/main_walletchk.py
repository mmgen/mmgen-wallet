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
from mmgen.crypto import *

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
-P, --passwd-file=  f  Get MMGen wallet passphrase from file 'f'
-q, --quiet            Suppress warnings; overwrite files without prompting
-r, --usr-randchars= n Get 'n' characters of additional randomness from
                       user (min={g.min_urandchars}, max={g.max_urandchars})
-S, --stdout           Print seed or mnemonic data to standard output
-v, --verbose          Produce more verbose output
-g, --export-incog     Export wallet to incognito format
-X, --export-incog-hex Export wallet to incognito hexadecimal format
-G, --export-incog-hidden=f,o  Hide incognito data in existing file 'f'
                       at offset 'o' (comma-separated)
-o, --old-incog-fmt    Use old (pre-0.7.8) incog format
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

def wallet_to_incog_data(infile,opts):

	d = get_data_from_wallet(infile,silent=True)
	seed_id,key_id,preset,salt,enc_seed = \
			d[1][0], d[1][1], d[2].split(":")[0], d[3], d[4]

	while True:
		passwd = get_mmgen_passphrase("{} wallet".format(g.proj_name),opts)
		key = make_key(passwd, salt, preset, "main key")
		seed = decrypt_seed(enc_seed, key, seed_id, key_id)
		if seed: break

	iv = get_random(g.aesctr_iv_len,opts)
	iv_id = make_iv_chksum(iv)
	msg("Incog ID: %s" % iv_id)

	if not 'old_incog_fmt' in opts:
		salt = get_random(g.salt_len,opts)
		key = make_key(passwd, salt, preset, "incog wallet key")
		key_id = make_chksum_8(key)
		from hashlib import sha256
		chk = sha256(seed).digest()[:8]
		enc_seed = encrypt_data(chk+seed, key, 1, "seed")

	# IV is used BOTH to initialize counter and to salt password!
	key = make_key(passwd, iv, preset, "incog wrapper key")
	m = "incog data"
	wrap_enc = encrypt_data(salt + enc_seed, key, int(hexlify(iv),16), m)

	return iv+wrap_enc,seed_id,key_id,iv_id,preset


def export_to_hidden_incog(incog_enc,opts):
	outfile,offset = opts['export_incog_hidden'].split(",") #Already sanity-checked
	if 'outdir' in opts: outfile = make_full_path(opts['outdir'],outfile)

	check_data_fits_file_at_offset(outfile,int(offset),len(incog_enc),"write")

	if not g.quiet: confirm_or_exit("","alter file '%s'" % outfile)
	import os
	f = os.open(outfile,os.O_RDWR)
	os.lseek(f, int(offset), os.SEEK_SET)
	os.write(f, incog_enc)
	os.close(f)
	msg("Data written to file '%s' at offset %s" %
			(os.path.relpath(outfile),offset))


opts,cmd_args = parse_opts(sys.argv,help_data)

if 'export_incog_hidden' in opts or 'export_incog_hex' in opts:
	opts['export_incog'] = True

if len(cmd_args) != 1: usage(help_data)

check_infile(cmd_args[0])

if set(['outdir','export_incog_hidden']).issubset(set(opts.keys())):
	msg("Warning: '--outdir' option is ignored when exporting hidden incog data")

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
		z = 0 if 'old_incog_fmt' in opts else 8
		seed_len = (len(incog_enc)-g.salt_len-g.aesctr_iv_len-z)*8
		fn = "%s-%s-%s[%s,%s].%s" % (
			seed_id, key_id, iv_id, seed_len, preset,
			g.incog_hex_ext if "export_incog_hex" in opts else g.incog_ext
		)
		data = pretty_hexdump(incog_enc,2,8,line_nums=False) \
					if "export_incog_hex" in opts else incog_enc
		write_to_file_or_stdout(fn, data, opts, "incognito wallet data")

	sys.exit()

seed = get_seed_retry(cmd_args[0], opts)
if seed: msg("Wallet is OK")
else:
	msg("Error opening wallet")
	sys.exit(2)

if 'export_mnemonic' in opts:
	wl = get_default_wordlist()
	from mmgen.mnemonic import get_mnemonic_from_seed
	mn = get_mnemonic_from_seed(seed, wl, g.default_wl, g.debug)
	fn = "%s.%s" % (make_chksum_8(seed).upper(), g.mn_ext)
	write_to_file_or_stdout(fn, " ".join(mn)+"\n", opts, "mnemonic data")

elif 'export_seed' in opts:
	from mmgen.bitcoin import b58encode_pad
	data = col4(b58encode_pad(seed))
	chk = make_chksum_6(b58encode_pad(seed))
	fn = "%s.%s" % (make_chksum_8(seed).upper(), g.seed_ext)
	write_to_file_or_stdout(fn, "%s %s\n" % (chk,data), opts, "seed data")
