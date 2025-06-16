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
help.txcreate: txcreate and txdo help notes for the MMGen Wallet suite
"""

def help(proto, cfg):
	outputs_info = (
	"""
Outputs are specified in the form ADDRESS,AMOUNT or ADDRESS.  The first form
creates an output sending the given amount to the given address.  The bare
address form designates the given address as either the change output or the
sole output of the transaction (excluding any data output).  Exactly one bare
address argument is required.

For convenience, the bare address argument may be given as ADDRTYPE_CODE or
SEED_ID:ADDRTYPE_CODE (see ADDRESS TYPES below). In the first form, the first
unused address of type ADDRTYPE_CODE for each Seed ID in the tracking wallet
will be displayed in a menu, with the user prompted to select one.  In the
second form, the user specifies the Seed ID as well, allowing the script to
select the transaction’s change output or single output without prompting.
See EXAMPLES below.

A single DATA_SPEC argument may also be given on the command line to create
an OP_RETURN data output with a zero spend amount.  This is the preferred way
to embed data in the blockchain.  DATA_SPEC may be of the form "data":DATA
or "hexdata":DATA. In the first form, DATA is a string in your system’s native
encoding, typically UTF-8.  In the second, DATA is a hexadecimal string (with
the leading ‘0x’ omitted) encoding the binary data to be embedded.  In both
cases, the resulting byte string must not exceed {bl} bytes in length.
""".format(bl=proto.max_op_return_data_len)
	if proto.base_proto == 'Bitcoin' else """
The transaction output is specified in the form ADDRESS,AMOUNT.
""")

	fee_info = """
If the transaction fee is not specified on the command line (see FEE
SPECIFICATION below), it will be calculated dynamically using network fee
estimation for the default (or user-specified) number of confirmations.
If network fee estimation fails, the user will be prompted for a fee.

Network-estimated fees will be multiplied by the value of --fee-adjust, if
specified.
""" if proto.has_usr_fee else ''

	return f"""
The transaction’s outputs are listed on the command line, while its inputs
are chosen from a list of the wallet’s unspent outputs via an interactive
menu.  Alternatively, inputs may be specified using the --inputs option.

Addresses on the command line can be either native coin addresses or MMGen
IDs in the form SEED_ID:ADDRTYPE_CODE:INDEX.
{outputs_info}{fee_info}"""
