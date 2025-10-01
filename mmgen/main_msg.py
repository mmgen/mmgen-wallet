#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
mmgen-msg: Message signing operations for the MMGen suite
"""

import sys
from .cfg import Config
from .base_obj import AsyncInit
from .util import msg, suf, async_run, die
from .msg import (
	NewMsg,
	UnsignedMsg,
	SignedMsg,
	SignedOnlineMsg,
	ExportedMsgSigs,
)

class MsgOps:
	ops = ('create', 'sign', 'verify')

	class create:

		def __init__(self, msg, addr_specs):
			NewMsg(
				cfg       = cfg,
				coin      = cfg._proto.coin,
				network   = cfg._proto.network,
				message   = msg,
				addrlists = addr_specs,
				msghash_type = cfg.msghash_type
			).write_to_file(ask_overwrite=False)

	class sign(metaclass=AsyncInit):

		async def __init__(self, msgfile, wallet_files):

			m = UnsignedMsg(cfg, infile=msgfile)

			if not wallet_files:
				from .filename import find_file_in_dir
				from .wallet import get_wallet_cls
				wallet_files = [find_file_in_dir(get_wallet_cls('mmgen'), cfg.data_dir)]

			await m.sign(wallet_files)

			m = SignedMsg(cfg, data=m.__dict__)

			m.write_to_file(ask_overwrite=False)

			if m.data.get('failed_sids'):
				sys.exit(1)

	class verify(sign):

		async def __init__(self, msgfile, *, addr=None):
			try:
				m = SignedOnlineMsg(cfg, infile=msgfile)
			except:
				m = ExportedMsgSigs(cfg, infile=msgfile)

			nSigs = await m.verify(addr=addr)

			summary = f'{nSigs} signature{suf(nSigs)} verified'

			if cfg.quiet:
				msg(summary)
			else:
				cfg._util.stdout_or_pager(m.format(addr) + '\n\n' + summary + '\n')

			if m.data.get('failed_sids'):
				sys.exit(1)

	class export(sign):

		async def __init__(self, msgfile, *, addr=None):

			from .fileutil import write_data_to_file
			write_data_to_file(
				cfg     = cfg,
				outfile = 'signatures.json',
				data    = SignedOnlineMsg(cfg, infile=msgfile).get_json_for_export(addr=addr),
				desc    = 'signature data')

opts_data = {
	'text': {
		'desc': 'Perform message signing operations for MMGen addresses',
		'usage2': [
			'[opts] create MESSAGE_TEXT ADDRESS_SPEC [...]',
			'[opts] sign   MESSAGE_FILE [WALLET_FILE ...]',
			'[opts] verify MESSAGE_FILE [MMGen ID]',
			'[opts] verify <exported JSON dump file> [address]',
			'[opts] export MESSAGE_FILE [MMGen ID]',
		],
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long (global) options
-d, --outdir=d       Output file to directory 'd' instead of working dir
-t, --msghash-type=T Specify the message hash type.  Supported values:
                     'eth_sign' (ETH default), 'raw' (non-ETH default)
-q, --quiet          Produce quieter output
""",
	'notes': """

                             SUPPORTED OPERATIONS

create - create a raw MMGen message file with specified message text for
         signing for addresses specified by ADDRESS_SPEC (see ADDRESS
         SPECIFIER below)
sign   - perform signing operation on an unsigned MMGen message file
verify - verify and display the contents of a signed MMGen message file
export - dump signed MMGen message file to ‘signatures.json’, including only
         data relevant for a third-party verifier


                              ADDRESS SPECIFIER

The `create` operation takes one or more ADDRESS_SPEC arguments with the
following format:

    SEED_ID:ADDRTYPE_CODE:ADDR_IDX_SPEC

where ADDRTYPE_CODE is a one-letter address type code from the list below, and
ADDR_IDX_SPEC is a comma-separated list of address indexes or hyphen-separated
address index ranges.

{n_at}


                                    NOTES

Message signing operations are supported for Bitcoin, Ethereum and code forks
thereof.

By default, Ethereum messages are prefixed before hashing in conformity with
the standard defined by the Geth ‘eth_sign’ JSON-RPC call.  This behavior may
be overridden with the --msghash-type option.

Messages signed for Segwit-P2SH addresses cannot be verified directly using
the Bitcoin Core `verifymessage` RPC call, since such addresses are not hashes
of public keys.  As a workaround for this limitation, this utility creates for
each Segwit-P2SH address a non-Segwit address with the same public key to be
used for verification purposes.  This non-Segwit verifying address should then
be passed on to the verifying party together with the signature. The verifying
party may then use a tool of their choice (e.g. `mmgen-tool addr2pubhash`) to
assure themselves that the verifying address and Segwit address share the same
public key.

Unfortunately, the aforementioned limitation applies to Segwit-P2PKH (Bech32)
addresses as well, despite the fact that Bech32 addresses are hashes of public
keys (we consider this an implementation shortcoming of `verifymessage`).
Therefore, the above procedure must be followed to verify messages for Bech32
addresses too.  `mmgen-tool addr2pubhash` or `bitcoin-cli validateaddress`
may then be used to demonstrate that the two addresses share the same public
key.


                                   EXAMPLES

Create a raw message file for the specified message and specified addresses,
where DEADBEEF is the Seed ID of the user’s default wallet and BEEFCAFE one
of its subwallets:
$ mmgen-msg create '16/3/2022 Earthquake strikes Fukushima coast' DEADBEEF:B:1-3,10,98 BEEFCAFE:S:3,9

Sign the raw message file created by the previous step:
$ mmgen-msg sign <raw message file>

Sign the raw message file using an explicitly supplied wallet:
$ mmgen-msg sign <raw message file> DEADBEEF.bip39

Verify and display all signatures in the signed message file:
$ mmgen-msg verify <signed message file>

Verify and display a single signature in the signed message file:
$ mmgen-msg verify <signed message file> DEADBEEF:B:98

Export data relevant for a third-party verifier to ‘signatures.json’:
$ mmgen-msg export <signed message file>

Same as above, but export only one signature:
$ mmgen-msg export <signed message file> DEADBEEF:B:98

Verify and display the exported JSON signature data:
$ mmgen-msg verify signatures.json
"""
	},
	'code': {
		'notes': lambda help_notes, s: s.format(
			n_at = help_notes('address_types'),
		)
	}
}

cfg = Config(opts_data=opts_data, need_amt=False)

cmd_args = cfg._args

if len(cmd_args) < 2:
	cfg._usage()

op = cmd_args.pop(0)
arg1 = cmd_args.pop(0)

if cfg.msghash_type and op != 'create':
	die(1, '--msghash-type option may only be used with the "create" command')

async def main():
	match op:
		case 'create':
			if not cmd_args:
				cfg._usage()
			MsgOps.create(arg1, ' '.join(cmd_args))
		case 'sign':
			await MsgOps.sign(arg1, cmd_args[:])
		case 'verify' | 'export':
			if len(cmd_args) not in (0, 1):
				cfg._usage()
			await getattr(MsgOps, op)(arg1, addr=cmd_args[0] if cmd_args else None)
		case _:
			die(1, f'{op!r}: unrecognized operation')

async_run(cfg, main)
