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
help: help notes functions for MMGen suite commands
"""

class help_notes:

	def __init__(self, proto, cfg):
		self.proto = proto
		self.cfg = cfg

	def txcreate_args(self):
		match self.proto.base_proto:
			case 'Bitcoin':
				return '[ADDR,AMT ... | DATA_SPEC] ADDR [addr file ...]'
			case 'Monero':
				return 'ADDR,AMT'
			case _:
				return 'ADDR,AMT [addr file ...]'

	def swaptxcreate_args(self):
		return 'COIN1 [AMT CHG_ADDR] COIN2 [ADDR]'

	def account_info_desc(self):
		return 'unspent outputs' if self.proto.base_proto == 'Bitcoin' else 'account info'

	def fee_spec_letters(self, *, use_quotes=False, proto=None):
		cu = (proto or self.proto).coin_amt.units
		pfx, sfx, sep, conj = (('', '', ',', ' or '), ("‘", "’", "’,‘", "’ or ‘"))[use_quotes]
		return pfx + sep.join(u[0] for u in cu[:-1]) + ('', conj)[len(cu)>1] + cu[-1][0] + sfx

	def stream_interval(self):
		from ..tx.new_swap import get_swap_proto_mod
		return get_swap_proto_mod(self.cfg.swap_proto).SwapCfg(self.cfg).si.dfl

	def fee_spec_names(self, *, proto=None, linebreak=' '):
		cu = (proto or self.proto).coin_amt.units
		return (
			', '.join(cu[:-1])
			+ ('', ' and ')[len(cu)>1]
			+ cu[-1]
			+ (f',{linebreak}respectively' if len(cu) > 1 else ''))

	def dfl_twname(self):
		from ..proto.btc.rpc.local import BitcoinRPCClient
		return BitcoinRPCClient.dfl_twname

	def tw_dir(self):
		from ..tw.ctl import TwCtl
		twctl_cls = self.proto.base_proto_subclass(TwCtl, 'tw.ctl')
		if hasattr(twctl_cls, 'get_tw_dir'):
			return twctl_cls.get_tw_dir(self.cfg, self.proto)
		else:
			raise ValueError(f'protocol {self.proto.name} does not support tracking wallet with store')

	def MasterShareIdx(self):
		from ..seedsplit import MasterShareIdx
		return MasterShareIdx

	def tool_help(self):
		from ..tool.help import main_help
		return main_help()

	def dfl_subseeds(self):
		from ..subseed import SubSeedList
		return str(SubSeedList.dfl_len)

	def dfl_seed_len(self):
		from ..seed import Seed
		return str(Seed.dfl_len)

	def password_formats(self):
		from ..passwdlist import PasswordList
		pwi_fs = '{:8} {:1} {:26} {:<7}  {:<7}  {}'
		return '\n  '.join(
			[pwi_fs.format('Code', '', 'Description', 'Min Len', 'Max Len', 'Default Len')] +
			[pwi_fs.format(k, '-', v.desc, v.min_len, v.max_len, v.dfl_len)
				for k, v in PasswordList.pw_info.items()]
		)

	def dfl_mmtype(self):
		from ..addr import MMGenAddrType
		return "'{}' or '{}'".format(self.proto.dfl_mmtype, MMGenAddrType.mmtypes[self.proto.dfl_mmtype].name)

	def address_types(self):
		from ..addr import MMGenAddrType
		return """
ADDRESS TYPES:

  Code Type           Description
  ---- ----           -----------
  """ + format('\n  '.join(['‘{}’  {:<12} - {}'.format(k, v.name, v.desc)
				for k, v in MMGenAddrType.mmtypes.items()]))

	def fmt_codes(self):
		from ..wallet import format_fmt_codes
		return """
FMT CODES:

  """ + '\n  '.join(format_fmt_codes().splitlines())

	def coin_id(self):
		return self.proto.coin_id

	def keygen_backends(self):
		from ..keygen import get_backends
		from ..addr import MMGenAddrType
		backends = get_backends(
			MMGenAddrType(self.proto, self.cfg.type or self.proto.dfl_mmtype).pubkey_type
		)
		return ' '.join('{n}:{k}{t}'.format(n=n, k=k, t=('', ' [default]')[n == 1])
			for n, k in enumerate(backends, 1))

	def coin_daemon_network_ids(self):
		from ..daemon import CoinDaemon
		from ..util import fmt_list
		return fmt_list(CoinDaemon.get_network_ids(self.cfg), fmt='bare')

	def tx_proxies(self):
		from ..util import fmt_list
		return fmt_list(self.cfg._autoset_opts['tx_proxy'].choices, fmt='fancy')

	def rel_fee_desc(self):
		if self.proto.has_usr_fee:
			from ..tx import BaseTX
			return BaseTX(cfg=self.cfg, proto=self.proto).rel_fee_desc
		else:
			return ''

	def gas_limit(self, target):
		return """
                                 GAS LIMIT

This option specifies the maximum gas allowance for an Ethereum transaction.
It’s generally of interest only for token transactions or swap transactions
from token assets.

Parameter must be an integer or one of the special values ‘fallback’ (for a
locally computed sane default) or ‘auto’ (for gas estimate via an RPC call,
in the case of a token transaction, or locally computed default, in the case
of a standard transaction). The default is ‘auto’.

		""" if target == 'swaptx' or self.proto.base_coin == 'ETH' else ''

	def fee(self, all_coins=False):

		if not self.proto.has_usr_fee:
			return ''

		from ..tx import BaseTX
		text = """
                               FEE SPECIFICATION

Transaction fees, both on the command line and at the interactive prompt, may
be specified as either absolute coin amounts, using a plain decimal number, or
as {r}, using an integer followed by {l}, for{s}{u}""".format(
			r = BaseTX(cfg=self.cfg, proto=self.proto).rel_fee_desc,
			l = self.fee_spec_letters(use_quotes=True),
			s = '\n' if self.proto.base_coin == 'ETH' else ' ',
			u = self.fee_spec_names())

		if all_coins:
			from ..protocol import init_proto
			eth_proto = init_proto(self.cfg, 'eth', need_amt=True)
			return text + (
				' (for\nBitcoin, Litecoin and Bitcoin Cash)'
				+ ", or {r}, using an integer followed\nby {l}, for {u}".format(
					r = BaseTX(cfg=self.cfg, proto=eth_proto).rel_fee_desc,
					l = self.fee_spec_letters(use_quotes=True, proto=eth_proto),
					u = self.fee_spec_names(proto=eth_proto, linebreak='\n'))
				+ ' (for Ethereum)\n\n')
		else:
			return text + '.\n\n'

	def passwd(self):
		return """
PASSPHRASE NOTE:

For passphrases all combinations of whitespace are equal, and leading and
trailing space are ignored.  This permits reading passphrase or brainwallet
data from a multi-line file with free spacing and indentation.
""".strip()

	def brainwallet(self):
		return """
BRAINWALLET NOTE:

To thwart dictionary attacks, it’s recommended to use a strong hash preset
with brainwallets.  For a brainwallet passphrase to generate the correct
seed, the same seed length and hash preset parameters must always be used.
""".strip()
