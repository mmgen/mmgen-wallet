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
mmgen-txdo: Create, sign and broadcast an online MMGen transaction
"""

from .common import *
from .wallet import Wallet
from .subseed import SubSeedIdxRange

opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': f'Create, sign and send an {g.proj_name} transaction',
		'usage':   '[opts]  <addr,amt> ... [change addr] [addr file] ... [seed source] ...',
		'options': """
-h, --help             Print this help message
--, --longhelp         Print help message for long options (common options)
-a, --tx-fee-adj=    f Adjust transaction fee by factor 'f' (see below)
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
                       brainwallet input
-B, --no-blank         Don't blank screen before displaying unspent outputs
-c, --comment-file=  f Source the transaction's comment from file 'f'
-C, --tx-confs=      c Desired number of confirmations (default: {g.tx_confs})
-d, --outdir=        d Specify an alternate directory 'd' for output
-D, --contract-data= D Path to hex-encoded contract data (ETH only)
-e, --echo-passphrase  Print passphrase to screen when typing it
-E, --fee-estimate-mode=M Specify the network fee estimate mode.  Choices:
                       {fe_all}.  Default: {fe_dfl!r}
-f, --tx-fee=        f Transaction fee, as a decimal {cu} amount or as
                       {fu} (an integer followed by {fl}).
                       See FEE SPECIFICATION below.  If omitted, fee will be
                       calculated using network fee estimation.
-g, --tx-gas=        g Specify start gas amount in Wei (ETH only)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-i, --in-fmt=        f Input is from wallet format 'f' (see FMT CODES below)
-I, --inputs=        i Specify transaction inputs (comma-separated list of
                       MMGen IDs or coin addresses).  Note that ALL unspent
                       outputs associated with each address will be included.
-l, --seed-len=      l Specify wallet seed length of 'l' bits. This option
                       is required only for brainwallet and incognito inputs
                       with non-standard (< {dsl}-bit) seed lengths.
-k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
-K, --keygen-backend=n Use backend 'n' for public key generation.  Options
                       for {coin_id}: {kgs}
-L, --locktime=      t Lock time (block height or unix seconds) (default: 0)
-m, --minconf=n        Minimum number of confirmations required to spend
                       outputs (default: 1)
-M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
                       address file (output of '{pnl}-keygen'). Permits
                       online signing without an {pnm} seed source. The
                       key-address file is also used to verify {pnm}-to-{cu}
                       mappings, so the user should record its checksum.
-O, --old-incog-fmt    Specify old-format incognito input
-p, --hash-preset=   p Use the scrypt hash parameters defined by preset 'p'
                       for password hashing (default: '{g.dfl_hash_preset}')
-P, --passwd-file=   f Get {pnm} wallet passphrase from file 'f'
-r, --rbf              Make transaction BIP 125 (replace-by-fee) replaceable
-q, --quiet            Suppress warnings; overwrite files without prompting
-u, --subseeds=      n The number of subseed pairs to scan for (default: {ss},
                       maximum: {ss_max}). Only the default or first supplied
                       wallet is scanned for subseeds.
-v, --verbose          Produce more verbose output
-V, --vsize-adj=     f Adjust transaction's estimated vsize by factor 'f'
-X, --cached-balances  Use cached balances (Ethereum only)
-y, --yes              Answer 'yes' to prompts, suppress non-essential output
-z, --show-hash-presets Show information on available hash presets
""",
	'notes': """
{}{}{}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

FMT CODES:

  {f}
"""
	},
	'code': {
		'options': lambda proto,help_notes,s: s.format(
			g=g,pnm=g.proj_name,pnl=g.proj_name.lower(),
			kgs=help_notes('keygen_backends'),
			coin_id=help_notes('coin_id'),
			fu=help_notes('rel_fee_desc'),
			fl=help_notes('fee_spec_letters'),
			ss=help_notes('dfl_subseeds'),
			ss_max=SubSeedIdxRange.max_idx,
			fe_all=fmt_list(g.autoset_opts['fee_estimate_mode'].choices,fmt='no_spc'),
			fe_dfl=g.autoset_opts['fee_estimate_mode'].choices[0],
			dsl=help_notes('dfl_seed_len'),
			cu=proto.coin),
		'notes': lambda help_notes,s: s.format(
			help_notes('txcreate'),
			help_notes('fee'),
			help_notes('txsign'),
			f=help_notes('fmt_codes')),
	}
}

cmd_args = opts.init(opts_data)

from .tx import *
from .txsign import *

seed_files = get_seed_files(opt,cmd_args)

async def main():
	from .tw import TrackingWallet

	from .protocol import init_proto_from_opts
	proto = init_proto_from_opts()

	tx1 = MMGenTX.New(
		proto = proto,
		tw    = await TrackingWallet(proto) if proto.tokensym else None )

	from .rpc import rpc_init
	tx1.rpc = await rpc_init(proto)

	tx2 = await tx1.create(
		cmd_args = cmd_args,
		locktime = int(opt.locktime or 0),
		caller   = 'txdo' )

	kal = get_keyaddrlist(proto,opt)
	kl = get_keylist(proto,opt)

	tx3 = await txsign(tx2,seed_files,kl,kal)

	if tx3:
		tx3.write_to_file(ask_write=False)
		await tx3.send(exit_on_fail=True)
		tx3.write_to_file(ask_overwrite=False,ask_write=False)
		tx3.print_contract_addr()
	else:
		die(2,'Transaction could not be signed')

run_session(main())
