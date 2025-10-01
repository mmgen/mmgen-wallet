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
mmgen-txdo: Create, sign and send an online MMGen transaction
"""

from .cfg import gc, Config
from .util import die, fmt_list, async_run
from .subseed import SubSeedIdxRange

target = gc.prog_name.split('-')[1].removesuffix('do')

opts_data = {
	'filter_codes': {
		'tx':     ['-', 't'],
		'swaptx': ['-', 's'],
	}[target],
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc': {
			'tx':     f'Create, sign and send an {gc.proj_name} transaction',
			'swaptx': f'Create, sign and send a DEX swap transaction from one {gc.proj_name} tracking wallet to another',
		}[target],
		'usage':   '[opts] {u_args} [addr file ...] [seed source ...]',
		'options': """
			-- -h, --help             Print this help message
			-- --, --longhelp         Print help message for long (global) options
			r- -A, --fee-adjust=    f Adjust transaction fee by factor ‘f’ (see below)
			-- -b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
			+                         brainwallet input
			-- -B, --no-blank         Don't blank screen before displaying {a_info}
			-- -c, --comment-file=  f Source the transaction's comment from file 'f'
			b- -C, --fee-estimate-confs=c Desired number of confirmations for fee estimation
			+                         (default: {cfg.fee_estimate_confs})
			-- -d, --outdir=        d Specify an alternate directory 'd' for output
			e- -D, --contract-data= D Path to file containing hex-encoded contract data
			-- -e, --echo-passphrase  Print passphrase to screen when typing it
			b- -E, --fee-estimate-mode=M Specify the network fee estimate mode.  Choices:
			+                         {fe_all}.  Default: {fe_dfl!r}
			r- -f, --fee=           f Transaction fee, as a decimal {cu} amount or as
			+                         {fu} (an integer followed by {fl}).
			+                         See FEE SPECIFICATION below.  If omitted, fee will be
			+                         calculated using network fee estimation.
			et -g, --gas=N            Set the gas limit (see GAS LIMIT below)
			-s -g, --gas=N            Set the gas limit for Ethereum (see GAS LIMIT below)
			-s -G, --router-gas=N     Set the gas limit for the Ethereum router contract
			+                         (integer).  When unset, a hardcoded default will be
			+                         used.  Applicable only for swaps from token assets.
			-- -H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
			+                        'f' at offset 'o' (comma-separated)
			-- -i, --in-fmt=        f Input is from wallet format 'f' (see FMT CODES below)
			-- -I, --inputs=        i Specify transaction inputs (comma-separated list of
			+                         MMGen IDs or coin addresses).  Note that ALL unspent
			+                         outputs associated with each address will be included.
			-- -l, --seed-len=      l Specify wallet seed length of 'l' bits. This option
			+                         is required only for brainwallet and incognito inputs
			+                         with non-standard (< {dsl}-bit) seed lengths.
			-- -k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
			-- -K, --keygen-backend=n Use backend 'n' for public key generation.  Options
			+                         for {coin_id}: {kgs}
			-s -l, --trade-limit=L    Minimum swap amount, as either percentage or absolute
			+                         coin amount (see TRADE LIMIT below)
			bt -l, --locktime=      t Lock time (block height or unix seconds) (default: 0)
			b- -L, --autochg-ignore-labels Ignore labels when autoselecting change addresses
			-- -m, --minconf=n        Minimum number of confirmations required to spend
			+                         outputs (default: 1)
			-- -M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
			+                         address file (output of '{pnl}-keygen'). Permits
			+                         online signing without an {pnm} seed source. The
			+                         key-address file is also used to verify {pnm}-to-{cu}
			+                         mappings, so the user should record its checksum.
			e- -n, --tx-proxy=P       Send transaction via public TX proxy ‘P’ (supported
			+                         proxies: {tx_proxies}).  This is done via a publicly
			+                         accessible web page, so no API key or registration is
			+                         required.
			-- -O, --old-incog-fmt    Specify old-format incognito input
			-- -p, --hash-preset=   p Use the scrypt hash parameters defined by preset 'p'
			+                         for password hashing (default: '{gc.dfl_hash_preset}')
			-- -P, --passwd-file=   f Get {pnm} wallet passphrase from file 'f'
			-- -q, --quiet            Suppress warnings; overwrite files without prompting
			-s -r, --stream-interval=N Set block interval for streaming swap (default: {si})
			bt -R, --no-rbf           Make transaction non-replaceable (non-replace-by-fee
			+                         according to BIP 125)
			-s -s, --swap-proto       Swap protocol to use (Default: {x_dfl},
			+                         Choices: {x_all})
			-- -T, --txhex-idx=N      Send only part ‘N’ of a multi-part transaction.
			+                         Indexing begins with one.
			-- -u, --subseeds=      n The number of subseed pairs to scan for (default: {ss},
			+                         maximum: {ss_max}). Only the default or first supplied
			+                         wallet is scanned for subseeds.
			-- -v, --verbose          Produce more verbose output
			b- -V, --vsize-adj=     f Adjust transaction's estimated vsize by factor 'f'
			e- -w, --wait             Wait for transaction confirmation
			rs -x, --proxy=P          Fetch the swap quote via SOCKS5h proxy ‘P’ (host:port).
			+                         Use special value ‘env’ to honor *_PROXY environment
			+                         vars instead.
			X- -x, --proxy=P          Connect to remote server(s) via SOCKS5h proxy ‘P’
			+                         (host:port).  Use special value ‘env’ to honor *_PROXY
			+                         environment vars instead.
			e- -X, --cached-balances  Use cached balances
			-- -y, --yes              Answer 'yes' to prompts, suppress non-essential output
			-- -z, --show-hash-presets Show information on available hash presets
		""",
		'notes': """
{c}
{n_at}

{g}{F}
                                 SIGNING NOTES
{s}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

{f}

{x}"""
	},
	'code': {
		'usage': lambda cfg, proto, help_notes, s: s.format(
			u_args  = help_notes(f'{target}create_args')),
		'options': lambda cfg, proto, help_notes, s: s.format(
			gc      = gc,
			cfg     = cfg,
			cu      = proto.coin,
			pnm     = gc.proj_name,
			pnl     = gc.proj_name.lower(),
			a_info  = help_notes('account_info_desc'),
			kgs     = help_notes('keygen_backends'),
			coin_id = help_notes('coin_id'),
			fu      = help_notes('rel_fee_desc'),
			fl      = help_notes('fee_spec_letters', use_quotes=True),
			dsl     = help_notes('dfl_seed_len'),
			ss      = help_notes('dfl_subseeds'),
			si      = help_notes('stream_interval'),
			tx_proxies = help_notes('tx_proxies'),
			ss_max  = SubSeedIdxRange.max_idx,
			fe_all  = fmt_list(cfg._autoset_opts['fee_estimate_mode'].choices, fmt='no_spc'),
			fe_dfl  = cfg._autoset_opts['fee_estimate_mode'].choices[0],
			x_all   = fmt_list(cfg._autoset_opts['swap_proto'].choices, fmt='no_spc'),
			x_dfl   = cfg._autoset_opts['swap_proto'].choices[0]),
		'notes': lambda cfg, help_mod, help_notes, s: s.format(
			c       = help_mod(f'{target}create'),
			g       = help_notes('gas_limit', target),
			F       = help_notes('fee'),
			n_at    = help_notes('address_types'),
			f       = help_notes('fmt_codes'),
			s       = help_mod('txsign'),
			x       = help_mod(f'{target}create_examples'))
	}
}

cfg = Config(opts_data=opts_data)

from .tx import NewTX, SentTX
from .tx.keys import TxKeys, pop_seedfiles

seedfiles = pop_seedfiles(cfg)

async def main():

	if target == 'swaptx':
		from .tx.new_swap import get_send_proto
		proto = get_send_proto(cfg)
	else:
		proto = cfg._proto

	tx1 = NewTX(cfg=cfg, proto=proto, target=target)

	tx2 = await tx1.create(
		cmd_args = cfg._args,
		locktime = int(cfg.locktime or 0),
		caller   = 'txdo')

	tx3 = await tx2.sign(TxKeys(cfg, tx2, seedfiles=seedfiles).keys)

	if tx3:
		tx3.file.write(ask_write=False)
		tx4 = await SentTX(cfg=cfg, data=tx3.__dict__)
		await tx4.send(cfg, asi=None)
	else:
		die(2, 'Transaction could not be signed')

async_run(cfg, main)
