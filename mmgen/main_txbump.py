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
mmgen-txbump: Create, and optionally send and sign, a replacement transaction
              on supporting networks
"""

from .cfg import gc, Config
from .util import msg, msg_r, die, async_run
from .color import green

opts_data = {
	'filter_codes': ['-'],
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': """
                Create, and optionally send and sign, a replacement transaction
                on supporting networks
		 """,
		'usage2':   (
			f'[opts] [{gc.proj_name} TX file] [seed source] ...',
			f'[opts] {{u_args}} [{gc.proj_name} TX file] [seed source] ...',
		),
		'options': """
			-- -h, --help             Print this help message
			-- --, --longhelp         Print help message for long (global) options
			-- -a, --autosign         Bump the most recent transaction created and sent with
			+                         the --autosign option. The removable device is mounted
			+                         and unmounted automatically.  The transaction file
			+                         argument must be omitted.  Note that only sent trans-
			+                         actions may be bumped with this option.  To redo an
			+                         unsent --autosign transaction, first delete it using
			+                         ‘mmgen-txsend --abort’ and then create a new one
			-- -b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
			+                         brainwallet input
			-- -c, --comment-file=  f Source the transaction's comment from file 'f'
			-- -d, --outdir=        d Specify an alternate directory 'd' for output
			-- -e, --echo-passphrase  Print passphrase to screen when typing it
			-- -f, --fee=           f Transaction fee, as a decimal {cu} amount or as
			+                         {fu} (an integer followed by {fl}).
			+                         See FEE SPECIFICATION below.
			e- -g, --gas=N            Set the gas limit (see GAS LIMIT below)
			-- -H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
			+                        'f' at offset 'o' (comma-separated)
			-- -i, --in-fmt=        f Input is from wallet format 'f' (see FMT CODES below)
			-- -l, --seed-len=      l Specify wallet seed length of 'l' bits. This option
			+                         is required only for brainwallet and incognito inputs
			+                         with non-standard (< {dsl}-bit) seed lengths.
			-- -k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
			-- -K, --keygen-backend=n Use backend 'n' for public key generation.  Options
			+                         for {coin_id}: {kgs}
			-- -M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
			+                         address file (output of '{pnl}-keygen'). Permits
			+                         online signing without an {pnm} seed source. The
			+                         key-address file is also used to verify {pnm}-to-{cu}
			+                         mappings, so the user should record its checksum.
			b- -o, --output-to-reduce=o Deduct the fee from output 'o' (an integer, or 'c'
			+                         for the transaction's change output, if present)
			-- -O, --old-incog-fmt    Specify old-format incognito input
			-- -p, --hash-preset=   p Use the scrypt hash parameters defined by preset 'p'
			+                         for password hashing (default: '{gc.dfl_hash_preset}')
			-- -P, --passwd-file=   f Get {pnm} wallet passphrase from file 'f'
			-- -q, --quiet            Suppress warnings; overwrite files without prompting
			-- -s, --send             Sign and send the transaction (the default if seed
			+                         data is provided)
			-- -T, --txhex-idx=N      Send only part ‘N’ of a multi-part transaction.
			+                         Indexing begins with one.
			-- -v, --verbose          Produce more verbose output
			e- -w, --wait             Wait for transaction confirmation
			-- -W, --allow-non-wallet-swap Allow signing of swap transactions that send funds
			+                         to non-wallet addresses
			-- -x, --proxy=P          Fetch the swap quote via SOCKS5h proxy ‘P’ (host:port).
			+                         Use special value ‘env’ to honor *_PROXY environment
			+                         vars instead.
			-- -y, --yes              Answer 'yes' to prompts, suppress non-essential output
			-- -z, --show-hash-presets Show information on available hash presets
""",
	'notes': """

With --autosign, the TX file argument is omitted, and the last submitted TX
file on the removable device will be used.

If no outputs are specified, the original outputs will be used for the
replacement transaction, otherwise a new transaction will be created with the
outputs listed on the command line.  The syntax for the output arguments is
identical to that of ‘mmgen-txcreate’.

The user should take care to select a fee sufficient to ensure the original
transaction is replaced in the mempool.

When bumping a swap transaction, the swap protocol’s quote server on the
Internet must be reachable either directly or via the SOCKS5 proxy specified
with the --proxy option.  To improve privacy, it’s recommended to proxy
requests to the quote server via Tor or some other anonymity network.

{g}{F}{s}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

{f}
"""
	},
	'code': {
		'usage': lambda cfg, proto, help_notes, s: s.format(
			u_args = help_notes('txcreate_args')),
		'options': lambda cfg, help_notes, proto, s: s.format(
			cfg     = cfg,
			gc      = gc,
			pnm     = gc.proj_name,
			pnl     = gc.proj_name.lower(),
			fu      = help_notes('rel_fee_desc'),
			fl      = help_notes('fee_spec_letters', use_quotes=True),
			kgs     = help_notes('keygen_backends'),
			coin_id = help_notes('coin_id'),
			dsl     = help_notes('dfl_seed_len'),
			cu      = proto.coin),
		'notes': lambda help_mod, help_notes, s: s.format(
			g       = help_notes('gas_limit', target=None),
			F       = help_notes('fee'),
			s       = help_mod('txsign'),
			f       = help_notes('fmt_codes')),
	}
}

cfg = Config(opts_data=opts_data)

from .tx import CompletedTX, BumpTX, UnsignedTX, OnlineSignedTX
from .tx.keys import TxKeys, pop_seedfiles, get_keylist, get_keyaddrlist

seedfiles = pop_seedfiles(cfg, ignore_dfl_wallet=not cfg.send, empty_ok=not cfg.send)

if cfg.autosign:
	if cfg.send:
		die(1, '--send cannot be used together with --autosign')
else:
	tx_file = cfg._args.pop()
	from .fileutil import check_infile
	check_infile(tx_file)

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
		sign_and_send = False
	else:
		orig_tx = await CompletedTX(cfg=cfg, filename=tx_file)
		kl = get_keylist(cfg)
		kal = get_keyaddrlist(cfg, orig_tx.proto)
		sign_and_send = any([seedfiles, kl, kal])

	if not silent:
		msg(green('ORIGINAL TRANSACTION'))
		msg(orig_tx.info.format(terse=True, sort='raw'))

	from .tw.ctl import TwCtl
	tx = BumpTX(
		cfg  = cfg,
		data = orig_tx.__dict__,
		automount = cfg.autosign,
		check_sent = cfg.autosign or sign_and_send,
		new_outputs = bool(cfg._args),
		twctl = await TwCtl(cfg, orig_tx.proto) if orig_tx.proto.tokensym else None)

	if tx.new_outputs:
		await tx.create(cfg._args, caller='txdo' if sign_and_send else 'txcreate')
	else:
		await tx.create_feebump(silent=silent)

	if not silent:
		msg(green('\nREPLACEMENT TRANSACTION:'))
		msg_r(tx.info.format(terse=True, sort='raw'))

	if sign_and_send:
		tx2 = UnsignedTX(cfg=cfg, data=tx.__dict__)
		if tx3 := await tx2.sign(
				TxKeys(cfg, tx2, seedfiles=seedfiles, keylist=kl, keyaddrlist=kal).keys):
			tx4 = await OnlineSignedTX(cfg=cfg, data=tx3.__dict__)
			tx4.file.write(ask_write=False)
			await tx4.send(cfg, asi if cfg.autosign else None)
		else:
			die(2, 'Transaction could not be signed')
	else:
		tx.file.write(
			outdir                = asi.txauto_dir if cfg.autosign else None,
			ask_write             = not cfg.yes,
			ask_write_default_yes = False,
			ask_overwrite         = not cfg.yes)

async_run(cfg, main)
