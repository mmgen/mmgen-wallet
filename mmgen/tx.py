#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
tx.py:  Transaction routines for the MMGen suite
"""

import sys,os,json
from stat import *
from .common import *
from .obj import *

wmsg = lambda k: {
	'addr_in_addrfile_only': """
Warning: output address {} is not in the tracking wallet, which means
its balance will not be tracked.  You're strongly advised to import the address
into your tracking wallet before broadcasting this transaction.
""".strip(),
	'addr_not_found': """
No data for {pnm} address {{}} could be found in either the tracking
wallet or the supplied address file.  Please import this address into your
tracking wallet, or supply an address file for it on the command line.
""".strip().format(pnm=g.proj_name),
	'addr_not_found_no_addrfile': """
No data for {pnm} address {{}} could be found in the tracking wallet.
Please import this address into your tracking wallet or supply an address file
for it on the command line.
""".strip().format(pnm=g.proj_name),
}[k]

def strfmt_locktime(num,terse=False):
	# Locktime itself is an unsigned 4-byte integer which can be parsed two ways:
	#
	# If less than 500 million, locktime is parsed as a block height. The transaction can be
	# added to any block which has this height or higher.
	# MMGen note: s/this height or higher/a higher block height/
	#
	# If greater than or equal to 500 million, locktime is parsed using the Unix epoch time
	# format (the number of seconds elapsed since 1970-01-01T00:00 UTC). The transaction can be
	# added to any block whose block time is greater than the locktime.
	if num == None:
		return '(None)'
	elif num >= 5 * 10**6:
		return ' '.join(time.strftime('%c',time.gmtime(num)).split()[1:])
	elif num > 0:
		return '{}{}'.format(('block height ','')[terse],num)
	else:
		die(2,"'{}': invalid nLockTime value!".format(num))

def mmaddr2coinaddr(mmaddr,ad_w,ad_f,proto):

	# assume mmaddr has already been checked
	coin_addr = ad_w.mmaddr2coinaddr(mmaddr)

	if not coin_addr:
		if ad_f:
			coin_addr = ad_f.mmaddr2coinaddr(mmaddr)
			if coin_addr:
				msg(wmsg('addr_in_addrfile_only').format(mmaddr))
				if not (opt.yes or keypress_confirm('Continue anyway?')):
					sys.exit(1)
			else:
				die(2,wmsg('addr_not_found').format(mmaddr))
		else:
			die(2,wmsg('addr_not_found_no_addrfile').format(mmaddr))

	return CoinAddr(proto,coin_addr)

def addr2pubhash(proto,addr):
	ap = proto.parse_addr(addr)
	assert ap,'coin address {!r} could not be parsed'.format(addr)
	return ap.bytes.hex()

def addr2scriptPubKey(proto,addr):
	return {
		'p2pkh': '76a914' + addr2pubhash(proto,addr) + '88ac',
		'p2sh':  'a914' + addr2pubhash(proto,addr) + '87',
		'bech32': proto.witness_vernum_hex + '14' + addr2pubhash(proto,addr)
	}[addr.addr_fmt]

def scriptPubKey2addr(proto,s):
	if len(s) == 50 and s[:6] == '76a914' and s[-4:] == '88ac':
		return proto.pubhash2addr(s[6:-4],p2sh=False),'p2pkh'
	elif len(s) == 46 and s[:4] == 'a914' and s[-2:] == '87':
		return proto.pubhash2addr(s[4:-2],p2sh=True),'p2sh'
	elif len(s) == 44 and s[:4] == proto.witness_vernum_hex + '14':
		return proto.pubhash2bech32addr(s[4:]),'bech32'
	else:
		raise NotImplementedError('Unknown scriptPubKey ({})'.format(s))

class DeserializedTX(dict,MMGenObject):
	"""
	Parse a serialized Bitcoin transaction
	For checking purposes, additionally reconstructs the raw (unsigned) tx hex from signed tx hex
	"""
	def __init__(self,proto,txhex):

		def bytes2int(bytes_le):
			if bytes_le[-1] & 0x80: # sign bit is set
				die(3,"{}: Negative values not permitted in transaction!".format(bytes_le[::-1].hex()))
			return int(bytes_le[::-1].hex(),16)

		def bytes2coin_amt(bytes_le):
			return proto.coin_amt(bytes2int(bytes_le) * proto.coin_amt.min_coin_unit)

		def bshift(n,skip=False,sub_null=False):
			ret = tx[self.idx:self.idx+n]
			self.idx += n
			if sub_null:
				self.raw_tx += b'\x00'
			elif not skip:
				self.raw_tx += ret
			return ret

		# https://bitcoin.org/en/developer-reference#compactsize-unsigned-integers
		# For example, the number 515 is encoded as 0xfd0302.
		def readVInt(skip=False):
			s = tx[self.idx]
			self.idx += 1
			if not skip:
				self.raw_tx.append(s)

			vbytes_len = 1 if s < 0xfd else 2 if s == 0xfd else 4 if s == 0xfe else 8

			if vbytes_len == 1:
				return s
			else:
				vbytes = tx[self.idx:self.idx+vbytes_len]
				self.idx += vbytes_len
				if not skip:
					self.raw_tx += vbytes
				return int(vbytes[::-1].hex(),16)

		def make_txid(tx_bytes):
			return sha256(sha256(tx_bytes).digest()).digest()[::-1].hex()

		self.idx = 0
		self.raw_tx = bytearray()

		tx = bytes.fromhex(txhex)
		d = { 'version': bytes2int(bshift(4)) }

		has_witness = tx[self.idx] == 0
		if has_witness:
			u = bshift(2,skip=True).hex()
			if u != '0001':
				raise IllegalWitnessFlagValue("'{}': Illegal value for flag in transaction!".format(u))

		d['num_txins'] = readVInt()

		d['txins'] = MMGenList([{
			'txid':      bshift(32)[::-1].hex(),
			'vout':      bytes2int(bshift(4)),
			'scriptSig': bshift(readVInt(skip=True),sub_null=True).hex(),
			'nSeq':      bshift(4)[::-1].hex()
		} for i in range(d['num_txins'])])

		d['num_txouts'] = readVInt()

		d['txouts'] = MMGenList([{
			'amount':       bytes2coin_amt(bshift(8)),
			'scriptPubKey': bshift(readVInt()).hex()
		} for i in range(d['num_txouts'])])

		for o in d['txouts']:
			o['address'] = scriptPubKey2addr(proto,o['scriptPubKey'])[0]

		if has_witness:
			# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
			# A non-witness program (defined hereinafter) txin MUST be associated with an empty
			# witness field, represented by a 0x00.

			d['txid'] = make_txid(tx[:4] + tx[6:self.idx] + tx[-4:])
			d['witness_size'] = len(tx) - self.idx + 2 - 4 # add len(marker+flag), subtract len(locktime)

			for txin in d['txins']:
				if tx[self.idx] == 0:
					bshift(1,skip=True)
					continue
				txin['witness'] = [
					bshift(readVInt(skip=True),skip=True).hex() for item in range(readVInt(skip=True)) ]
		else:
			d['txid'] = make_txid(tx)
			d['witness_size'] = 0

		if len(tx) - self.idx != 4:
			raise TxHexParseError('TX hex has invalid length: {} extra bytes'.format(len(tx)-self.idx-4))

		d['lock_time'] = bytes2int(bshift(4))
		d['unsigned_hex'] = self.raw_tx.hex()

		dict.__init__(self,d)

class MMGenTxIO(MMGenListItem):
	vout     = ListItemAttr(int,typeconv=False)
	amt      = ImmutableAttr(None)
	label    = ListItemAttr('TwComment',reassign_ok=True)
	mmid     = ListItemAttr('MMGenID',include_proto=True)
	addr     = ImmutableAttr('CoinAddr',include_proto=True)
	confs    = ListItemAttr(int) # confs of type long exist in the wild, so convert
	txid     = ListItemAttr('CoinTxID')
	have_wif = ListItemAttr(bool,typeconv=False,delete_ok=True)

	invalid_attrs = {'proto','tw_copy_attrs'}

	def __init__(self,proto,**kwargs):
		self.__dict__['proto'] = proto
		MMGenListItem.__init__(self,**kwargs)

	class conv_funcs:
		def amt(self,value):
			return self.proto.coin_amt(value)

class MMGenTxInput(MMGenTxIO):
	scriptPubKey = ListItemAttr('HexStr')
	sequence     = ListItemAttr(int,typeconv=False)
	tw_copy_attrs = { 'scriptPubKey','vout','amt','label','mmid','addr','confs','txid' }

class MMGenTxOutput(MMGenTxIO):
	is_chg = ListItemAttr(bool,typeconv=False)

class MMGenTxIOList(MMGenObject):

	def __init__(self,parent,data=None):
		self.parent = parent
		if data:
			assert isinstance(data,list), 'MMGenTxIOList_check1'
			self.data = data
		else:
			self.data = list()

	def __getitem__(self,val):     return self.data.__getitem__(val)
	def __setitem__(self,key,val): return self.data.__setitem__(key,val)
	def __delitem__(self,val):     return self.data.__delitem__(val)
	def __contains__(self,val):    return self.data.__contains__(val)
	def __iter__(self):            return self.data.__iter__()
	def __len__(self):             return self.data.__len__()
	def __add__(self,val):         return self.data.__add__(val)
	def __eq__(self,val):          return self.data.__eq__(val)
	def append(self,val):          return self.data.append(val)
	def sort(self,*args,**kwargs): return self.data.sort(*args,**kwargs)

class MMGenTxInputList(MMGenTxIOList):

	desc = 'transaction inputs'
	member_type = 'MMGenTxInput'

#	def convert_coin(self,verbose=False):
#		if verbose:
#			msg(f'{self.desc}:')
#		for i in self:
#			i.amt = self.parent.proto.coin_amt(i.amt)

	# Lexicographical Indexing of Transaction Inputs and Outputs
	# https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki
	def sort_bip69(self):
		def sort_func(a):
			return (
				bytes.fromhex(a.txid)
				+ int.to_bytes(a.vout,4,'big') )
		self.sort(key=sort_func)

class MMGenTxOutputList(MMGenTxIOList):

	desc = 'transaction outputs'
	member_type = 'MMGenTxOutput'

	def sort_bip69(self):
		def sort_func(a):
			return (
				int.to_bytes(a.amt.toSatoshi(),8,'big')
				+ bytes.fromhex(addr2scriptPubKey(self.parent.proto,a.addr)) )
		self.sort(key=sort_func)

class MMGenTX:

	class Base(MMGenObject):
		desc         = 'transaction'
		hex          = ''                     # raw serialized hex transaction
		label        = MMGenTxLabel('')
		txid         = ''
		coin_txid    = ''
		timestamp    = ''
		blockcount   = 0
		coin         = None
		dcoin        = None
		locktime     = None
		chain        = None
		rel_fee_desc = 'satoshis per byte'
		rel_fee_disp = 'satoshis per byte'
		non_mmgen_inputs_msg = f"""
			This transaction includes inputs with non-{g.proj_name} addresses.  When
			signing the transaction, private keys for the addresses must be supplied using
			the --keys-from-file option.  The key file must contain one key per line.
			Please note that this transaction cannot be autosigned, as autosigning does
			not support the use of key files.

			Non-{g.proj_name} addresses found in inputs:
			    {{}}
		"""

		def __new__(cls,*args,**kwargs):
			"""
			determine correct protocol and pass the proto to altcoin_subclass(), which returns the
			transaction object
			"""
			assert args == (), f'MMGenTX.Base_chk1: only keyword args allowed in {cls.__name__} initializer'
			if 'proto' in kwargs:
				return MMGenObject.__new__(altcoin_subclass(cls,kwargs['proto'],'tx'))
			elif 'data' in kwargs:
				return MMGenObject.__new__(altcoin_subclass(cls,kwargs['data']['proto'],'tx'))
			elif 'filename' in kwargs:
				from .txfile import MMGenTxFile
				tmp_tx = MMGenObject.__new__(cls)
				MMGenTxFile(tmp_tx).parse(
					infile        = kwargs['filename'],
					quiet_open    = kwargs.get('quiet_open'),
					metadata_only = True )
				me = MMGenObject.__new__(altcoin_subclass(cls,tmp_tx.proto,'tx'))
				me.proto = tmp_tx.proto
				return me
			elif cls.__name__ == 'Base' and args == () and kwargs == {}: # allow instantiation of empty Base()
				return cls
			else:
				raise ValueError(
					f"MMGenTX.Base: {cls.__name__} must be instantiated with 'proto','data' or 'filename' keyword")

		def __init__(self):
			self.inputs   = MMGenTxInputList(self)
			self.outputs  = MMGenTxOutputList(self)
			self.name     = type(self).__name__

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

		def has_segwit_inputs(self):
			return any(i.mmid and i.mmid.mmtype in ('S','B') for i in self.inputs)

		def has_segwit_outputs(self):
			return any(o.mmid and o.mmid.mmtype in ('S','B') for o in self.outputs)

		# https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
		# 180: uncompressed, 148: compressed
		def estimate_size_old(self):
			if not self.inputs or not self.outputs:
				return None
			return len(self.inputs)*180 + len(self.outputs)*34 + 10

		# https://bitcoincore.org/en/segwit_wallet_dev/
		# vsize: 3 times of the size with original serialization, plus the size with new
		# serialization, divide the result by 4 and round up to the next integer.

		# TODO: results differ slightly from actual transaction size
		def estimate_size(self):
			if not self.inputs or not self.outputs:
				return None

			sig_size = 72 # sig in DER format
			pubkey_size_uncompressed = 65
			pubkey_size_compressed = 33

			def get_inputs_size():
				# txid vout [scriptSig size (vInt)] scriptSig (<sig> <pubkey>) nSeq
				isize_common = 32 + 4 + 1 + 4 # txid vout [scriptSig size] nSeq = 41
				input_size = {
					'L': isize_common + sig_size + pubkey_size_uncompressed, # = 180
					'C': isize_common + sig_size + pubkey_size_compressed,   # = 148
					'S': isize_common + 23,                                  # = 64
					'B': isize_common + 0                                    # = 41
				}
				ret = sum(input_size[i.mmid.mmtype] for i in self.inputs if i.mmid)

				# We have no way of knowing whether a non-MMGen addr is compressed or uncompressed until
				# we see the key, so assume compressed for fee-estimation purposes.  If fee estimate is
				# off by more than 5%, sign() aborts and user is instructed to use --vsize-adj option
				return ret + sum(input_size['C'] for i in self.inputs if not i.mmid)

			def get_outputs_size():
				# output bytes = amt: 8, byte_count: 1+, pk_script
				# pk_script bytes: p2pkh: 25, p2sh: 23, bech32: 22
				return sum({'p2pkh':34,'p2sh':32,'bech32':31}[o.addr.addr_fmt] for o in self.outputs)

			# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
			# The witness is a serialization of all witness data of the transaction. Each txin is
			# associated with a witness field. A witness field starts with a var_int to indicate the
			# number of stack items for the txin. It is followed by stack items, with each item starts
			# with a var_int to indicate the length. Witness data is NOT script.

			# A non-witness program txin MUST be associated with an empty witness field, represented
			# by a 0x00. If all txins are not witness program, a transaction's wtxid is equal to its txid.
			def get_witness_size():
				if not self.has_segwit_inputs():
					return 0
				wf_size = 1 + 1 + sig_size + 1 + pubkey_size_compressed # vInt vInt sig vInt pubkey = 108
				return sum((1,wf_size)[bool(i.mmid) and i.mmid.mmtype in ('S','B')] for i in self.inputs)

			isize = get_inputs_size()
			osize = get_outputs_size()
			wsize = get_witness_size()

			# TODO: compute real varInt sizes instead of assuming 1 byte
			# old serialization: [nVersion]              [vInt][txins][vInt][txouts]         [nLockTime]
			old_size =           4                     + 1   + isize + 1  + osize          + 4
			# marker = 0x00, flag = 0x01
			# new serialization: [nVersion][marker][flag][vInt][txins][vInt][txouts][witness][nLockTime]
			new_size =           4       + 1     + 1   + 1   + isize + 1  + osize + wsize  + 4 \
					if wsize else old_size

			ret = (old_size * 3 + new_size) // 4

			dmsg('\nData from estimate_size():')
			dmsg(f'  inputs size: {isize}, outputs size: {osize}, witness size: {wsize}')
			dmsg(f'  size: {new_size}, vsize: {ret}, old_size: {old_size}')

			return int(ret * float(opt.vsize_adj)) if hasattr(opt,'vsize_adj') and opt.vsize_adj else ret

		# convert absolute BTC fee to satoshis-per-byte using estimated size
		def fee_abs2rel(self,abs_fee,to_unit=None):
			unit = getattr(self.proto.coin_amt,to_unit or 'min_coin_unit')
			return int(abs_fee // unit // self.estimate_size())

		def get_fee(self):
			return self.sum_inputs() - self.sum_outputs()

		def get_hex_locktime(self):
			return int(bytes.fromhex(self.hex[-8:])[::-1].hex(),16)

		def set_hex_locktime(self,val):
			assert isinstance(val,int),'locktime value not an integer'
			self.hex = self.hex[:-8] + bytes.fromhex('{:08x}'.format(val))[::-1].hex()

		def add_timestamp(self):
			self.timestamp = make_timestamp()

		def add_blockcount(self):
			self.blockcount = self.rpc.blockcount

		# returns true if comment added or changed
		def add_comment(self,infile=None):
			if infile:
				self.label = MMGenTxLabel(get_data_from_file(infile,'transaction comment'))
			else: # get comment from user, or edit existing comment
				m = ('Add a comment to transaction?','Edit transaction comment?')[bool(self.label)]
				if keypress_confirm(m,default_yes=False):
					while True:
						s = MMGenTxLabel(my_raw_input('Comment: ',insert_txt=self.label))
						if s:
							lbl_save = self.label
							self.label = s
							return (True,False)[lbl_save == self.label]
						else:
							msg('Invalid comment')
				return False

		def get_non_mmaddrs(self,desc):
			return {i.addr for i in getattr(self,desc) if not i.mmid}

		def check_non_mmgen_inputs(self,caller,non_mmaddrs=None):
			non_mmaddrs = non_mmaddrs or self.get_non_mmaddrs('inputs')
			if non_mmaddrs:
				fs = fmt(self.non_mmgen_inputs_msg,strip_char='\t')
				m = fs.format('\n    '.join(non_mmaddrs))
				if caller in ('txdo','txsign'):
					if not opt.keys_from_file:
						raise UserOptError('ERROR: ' + m)
				else:
					msg('WARNING: ' + m)
					if not (opt.yes or keypress_confirm('Continue?',default_yes=True)):
						die(1,'Exiting at user request')

	class New(Base):
		usr_fee_prompt = 'Enter transaction fee: '
		fee_is_approximate = False
		fee_fail_fs = 'Network fee estimation for {c} confirmations failed ({t})'
		no_chg_msg = 'Warning: Change address will be deleted as transaction produces no change'
		msg_wallet_low_coin = 'Wallet has insufficient funds for this transaction ({} {} needed)'
		msg_low_coin = 'Selected outputs insufficient to fund this transaction ({} {} needed)'
		msg_no_change_output = fmt("""
			ERROR: No change address specified.  If you wish to create a transaction with
			only one output, specify a single output address with no {} amount
		""").strip()

		def __init__(self,proto,tw=None): # tw required for resolving ERC20 token data
			MMGenTX.Base.__init__(self)
			self.proto = proto
			self.tw    = tw

		def get_chg_output_idx(self):
			ch_ops = [x.is_chg for x in self.outputs]
			try:
				return ch_ops.index(True)
			except ValueError:
				return None

		def del_output(self,idx):
			self.outputs.pop(idx)

		def update_output_amt(self,idx,amt):
			o = self.outputs[idx]._asdict()
			o['amt'] = amt
			self.outputs[idx] = MMGenTxOutput(self.proto,**o)

		def add_mmaddrs_to_outputs(self,ad_w,ad_f):
			a = [e.addr for e in self.outputs]
			d = ad_w.make_reverse_dict(a)
			if ad_f:
				d.update(ad_f.make_reverse_dict(a))
			for e in self.outputs:
				if e.addr and e.addr in d:
					e.mmid,f = d[e.addr]
					if f:
						e.label = f

		def check_dup_addrs(self,io_str):
			assert io_str in ('inputs','outputs')
			addrs = [e.addr for e in getattr(self,io_str)]
			if len(addrs) != len(set(addrs)):
				die(2,f'{addrs}: duplicate address in transaction {io_str}')

		# coin-specific fee routines
		@property
		def relay_fee(self):
			kb_fee = self.proto.coin_amt(self.rpc.cached['networkinfo']['relayfee'])
			ret = kb_fee * self.estimate_size() // 1024
			vmsg('Relay fee: {} {c}/kB, for transaction: {} {c}'.format(kb_fee,ret,c=self.coin))
			return ret

		async def get_rel_fee_from_network(self):
			try:
				ret = await self.rpc.call('estimatesmartfee',opt.tx_confs,opt.fee_estimate_mode.upper())
				fee_per_kb = ret['feerate'] if 'feerate' in ret else -2
				fe_type = 'estimatesmartfee'
			except:
				args = () if self.coin=='BCH' and self.rpc.daemon_version >= 190100 else (opt.tx_confs,)
				fee_per_kb = await self.rpc.call('estimatefee',*args)
				fe_type = 'estimatefee'

			return fee_per_kb,fe_type

		# given tx size, rel fee and units, return absolute fee
		def convert_fee_spec(self,tx_size,units,amt,unit):
			self.usr_rel_fee = None # TODO
			return self.proto.coin_amt(int(amt)*tx_size*getattr(self.proto.coin_amt,units[unit])) \
				if tx_size else None

		# given network fee estimate in BTC/kB, return absolute fee using estimated tx size
		def fee_est2abs(self,fee_per_kb,fe_type=None):
			tx_size = self.estimate_size()
			f = fee_per_kb * opt.tx_fee_adj * tx_size / 1024
			ret = self.proto.coin_amt(f,from_decimal=True)
			if opt.verbose:
				msg(fmt(f"""
					{fe_type.upper()} fee for {opt.tx_confs} confirmations: {fee_per_kb} {self.coin}/kB
					TX size (estimated): {tx_size} bytes
					Fee adjustment factor: {opt.tx_fee_adj}
					Absolute fee (fee_per_kb * adj_factor * tx_size / 1024): {ret} {self.coin}
				""").strip())
			return ret

		def convert_and_check_fee(self,tx_fee,desc='Missing description'):
			abs_fee = self.process_fee_spec(tx_fee,self.estimate_size())
			if abs_fee == None:
				raise ValueError(f'{tx_fee}: cannot convert {self.rel_fee_desc} to {self.coin}'
									+ ' because transaction size is unknown')
			if abs_fee == False:
				err = f'{tx_fee!r}: invalid TX fee (not a {self.coin} amount or {self.rel_fee_desc} specification)'
			elif abs_fee > self.proto.max_tx_fee:
				err = f'{abs_fee} {self.coin}: {desc} fee too large (maximum fee: {self.proto.max_tx_fee} {self.coin})'
			elif abs_fee < self.relay_fee:
				err = f'{abs_fee} {self.coin}: {desc} fee too small (less than relay fee of {self.relay_fee} {self.coin})'
			else:
				return abs_fee
			msg(err)
			return False

		# non-coin-specific fee routines

		# given tx size and absolute fee or fee spec, return absolute fee
		# relative fee is N+<first letter of unit name>
		def process_fee_spec(self,tx_fee,tx_size):
			fee = get_obj(self.proto.coin_amt,num=tx_fee,silent=True)
			if fee:
				return fee
			else:
				import re
				units = {u[0]:u for u in self.proto.coin_amt.units}
				pat = re.compile(r'([1-9][0-9]*)({})'.format('|'.join(units)))
				if pat.match(tx_fee):
					amt,unit = pat.match(tx_fee).groups()
					return self.convert_fee_spec(tx_size,units,amt,unit)
			return False

		def get_usr_fee_interactive(self,tx_fee=None,desc='Starting'):
			abs_fee = None
			while True:
				if tx_fee:
					abs_fee = self.convert_and_check_fee(tx_fee,desc)
				if abs_fee:
					prompt = '{} TX fee{}: {}{} {} ({} {})\n'.format(
							desc,
							(f' (after {opt.tx_fee_adj}X adjustment)'
								if opt.tx_fee_adj != 1 and desc.startswith('Network-estimated')
									else ''),
							('','≈')[self.fee_is_approximate],
							abs_fee.hl(),
							self.coin,
							pink(str(self.fee_abs2rel(abs_fee))),
							self.rel_fee_disp)
					if opt.yes or keypress_confirm(prompt+'OK?',default_yes=True):
						if opt.yes:
							msg(prompt)
						return abs_fee
				tx_fee = my_raw_input(self.usr_fee_prompt)
				desc = 'User-selected'

		async def get_fee_from_user(self,have_estimate_fail=[]):

			if opt.tx_fee:
				desc = 'User-selected'
				start_fee = opt.tx_fee
			else:
				desc = f'Network-estimated (mode: {opt.fee_estimate_mode.upper()})'
				fee_per_kb,fe_type = await self.get_rel_fee_from_network()

				if fee_per_kb < 0:
					if not have_estimate_fail:
						msg(self.fee_fail_fs.format(c=opt.tx_confs,t=fe_type))
						have_estimate_fail.append(True)
					start_fee = None
				else:
					start_fee = self.fee_est2abs(fee_per_kb,fe_type)

			return self.get_usr_fee_interactive(start_fee,desc=desc)

		def add_output(self,coinaddr,amt,is_chg=None):
			self.outputs.append(MMGenTxOutput(self.proto,addr=coinaddr,amt=amt,is_chg=is_chg))

		def process_cmd_arg(self,arg,ad_f,ad_w):

			def add_output_chk(addr,amt,err_desc):
				if not amt and self.get_chg_output_idx() != None:
					die(2,'ERROR: More than one change address listed on command line')
				if is_mmgen_id(self.proto,addr) or is_coin_addr(self.proto,addr):
					coin_addr = ( mmaddr2coinaddr(addr,ad_w,ad_f,self.proto) if is_mmgen_id(self.proto,addr)
									else CoinAddr(self.proto,addr) )
					self.add_output(coin_addr,self.proto.coin_amt(amt or '0'),is_chg=not amt)
				else:
					die(2,f'{addr}: invalid {err_desc} {{!r}}'.format(f'{addr},{amt}' if amt else addr))

			if ',' in arg:
				addr,amt = arg.split(',',1)
				add_output_chk(addr,amt,'coin argument in command-line argument')
			else:
				add_output_chk(arg,None,'command-line argument')

		async def get_cmdline_input_addrs(self):
			# Bitcoin full node, call doesn't go to the network, so just call listunspent with addrs=[]
			return []

		def process_cmd_args(self,cmd_args,ad_f,ad_w):

			for a in cmd_args:
				self.process_cmd_arg(a,ad_f,ad_w)

			if self.get_chg_output_idx() == None:
				die(2,( 'ERROR: No change output specified',
						self.msg_no_change_output.format(self.dcoin))[len(self.outputs) == 1])

			if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
				rdie(2,f'{g.proj_name} Segwit address requested on the command line, '
						+ 'but Segwit is not active on this chain')

			if not self.outputs:
				die(2,'At least one output must be specified on the command line')

		async def get_outputs_from_cmdline(self,cmd_args):
			from .addr import AddrList,AddrData,TwAddrData
			addrfiles = [a for a in cmd_args if get_extension(a) == AddrList.ext]
			cmd_args = set(cmd_args) - set(addrfiles)

			ad_f = AddrData(self.proto)
			for a in addrfiles:
				check_infile(a)
				ad_f.add(AddrList(self.proto,a))

			ad_w = await TwAddrData(self.proto,wallet=self.tw)

			self.process_cmd_args(cmd_args,ad_f,ad_w)

			self.add_mmaddrs_to_outputs(ad_w,ad_f)
			self.check_dup_addrs('outputs')

		# inputs methods
		def select_unspent(self,unspent):
			prompt = 'Enter a range or space-separated list of outputs to spend: '
			while True:
				reply = my_raw_input(prompt).strip()
				if reply:
					selected = get_obj(AddrIdxList, fmt_str=','.join(reply.split()) )
					if selected:
						if selected[-1] <= len(unspent):
							return selected
						msg(f'Unspent output number must be <= {len(unspent)}')

		def select_unspent_cmdline(self,unspent):

			def idx2num(idx):
				uo = unspent[idx]
				mmid_disp = f' ({uo.twmmid})' if uo.twmmid.type == 'mmgen' else ''
				msg(f'Adding input: {idx + 1} {uo.addr}{mmid_disp}')
				return idx + 1

			def get_uo_nums():
				for addr in opt.inputs.split(','):
					if is_mmgen_id(self.proto,addr):
						attr = 'twmmid'
					elif is_coin_addr(self.proto,addr):
						attr = 'addr'
					else:
						die(1,f'{addr!r}: not an MMGen ID or {self.coin} address')

					found = False
					for idx in range(len(unspent)):
						if getattr(unspent[idx],attr) == addr:
							yield idx2num(idx)
							found = True

					if not found:
						die(1,f'{addr!r}: address not found in tracking wallet')

			return set(get_uo_nums()) # silently discard duplicates

		# we don't know fee yet, so perform preliminary check with fee == 0
		async def precheck_sufficient_funds(self,inputs_sum,sel_unspent):
			if self.twuo.total < self.send_amt:
				msg(self.msg_wallet_low_coin.format(self.send_amt-inputs_sum,self.dcoin))
				return False
			if inputs_sum < self.send_amt:
				msg(self.msg_low_coin.format(self.send_amt-inputs_sum,self.dcoin))
				return False
			return True

		def copy_inputs_from_tw(self,tw_unspent_data):
			def gen_inputs():
				for d in tw_unspent_data:
					i = MMGenTxInput(
						self.proto,
						**{attr:getattr(d,attr) for attr in d.__dict__ if attr in MMGenTxInput.tw_copy_attrs} )
					if d.twmmid.type == 'mmgen':
						i.mmid = d.twmmid # twmmid -> mmid
					yield i
			self.inputs = MMGenTxInputList(self,list(gen_inputs()))

		async def get_change_amt(self):
			return self.sum_inputs() - self.send_amt - self.fee

		def final_inputs_ok_msg(self,change_amt):
			return f'Transaction produces {self.proto.coin_amt(change_amt).hl()} {self.coin} in change'

		def warn_insufficient_chg(self,change_amt):
			msg(self.msg_low_coin.format(self.proto.coin_amt(-change_amt).hl(),self.coin))

		async def get_inputs_from_user(self):

			while True:
				us_f = self.select_unspent_cmdline if opt.inputs else self.select_unspent
				sel_nums = us_f(self.twuo.unspent)

				msg(f'Selected output{suf(sel_nums)}: {{}}'.format(' '.join(str(n) for n in sel_nums)))
				sel_unspent = self.twuo.MMGenTwOutputList([self.twuo.unspent[i-1] for i in sel_nums])

				inputs_sum = sum(s.amt for s in sel_unspent)
				if not await self.precheck_sufficient_funds(inputs_sum,sel_unspent):
					continue

				self.copy_inputs_from_tw(sel_unspent)  # makes self.inputs

				self.fee = await self.get_fee_from_user()

				change_amt = await self.get_change_amt()

				if change_amt >= 0:
					p = self.final_inputs_ok_msg(change_amt)
					if opt.yes or keypress_confirm(p+'. OK?',default_yes=True):
						if opt.yes:
							msg(p)
						return change_amt
				else:
					self.warn_insufficient_chg(change_amt)

		def update_change_output(self,change_amt):
			chg_idx = self.get_chg_output_idx()
			if change_amt == 0:
				msg(self.no_chg_msg)
				self.del_output(chg_idx)
			else:
				self.update_output_amt(chg_idx,self.proto.coin_amt(change_amt))

		def update_send_amt(self,change_amt):
			if not self.send_amt:
				self.send_amt = change_amt

		def check_fee(self):
			fee = self.sum_inputs() - self.sum_outputs()
			if fee > self.proto.max_tx_fee:
				c = self.proto.coin
				raise MaxFeeExceeded(f'Transaction fee of {fee} {c} too high! (> {self.proto.max_tx_fee} {c})')

		def update_txid(self):
			self.txid = MMGenTxID(make_chksum_6(bytes.fromhex(self.hex)).upper())

		async def create_raw(self):
			i = [{'txid':e.txid,'vout':e.vout} for e in self.inputs]
			if self.inputs[0].sequence:
				i[0]['sequence'] = self.inputs[0].sequence
			o = {e.addr:e.amt for e in self.outputs}
			self.hex = HexStr(await self.rpc.call('createrawtransaction',i,o))
			self.update_txid()

		async def create(self,cmd_args,locktime,do_info=False,caller='txcreate'):

			assert isinstance(locktime,int),'locktime must be of type int'

			from .tw import TwUnspentOutputs

			if opt.comment_file:
				self.add_comment(opt.comment_file)

			twuo_addrs = await self.get_cmdline_input_addrs()

			self.twuo = await TwUnspentOutputs(self.proto,minconf=opt.minconf,addrs=twuo_addrs)
			await self.twuo.get_unspent_data()

			if not do_info:
				await self.get_outputs_from_cmdline(cmd_args)

			do_license_msg()

			if not opt.inputs:
				await self.twuo.view_and_sort(self)

			self.twuo.display_total()

			if do_info:
				del self.twuo.wallet
				sys.exit(0)

			self.send_amt = self.sum_outputs()

			msg_r('Total amount to spend: ')
			msg(f'{self.send_amt.hl()} {self.dcoin}' if self.send_amt else 'Unknown')

			change_amt = await self.get_inputs_from_user()

			self.check_non_mmgen_inputs(caller)

			self.update_change_output(change_amt)
			self.update_send_amt(change_amt)

			if self.proto.base_proto == 'Bitcoin':
				self.inputs.sort_bip69()
				self.outputs.sort_bip69()
				# do this only after inputs are sorted
				if opt.rbf:
					self.inputs[0].sequence = g.max_int - 2 # handles the nLockTime case too
				elif locktime:
					self.inputs[0].sequence = g.max_int - 1

			if not opt.yes:
				self.add_comment()  # edits an existing comment

			await self.create_raw() # creates self.hex, self.txid

			if self.proto.base_proto == 'Bitcoin' and locktime:
				msg(f'Setting nLockTime to {strfmt_locktime(locktime)}!')
				self.set_hex_locktime(locktime)
				self.update_txid()
				self.locktime = locktime

			self.add_timestamp()
			self.add_blockcount()
			self.chain = self.proto.chain_name
			self.check_fee()

			qmsg('Transaction successfully created')

			new = MMGenTX.Unsigned(data=self.__dict__)

			if not opt.yes:
				new.view_with_prompt('View transaction details?')

			del new.twuo.wallet
			return new

	class Completed(Base):
		"""
		signed or unsigned transaction with associated file
		"""
		fn_fee_unit = 'satoshi'
		view_sort_orders = ('addr','raw')
		dfl_view_sort_order = 'addr'
		txview_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} RBF={r} Sig={s} Locktime={l}\n'
		txview_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} RBF={r} Sig={s} Locktime={l}\n'
		txview_ftr_fs = 'Total input:  {i} {d}\nTotal output: {o} {d}\nTX fee:       {a} {c}{r}\n'
		txview_ftr_fs_short = 'In {i} {d} - Out {o} {d}\nFee {a} {c}{r}\n'
		parsed_hex = None

		def __init__(self,filename=None,quiet_open=False,data=None):
			MMGenTX.Base.__init__(self)
			if data:
				assert filename is None, 'MMGenTX.Completed_chk1'
				assert type(data) is dict, 'MMGenTX.Completed_chk2'
				self.__dict__ = data
				return
			elif filename:
				assert data is None, 'MMGenTX.Completed_chk3'
				from .txfile import MMGenTxFile
				MMGenTxFile(self).parse(filename,quiet_open=quiet_open)
				self.check_pubkey_scripts()

			# repeat with sign and send, because coin daemon could be restarted
			self.check_correct_chain()

		# check signature and witness data
		def check_sigs(self): # return False if no sigs, raise exception on error
			txins = (self.parsed_hex or DeserializedTX(self.proto,self.hex))['txins']
			has_ss = any(ti['scriptSig'] for ti in txins)
			has_witness = any('witness' in ti and ti['witness'] for ti in txins)
			if not (has_ss or has_witness):
				return False
			fs = "Hex TX has {} scriptSig but input is of type '{}'!"
			for n in range(len(txins)):
				ti,mmti = txins[n],self.inputs[n]
				if ti['scriptSig'] == '' or ( len(ti['scriptSig']) == 46 and # native P2WPKH or P2SH-P2WPKH
						ti['scriptSig'][:6] == '16' + self.proto.witness_vernum_hex + '14' ):
					assert 'witness' in ti, 'missing witness'
					assert type(ti['witness']) == list and len(ti['witness']) == 2, 'malformed witness'
					assert len(ti['witness'][1]) == 66, 'incorrect witness pubkey length'
					assert mmti.mmid, fs.format('witness-type','non-MMGen')
					assert mmti.mmid.mmtype == ('S','B')[ti['scriptSig']==''],(
								fs.format('witness-type',mmti.mmid.mmtype))
				else: # non-witness
					if mmti.mmid:
						assert mmti.mmid.mmtype not in ('S','B'), fs.format('signature in',mmti.mmid.mmtype)
					assert not 'witness' in ti, 'non-witness input has witness'
					# sig_size 72 (DER format), pubkey_size 'compressed':33, 'uncompressed':65
					assert (200 < len(ti['scriptSig']) < 300), 'malformed scriptSig' # VERY rough check
			return True

		def check_pubkey_scripts(self):
			for n,i in enumerate(self.inputs,1):
				addr,fmt = scriptPubKey2addr(self.proto,i.scriptPubKey)
				if i.addr != addr:
					if fmt != i.addr.addr_fmt:
						m = 'Address format of scriptPubKey ({}) does not match that of address ({}) in input #{}'
						msg(m.format(fmt,i.addr.addr_fmt,n))
					m = 'ERROR: Address and scriptPubKey of transaction input #{} do not match!'
					die(3,(m+'\n  {:23}{}'*3).format(n, 'address:',i.addr,
														'scriptPubKey:',i.scriptPubKey,
														'scriptPubKey->address:',addr ))

#		def is_replaceable_from_rpc(self):
#			dec_tx = await self.rpc.call('decoderawtransaction',self.hex)
#			return None < dec_tx['vin'][0]['sequence'] <= g.max_int - 2

		def is_replaceable(self):
			return self.inputs[0].sequence == g.max_int - 2

		def check_txfile_hex_data(self):
			self.hex = HexStr(self.hex)

		def parse_txfile_hex_data(self):
			pass

		def write_to_file(self,*args,**kwargs):
			from .txfile import MMGenTxFile
			MMGenTxFile(self).write(*args,**kwargs)

		def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse,sort):

			if sort not in self.view_sort_orders:
				die(1,f'{sort!r}: invalid transaction view sort order. Valid options: {{}}'.format(
						','.join(self.view_sort_orders) ))

			def format_io(desc):
				io = getattr(self,desc)
				is_input = desc == 'inputs'
				yield desc.capitalize() + ':\n' + enl
				addr_w = max(len(e.addr) for e in io)
				confs_per_day = 60*60*24 // self.proto.avg_bdi
				io_sorted = {
					# prepend '/' (sorts before '0') to ensure non-MMGen addrs are displayed first
					'addr': lambda: sorted(io,key=lambda o: o.mmid.sort_key if o.mmid else '/'+o.addr),
					'raw':  lambda: io
				}[sort]
				for n,e in enumerate(io_sorted()):
					if is_input and blockcount:
						confs = e.confs + blockcount - self.blockcount
						days = int(confs // confs_per_day)
					if e.mmid:
						mmid_fmt = e.mmid.fmt(
							width=max_mmwid,
							encl='()',
							color=True,
							append_chars=('',' (chg)')[bool(not is_input and e.is_chg and terse)],
							append_color='green')
					else:
						mmid_fmt = MMGenID.fmtc(nonmm_str,width=max_mmwid,color=True)
					if terse:
						yield '{:3} {} {} {} {}\n'.format(
							n+1,
							e.addr.fmt(color=True,width=addr_w),
							mmid_fmt,
							e.amt.hl(),
							self.dcoin )
					else:
						def gen():
							if is_input:
								yield (n+1,      'tx,vout:', e.txid + ',' + str(e.vout))
								yield ('',       'address:', e.addr.fmt(color=True,width=addr_w) + ' ' + mmid_fmt)
							else:
								yield (n+1,      'address:', e.addr.fmt(color=True,width=addr_w) + ' ' + mmid_fmt)
							if e.label:
								yield ('',       'comment:', e.label.hl())
							yield     ('',       'amount:',  e.amt.hl() + ' ' + self.dcoin)
							if is_input and blockcount:
								yield ('',       'confirmations:', f'{confs} (around {days} days)')
							if not is_input and e.is_chg:
								yield ('',       'change:',  green('True'))
						yield '\n'.join('{:>3} {:<8} {}'.format(*d) for d in gen()) + '\n\n'

			return (
				'Displaying inputs and outputs in {} sort order'.format({'raw':'raw','addr':'address'}[sort])
				+ ('\n\n','\n')[terse]
				+ ''.join(format_io('inputs'))
				+ ''.join(format_io('outputs')) )

		def format_view_rel_fee(self,terse):
			return ' ({} {})\n'.format(
				pink(str(self.fee_abs2rel(self.get_fee()))),
				self.rel_fee_disp)

		def format_view_abs_fee(self):
			return self.proto.coin_amt(self.get_fee()).hl()

		def format_view_verbose_footer(self):
			tsize = len(self.hex)//2 if self.hex else 'unknown'
			out = f'Transaction size: Vsize {self.estimate_size()} (estimated), Total {tsize}'
			if self.name == 'Signed':
				wsize = DeserializedTX(self.proto,self.hex)['witness_size']
				out += f', Base {tsize-wsize}, Witness {wsize}'
			return out + '\n'

		def format_view(self,terse=False,sort=dfl_view_sort_order):
			blockcount = None
			if self.proto.base_coin != 'ETH':
				try:
					blockcount = self.rpc.blockcount
				except:
					pass

			def get_max_mmwid(io):
				if io == self.inputs:
					sel_f = lambda o: len(o.mmid) + 2 # len('()')
				else:
					sel_f = lambda o: len(o.mmid) + (2,8)[bool(o.is_chg)] # + len(' (chg)')
				return  max(max([sel_f(o) for o in io if o.mmid] or [0]),len(nonmm_str))

			nonmm_str = f'(non-{g.proj_name} address)'
			max_mmwid = max(get_max_mmwid(self.inputs),get_max_mmwid(self.outputs))

			def gen_view():
				yield (self.txview_hdr_fs_short if terse else self.txview_hdr_fs).format(
					i = self.txid.hl(),
					a = self.send_amt.hl(),
					c = self.dcoin,
					t = self.timestamp,
					r = (red('False'),green('True'))[self.is_replaceable()],
					s = (red('False'),green('True'))[self.name == 'Signed'],
					l = (green('None'),orange(strfmt_locktime(self.locktime,terse=True)))[bool(self.locktime)] )

				if self.chain != 'mainnet': # if mainnet has a coin-specific name, display it
					yield green(f'Chain: {self.chain.upper()}') + '\n'

				if self.coin_txid:
					yield f'{self.coin} TxID: {self.coin_txid.hl()}\n'

				enl = ('\n','')[bool(terse)]
				yield enl

				if self.label:
					yield f'Comment: {self.label.hl()}\n{enl}'

				yield self.format_view_body(blockcount,nonmm_str,max_mmwid,enl,terse=terse,sort=sort)

				yield (self.txview_ftr_fs_short if terse else self.txview_ftr_fs).format(
					i = self.sum_inputs().hl(),
					o = self.sum_outputs().hl(),
					a = self.format_view_abs_fee(),
					r = self.format_view_rel_fee(terse),
					d = self.dcoin,
					c = self.coin )

				if opt.verbose:
					yield self.format_view_verbose_footer()

			return ''.join(gen_view()) # TX label might contain non-ascii chars

		def view_with_prompt(self,prompt='',pause=True):
			prompt += ' (y)es, (N)o, pager (v)iew, (t)erse view: '
			from .term import get_char
			ok_chars = 'YyNnVvTt'
			while True:
				reply = get_char(prompt,immed_chars=ok_chars).strip('\n\r')
				msg('')
				if reply == '' or reply in 'Nn':
					break
				elif reply in 'YyVvTt':
					self.view(pager=reply in 'Vv',terse=reply in 'Tt',pause=pause)
					break
				else:
					msg('Invalid reply')

		def view(self,pager=False,pause=True,terse=False):
			o = self.format_view(terse=terse)
			if pager:
				do_pager(o)
			else:
				msg_r(o)
				from .term import get_char
				if pause:
					get_char('Press any key to continue: ')
					msg('')

	class Unsigned(Completed):
		desc = 'unsigned transaction'
		ext  = 'rawtx'

		def __init__(self,*args,**kwargs):
			super().__init__(*args,**kwargs)
			if self.check_sigs():
				die(1,'Transaction is signed!')

		def delete_attrs(self,desc,attr):
			for e in getattr(self,desc):
				if hasattr(e,attr):
					delattr(e,attr)

		def get_input_sids(self):
			return set(e.mmid.sid for e in self.inputs if e.mmid)

		def get_output_sids(self):
			return set(e.mmid.sid for e in self.outputs if e.mmid)

		async def sign(self,tx_num_str,keys): # return signed object or False; don't exit or raise exception

			try:
				self.check_correct_chain()
			except TransactionChainMismatch:
				return False

			if (self.has_segwit_inputs() or self.has_segwit_outputs()) and not self.proto.cap('segwit'):
				ymsg(f"TX has Segwit inputs or outputs, but {self.coin} doesn't support Segwit!")
				return False

			self.check_pubkey_scripts()

			qmsg(f'Passing {len(keys)} key{suf(keys)} to {self.rpc.daemon.coind_exec}')

			if self.has_segwit_inputs():
				from .addr import KeyGenerator,AddrGenerator
				kg = KeyGenerator(self.proto,'std')
				ag = AddrGenerator(self.proto,'segwit')
				keydict = MMGenDict([(d.addr,d.sec) for d in keys])

			sig_data = []
			for d in self.inputs:
				e = {k:getattr(d,k) for k in ('txid','vout','scriptPubKey','amt')}
				e['amount'] = e['amt']
				del e['amt']
				if d.mmid and d.mmid.mmtype == 'S':
					e['redeemScript'] = ag.to_segwit_redeem_script(kg.to_pubhex(keydict[d.addr]))
				sig_data.append(e)

			msg_r(f'Signing transaction{tx_num_str}...')
			wifs = [d.sec.wif for d in keys]

			try:
				args = (
					('signrawtransaction',       self.hex,sig_data,wifs,self.proto.sighash_type),
					('signrawtransactionwithkey',self.hex,wifs,sig_data,self.proto.sighash_type)
				)['sign_with_key' in self.rpc.caps]
				ret = await self.rpc.call(*args)
			except Exception as e:
				msg(yellow((
					e.args[0],
					'This is not the BCH chain.\nRe-run the script without the --coin=bch option.'
				)['Invalid sighash param' in e.args[0]]))
				return False

			try:
				self.hex = HexStr(ret['hex'])
				self.parsed_hex = dtx = DeserializedTX(self.proto,self.hex)
				new = MMGenTX.Signed(data=self.__dict__)
				tx_decoded = await self.rpc.call('decoderawtransaction',ret['hex'])
				new.compare_size_and_estimated_size(tx_decoded)
				new.check_hex_tx_matches_mmgen_tx(dtx)
				new.coin_txid = CoinTxID(dtx['txid'])
				if not new.coin_txid == tx_decoded['txid']:
					raise BadMMGenTxID('txid mismatch (after signing)')
				msg('OK')
				return new
			except Exception as e:
				try: m = '{}'.format(e.args[0])
				except: m = repr(e.args[0])
				msg('\n'+yellow(m))
				if g.traceback:
					import traceback
					ymsg('\n'+''.join(traceback.format_exception(*sys.exc_info())))
				return False

	class Signed(Completed):
		desc = 'signed transaction'
		ext  = 'sigtx'

		def __init__(self,*args,**kwargs):
			if 'tw' in kwargs:
				self.tw = kwargs['tw']
				del kwargs['tw']
			super().__init__(*args,**kwargs)
			if not self.check_sigs():
				die(1,'Transaction is not signed!')

		# check that a malicious, compromised or malfunctioning coin daemon hasn't altered hex tx data:
		# does not check witness or signature data
		def check_hex_tx_matches_mmgen_tx(self,dtx):
			m = 'A malicious or malfunctioning coin daemon or other program may have altered your data!'

			lt = dtx['lock_time']
			if lt != int(self.locktime or 0):
				m2 = 'Transaction hex nLockTime ({}) does not match MMGen transaction nLockTime ({})\n{}'
				raise TxHexMismatch(m2.format(lt,self.locktime,m))

			def check_equal(desc,hexio,mmio):
				if mmio != hexio:
					msg('\nMMGen {}:\n{}'.format(desc,pp_fmt(mmio)))
					msg('Hex {}:\n{}'.format(desc,pp_fmt(hexio)))
					m2 = '{} in hex transaction data from coin daemon do not match those in MMGen transaction!\n'
					raise TxHexMismatch((m2+m).format(desc.capitalize()))

			seq_hex   = [int(i['nSeq'],16) for i in dtx['txins']]
			seq_mmgen = [i.sequence or g.max_int for i in self.inputs]
			check_equal('sequence numbers',seq_hex,seq_mmgen)

			d_hex   = sorted((i['txid'],i['vout']) for i in dtx['txins'])
			d_mmgen = sorted((i.txid,i.vout) for i in self.inputs)
			check_equal('inputs',d_hex,d_mmgen)

			d_hex   = sorted((o['address'],self.proto.coin_amt(o['amount'])) for o in dtx['txouts'])
			d_mmgen = sorted((o.addr,o.amt) for o in self.outputs)
			check_equal('outputs',d_hex,d_mmgen)

			uh = dtx['unsigned_hex']
			if str(self.txid) != make_chksum_6(bytes.fromhex(uh)).upper():
				raise TxHexMismatch('MMGen TxID ({}) does not match hex transaction data!\n{}'.format(self.txid,m))

		def compare_size_and_estimated_size(self,tx_decoded):
			est_vsize = self.estimate_size()
			d = tx_decoded
			vsize = d['vsize'] if 'vsize' in d else d['size']
			vmsg(f'\nVsize: {vsize} (true) {est_vsize} (estimated)')
			ratio = float(est_vsize) / vsize
			if not (0.95 < ratio < 1.05): # allow for 5% error
				raise BadTxSizeEstimate(fmt(f"""
					Estimated transaction vsize is {ratio:1.2f} times the true vsize
					Your transaction fee estimates will be inaccurate
					Please re-create and re-sign the transaction using the option --vsize-adj={1/ratio:1.2f}
				""").strip())

		async def get_status(self,status=False):

			class r(object):
				pass

			async def is_in_wallet():
				try: ret = await self.rpc.call('gettransaction',self.coin_txid)
				except: return False
				if ret.get('confirmations',0) > 0:
					r.confs = ret['confirmations']
					return True
				else:
					return False

			async def is_in_utxos():
				try: return 'txid' in await self.rpc.call('getrawtransaction',self.coin_txid,True)
				except: return False

			async def is_in_mempool():
				try: return 'height' in await self.rpc.call('getmempoolentry',self.coin_txid)
				except: return False

			async def is_replaced():
				if await is_in_mempool():
					return False
				try:
					ret = await self.rpc.call('gettransaction',self.coin_txid)
				except:
					return False
				else:
					if 'bip125-replaceable' in ret and ret.get('confirmations',1) <= 0:
						r.replacing_confs = -ret['confirmations']
						r.replacing_txs = ret['walletconflicts']
						return True
					else:
						return False

			if await is_in_mempool():
				if status:
					d = await self.rpc.call('gettransaction',self.coin_txid)
					rep = ('' if d.get('bip125-replaceable') == 'yes' else 'NOT ') + 'replaceable'
					t = d['timereceived']
					if opt.quiet:
						msg('Transaction is in mempool')
					else:
						msg(f'TX status: in mempool, {rep}')
						msg('Sent {} ({} ago)'.format(
							time.strftime('%c',time.gmtime(t)),
							secs_to_dhms(int(time.time()-t))) )
				else:
					msg('Warning: transaction is in mempool!')
			elif await is_in_wallet():
				die(0,f'Transaction has {r.confs} confirmation{suf(r.confs)}')
			elif await is_in_utxos():
				die(2,red('ERROR: transaction is in the blockchain (but not in the tracking wallet)!'))
			elif await is_replaced():
				msg('Transaction has been replaced')
				msg('Replacement transaction ' + (
						f'has {r.replacing_confs} confirmation{suf(r.replacing_confs)}'
					if r.replacing_confs else
						'is in mempool' ) )
				if not opt.quiet:
					msg('Replacing transactions:')
					d = []
					for txid in r.replacing_txs:
						try:    d.append(await self.rpc.call('getmempoolentry',txid))
						except: d.append({})
					for txid,mp_entry in zip(r.replacing_txs,d):
						msg(f'  {txid}' + (' in mempool' if 'height' in mp_entry else '') )
				die(0,'')

		def confirm_send(self):
			confirm_or_raise(
				('' if opt.quiet else "Once this transaction is sent, there's no taking it back!"),
				f'broadcast this transaction to the {self.proto.coin} {self.proto.network.upper()} network',
				('YES' if opt.quiet or opt.yes else 'YES, I REALLY WANT TO DO THIS') )
			msg('Sending transaction')

		async def send(self,prompt_user=True,exit_on_fail=False):

			self.check_correct_chain()
			self.check_pubkey_scripts()
			self.check_hex_tx_matches_mmgen_tx(DeserializedTX(self.proto,self.hex))

			if not g.bogus_send:
				if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
					die(2,'Transaction has Segwit outputs, but this blockchain does not support Segwit'
							+ ' at the current height')

			if self.get_fee() > self.proto.max_tx_fee:
				die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
					self.get_fee(),
					self.proto.name,
					self.proto.max_tx_fee,
					self.proto.coin ))

			await self.get_status()

			if prompt_user:
				self.confirm_send()

			if g.bogus_send:
				ret = None
			else:
				try:
					ret = await self.rpc.call('sendrawtransaction',self.hex)
				except Exception as e:
					errmsg = e
					ret = False

			if ret == False: # TODO: test send errors
				if 'Signature must use SIGHASH_FORKID' in errmsg:
					m = ('The Aug. 1 2017 UAHF has activated on this chain.\n'
						+ 'Re-run the script with the --coin=bch option.' )
				elif 'Illegal use of SIGHASH_FORKID' in errmsg:
					m  = ('The Aug. 1 2017 UAHF is not yet active on this chain.\n'
						+ 'Re-run the script without the --coin=bch option.' )
				elif '64: non-final' in errmsg:
					m = "Transaction with nLockTime {!r} can't be included in this block!".format(
						strfmt_locktime(self.get_hex_locktime()) )
				else:
					m = errmsg
				ymsg(m)
				rmsg(f'Send of MMGen transaction {self.txid} failed')
				if exit_on_fail:
					sys.exit(1)
				return False
			else:
				if g.bogus_send:
					m = 'BOGUS transaction NOT sent: {}'
				else:
					m = 'Transaction sent: {}'
					assert ret == self.coin_txid, 'txid mismatch (after sending)'
				msg(m.format(self.coin_txid.hl()))
				self.add_timestamp()
				self.add_blockcount()
				self.desc = 'sent transaction'
				return True

		def print_contract_addr(self):
			pass

		@staticmethod
		async def get_tracking_wallet(filename):
			from .txfile import MMGenTxFile
			tmp_tx = MMGenTX.Base()
			MMGenTxFile(tmp_tx).parse(filename,metadata_only=True)
			if tmp_tx.proto.tokensym:
				from .tw import TrackingWallet
				return await TrackingWallet(tmp_tx.proto)
			else:
				return None

	class Bump(Completed,New):
		desc = 'fee-bumped transaction'
		ext  = 'rawtx'

		min_fee = None
		bump_output_idx = None

		def __init__(self,data,send,tw=None):
			MMGenTX.Completed.__init__(self,data=data)
			self.tw = tw

			if not self.is_replaceable():
				die(1,f'Transaction {self.txid} is not replaceable')

			# If sending, require original tx to be sent
			if send and not self.coin_txid:
				die(1,'Transaction {self.txid!r} was not broadcast to the network')

			self.coin_txid = ''

		def check_bumpable(self):
			if not [o.amt for o in self.outputs if o.amt >= self.min_fee]:
				die(1,
					'Transaction cannot be bumped.\n' +
					f'All outputs contain less than the minimum fee ({self.min_fee} {self.coin})')

		def choose_output(self):
			chg_idx = self.get_chg_output_idx()
			init_reply = opt.output_to_reduce

			def check_sufficient_funds(o_amt):
				if o_amt < self.min_fee:
					msg(f'Minimum fee ({self.min_fee} {self.coin}) is greater than output amount ({o_amt} {self.coin})')
					return False
				return True

			if len(self.outputs) == 1:
				if check_sufficient_funds(self.outputs[0].amt):
					self.bump_output_idx = 0
					return 0
				else:
					die(1,'Insufficient funds to bump transaction')

			while True:
				if init_reply == None:
					m = 'Choose an output to deduct the fee from (Hit ENTER for the change output): '
					reply = my_raw_input(m) or 'c'
				else:
					reply,init_reply = init_reply,None
				if chg_idx == None and not is_int(reply):
					msg('Output must be an integer')
				elif chg_idx != None and not is_int(reply) and reply != 'c':
					msg("Output must be an integer, or 'c' for the change output")
				else:
					idx = chg_idx if reply == 'c' else (int(reply) - 1)
					if idx < 0 or idx >= len(self.outputs):
						msg(f'Output must be in the range 1-{len(self.outputs)}')
					else:
						o_amt = self.outputs[idx].amt
						cm = ' (change output)' if chg_idx == idx else ''
						prompt = f'Fee will be deducted from output {idx+1}{cm} ({o_amt} {self.coin})'
						if check_sufficient_funds(o_amt):
							if opt.yes or keypress_confirm(prompt+'.  OK?',default_yes=True):
								if opt.yes:
									msg(prompt)
								self.bump_output_idx = idx
								return idx

		@property
		def min_fee(self):
			return self.sum_inputs() - self.sum_outputs() + self.relay_fee

		def update_fee(self,op_idx,fee):
			amt = self.sum_inputs() - self.sum_outputs(exclude=op_idx) - fee
			self.update_output_amt(op_idx,amt)

		def convert_and_check_fee(self,tx_fee,desc):
			ret = super().convert_and_check_fee(tx_fee,desc)
			if ret < self.min_fee:
				msg('{} {c}: {} fee too small. Minimum fee: {} {c} ({} {})'.format(
					ret.hl(),
					desc,
					self.min_fee,
					self.fee_abs2rel(self.min_fee.hl()),
					self.rel_fee_desc,
					c = self.coin ))
				return False
			output_amt = self.outputs[self.bump_output_idx].amt
			if ret >= output_amt:
				msg('{} {c}: {} fee too large. Maximum fee: <{} {c}'.format(
					ret.hl(),
					desc,
					output_amt.hl(),
					c = self.coin ))
				return False
			return ret

# NOT MAINTAINED
#	class Split(Base):
#
#		async def get_outputs_from_cmdline(self,mmid): # TODO: check that addr is empty
#
#			from .addr import TwAddrData
#			ad_w = await TwAddrData()
#
#			if is_mmgen_id(self.proto,mmid):
#				coin_addr = mmaddr2coinaddr(mmid,ad_w,None) if is_mmgen_id(self.proto,mmid) else CoinAddr(mmid)
#				self.add_output(coin_addr,self.proto.coin_amt('0'),is_chg=True)
#			else:
#				die(2,'{}: invalid command-line argument'.format(mmid))
#
#			self.add_mmaddrs_to_outputs(ad_w,None)
#
#			if not segwit_is_active() and self.has_segwit_outputs():
#				fs = '{} Segwit address requested on the command line, but Segwit is not active on this chain'
#				rdie(2,fs.format(g.proj_name))
#
#		def get_split_fee_from_user(self):
#			if opt.rpc_host2:
#				g.rpc_host = opt.rpc_host2
#			if opt.tx_fees:
#				opt.tx_fee = opt.tx_fees.split(',')[1]
#			return super().get_fee_from_user()
#
#		async def create_split(self,mmid):
#
#			self.outputs = self.MMGenTxOutputList(self)
#			await self.get_outputs_from_cmdline(mmid)
#
#			while True:
#				change_amt = self.sum_inputs() - self.get_split_fee_from_user()
#				if change_amt >= 0:
#					p = 'Transaction produces {} {} in change'.format(change_amt.hl(),self.coin)
#					if opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
#						if opt.yes:
#							msg(p)
#						break
#				else:
#					self.warn_insufficient_chg(change_amt)
#
#			self.update_output_amt(0,change_amt)
#			self.send_amt = change_amt
#
#			if not opt.yes:
#				self.add_comment()  # edits an existing comment
#
#			await self.create_raw()       # creates self.hex, self.txid
#
#			self.add_timestamp()
#			self.add_blockcount() # TODO
#			self.chain = g.chain
#
#			assert self.sum_inputs() - self.sum_outputs() <= self.proto.max_tx_fee
#
#			qmsg('Transaction successfully created')
#
#			if not opt.yes:
#				self.view_with_prompt('View transaction details?')
