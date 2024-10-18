#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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

from .cfg import gc, Config
from .util import msg, msg_r, die, async_run
from .color import green

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': f"""
                Increase the fee on a replaceable (RBF) {gc.proj_name} transaction,
                creating a new transaction, and optionally sign and send the
                new transaction
		 """,
		'usage':   f'[opts] [{gc.proj_name} TX file] [seed source] ...',
		'options': """
-h, --help             Print this help message
--, --longhelp         Print help message for long (global) options
-a, --autosign         Bump the most recent transaction created and sent with
                       the --autosign option. The removable device is mounted
                       and unmounted automatically.  The transaction file
                       argument must be omitted.  Note that only sent trans-
                       actions may be bumped with this option.  To redo an
                       unsent --autosign transaction, first delete it using
                       ‘mmgen-txsend --abort’ and then create a new one
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
                       brainwallet input
-c, --comment-file=  f Source the transaction's comment from file 'f'
-d, --outdir=        d Specify an alternate directory 'd' for output
-e, --echo-passphrase  Print passphrase to screen when typing it
-f, --fee=           f Transaction fee, as a decimal {cu} amount or as
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
                       for password hashing (default: '{gc.dfl_hash_preset}')
-P, --passwd-file=   f Get {pnm} wallet passphrase from file 'f'
-q, --quiet            Suppress warnings; overwrite files without prompting
-s, --send             Sign and send the transaction (the default if seed
                       data is provided)
-v, --verbose          Produce more verbose output
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
-z, --show-hash-presets Show information on available hash presets
""",
	'notes': """
{e}{s}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

FMT CODES:

  {f}
"""
	},
	'code': {
		'options': lambda cfg, help_notes, proto, s: s.format(
			cfg     = cfg,
			gc      = gc,
			pnm     = gc.proj_name,
			pnl     = gc.proj_name.lower(),
			fu      = help_notes('rel_fee_desc'),
			fl      = help_notes('fee_spec_letters'),
			kgs     = help_notes('keygen_backends'),
			coin_id = help_notes('coin_id'),
			dsl     = help_notes('dfl_seed_len'),
			cu      = proto.coin),
		'notes': lambda help_notes, s: s.format(
			e       = help_notes('fee'),
			s       = help_notes('txsign'),
			f       = help_notes('fmt_codes')),
	}
}

cfg = Config(opts_data=opts_data)

if not cfg.autosign:
	tx_file = cfg._args.pop(0)
	from .fileutil import check_infile
	check_infile(tx_file)

from .tx import CompletedTX, BumpTX, UnsignedTX, OnlineSignedTX
from .tx.sign import txsign, get_seed_files, get_keyaddrlist, get_keylist

seed_files = get_seed_files(cfg, cfg._args) if (cfg._args or cfg.send) else None

from .ui import do_license_msg
do_license_msg(cfg)

silent = cfg.yes and cfg.fee is not None and cfg.output_to_reduce is not None

async def main():

	if cfg.autosign:
		from .tx.util import mount_removable_device
		from .autosign import Signable
		asi = mount_removable_device(cfg)
		si = Signable.automount_transaction(asi)
		if si.unsigned or si.unsent:
			state = 'unsigned' if si.unsigned else 'unsent'
			die(1,
				'Only sent transactions can be bumped with --autosign.  Instead of bumping\n'
				f'your {state} transaction, abort it with ‘mmgen-txsend --abort’ and create\n'
				'a new one.')
		orig_tx = await si.get_last_created()
		kal = kl = sign_and_send = None
	else:
		orig_tx = await CompletedTX(cfg=cfg, filename=tx_file)

	if not silent:
		msg(green('ORIGINAL TRANSACTION'))
		msg(orig_tx.info.format(terse=True))

	if not cfg.autosign:
		kal = get_keyaddrlist(cfg, orig_tx.proto)
		kl = get_keylist(cfg)
		sign_and_send = any([seed_files, kl, kal])

	from .tw.ctl import TwCtl
	tx = await BumpTX(
		cfg  = cfg,
		data = orig_tx.__dict__,
		automount = cfg.autosign,
		check_sent = cfg.autosign or sign_and_send,
		twctl = await TwCtl(cfg, orig_tx.proto) if orig_tx.proto.tokensym else None)

	from .rpc import rpc_init
	tx.rpc = await rpc_init(cfg, tx.proto)

	msg('Creating replacement transaction')

	tx.check_sufficient_funds_for_bump()

	output_idx = tx.choose_output()

	if not silent:
		msg(f'Minimum fee for new transaction: {tx.min_fee.hl()} {tx.proto.coin}')

	tx.usr_fee = tx.get_usr_fee_interactive(fee=cfg.fee, desc='User-selected')

	tx.bump_fee(output_idx, tx.usr_fee)

	assert tx.fee <= tx.proto.max_tx_fee

	if not cfg.yes:
		tx.add_comment()   # edits an existing comment

	await tx.create_serialized(bump=True)

	tx.add_timestamp()
	tx.add_blockcount()

	cfg._util.qmsg('Fee successfully increased')

	if not silent:
		msg(green('\nREPLACEMENT TRANSACTION:'))
		msg_r(tx.info.format(terse=True))

	if sign_and_send:
		tx2 = UnsignedTX(cfg=cfg, data=tx.__dict__)
		tx3 = await txsign(cfg, tx2, seed_files, kl, kal)
		if tx3:
			tx4 = await OnlineSignedTX(cfg=cfg, data=tx3.__dict__)
			tx4.file.write(ask_write=False)
			if await tx4.send():
				tx4.file.write(ask_write=False)
		else:
			die(2, 'Transaction could not be signed')
	else:
		tx.file.write(
			outdir                = asi.txauto_dir if cfg.autosign else None,
			ask_write             = not cfg.yes,
			ask_write_default_yes = False,
			ask_overwrite         = not cfg.yes)

async_run(main())
