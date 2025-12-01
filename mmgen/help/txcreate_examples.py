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
help.txcreate_examples: txcreate and txdo help examples for the MMGen Wallet suite
"""

from ..cfg import gc

def help(proto, cfg):

	mmtype = 'B' if 'B' in proto.mmtypes else proto.mmtypes[0]
	from ..tool.coin import tool_cmd
	t = tool_cmd(cfg, mmtype=mmtype)
	addr = t.privhex2addr('bead' * 16)
	sample_addr = addr.views[addr.view_pref]

	match proto.base_proto:
		case 'Bitcoin':
			return f"""
EXAMPLES:

  Send 0.123 {proto.coin} to an external {proto.name} address, returning the change to a
  specific MMGen address in the tracking wallet:

    $ {gc.prog_name} {sample_addr},0.123 01ABCDEF:{mmtype}:7

  Same as above, but select the change address automatically:

    $ {gc.prog_name} {sample_addr},0.123 01ABCDEF:{mmtype}

  Same as above, but select the change address automatically by address type:

    $ {gc.prog_name} {sample_addr},0.123 {mmtype}

  Same as above, but reduce verbosity and specify fee of 20 satoshis
  per byte:

    $ {gc.prog_name} -q -f 20s {sample_addr},0.123 {mmtype}

  Send entire balance of selected inputs minus fee to an external {proto.name}
  address:

    $ {gc.prog_name} {sample_addr}

  Send entire balance of selected inputs minus fee to first unused wallet
  address of specified type:

    $ {gc.prog_name} {mmtype}
"""

		case 'Monero':
			return f"""
EXAMPLES:

  Send 0.123 {proto.coin} to an external {proto.name} address:

    $ {gc.prog_name} {sample_addr},0.123
"""

		case _:
			return f"""
EXAMPLES:

  Send 0.123 {proto.coin} to an external {proto.name} address:

    $ {gc.prog_name} {sample_addr},0.123

  Send 0.123 {proto.coin} to another account in wallet 01ABCDEF:

    $ {gc.prog_name} 01ABCDEF:{mmtype}:7,0.123
"""
