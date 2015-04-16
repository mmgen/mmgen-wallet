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
mmgen-walletgen: Generate an MMGen deterministic wallet
"""

import sys, os
from hashlib import sha256

import mmgen.globalvars as g
import mmgen.opt as opt
from mmgen.util import *
from mmgen.crypto import *

pnm = g.proj_name

opts_data = {
	'desc':    "Generate an {pnm} deterministic wallet".format(pnm=pnm),
	'usage':   "[opts] [infile]",
	'options': """
-h, --help                 Print this help message
-d, --outdir=           d  Specify an alternate directory 'd' for output
-e, --echo-passphrase      Print passphrase to screen when typing it
-H, --show-hash-presets    Show information on available hash presets
-l, --seed-len=         n  Create seed of length 'n'. Options: {seed_lens}
                           (default: {g.seed_len})
-L, --label=            l  Label to identify this wallet (32 chars max.
                           Allowed symbols: A-Z, a-z, 0-9, " ", "_", ".")
-p, --hash-preset=      p  Use scrypt.hash() parameters from preset 'p'
                           (default: '{g.hash_preset}')
-P, --passwd-file=      f  Get {pnm} wallet passphrase from file 'f'
-q, --quiet                Produce quieter output; overwrite files without
                           prompting
-r, --usr-randchars=    n  Get 'n' characters of additional randomness from
                           user (min={g.min_urandchars}, max={g.max_urandchars})
-v, --verbose              Produce more verbose output

-b, --from-brain=      l,p Generate wallet from a user-created passphrase,
                           i.e. a "brainwallet", using seed length 'l' and
                           hash preset 'p' (comma-separated)
-g, --from-incog           Generate wallet from an incognito-format wallet
-G, --from-incog-hidden=   f,o,l  Generate keys from incognito data in file
                           'f' at offset 'o', with seed length of 'l'
-o, --old-incog-fmt        Use old (pre-0.7.8) incog format
-m, --from-mnemonic        Generate wallet from an Electrum-like mnemonic
-s, --from-seed            Generate wallet from a seed in .{g.seed_ext} format
""".format(seed_lens=",".join([str(i) for i in g.seed_lens]),g=g,pnm=pnm),
	'notes': """

By default (i.e. when invoked without any of the '--from-<what>' options),
{g.prog_name} generates a wallet based on a random seed.

Data for the --from-<what> options will be taken from <infile> if <infile>
is specified.  Otherwise, the user will be prompted to enter the data.

For passphrases all combinations of whitespace are equal, and leading and
trailing space are ignored.  This permits reading passphrase data from a
multi-line file with free spacing and indentation.  This is particularly
convenient for long brainwallet passphrases, for example.

Since good randomness is particularly important when generating wallets,
the '--usr-randchars' option is turned on by default to gather additional
entropy from the user.  If you fully trust your OS's random number gener-
ator and wish to disable this option, specify '-r0' on the command line.

BRAINWALLET NOTE:

As brainwallets require especially strong hashing to thwart dictionary
attacks, the brainwallet hash preset must be specified by the user, using
the 'p' parameter of the '--from-brain' option.  This preset should be
stronger than the one used for hashing the seed (i.e. the default value or
the one specified in the '--hash-preset' option).

The '--from-brain' option also requires the user to specify a seed length
(the 'l' parameter), which overrides both the default and any one given in
the '--seed-len' option.

For a brainwallet passphrase to always generate the same keys and
addresses, the same 'l' and 'p' parameters to '--from-brain' must be used
in all future invocations with that passphrase.
""".format(g=g)
}

wmsg = {
	'choose_wallet_passphrase': """
You must choose a passphrase to encrypt the wallet with.  A key will be
generated from your passphrase using a hash preset of '%s'.  Please note that
no strength checking of passphrases is performed.  For an empty passphrase,
just hit ENTER twice.
""".strip(),
	'brain_warning': """
############################## EXPERTS ONLY! ##############################

A brainwallet will be secure only if you really know what you're doing and
have put much care into its creation.  The creators of {pnm} assume no
responsibility for coins stolen as a result of a poorly crafted brainwallet
passphrase.

A key will be generated from your passphrase using the parameters requested
by you: seed length {}, hash preset '{}'.  For brainwallets it's highly
recommended to use one of the higher-numbered presets.

Remember the seed length and hash preset parameters you've specified.  To
generate the correct keys/addresses associated with this passphrase in the
future, you must continue using these same parameters.
""",
}

import mmgen.opt as opt
cmd_args = opt.opts.init(opts_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]
	check_infile(infile)
	ext = infile.split(".")[-1]
	ok_exts = g.seedfile_exts
	for e in ok_exts:
		if e == ext: break
	else:
		msg(
"Input file must have one of the following extensions: .%s" % ", .".join(ok_exts))
		sys.exit(1)
elif len(cmd_args) == 0:
	infile = ""
else: opt.opts.usage()

g.use_urandchars = True

# Begin execution

do_license_msg()

if opt.from_brain and not opt.quiet:
	confirm_or_exit(wmsg['brain_warning'].format(
			pnm=pnm, *get_from_brain_opt_params()),
		"continue")

if infile or any([
		opt.from_mnemonic,opt.from_brain,opt.from_seed,opt.from_incog]):
	seed = get_seed_retry(infile)
	qmsg("")
else:
	# Truncate random data for smaller seed lengths
	seed = sha256(get_random(128)).digest()[:opt.seed_len/8]

salt = sha256(get_random(128)).digest()[:g.salt_len]

qmsg(wmsg['choose_wallet_passphrase'] % opt.hash_preset)

passwd = get_new_passphrase("new {pnm} wallet".format(pnm=pnm))

key = make_key(passwd, salt, opt.hash_preset)

enc_seed = encrypt_seed(seed, key)

write_wallet_to_file(seed,passwd,make_chksum_8(key),salt,enc_seed)
