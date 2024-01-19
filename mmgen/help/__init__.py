#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
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
help: help notes for MMGen suite commands
"""

from ..cfg import gc

def help_notes_func(proto,cfg,k):

	def fee_spec_letters(use_quotes=False):
		cu = proto.coin_amt.units
		sep,conj = ((',',' or '),("','","' or '"))[use_quotes]
		return sep.join(u[0] for u in cu[:-1]) + ('',conj)[len(cu)>1] + cu[-1][0]

	def fee_spec_names():
		cu = proto.coin_amt.units
		return ', '.join(cu[:-1]) + ('',' and ')[len(cu)>1] + cu[-1] + ('',',\nrespectively')[len(cu)>1]

	def coind_exec():
		from ..daemon import CoinDaemon
		return (
			CoinDaemon(cfg,proto.coin).exec_fn if proto.coin in CoinDaemon.coins else 'bitcoind' )

	class help_notes:

		def MasterShareIdx():
			from ..seedsplit import MasterShareIdx
			return MasterShareIdx

		def tool_help():
			from ..tool.help import main_help
			return main_help()

		def dfl_subseeds():
			from ..subseed import SubSeedList
			return str(SubSeedList.dfl_len)

		def dfl_seed_len():
			from ..seed import Seed
			return str(Seed.dfl_len)

		def password_formats():
			from ..passwdlist import PasswordList
			pwi_fs = '{:8} {:1} {:26} {:<7}  {:<7}  {}'
			return '\n  '.join(
				[pwi_fs.format('Code','','Description','Min Len','Max Len','Default Len')] +
				[pwi_fs.format(k,'-',v.desc,v.min_len,v.max_len,v.dfl_len) for k,v in PasswordList.pw_info.items()]
			)

		def dfl_mmtype():
			from ..addr import MMGenAddrType
			return "'{}' or '{}'".format(
				proto.dfl_mmtype,
				MMGenAddrType.mmtypes[proto.dfl_mmtype].name )

		def address_types():
			from ..addr import MMGenAddrType
			return '\n  '.join([
				"'{}','{:<12} - {}".format( k, v.name+"'", v.desc )
					for k,v in MMGenAddrType.mmtypes.items()
			])

		def fmt_codes():
			from ..wallet import format_fmt_codes
			return '\n  '.join( format_fmt_codes().splitlines() )

		def coin_id():
			return proto.coin_id

		def keygen_backends():
			from ..keygen import get_backends
			from ..addr import MMGenAddrType
			backends = get_backends(
				MMGenAddrType(proto,cfg.type or proto.dfl_mmtype).pubkey_type
			)
			return ' '.join( f'{n}:{k}{" [default]" if n==1 else ""}' for n,k in enumerate(backends,1) )

		def coind_exec():
			return coind_exec()

		def coin_daemon_network_ids():
			from ..daemon import CoinDaemon
			from ..util import fmt_list
			return fmt_list(CoinDaemon.get_network_ids(cfg),fmt='bare')

		def rel_fee_desc():
			from ..tx import BaseTX
			return BaseTX(cfg=cfg,proto=proto).rel_fee_desc

		def fee_spec_letters():
			return fee_spec_letters()

		def fee():
			from ..tx import BaseTX
			return """
                               FEE SPECIFICATION

Transaction fees, both on the command line and at the interactive prompt, may
be specified as either absolute {c} amounts, using a plain decimal number, or
as {r}, using an integer followed by '{l}', for {u}.
""".format(
	c = proto.coin,
	r = BaseTX(cfg=cfg,proto=proto).rel_fee_desc,
	l = fee_spec_letters(use_quotes=True),
	u = fee_spec_names() )

		def passwd():
			return """
PASSPHRASE NOTE:

For passphrases all combinations of whitespace are equal, and leading and
trailing space are ignored.  This permits reading passphrase or brainwallet
data from a multi-line file with free spacing and indentation.
""".strip()

		def brainwallet():
			return """
BRAINWALLET NOTE:

To thwart dictionary attacks, it’s recommended to use a strong hash preset
with brainwallets.  For a brainwallet passphrase to generate the correct
seed, the same seed length and hash preset parameters must always be used.
""".strip()

		def txcreate_examples():

			mmtype = 'S' if 'segwit' in proto.caps else 'C'
			from ..tool.coin import tool_cmd
			t = tool_cmd(cfg,mmtype=mmtype)
			sample_addr = t.privhex2addr('bead'*16)

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

		def txcreate():
			return f"""
The transaction’s outputs are listed on the command line, while its inputs
are chosen from a list of the wallet’s unspent outputs via an interactive
menu.  Alternatively, inputs may be specified using the --inputs option.

All addresses on the command line can be either {proto.name} addresses or MMGen
IDs in the form <seed ID>:<address type letter>:<index>.

Outputs are specified in the form <address>,<amount>, with the change output
specified by address only.  Alternatively, the change output may be an
addrlist ID in the form <seed ID>:<address type letter>, in which case the
first unused address in the tracking wallet matching the requested ID will
be automatically selected as the change output.

If the transaction fee is not specified on the command line (see FEE
SPECIFICATION below), it will be calculated dynamically using network fee
estimation for the default (or user-specified) number of confirmations.
If network fee estimation fails, the user will be prompted for a fee.

Network-estimated fees will be multiplied by the value of --fee-adjust, if
specified.

To send the value of all inputs (minus TX fee) to a single output, specify
a single address with no amount on the command line.  Alternatively, an
addrlist ID may be specified, and the address will be chosen automatically
as described above for the change output.
"""

		def txsign():
			from ..proto.btc.params import mainnet
			return """
Transactions may contain both {pnm} or non-{pnm} input addresses.

To sign non-{pnm} inputs, a {wd}flat key list is used
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
	wd  = (f'{coind_exec()} wallet dump or ' if isinstance(proto,mainnet) else ''),
	pnm = gc.proj_name,
	pnu = proto.name,
	pnl = gc.proj_name.lower() )

		def subwallet():
			from ..subseed import SubSeedIdxRange
			return f"""
SUBWALLETS:

Subwallets (subseeds) are specified by a ‘Subseed Index’ consisting of:

  a) an integer in the range 1-{SubSeedIdxRange.max_idx}, plus
  b) an optional single letter, ‘L’ or ‘S’

The letter designates the length of the subseed.  If omitted, ‘L’ is assumed.

Long (‘L’) subseeds are the same length as their parent wallet’s seed
(typically 256 bits), while short (‘S’) subseeds are always 128-bit.
The long and short subseeds for a given index are derived independently,
so both may be used.

MMGen Wallet has no notion of ‘depth’, and to an outside observer subwallets
are identical to ordinary wallets.  This is a feature rather than a bug, as
it denies an attacker any way of knowing whether a given wallet has a parent.

Since subwallets are just wallets, they may be used to generate other
subwallets, leading to hierarchies of arbitrary depth.  However, this is
inadvisable in practice for two reasons:  Firstly, it creates accounting
complexity, requiring the user to independently keep track of a derivation
tree.  More importantly, however, it leads to the danger of Seed ID
collisions between subseeds at different levels of the hierarchy, as
MMGen checks and avoids ID collisions only among sibling subseeds.

An exception to this caveat would be a multi-user setup where sibling
subwallets are distributed to different users as their default wallets.
Since the subseeds derived from these subwallets are private to each user,
Seed ID collisions among them doesn’t present a problem.

A safe rule of thumb, therefore, is for *each user* to derive all of his/her
subwallets from a single parent.  This leaves each user with a total of two
million subwallets, which should be enough for most practical purposes.
""".strip()

	return getattr(help_notes,k)()
