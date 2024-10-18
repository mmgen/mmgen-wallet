#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.base: base transaction class
"""

from ..cfg import gc
from ..objmethods import MMGenObject
from ..obj import (
	ImmutableAttr,
	ListItemAttr,
	MMGenListItem,
	MMGenTxComment,
	TwComment,
	CoinTxID,
	HexStr,
	NonNegativeInt
)
from ..amt import CoinAmtChk
from ..addr import MMGenID, CoinAddr
from ..util import msg, ymsg, fmt, remove_dups, make_timestamp, die

class MMGenTxIO(MMGenListItem):
	vout     = ListItemAttr(NonNegativeInt)
	amt      = ImmutableAttr(CoinAmtChk, include_proto=True)
	comment  = ListItemAttr(TwComment, reassign_ok=True)
	mmid     = ListItemAttr(MMGenID, include_proto=True)
	addr     = ImmutableAttr(CoinAddr, include_proto=True)
	confs    = ListItemAttr(int) # confs of type long exist in the wild, so convert
	txid     = ListItemAttr(CoinTxID)
	have_wif = ListItemAttr(bool, typeconv=False, delete_ok=True)

	invalid_attrs = {'proto', 'tw_copy_attrs'}

	def __init__(self, proto, **kwargs):
		self.__dict__['proto'] = proto
		MMGenListItem.__init__(self, **kwargs)

	@property
	def mmtype(self):
		"""
		Attempt to determine input or output’s MMGenAddrType.  For non-MMGen
		addresses, infer the type from the address format, returning None for
		P2PKH, which could be either 'L' or 'C'.
		"""
		return (
			str(self.mmid.mmtype) if self.mmid else
			'B' if self.addr.addr_fmt == 'bech32' else
			'S' if self.addr.addr_fmt == 'p2sh' else
			None)

class MMGenTxIOList(list, MMGenObject):

	def __init__(self, parent, data=None):
		self.parent = parent
		if data:
			assert isinstance(data, list), 'MMGenTxIOList_check1'
		else:
			data = []
		list.__init__(self, data)

class Base(MMGenObject):
	desc         = 'transaction'
	comment      = None
	txid         = None
	coin_txid    = None
	timestamp    = None
	sent_timestamp = None
	blockcount   = None
	locktime     = None
	chain        = None
	signed       = False
	non_mmgen_inputs_msg = f"""
		This transaction includes inputs with non-{gc.proj_name} addresses.  When
		signing the transaction, private keys for the addresses listed below must
		be supplied using the --keys-from-file option.  The key file must contain
		one key per line.  Please note that this transaction cannot be autosigned,
		as autosigning does not support the use of key files.

		Non-{gc.proj_name} addresses found in inputs:
		    {{}}
	"""
	file_format = 'json'

	class Input(MMGenTxIO):
		scriptPubKey = ListItemAttr(HexStr)
		sequence     = ListItemAttr(int, typeconv=False)
		tw_copy_attrs = {'scriptPubKey', 'vout', 'amt', 'comment', 'mmid', 'addr', 'confs', 'txid'}

	class Output(MMGenTxIO):
		is_chg = ListItemAttr(bool, typeconv=False)

	class InputList(MMGenTxIOList):
		desc = 'transaction inputs'

	class OutputList(MMGenTxIOList):
		desc = 'transaction outputs'

	def __init__(self, *args, **kwargs):
		self.cfg      = kwargs['cfg']
		self.inputs   = self.InputList(self)
		self.outputs  = self.OutputList(self)
		self.name     = type(self).__name__
		self.proto    = kwargs['proto']
		self.twctl    = kwargs.get('twctl')

	@property
	def coin(self):
		return self.proto.coin

	@property
	def dcoin(self):
		return self.proto.dcoin

	@property
	def info(self):
		from .info import init_info
		return init_info(self.cfg, self)

	def check_correct_chain(self):
		if hasattr(self, 'rpc'):
			if self.chain != self.rpc.chain:
				die('TransactionChainMismatch',
					f'Transaction is for {self.chain}, but coin daemon chain is {self.rpc.chain}!')

	def sum_inputs(self):
		return sum(e.amt for e in self.inputs)

	def sum_outputs(self, exclude=None):
		if exclude is None:
			olist = self.outputs
		else:
			olist = self.outputs[:exclude] + self.outputs[exclude+1:]
		if not olist:
			return self.proto.coin_amt('0')
		return sum(e.amt for e in olist)

	def _chg_output_ops(self, op):
		is_chgs = [x.is_chg for x in self.outputs]
		if is_chgs.count(True) == 1:
			return (
				is_chgs.index(True) if op == 'idx' else
				self.outputs[is_chgs.index(True)])
		elif is_chgs.count(True) == 0:
			return None
		else:
			raise ValueError('more than one change output!')

	@property
	def chg_idx(self):
		return self._chg_output_ops('idx')

	@property
	def chg_output(self):
		return self._chg_output_ops('output')

	def add_timestamp(self):
		self.timestamp = make_timestamp()

	def add_sent_timestamp(self):
		self.sent_timestamp = make_timestamp()

	def add_blockcount(self):
		self.blockcount = self.rpc.blockcount

	# returns True if comment added or changed, False otherwise
	def add_comment(self, infile=None):
		if infile:
			from ..fileutil import get_data_from_file
			self.comment = MMGenTxComment(get_data_from_file(self.cfg, infile, 'transaction comment'))
		else:
			from ..ui import keypress_confirm, line_input
			if keypress_confirm(
					self.cfg,
					prompt = 'Edit transaction comment?' if self.comment else 'Add a comment to transaction?',
					default_yes = False):
				res = MMGenTxComment(line_input(self.cfg, 'Comment: ', insert_txt=self.comment))
				if not res:
					ymsg('Warning: comment is empty')
				changed = res != self.comment
				self.comment = res
				return changed
			else:
				return False

	def get_non_mmaddrs(self, desc):
		return remove_dups(
			(i.addr for i in getattr(self, desc) if not i.mmid),
			edesc = 'non-MMGen address',
			quiet = True)

	def check_non_mmgen_inputs(self, caller, non_mmaddrs=None):
		non_mmaddrs = non_mmaddrs or self.get_non_mmaddrs('inputs')
		if non_mmaddrs:
			indent = '  '
			fs = fmt(self.non_mmgen_inputs_msg, strip_char='\t', indent=indent).strip()
			m = fs.format('\n    '.join(non_mmaddrs))
			if caller in ('txdo', 'txsign'):
				if not self.cfg.keys_from_file:
					die('UserOptError', f'\n{indent}ERROR: {m}\n')
			else:
				msg(f'\n{indent}WARNING: {m}\n')
				if not self.cfg.yes:
					from ..ui import keypress_confirm
					if not keypress_confirm(self.cfg, 'Continue?', default_yes=True):
						die(1, 'Exiting at user request')
