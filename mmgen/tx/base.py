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
tx.base: base transaction class
"""

from ..globalvars import *
from ..objmethods import MMGenObject
from ..obj import ImmutableAttr,ListItemAttr,MMGenListItem,MMGenTxLabel,TwComment,CoinTxID,HexStr
from ..addr import MMGenID,CoinAddr
from ..util import msg,ymsg,fmt,remove_dups,keypress_confirm,make_timestamp,line_input
from ..opts import opt

class MMGenTxIO(MMGenListItem):
	vout     = ListItemAttr(int,typeconv=False)
	amt      = ImmutableAttr(None)
	label    = ListItemAttr(TwComment,reassign_ok=True)
	mmid     = ListItemAttr(MMGenID,include_proto=True)
	addr     = ImmutableAttr(CoinAddr,include_proto=True)
	confs    = ListItemAttr(int) # confs of type long exist in the wild, so convert
	txid     = ListItemAttr(CoinTxID)
	have_wif = ListItemAttr(bool,typeconv=False,delete_ok=True)

	invalid_attrs = {'proto','tw_copy_attrs'}

	def __init__(self,proto,**kwargs):
		self.__dict__['proto'] = proto
		MMGenListItem.__init__(self,**kwargs)

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
			None )

	class conv_funcs:
		def amt(self,value):
			return self.proto.coin_amt(value)

class MMGenTxIOList(list,MMGenObject):

	def __init__(self,parent,data=None):
		self.parent = parent
		if data:
			assert isinstance(data,list), 'MMGenTxIOList_check1'
			data = data
		else:
			data = list()
		list.__init__(self,data)

class Base(MMGenObject):
	desc         = 'transaction'
	label        = None
	txid         = None
	coin_txid    = None
	timestamp    = None
	blockcount   = None
	coin         = None
	dcoin        = None
	locktime     = None
	chain        = None
	signed       = False
	non_mmgen_inputs_msg = f"""
		This transaction includes inputs with non-{g.proj_name} addresses.  When
		signing the transaction, private keys for the addresses listed below must
		be supplied using the --keys-from-file option.  The key file must contain
		one key per line.  Please note that this transaction cannot be autosigned,
		as autosigning does not support the use of key files.

		Non-{g.proj_name} addresses found in inputs:
		    {{}}
	"""

	class Input(MMGenTxIO):
		scriptPubKey = ListItemAttr(HexStr)
		sequence     = ListItemAttr(int,typeconv=False)
		tw_copy_attrs = { 'scriptPubKey','vout','amt','label','mmid','addr','confs','txid' }

	class Output(MMGenTxIO):
		is_chg = ListItemAttr(bool,typeconv=False)

	class InputList(MMGenTxIOList):
		desc = 'transaction inputs'

	class OutputList(MMGenTxIOList):
		desc = 'transaction outputs'

	def __init__(self,*args,**kwargs):
		self.inputs   = self.InputList(self)
		self.outputs  = self.OutputList(self)
		self.name     = type(self).__name__
		self.proto    = kwargs.get('proto')
		self.tw       = kwargs.get('tw')

	@property
	def coin(self):
		return self.proto.coin

	@property
	def dcoin(self):
		return self.proto.dcoin

	def check_correct_chain(self):
		if hasattr(self,'rpc'):
			if self.chain != self.rpc.chain:
				raise TransactionChainMismatch(
					f'Transaction is for {self.chain}, but coin daemon chain is {self.rpc.chain}!')

	def sum_inputs(self):
		return sum(e.amt for e in self.inputs)

	def sum_outputs(self,exclude=None):
		if exclude == None:
			olist = self.outputs
		else:
			olist = self.outputs[:exclude] + self.outputs[exclude+1:]
		if not olist:
			return self.proto.coin_amt('0')
		return self.proto.coin_amt(sum(e.amt for e in olist))

	def get_chg_output_idx(self):
		ch_ops = [x.is_chg for x in self.outputs]
		try:
			return ch_ops.index(True)
		except ValueError:
			return None

	def add_timestamp(self):
		self.timestamp = make_timestamp()

	def add_blockcount(self):
		self.blockcount = self.rpc.blockcount

	# returns true if comment added or changed
	def add_comment(self,infile=None):
		if infile:
			from ..fileutil import get_data_from_file
			self.label = MMGenTxLabel(get_data_from_file(infile,'transaction comment'))
		else: # get comment from user, or edit existing comment
			m = ('Add a comment to transaction?','Edit transaction comment?')[bool(self.label)]
			if keypress_confirm(m,default_yes=False):
				while True:
					s = MMGenTxLabel(line_input('Comment: ',insert_txt=self.label))
					if not s:
						ymsg('Warning: comment is empty')
					lbl_save = self.label
					self.label = s
					return (True,False)[lbl_save == self.label]
			return False

	def get_non_mmaddrs(self,desc):
		return remove_dups(
			(i.addr for i in getattr(self,desc) if not i.mmid),
			edesc = 'non-MMGen address',
			quiet = True )

	def check_non_mmgen_inputs(self,caller,non_mmaddrs=None):
		non_mmaddrs = non_mmaddrs or self.get_non_mmaddrs('inputs')
		if non_mmaddrs:
			indent = '  '
			fs = fmt(self.non_mmgen_inputs_msg,strip_char='\t',indent=indent).strip()
			m = fs.format('\n    '.join(non_mmaddrs))
			if caller in ('txdo','txsign'):
				if not opt.keys_from_file:
					raise UserOptError(f'\n{indent}ERROR: {m}\n')
			else:
				msg(f'\n{indent}WARNING: {m}\n')
				if not (opt.yes or keypress_confirm('Continue?',default_yes=True)):
					die(1,'Exiting at user request')
