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
mmgen-addrgen: Generate a series or range of addresses from an MMGen
               deterministic wallet
"""

import sys

import mmgen.config as g
import mmgen.opt as opt
from mmgen.util import *
from mmgen.crypto import *
from mmgen.addr import *

what = "keys" if sys.argv[0].split("-")[-1] == "keygen" else "addresses"

opts_data = {
	'desc': """Generate a range or list of {w} from an {pnm} wallet,
                  mnemonic, seed or password""".format(w=what,pnm=g.proj_name),
	'usage':"[opts] [infile] <address range or list>",
	'options': """
-h, --help              Print this help message{}
-d, --outdir=       d   Specify an alternate directory 'd' for output
-c, --save-checksum     Save address list checksum to file
-e, --echo-passphrase   Echo passphrase or mnemonic to screen upon entry
-H, --show-hash-presets Show information on available hash presets
-K, --no-keyconv        Force use of internal libraries for address gener-
                        ation, even if 'keyconv' is available
-l, --seed-len=     N   Length of seed.  Options: {seed_lens}
                        (default: {g.seed_len})
-p, --hash-preset=  p   Use scrypt.hash() parameters from preset 'p' when
                        hashing password (default: '{g.hash_preset}')
-P, --passwd-file=  f   Get {pnm} wallet passphrase from file 'f'
-q, --quiet             Suppress warnings; overwrite files without
                        prompting
-S, --stdout            Print {what} to stdout
-v, --verbose           Produce more verbose output{}

-b, --from-brain=  l,p  Generate {what} from a user-created password,
                        i.e. a "brainwallet", using seed length 'l' and
                        hash preset 'p' (comma-separated)
-g, --from-incog        Generate {what} from an incognito wallet
-X, --from-incog-hex    Generate {what} from incognito hexadecimal wallet
-G, --from-incog-hidden=f,o,l Generate {what} from incognito data in file
                        'f' at offset 'o', with seed length of 'l'
-o, --old-incog-fmt     Use old (pre-0.7.8) incog format
-m, --from-mnemonic     Generate {what} from an electrum-like mnemonic
-s, --from-seed         Generate {what} from a seed in .{g.seed_ext} format
""".format(
		*(
			(
"\n-A, --no-addresses      Print only secret keys, no addresses",
"\n-x, --b16               Print secret keys in hexadecimal too"
			)
		if what == "keys" else ("","")),
		seed_lens=", ".join([str(i) for i in g.seed_lens]),
		what=what,g=g,pnm=g.proj_name
),
	'notes': """

Addresses are given in a comma-separated list.  Hyphen-separated ranges are
also allowed.{}

If available, the external 'keyconv' program will be used for address
generation.

Data for the --from-<what> options will be taken from <infile> if <infile>
is specified.  Otherwise, the user will be prompted to enter the data.

For passphrases all combinations of whitespace are equal, and leading and
trailing space are ignored.  This permits reading passphrase data from a
multi-line file with free spacing and indentation.  This is particularly
convenient for long brainwallet passphrases, for example.

BRAINWALLET NOTE:

As brainwallets require especially strong hashing to thwart dictionary
attacks, the brainwallet hash preset must be specified by the user, using
the 'p' parameter of the '--from-brain' option

The '--from-brain' option also requires the user to specify a seed length
(the 'l' parameter)

For a brainwallet passphrase to always generate the same keys and addresses,
the same 'l' and 'p' parameters to '--from-brain' must be used in all future
invocations with that passphrase
""".format("\n\nBy default, both addresses and secret keys are generated."
				if what == "keys" else "")
}

wmsg = {
	'unencrypted_secret_keys': """
This program generates secret keys from your {pnm} seed, outputting them in
UNENCRYPTED form.  Generate only the key(s) you need and guard them carefully.
""".format(pnm=g.proj_name),
}

cmd_args = opt.opts.init(opts_data,add_opts=["b16"])

if opt.from_incog_hex or opt.from_incog_hidden: opt.from_incog = True

if len(cmd_args) == 1 and any([
		opt.from_mnemonic,opt.from_brain,opt.from_seed,opt.from_incog_hidden]):
	infile,addr_idx_arg = "",cmd_args[0]
elif len(cmd_args) == 2:
	infile,addr_idx_arg = cmd_args
	check_infile(infile)
else: opt.opts.usage()

addr_idxs = parse_addr_idxs(addr_idx_arg)

if not addr_idxs: sys.exit(2)

do_license_msg()

# Interact with user:
if what == "keys" and not opt.quiet:
	confirm_or_exit(wmsg['unencrypted_secret_keys'], 'continue')

# Generate data:

seed = get_seed_retry(infile)

opt.gen_what = "a" if what == "addresses" else (
	"k" if opt.no_addresses else "ka")

ainfo = generate_addrs(seed,addr_idxs)

addrdata_str = ainfo.fmt_data()
outfile_base = "{}[{}]".format(make_chksum_8(seed), ainfo.idxs_fmt)

if 'a' in opt.gen_what and opt.save_checksum:
	w = "key-address" if 'k' in opt.gen_what else "address"
	write_to_file(outfile_base+"."+g.addrfile_chksum_ext,
		ainfo.checksum+"\n","%s data checksum" % w,True,True,False)

if 'k' in opt.gen_what and keypress_confirm("Encrypt key list?"):
	addrdata_str = mmgen_encrypt(addrdata_str,"new key list","")
	enc_ext = "." + g.mmenc_ext
else: enc_ext = ""

# Output data:
if opt.stdout or not sys.stdout.isatty():
	if enc_ext and sys.stdout.isatty():
		msg("Cannot write encrypted data to screen.  Exiting")
		sys.exit(2)
	write_to_stdout(addrdata_str,what,
		(what=="keys"and not opt.quiet and sys.stdout.isatty()))
else:
	outfile = "%s.%s%s" % (outfile_base, (
		g.keyaddrfile_ext if "ka" in opt.gen_what else (
		g.keyfile_ext if "k" in opt.gen_what else
		g.addrfile_ext)), enc_ext)
	write_to_file(outfile,addrdata_str,what,not opt.quiet,True)
