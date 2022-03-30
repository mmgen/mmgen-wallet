#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
mmgen.main_msg: Message signing operations for the MMGen suite
"""

from .base_obj import AsyncInit
from .common import *
from .msg import *

class MsgOps:
	ops = ('create','sign','verify')

	class create:

		def __init__(self,msg,addr_specs):
			from .protocol import init_proto_from_opts
			proto = init_proto_from_opts()
			if proto.base_proto != 'Bitcoin':
				die('Message signing operations are supported for Bitcoin and Bitcoin-derived coins only')
			NewMsg(
				coin      = proto.coin,
				network   = proto.network,
				message   = msg,
				addrlists = addr_specs ).write_to_file( ask_overwrite=False )

	class sign(metaclass=AsyncInit):

		async def __init__(self,msgfile,wallet_files):

			m = UnsignedMsg( infile=msgfile )

			if not wallet_files:
				from .filename import find_file_in_dir
				from .wallet import get_wallet_cls
				wallet_files = [find_file_in_dir( get_wallet_cls('mmgen'), g.data_dir )]

			await m.sign(wallet_files)

			m = SignedMsg( data=m.__dict__ )

			m.write_to_file( ask_overwrite=False )

	class verify(sign):

		async def __init__(self,msgfile,addr=None):

			m = SignedOnlineMsg( infile=msgfile )

			qmsg(m.format(addr) + '\n')

			await m.verify(addr,summary=True)

opts_data = {
	'text': {
		'desc': 'Perform message signing operations for MMGen addresses',
		'usage2': [
			'[opts] create MESSAGE_TEXT ADDRESS_SPEC [...]',
			'[opts] sign   MESSAGE_FILE [WALLET_FILE ...]',
			'[opts] verify MESSAGE_FILE',
		],
		'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long options (common options)
-d, --outdir=d  Output file to directory 'd' instead of working dir
-q, --quiet     Produce quieter output
""",
	'notes': """

                             SUPPORTED OPERATIONS

create - create a raw MMGen message file with specified message text for
         signing for addresses specified by ADDRESS_SPEC (see ADDRESS
         SPECIFIER below)
sign   - perform signing operation on an unsigned MMGen message file
verify - verify and display the contents of a signed MMGen message file


                              ADDRESS SPECIFIER

The `create` operation takes one or more ADDRESS_SPEC arguments with the
following format:

    SEED_ID:ADDR_TYPE:ADDR_IDX_SPEC

where ADDR_TYPE is an address type letter from the list below, and
ADDR_IDX_SPEC is a comma-separated list of address indexes or hyphen-
separated address index ranges.


                                ADDRESS TYPES

  {n_at}


                                    NOTES

Message signing operations are currently supported for Bitcoin and Bitcoin
code fork coins only.

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
"""
	},
	'code': {
		'notes': lambda help_notes,s: s.format(
			n_at=help_notes('address_types'),
		)
	}
}

cmd_args = opts.init(opts_data)

if len(cmd_args) < 2:
	opts.usage()

op = cmd_args.pop(0)

async def main():
	if op == 'create':
		if len(cmd_args) < 2:
			opts.usage()
		MsgOps.create( cmd_args[0], ' '.join(cmd_args[1:]) )
	elif op == 'sign':
		if len(cmd_args) < 1:
			opts.usage()
		await MsgOps.sign( cmd_args[0], cmd_args[1:] )
	elif op == 'verify':
		if len(cmd_args) not in (1,2):
			opts.usage()
		await MsgOps.verify( cmd_args[0], cmd_args[1] if len(cmd_args) == 2 else None )
	else:
		die(1,f'{op!r}: unrecognized operation')

run_session(main())
