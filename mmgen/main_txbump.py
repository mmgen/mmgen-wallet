#!/usr/bin/env python
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
mmgen-txbump: Increase the fee on a replaceable (replace-by-fee) MMGen
              transaction, and optionally sign and send it
"""

from mmgen.common import *

opts_data = lambda: {
	'desc': 'Increase the fee on a replaceable (RBF) {g.proj_name} transaction, creating a new transaction, and optionally sign and send the new transaction'.format(g=g),
	'usage':   '[opts] <{g.proj_name} TX file> [seed source] ...'.format(g=g),
	'sets': ( ('yes', True, 'quiet', True), ),
	'options': """
-h, --help             Print this help message
--, --longhelp         Print help message for long options (common options)
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
                       brainwallet input
-c, --comment-file=  f Source the transaction's comment from file 'f'
-d, --outdir=        d Specify an alternate directory 'd' for output
-e, --echo-passphrase  Print passphrase to screen when typing it
-f, --tx-fee=        f Transaction fee, as a decimal {cu} amount or as
                       {fu} (an integer followed by {fl}).
                       See FEE SPECIFICATION below.
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-i, --in-fmt=        f Input is from wallet format 'f' (see FMT CODES below)
-l, --seed-len=      l Specify wallet seed length of 'l' bits. This option
                       is required only for brainwallet and incognito inputs
                       with non-standard (< {g.seed_len}-bit) seed lengths.
-k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
-K, --key-generator= m Use method 'm' for public key generation
                       Options: {kgs}
                       (default: {kg})
-M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
                       address file (output of '{pnl}-keygen'). Permits
                       online signing without an {pnm} seed source. The
                       key-address file is also used to verify {pnm}-to-{cu}
                       mappings, so the user should record its checksum.
-o, --output-to-reduce=o Deduct the fee from output 'o' (an integer, or 'c'
                       for the transaction's change output, if present)
-O, --old-incog-fmt    Specify old-format incognito input
-p, --hash-preset=   p Use the scrypt hash parameters defined by preset 'p'
                       for password hashing (default: '{g.hash_preset}')
-P, --passwd-file=   f Get {pnm} wallet or {dn} passphrase from file 'f'
-q, --quiet            Suppress warnings; overwrite files without prompting
-s, --send             Sign and send the transaction (the default if seed
                       data is provided)
-v, --verbose          Produce more verbose output
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
-z, --show-hash-presets Show information on available hash presets
""",
	'options_fmt_args': lambda: dict(
		g=g,pnm=g.proj_name,pnl=g.proj_name.lower(),dn=g.proto.daemon_name,
		fu=help_notes('rel_fee_desc'),fl=help_notes('fee_spec_letters'),
		kgs=' '.join(['{}:{}'.format(n,k) for n,k in enumerate(g.key_generators,1)]),
		kg=g.key_generator,
		cu=g.coin),
	'notes': lambda: '\n' + help_notes('fee') + help_notes('txsign')
}

cmd_args = opts.init(opts_data)

rpc_init()

tx_file = cmd_args.pop(0)
check_infile(tx_file)

from mmgen.tx import *
from mmgen.txsign import *

seed_files = get_seed_files(opt,cmd_args) if (cmd_args or opt.send) else None

kal = get_keyaddrlist(opt)
kl = get_keylist(opt)

tx = MMGenBumpTX(filename=tx_file,send=(seed_files or kl or kal))

do_license_msg()

silent = opt.yes and opt.tx_fee != None and opt.output_to_reduce != None

if not silent:
	msg(green('ORIGINAL TRANSACTION'))
	msg(tx.format_view(terse=True))

tx.set_min_fee()

tx.check_bumpable()

msg('Creating new transaction')

op_idx = tx.choose_output()

if not silent:
	msg('Minimum fee for new transaction: {} {}'.format(tx.min_fee.hl(),g.coin))

fee = tx.get_usr_fee_interactive(tx_fee=opt.tx_fee,desc='User-selected')

tx.update_fee(op_idx,fee)

d = tx.get_fee_from_tx()
assert d == fee and d <= g.proto.max_tx_fee

if not opt.yes:
	tx.add_comment()   # edits an existing comment
tx.create_raw()        # creates tx.hex, tx.txid
tx.add_timestamp()
tx.add_blockcount()

qmsg('Fee successfully increased')

if not silent:
	msg(green('\nREPLACEMENT TRANSACTION:'))
	msg_r(tx.format_view(terse=True))

if seed_files or kl or kal:
	if txsign(tx,seed_files,kl,kal):
		tx.write_to_file(ask_write=False)
		tx.send(exit_on_fail=True)
		tx.write_to_file(ask_write=False)
	else:
		die(2,'Transaction could not be signed')
else:
	tx.write_to_file(ask_write=not opt.yes,ask_write_default_yes=False,ask_overwrite=not opt.yes)
