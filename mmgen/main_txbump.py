#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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

from .common import *
from .wallet import Wallet

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': f"""
                Increase the fee on a replaceable (RBF) {g.proj_name} transaction,
                creating a new transaction, and optionally sign and send the
                new transaction
		 """,
		'usage':   f'[opts] <{g.proj_name} TX file> [seed source] ...',
		'options': """
-h, --help             Print this help message
--, --longhelp         Print help message for long options (common options)
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
                       brainwallet input
-c, --comment-file=  f Source the transaction's comment from file 'f'
-d, --outdir=        d Specify an alternate directory 'd' for output
-e, --echo-passphrase  Print passphrase to screen when typing it
-f, --tx-fee=        f Transaction fee, as a decimal {cu} amount or as
                       {fu} (an integer followed by {fl!r}).
                       See FEE SPECIFICATION below.
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-i, --in-fmt=        f Input is from wallet format 'f' (see FMT CODES below)
-l, --seed-len=      l Specify wallet seed length of 'l' bits. This option
                       is required only for brainwallet and incognito inputs
                       with non-standard (< {dsl}-bit) seed lengths.
-k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
-K, --keygen-backend=n Use backend 'n' for public key generation.  Options
                       for {coin_id}: {kgs}
-M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
                       address file (output of '{pnl}-keygen'). Permits
                       online signing without an {pnm} seed source. The
                       key-address file is also used to verify {pnm}-to-{cu}
                       mappings, so the user should record its checksum.
-o, --output-to-reduce=o Deduct the fee from output 'o' (an integer, or 'c'
                       for the transaction's change output, if present)
-O, --old-incog-fmt    Specify old-format incognito input
-p, --hash-preset=   p Use the scrypt hash parameters defined by preset 'p'
                       for password hashing (default: '{g.dfl_hash_preset}')
-P, --passwd-file=   f Get {pnm} wallet passphrase from file 'f'
-q, --quiet            Suppress warnings; overwrite files without prompting
-s, --send             Sign and send the transaction (the default if seed
                       data is provided)
-v, --verbose          Produce more verbose output
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
-z, --show-hash-presets Show information on available hash presets
""",
	'notes': """
{}{}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

FMT CODES:

  {f}
"""
	},
	'code': {
		'options': lambda help_notes,proto,s: s.format(
			g=g,
			pnm=g.proj_name,
			pnl=g.proj_name.lower(),
			fu=help_notes('rel_fee_desc'),
			fl=help_notes('fee_spec_letters'),
			kgs=help_notes('keygen_backends'),
			coin_id=help_notes('coin_id'),
			dsl=help_notes('dfl_seed_len'),
			cu=proto.coin),
		'notes': lambda help_notes,s: s.format(
			help_notes('fee'),
			help_notes('txsign'),
			f=help_notes('fmt_codes')),
	}
}

cmd_args = opts.init(opts_data)

tx_file = cmd_args.pop(0)

from .fileutil import check_infile
check_infile(tx_file)

from .tx import *
from .txsign import *

seed_files = get_seed_files(opt,cmd_args) if (cmd_args or opt.send) else None

do_license_msg()

silent = opt.yes and opt.tx_fee != None and opt.output_to_reduce != None

ext = get_extension(tx_file)
ext_data = {
	MMGenTX.Unsigned.ext: 'Unsigned',
	MMGenTX.Signed.ext:   'Signed',
}
if ext not in ext_data:
	die(1,f'{ext!r}: unrecognized file extension')

async def main():

	orig_tx = getattr(MMGenTX,ext_data[ext])(filename=tx_file)

	if not silent:
		msg(green('ORIGINAL TRANSACTION'))
		msg(orig_tx.format_view(terse=True))

	kal = get_keyaddrlist(orig_tx.proto,opt)
	kl = get_keylist(orig_tx.proto,opt)
	sign_and_send = bool(seed_files or kl or kal)

	from .twctl import TrackingWallet
	tx = MMGenTX.Bump(
		data = orig_tx.__dict__,
		send = sign_and_send,
		tw   = await TrackingWallet(orig_tx.proto) if orig_tx.proto.tokensym else None )

	from .rpc import rpc_init
	tx.rpc = await rpc_init(tx.proto)

	msg('Creating replacement transaction')

	tx.check_sufficient_funds_for_bump()

	output_idx = tx.choose_output()

	if not silent:
		msg(f'Minimum fee for new transaction: {tx.min_fee.hl()} {tx.proto.coin}')

	tx.usr_fee = tx.get_usr_fee_interactive(tx_fee=opt.tx_fee,desc='User-selected')

	tx.bump_fee(output_idx,tx.usr_fee)

	assert tx.fee <= tx.proto.max_tx_fee

	if tx.proto.base_proto == 'Bitcoin':
		tx.outputs.sort_bip69() # output amts have changed, so re-sort

	if not opt.yes:
		tx.add_comment()   # edits an existing comment

	await tx.create_raw() # creates tx.hex, tx.txid

	tx.add_timestamp()
	tx.add_blockcount()

	qmsg('Fee successfully increased')

	if not silent:
		msg(green('\nREPLACEMENT TRANSACTION:'))
		msg_r(tx.format_view(terse=True))

	if sign_and_send:
		tx2 = MMGenTX.Unsigned(data=tx.__dict__)
		tx3 = await txsign(tx2,seed_files,kl,kal)
		if tx3:
			tx3.write_to_file(ask_write=False)
			await tx3.send(exit_on_fail=True)
			tx3.write_to_file(ask_write=False)
		else:
			die(2,'Transaction could not be signed')
	else:
		tx.write_to_file(ask_write=not opt.yes,ask_write_default_yes=False,ask_overwrite=not opt.yes)

run_session(main())
