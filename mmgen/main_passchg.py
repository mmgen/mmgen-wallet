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
mmgen-passchg: Change an MMGen deterministic wallet's passphrase, label or
               hash preset
"""

import sys
from mmgen.util import *
from mmgen.crypto import *
import mmgen.config as g
import mmgen.opt as opt

opts_data = {
	'desc':  """Change the passphrase, hash preset or label of an {}
                  deterministic wallet""".format(g.proj_name),
	'usage':   "[opts] [filename]",
	'options': """
-h, --help                Print this help message
-d, --outdir=           d Specify an alternate directory 'd' for output
-H, --show-hash-presets   Show information on available hash presets
-k, --keep-old-passphrase Keep old passphrase (use when changing hash
                          strength or label only)
-L, --label=            l Change the wallet's label to 'l'
-p, --hash-preset=      p Change scrypt.hash() parameters to preset 'p'
                          (default: '{g.hash_preset}')
-P, --passwd-file=      f Get new MMGen wallet passphrase from file 'f'
-r, --usr-randchars=    n Get 'n' characters of additional randomness from
                          user (min={g.min_urandchars}, max={g.max_urandchars})
-q, --quiet               Suppress warnings; overwrite files without
                          prompting
-v, --verbose             Produce more verbose output
""".format(g=g),
	'notes': """

NOTE: The key ID will change if either the passphrase or hash preset are
      changed
"""
}

cmd_args = opt.opts.init(opts_data)

if opt.show_hash_presets: show_hash_presets()

if len(cmd_args) != 1:
	msg("One input file must be specified")
	sys.exit(2)
infile = cmd_args[0]

# Old key:
label,metadata,hash_preset,salt,enc_seed = get_data_from_wallet(infile)
seed_id,key_id = metadata[:2]

# Repeat on incorrect pw entry
while True:
	p = "{} wallet".format(g.proj_name)
	passwd = get_mmgen_passphrase(p,not opt.keep_old_passphrase)
	key = make_key(passwd, salt, hash_preset)
	seed = decrypt_seed(enc_seed, key, seed_id, key_id)
	if seed: break

changed = {}

if opt.label:
	if opt.label != label:
		msg("Label changed: '%s' -> '%s'" % (label, opt.label))
		changed['label'] = True
	else:
		msg("Label is unchanged: '%s'" % (label))
else: opt.label = label  # Copy the old label

if opt.hash_preset:
	if hash_preset != opt.hash_preset:
		qmsg("Hash preset has changed (%s -> %s)" %
			(hash_preset, opt.hash_preset))
		changed['preset'] = True
	else:
		msg("Hash preset is unchanged")
else:
	opt.hash_preset = hash_preset

if opt.keep_old_passphrase:
	msg("Keeping old passphrase by user request")
else:
	new_passwd = get_new_passphrase(
			"{} wallet".format(g.proj_name), True)

	if new_passwd == passwd:
		qmsg("Passphrase is unchanged")
	else:
		qmsg("Passphrase has changed")
		passwd = new_passwd
		changed['passwd'] = True

if 'preset' in changed or 'passwd' in changed: # Update key ID, salt
	qmsg("Will update salt and key ID")

	from hashlib import sha256

	salt = sha256(salt + get_random(128)).digest()[:g.salt_len]
	key = make_key(passwd, salt, opt.hash_preset)
	new_key_id = make_chksum_8(key)
	qmsg("Key ID changed: %s -> %s" % (key_id,new_key_id))
	key_id = new_key_id
	enc_seed = encrypt_seed(seed, key)
elif not 'label' in changed:
	msg("Data unchanged.  No file will be written")
	sys.exit(2)

write_wallet_to_file(seed, passwd, key_id, salt, enc_seed)
