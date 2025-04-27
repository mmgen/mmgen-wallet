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
help.txsign: txsign help notes for the MMGen Wallet suite
"""

from ..cfg import gc
from ..daemon import CoinDaemon

def help(proto, cfg):

	def coind_exec():
		return CoinDaemon(cfg, network_id=proto.coin).exec_fn if proto.coin in CoinDaemon.coins else 'bitcoind'

	return """
Transactions may contain both {pnm} or non-{pnm} input addresses.

To sign non-{pnm} inputs, a coin daemon wallet dump or flat key list is used
as the key source (--keys-from-file option).

To sign {pnm} inputs, key data is generated from a seed as with the
{pnl}-addrgen and {pnl}-keygen commands.  Alternatively, a key-address file
may be used (--mmgen-keys-from-file option).

Multiple wallets or other seed files can be listed on the command line in
any order.  If the seeds required to sign the transaction’s inputs are not
found in these files (or in the default wallet), the user will be prompted
for seed data interactively.

To prevent an attacker from crafting transactions with bogus {pnm}-to-{pnu}
address mappings, all outputs to {pnm} addresses are verified with a seed
source.  Therefore, seed files or a key-address file for all {pnm} outputs
must also be supplied on the command line if the data can’t be found in the
default wallet.
""".format(
	pnm = gc.proj_name,
	pnu = proto.name,
	pnl = gc.proj_name.lower())
