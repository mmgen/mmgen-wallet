#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
		die(2,"'{}': invalid locktime value!".format(num))

def mmaddr2coinaddr(mmaddr,ad_w,ad_f):

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

	return CoinAddr(coin_addr)

def segwit_is_active(exit_on_error=False):
	d = g.rpc.cached['blockchaininfo']
	if d['chain'] == 'regtest':
		return True
	if (    'bip9_softforks' in d
			and 'segwit' in d['bip9_softforks']
			and d['bip9_softforks']['segwit']['status'] == 'active'):
		return True
	if g.test_suite:
		return True
	if exit_on_error:
		die(2,'Segwit not active on this chain.  Exiting')
	else:
		return False

def addr2pubhash(addr):
	ap = g.proto.parse_addr(addr)
	assert ap,'coin address {!r} could not be parsed'.format(addr)
	return ap.bytes.hex()

def addr2scriptPubKey(addr):
	return {
		'p2pkh': '76a914' + addr2pubhash(addr) + '88ac',
		'p2sh':  'a914' + addr2pubhash(addr) + '87',
		'bech32': g.proto.witness_vernum_hex + '14' + addr2pubhash(addr)
	}[addr.addr_fmt]

def scriptPubKey2addr(s):
	if len(s) == 50 and s[:6] == '76a914' and s[-4:] == '88ac':
		return g.proto.pubhash2addr(s[6:-4],p2sh=False),'p2pkh'
	elif len(s) == 46 and s[:4] == 'a914' and s[-2:] == '87':
		return g.proto.pubhash2addr(s[4:-2],p2sh=True),'p2sh'
	elif len(s) == 44 and s[:4] == g.proto.witness_vernum_hex + '14':
		return g.proto.pubhash2bech32addr(s[4:]),'bech32'
	else:
		raise NotImplementedError('Unknown scriptPubKey ({})'.format(s))

class DeserializedTX(dict,MMGenObject):
	"""
	Parse a serialized Bitcoin transaction
	For checking purposes, additionally reconstructs the raw (unsigned) tx hex from signed tx hex
	"""
	def __init__(self,txhex):

		def bytes2int(bytes_le):
			if bytes_le[-1] & 0x80: # sign bit is set
				die(3,"{}: Negative values not permitted in transaction!".format(bytes_le[::-1].hex()))
			return int(bytes_le[::-1].hex(),16)

		def bytes2coin_amt(bytes_le):
			return g.proto.coin_amt(bytes2int(bytes_le) * g.proto.coin_amt.min_coin_unit)

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
			o['address'] = scriptPubKey2addr(o['scriptPubKey'])[0]

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
	amt      = ImmutableAttr(lambda:g.proto.coin_amt,typeconv=False)
	label    = ListItemAttr('TwComment',reassign_ok=True)
	mmid     = ListItemAttr('MMGenID')
	addr     = ImmutableAttr('CoinAddr')
	confs    = ListItemAttr(int,typeconv=True) # confs of type long exist in the wild, so convert
	txid     = ListItemAttr('CoinTxID')
	have_wif = ListItemAttr(bool,typeconv=False,delete_ok=True)

class MMGenTxInput(MMGenTxIO):
	scriptPubKey = ListItemAttr('HexStr')
	sequence     = ListItemAttr(int,typeconv=False)
	# required by copy_inputs_from_tw()
	copy_attrs = { 'scriptPubKey','vout','amt','label','mmid','addr','confs','txid' }

class MMGenTxOutput(MMGenTxIO):
	is_chg = ListItemAttr(bool,typeconv=False)

class MMGenTxInputList(list,MMGenObject):

	desc = 'transaction inputs'
	member_type = 'MMGenTxInput'

	def convert_coin(self,verbose=False):
		if verbose:
			msg(f'{self.desc}:')
		for i in self:
			setattr(i,'amt',g.proto.coin_amt(i.amt))

	def check_coin_mismatch(self):
		for i in self:
			if type(i.amt) != g.proto.coin_amt:
				die(2,f'Coin mismatch in transaction: amount {i.amt} not of type {g.proto.coin_amt}!')

	# Lexicographical Indexing of Transaction Inputs and Outputs
	# https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki
	def sort_bip69(self):
		from struct import pack
		self.sort(key=lambda a: bytes.fromhex(a.txid) + pack('>i',a.vout))

class MMGenTxOutputList(MMGenTxInputList):

	desc = 'transaction outputs'
	member_type = 'MMGenTxOutput'

	def sort_bip69(self):
		from struct import pack
		self.sort(key=lambda a: pack('>q',a.amt.toSatoshi()) + bytes.fromhex(addr2scriptPubKey(a.addr)))

class MMGenTX(MMGenObject):

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tx','MMGenTX'))

	ext      = 'rawtx'
	raw_ext  = 'rawtx'
	sig_ext  = 'sigtx'
	txid_ext = 'txid'
	desc     = 'transaction'
	hexdata_type = 'hex'
	fee_fail_fs = 'Network fee estimation for {c} confirmations failed ({t})'
	no_chg_msg = 'Warning: Change address will be deleted as transaction produces no change'
	rel_fee_desc = 'satoshis per byte'
	rel_fee_disp = 'satoshis per byte'
	txview_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} RBF={r} Sig={s} Locktime={l}\n'
	txview_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} RBF={r} Sig={s} Locktime={l}\n'
	txview_ftr_fs = 'Total input:  {i} {d}\nTotal output: {o} {d}\nTX fee:       {a} {c}{r}\n'
	txview_ftr_fs_short = 'In {i} {d} - Out {o} {d}\nFee {a} {c}{r}\n'
	usr_fee_prompt = 'Enter transaction fee: '
	fee_is_approximate = False
	fn_fee_unit = 'satoshi'
	view_sort_orders = ('addr','raw')
	dfl_view_sort_order = 'addr'

	msg_wallet_low_coin = 'Wallet has insufficient funds for this transaction ({} {} needed)'
	msg_low_coin = 'Selected outputs insufficient to fund this transaction ({} {} needed)'
	msg_no_change_output = fmt("""
		ERROR: No change address specified.  If you wish to create a transaction with
		only one output, specify a single output address with no {} amount
	""").strip()
	msg_non_mmgen_inputs = fmt(f"""
		NOTE: This transaction includes non-{g.proj_name} inputs, which makes the signing
		process more complicated.  When signing the transaction, keys for non-{g.proj_name}
		inputs must be supplied to '{g.proj_name.lower()}-txsign' in a file with the '--keys-from-file'
		option.
		Selected non-{g.proj_name} inputs: {{}}
	""").strip()

	def __init__(self,filename=None,metadata_only=False,caller=None,quiet_open=False,data=None,tw=None):
		if data:
			assert type(data) is dict, type(data)
			self.__dict__ = data
			return
		self.inputs      = MMGenTxInputList()
		self.outputs     = MMGenTxOutputList()
		self.send_amt    = g.proto.coin_amt('0')  # total amt minus change
		self.fee         = g.proto.coin_amt('0')
		self.hex         = ''                     # raw serialized hex transaction
		self.label       = MMGenTxLabel('')
		self.txid        = ''
		self.coin_txid    = ''
		self.timestamp   = ''
		self.chksum      = ''
		self.fmt_data    = ''
		self.fn          = ''
		self.blockcount  = 0
		self.chain       = None
		self.coin        = None
		self.dcoin       = None
		self.caller      = caller
		self.locktime    = None
		self.tw          = tw

		if filename:
			self.parse_tx_file(filename,metadata_only=metadata_only,quiet_open=quiet_open)
			if metadata_only:
				return
			self.check_pubkey_scripts()
			self.check_sigs() # marks the tx as signed

		# repeat with sign and send, because coin daemon could be restarted
		self.check_correct_chain()

	def check_correct_chain(self):
		bad = self.chain and g.chain and self.chain != g.chain
		if bad and hasattr(g.proto,'chain_name'):
			bad = self.chain != g.proto.chain_name
		if bad:
			raise TransactionChainMismatch(f'Transaction is for {self.chain}, but current chain is {g.chain}!')

	def add_output(self,coinaddr,amt,is_chg=None):
		self.outputs.append(MMGenTxOutput(addr=coinaddr,amt=amt,is_chg=is_chg))

	def get_chg_output_idx(self):
		ch_ops = [x.is_chg for x in self.outputs]
		try:
			return ch_ops.index(True)
		except ValueError:
			return None

	def update_output_amt(self,idx,amt):
		o = self.outputs[idx].__dict__
		o['amt'] = amt
		self.outputs[idx] = MMGenTxOutput(**o)

	def update_change_output(self,change_amt):
		chg_idx = self.get_chg_output_idx()
		if change_amt == 0:
			msg(self.no_chg_msg)
			self.del_output(chg_idx)
		else:
			self.update_output_amt(chg_idx,g.proto.coin_amt(change_amt))

	def del_output(self,idx):
		self.outputs.pop(idx)

	def sum_outputs(self,exclude=None):
		if exclude == None:
			olist = self.outputs
		else:
			olist = self.outputs[:exclude] + self.outputs[exclude+1:]
		if not olist:
			return g.proto.coin_amt('0')
		return g.proto.coin_amt(sum(e.amt for e in olist))

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

	def update_txid(self):
		self.txid = MMGenTxID(make_chksum_6(bytes.fromhex(self.hex)).upper())

	async def create_raw(self):
		i = [{'txid':e.txid,'vout':e.vout} for e in self.inputs]
		if self.inputs[0].sequence:
			i[0]['sequence'] = self.inputs[0].sequence
		o = {e.addr:e.amt for e in self.outputs}
		self.hex = HexStr(await g.rpc.call('createrawtransaction',i,o))
		self.update_txid()

	def print_contract_addr(self):
		pass

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

	def edit_comment(self):
		return self.add_comment(self)

	def get_fee_from_tx(self):
		return self.sum_inputs() - self.sum_outputs()

	def has_segwit_inputs(self):
		return any(i.mmid and i.mmid.mmtype in ('S','B') for i in self.inputs)

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
		dmsg('  inputs size: {}, outputs size: {}, witness size: {}'.format(isize,osize,wsize))
		dmsg('  size: {}, vsize: {}, old_size: {}'.format(new_size,ret,old_size))

		return int(ret * float(opt.vsize_adj)) if hasattr(opt,'vsize_adj') and opt.vsize_adj else ret

	# coin-specific fee routines
	@property
	def relay_fee(self):
		kb_fee = g.proto.coin_amt(g.rpc.cached['networkinfo']['relayfee'])
		ret = kb_fee * self.estimate_size() // 1024
		vmsg('Relay fee: {} {c}/kB, for transaction: {} {c}'.format(kb_fee,ret,c=g.coin))
		return ret

	# convert absolute BTC fee to satoshis-per-byte using estimated size
	def fee_abs2rel(self,abs_fee,to_unit=None):
		unit = getattr(g.proto.coin_amt,to_unit or 'min_coin_unit')
		return int(abs_fee // unit // self.estimate_size())

	async def get_rel_fee_from_network(self):
		try:
			ret = await g.rpc.call('estimatesmartfee',opt.tx_confs,opt.fee_estimate_mode.upper())
			fee_per_kb = ret['feerate'] if 'feerate' in ret else -2
			fe_type = 'estimatesmartfee'
		except:
			args = () if g.coin=='BCH' and g.rpc.daemon_version >= 190100 else (opt.tx_confs,)
			fee_per_kb = await g.rpc.call('estimatefee',*args)
			fe_type = 'estimatefee'

		return fee_per_kb,fe_type

	# given tx size, rel fee and units, return absolute fee
	def convert_fee_spec(self,tx_size,units,amt,unit):
		self.usr_rel_fee = None # TODO
		return g.proto.coin_amt(int(amt)*tx_size*getattr(g.proto.coin_amt,units[unit])) \
			if tx_size else None

	# given network fee estimate in BTC/kB, return absolute fee using estimated tx size
	def fee_est2abs(self,fee_per_kb,fe_type=None):
		tx_size = self.estimate_size()
		f = fee_per_kb * opt.tx_fee_adj * tx_size / 1024
		ret = g.proto.coin_amt(f,from_decimal=True)
		if opt.verbose:
			msg(fmt(f"""
				{fe_type.upper()} fee for {opt.tx_confs} confirmations: {fee_per_kb} {g.coin}/kB
				TX size (estimated): {tx_size} bytes
				Fee adjustment factor: {opt.tx_fee_adj}
				Absolute fee (fee_per_kb * adj_factor * tx_size / 1024): {ret} {g.coin}
			""").strip())
		return ret

	def convert_and_check_fee(self,tx_fee,desc='Missing description'):
		abs_fee = self.process_fee_spec(tx_fee,self.estimate_size())
		if abs_fee == None: # we shouldn't be calling this method if tx size is unknown
			raise ValueError(
				f'{tx_fee}: cannot convert {self.rel_fee_desc} to {g.coin} because transaction size is unknown')
		elif abs_fee == False:
			msg(f'{tx_fee!r}: invalid TX fee (not a {g.coin} amount or {self.rel_fee_desc} specification)')
			return False
		elif abs_fee > g.proto.max_tx_fee:
			msg(f'{abs_fee} {g.coin}: {desc} fee too large (maximum fee: {g.proto.max_tx_fee} {g.coin})')
			return False
		elif abs_fee < self.relay_fee:
			msg(f'{abs_fee} {g.coin}: {desc} fee too small (less than relay fee of {self.relay_fee} {g.coin})')
			return False
		else:
			return abs_fee

	# non-coin-specific fee routines

	# given tx size and absolute fee or fee spec, return absolute fee
	# relative fee is N+<first letter of unit name>
	def process_fee_spec(self,tx_fee,tx_size):
		if g.proto.coin_amt(tx_fee,on_fail='silent'):
			return g.proto.coin_amt(tx_fee)
		else:
			import re
			units = {u[0]:u for u in g.proto.coin_amt.units}
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
						g.coin,
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

	def delete_attrs(self,desc,attr):
		for e in getattr(self,desc):
			if hasattr(e,attr):
				delattr(e,attr)

	# inputs methods
	def copy_inputs_from_tw(self,tw_unspent_data):
		self.inputs = MMGenTxInputList()
		for d in tw_unspent_data:
			t = MMGenTxInput(**{attr:getattr(d,attr) for attr in d.__dict__ if attr in MMGenTxInput.copy_attrs})
			if d.twmmid.type == 'mmgen':
				t.mmid = d.twmmid # twmmid -> mmid
			self.inputs.append(t)

	def get_input_sids(self):
		return set(e.mmid.sid for e in self.inputs if e.mmid)

	def get_output_sids(self):
		return set(e.mmid.sid for e in self.outputs if e.mmid)

	def sum_inputs(self):
		return sum(e.amt for e in self.inputs)

	def add_timestamp(self):
		self.timestamp = make_timestamp()

	def get_hex_locktime(self):
		return int(bytes.fromhex(self.hex[-8:])[::-1].hex(),16)

	def set_hex_locktime(self,val):
		assert isinstance(val,int),'locktime value not an integer'
		self.hex = self.hex[:-8] + bytes.fromhex('{:08x}'.format(val))[::-1].hex()

	def add_blockcount(self):
		self.blockcount = g.rpc.blockcount

	def format(self):
		self.inputs.check_coin_mismatch()
		self.outputs.check_coin_mismatch()
		def amt_to_str(d):
			return {k: (str(d[k]) if k == 'amt' else d[k]) for k in d}
		coin_id = '' if g.coin == 'BTC' else g.coin + ('' if g.coin == g.dcoin else ':'+g.dcoin)
		lines = [
			'{}{} {} {} {} {}{}'.format(
				(coin_id+' ' if coin_id else ''),
				self.chain.upper() if self.chain else 'Unknown',
				self.txid,
				self.send_amt,
				self.timestamp,
				self.blockcount,
				('',' LT={}'.format(self.locktime))[bool(self.locktime)]
			),
			self.hex,
			repr([amt_to_str(e.__dict__) for e in self.inputs]),
			repr([amt_to_str(e.__dict__) for e in self.outputs])
		]
		if self.label:
			from .baseconv import baseconv
			lines.append(baseconv.frombytes(self.label.encode(),'b58',tostr=True))
		if self.coin_txid:
			if not self.label:
				lines.append('-') # keep old tx files backwards compatible
			lines.append(self.coin_txid)
		self.chksum = make_chksum_6(' '.join(lines))
		self.fmt_data = '\n'.join([self.chksum] + lines)+'\n'

		assert len(self.fmt_data) <= g.max_tx_file_size,(
			'Transaction file size exceeds limit ({} bytes)'.format(g.max_tx_file_size))

	def get_non_mmaddrs(self,desc):
		return {i.addr for i in getattr(self,desc) if not i.mmid}

	def mark_raw(self):
		self.desc = 'transaction'
		self.ext = self.raw_ext

	def mark_signed(self): # called ONLY by check_sigs()
		self.desc = 'signed transaction'
		self.ext = self.sig_ext

	def marked_signed(self,color=False):
		ret = self.desc == 'signed transaction'
		return (red,green)[ret](str(ret)) if color else ret

	# check that a malicious, compromised or malfunctioning coin daemon hasn't altered hex tx data:
	# does not check witness or signature data
	def check_hex_tx_matches_mmgen_tx(self,deserial_tx):
		m = 'A malicious or malfunctioning coin daemon or other program may have altered your data!'

		lt = deserial_tx['lock_time']
		if lt != int(self.locktime or 0):
			m2 = 'Transaction hex locktime ({}) does not match MMGen transaction locktime ({})\n{}'
			raise TxHexMismatch(m2.format(lt,self.locktime,m))

		def check_equal(desc,hexio,mmio):
			if mmio != hexio:
				msg('\nMMGen {}:\n{}'.format(desc,pp_fmt(mmio)))
				msg('Hex {}:\n{}'.format(desc,pp_fmt(hexio)))
				m2 = '{} in hex transaction data from coin daemon do not match those in MMGen transaction!\n'
				raise TxHexMismatch((m2+m).format(desc.capitalize()))

		seq_hex   = [int(i['nSeq'],16) for i in deserial_tx['txins']]
		seq_mmgen = [i.sequence or g.max_int for i in self.inputs]
		check_equal('sequence numbers',seq_hex,seq_mmgen)

		d_hex   = sorted((i['txid'],i['vout']) for i in deserial_tx['txins'])
		d_mmgen = sorted((i.txid,i.vout) for i in self.inputs)
		check_equal('inputs',d_hex,d_mmgen)

		d_hex   = sorted((o['address'],g.proto.coin_amt(o['amount'])) for o in deserial_tx['txouts'])
		d_mmgen = sorted((o.addr,o.amt) for o in self.outputs)
		check_equal('outputs',d_hex,d_mmgen)

		uh = deserial_tx['unsigned_hex']
		if str(self.txid) != make_chksum_6(bytes.fromhex(uh)).upper():
			raise TxHexMismatch('MMGen TxID ({}) does not match hex transaction data!\n{}'.format(self.txid,m))

	def check_pubkey_scripts(self):
		for n,i in enumerate(self.inputs,1):
			addr,fmt = scriptPubKey2addr(i.scriptPubKey)
			if i.addr != addr:
				if fmt != i.addr.addr_fmt:
					m = 'Address format of scriptPubKey ({}) does not match that of address ({}) in input #{}'
					msg(m.format(fmt,i.addr.addr_fmt,n))
				m = 'ERROR: Address and scriptPubKey of transaction input #{} do not match!'
				die(3,(m+'\n  {:23}{}'*3).format(n, 'address:',i.addr,
													'scriptPubKey:',i.scriptPubKey,
													'scriptPubKey->address:',addr ))

	# check signature and witness data
	def check_sigs(self,deserial_tx=None): # return False if no sigs, raise exception on error
		txins = (deserial_tx or DeserializedTX(self.hex))['txins']
		has_ss = any(ti['scriptSig'] for ti in txins)
		has_witness = any('witness' in ti and ti['witness'] for ti in txins)
		if not (has_ss or has_witness):
			return False
		fs = "Hex TX has {} scriptSig but input is of type '{}'!"
		for n in range(len(txins)):
			ti,mmti = txins[n],self.inputs[n]
			if ti['scriptSig'] == '' or ( len(ti['scriptSig']) == 46 and # native P2WPKH or P2SH-P2WPKH
					ti['scriptSig'][:6] == '16' + g.proto.witness_vernum_hex + '14' ):
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
		self.mark_signed()
		return True

	def has_segwit_outputs(self):
		return any(o.mmid and o.mmid.mmtype in ('S','B') for o in self.outputs)

	async def get_status(self,status=False):

		class r(object):
			pass

		async def is_in_wallet():
			try: ret = await g.rpc.call('gettransaction',self.coin_txid)
			except: return False
			if 'confirmations' in ret and ret['confirmations'] > 0:
				r.confs = ret['confirmations']
				return True
			else:
				return False

		async def is_in_utxos():
			try: return 'txid' in await g.rpc.call('getrawtransaction',self.coin_txid,True)
			except: return False

		async def is_in_mempool():
			try: return 'height' in await g.rpc.call('getmempoolentry',self.coin_txid)
			except: return False

		async def is_replaced():
			if await is_in_mempool():
				return False
			try:
				ret = await g.rpc.call('gettransaction',self.coin_txid)
			except:
				return False
			else:
				if 'bip125-replaceable' in ret and 'confirmations' in ret and ret['confirmations'] <= 0:
					r.replacing_confs = -ret['confirmations']
					r.replacing_txs = ret['walletconflicts']
					return True
				else:
					return False

		if await is_in_mempool():
			if status:
				d = await g.rpc.call('gettransaction',self.coin_txid)
				brs = 'bip125-replaceable'
				rep = '{}replaceable'.format(('NOT ','')[brs in d and d[brs]=='yes'])
				t = d['timereceived']
				m = 'Sent {} ({} h/m/s ago)'
				b = m.format(time.strftime('%c',time.gmtime(t)),secs_to_dhms(int(time.time()-t)))
				if opt.quiet:
					msg('Transaction is in mempool')
				else:
					msg('TX status: in mempool, {}\n{}'.format(rep,b))
			else:
				msg('Warning: transaction is in mempool!')
		elif await is_in_wallet():
			die(0,'Transaction has {} confirmation{}'.format(r.confs,suf(r.confs)))
		elif await is_in_utxos():
			die(2,red('ERROR: transaction is in the blockchain (but not in the tracking wallet)!'))
		elif await is_replaced():
			msg('Transaction has been replaced\nReplacement transaction ' + (
					f'has {r.replacing_confs} confirmation{suf(r.replacing_confs)}'
				if r.replacing_confs else
					'is in mempool' ))
			if not opt.quiet:
				msg('Replacing transactions:')
				d = []
				for txid in r.replacing_txs:
					try:    d.append(await g.rpc.call('getmempoolentry',txid))
					except: d.append({})
				for txid,mp_entry in zip(r.replacing_txs,d):
					msg(f'  {txid}' + ('',' in mempool')['height' in mp_entry])
			die(0,'')

	def confirm_send(self):
		m1 = ("Once this transaction is sent, there's no taking it back!",'')[bool(opt.quiet)]
		m2 = 'broadcast this transaction to the {} network'.format(g.chain.upper())
		m3 = ('YES, I REALLY WANT TO DO THIS','YES')[bool(opt.quiet or opt.yes)]
		confirm_or_raise(m1,m2,m3)
		msg('Sending transaction')

	async def send(self,prompt_user=True,exit_on_fail=False):
		if not self.marked_signed():
			die(1,'Transaction is not signed!')

		self.check_correct_chain()

		self.check_pubkey_scripts()

		self.check_hex_tx_matches_mmgen_tx(DeserializedTX(self.hex))

		if self.has_segwit_outputs() and not segwit_is_active() and not g.bogus_send:
			m = 'Transaction has MMGen Segwit outputs, but this blockchain does not support Segwit'
			die(2,m+' at the current height')

		if self.get_fee_from_tx() > g.proto.max_tx_fee:
			die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				self.get_fee_from_tx(),
				g.proto.name,
				g.proto.max_tx_fee,
				g.proto.coin ))

		await self.get_status()

		if prompt_user:
			self.confirm_send()

		if g.bogus_send:
			ret = None
		else:
			try:
				ret = await g.rpc.call('sendrawtransaction',self.hex)
			except Exception as e:
				ret = False

		if ret == False:
			errmsg = e
			if 'Signature must use SIGHASH_FORKID' in errmsg:
				m  = 'The Aug. 1 2017 UAHF has activated on this chain.'
				m += "\nRe-run the script with the --coin=bch option."
			elif 'Illegal use of SIGHASH_FORKID' in errmsg:
				m  = 'The Aug. 1 2017 UAHF is not yet active on this chain.'
				m += "\nRe-run the script without the --coin=bch option."
			elif '64: non-final' in errmsg:
				m2 = "Transaction with locktime '{}' can't be included in this block!"
				m = m2.format(strfmt_locktime(self.get_hex_locktime()))
			else:
				m = errmsg
			msg(yellow(m))
			msg(red('Send of MMGen transaction {} failed'.format(self.txid)))
			if exit_on_fail:
				sys.exit(1)
			return False
		else:
			if g.bogus_send:
				m = 'BOGUS transaction NOT sent: {}'
			else:
				assert ret == self.coin_txid, 'txid mismatch (after sending)'
				m = 'Transaction sent: {}'
			self.desc = 'sent transaction'
			msg(m.format(self.coin_txid.hl()))
			self.add_timestamp()
			self.add_blockcount()
			return True

	def create_fn(self):
		tl = self.get_hex_locktime()
		tn = ('','.testnet')[g.proto.testnet]
		self.fn = '{}{}[{!s}{}{}]{x}{}.{}'.format(
			self.txid,
			('-'+g.dcoin,'')[g.coin=='BTC'],
			self.send_amt,
			('',',{}'.format(self.fee_abs2rel(
								self.get_fee_from_tx(),to_unit=self.fn_fee_unit))
							)[self.is_replaceable()],
			('',',tl={}'.format(tl))[bool(tl)],
			tn,self.ext,
			x='-α' if g.debug_utf8 else '')

	def write_to_file(  self,
						add_desc='',
						ask_write=True,
						ask_write_default_yes=False,
						ask_tty=True,
						ask_overwrite=True):

		if ask_write == False:
			ask_write_default_yes = True

		if not self.fmt_data:
			self.format()

		if not self.fn:
			self.create_fn()

		write_data_to_file(self.fn,self.fmt_data,self.desc+add_desc,
			ask_overwrite=ask_overwrite,
			ask_write=ask_write,
			ask_tty=ask_tty,
			ask_write_default_yes=ask_write_default_yes)

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

#	def is_replaceable_from_rpc(self):
#		dec_tx = await g.rpc.call('decoderawtransaction',self.hex)
#		return None < dec_tx['vin'][0]['sequence'] <= g.max_int - 2

	def is_replaceable(self):
		return self.inputs[0].sequence == g.max_int - 2

	def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse,sort):

		if sort not in self.view_sort_orders:
			die(1,f'{sort!r}: invalid transaction view sort order. Valid options: {{}}'.format(
					','.join(self.view_sort_orders) ))

		def format_io(desc):
			io = getattr(self,desc)
			is_input = desc == 'inputs'
			yield desc.capitalize() + ':\n' + enl
			addr_w = max(len(e.addr) for e in io)
			confs_per_day = 60*60*24 // g.proto.avg_bdi
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
						g.dcoin )
				else:
					def gen():
						if is_input:
							yield (n+1,      'tx,vout:', e.txid + ',' + str(e.vout))
							yield ('',       'address:', e.addr.fmt(color=True,width=addr_w) + ' ' + mmid_fmt)
						else:
							yield (n+1,      'address:', e.addr.fmt(color=True,width=addr_w) + ' ' + mmid_fmt)
						if e.label:
							yield ('',       'comment:', e.label.hl())
						yield     ('',       'amount:',  e.amt.hl() + ' ' + g.dcoin)
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
			pink(str(self.fee_abs2rel(self.get_fee_from_tx()))),
			self.rel_fee_disp)

	def format_view_abs_fee(self):
		return g.proto.coin_amt(self.get_fee_from_tx()).hl()

	def format_view_verbose_footer(self):
		tsize = len(self.hex)//2 if self.hex else 'unknown'
		out = f'Transaction size: Vsize {self.estimate_size()} (estimated), Total {tsize}'
		if self.marked_signed():
			wsize = DeserializedTX(self.hex)['witness_size']
			out += f', Base {tsize-wsize}, Witness {wsize}'
		return out + '\n'

	def format_view(self,terse=False,sort=dfl_view_sort_order):
		blockcount = None
		if g.proto.base_coin != 'ETH':
			try:
				blockcount = g.rpc.blockcount
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
				c = g.dcoin,
				t = self.timestamp,
				r = (red('False'),green('True'))[self.is_replaceable()],
				s = self.marked_signed(color=True),
				l = (green('None'),orange(strfmt_locktime(self.locktime,terse=True)))[bool(self.locktime)] )

			if self.chain != 'mainnet':
				yield green(f'Chain: {self.chain.upper()}') + '\n'

			if self.coin_txid:
				yield f'{g.coin} TxID: {self.coin_txid.hl()}\n'

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
				d = g.dcoin,
				c = g.coin )

			if opt.verbose:
				yield self.format_view_verbose_footer()

		return ''.join(gen_view()) # TX label might contain non-ascii chars

	def check_txfile_hex_data(self):
		self.hex = HexStr(self.hex,on_fail='raise')

	def parse_txfile_hex_data(self):
		pass

	def parse_tx_file(self,infile,metadata_only=False,quiet_open=False):

		def eval_io_data(raw_data,desc):
			from ast import literal_eval
			try:
				d = literal_eval(raw_data)
			except:
				if desc == 'inputs' and not quiet_open:
					ymsg('Warning: transaction data appears to be in old format')
				import re
				d = literal_eval(re.sub(r"[A-Za-z]+?\(('.+?')\)",r'\1',raw_data))
			assert type(d) == list,'{} data not a list!'.format(desc)
			if not (desc == 'outputs' and g.proto.base_coin == 'ETH'): # ETH txs can have no outputs
				assert len(d),'no {}!'.format(desc)
			for e in d:
				e['amt'] = g.proto.coin_amt(e['amt'])
			io,io_list = (
				(MMGenTxOutput,MMGenTxOutputList),
				(MMGenTxInput,MMGenTxInputList)
			)[desc=='inputs']
			return io_list([io(**e) for e in d])

		tx_data = get_data_from_file(infile,self.desc+' data',quiet=quiet_open)

		try:
			desc = 'data'
			assert len(tx_data) <= g.max_tx_file_size,(
				'Transaction file size exceeds limit ({} bytes)'.format(g.max_tx_file_size))
			tx_data = tx_data.splitlines()
			assert len(tx_data) >= 5,'number of lines less than 5'
			assert len(tx_data[0]) == 6,'invalid length of first line'
			self.chksum = HexStr(tx_data.pop(0),on_fail='raise')
			assert self.chksum == make_chksum_6(' '.join(tx_data)),'file data does not match checksum'

			if len(tx_data) == 6:
				assert len(tx_data[-1]) == 64,'invalid coin TxID length'
				desc = f'{g.proto.name} TxID'
				self.coin_txid = CoinTxID(tx_data.pop(-1),on_fail='raise')

			if len(tx_data) == 5:
				# rough check: allow for 4-byte utf8 characters + base58 (4 * 11 / 8 = 6 (rounded up))
				assert len(tx_data[-1]) < MMGenTxLabel.max_len*6,'invalid comment length'
				c = tx_data.pop(-1)
				if c != '-':
					desc = 'encoded comment (not base58)'
					from .baseconv import baseconv
					comment = baseconv.tobytes(c,'b58').decode()
					assert comment != False,'invalid comment'
					desc = 'comment'
					self.label = MMGenTxLabel(comment,on_fail='raise')

			desc = 'number of lines' # four required lines
			metadata,self.hex,inputs_data,outputs_data = tx_data
			assert len(metadata) < 100,'invalid metadata length' # rough check
			metadata = metadata.split()

			if metadata[-1].find('LT=') == 0:
				desc = 'locktime'
				self.locktime = int(metadata.pop()[3:])

			self.coin = metadata.pop(0) if len(metadata) == 6 else 'BTC'
			if ':' in self.coin:
				self.coin,self.dcoin = self.coin.split(':')

			if len(metadata) == 5:
				t = metadata.pop(0)
				self.chain = (t.lower(),None)[t=='Unknown']

			desc = 'metadata (4 items minimum required)'
			txid,send_amt,self.timestamp,blockcount = metadata

			desc = 'txid in metadata'
			self.txid = MMGenTxID(txid,on_fail='raise')
			desc = 'send amount in metadata'
			self.send_amt = UnknownCoinAmt(send_amt) # temporary, for 'metadata_only'
			desc = 'block count in metadata'
			self.blockcount = int(blockcount)

			if metadata_only:
				return

			desc = 'send amount in metadata'
			self.send_amt = g.proto.coin_amt(send_amt,on_fail='raise')

			desc = 'transaction file hex data'
			self.check_txfile_hex_data()
			desc = f'transaction file {self.hexdata_type} data'
			self.parse_txfile_hex_data()
			# the following ops will all fail if g.coin doesn't match self.coin
			desc = 'coin type in metadata'
			assert self.coin == g.coin,self.coin
			desc = 'inputs data'
			self.inputs  = eval_io_data(inputs_data,'inputs')
			desc = 'outputs data'
			self.outputs = eval_io_data(outputs_data,'outputs')
		except Exception as e:
			die(2,f'Invalid {desc} in transaction file: {e.args[0]}')

		# test doesn't work for Ethereum: test and mainnet addrs have same format
		if not self.chain and not self.inputs[0].addr.is_for_chain('testnet'):
			self.chain = 'mainnet'

		if self.dcoin:
			self.resolve_g_token_from_txfile()
			g.proto.dcoin = self.dcoin

	def process_cmd_arg(self,arg,ad_f,ad_w):

		def add_output_chk(addr,amt,err_desc):
			if not amt and self.get_chg_output_idx() != None:
				die(2,'ERROR: More than one change address listed on command line')
			if is_mmgen_id(addr) or is_coin_addr(addr):
				coin_addr = mmaddr2coinaddr(addr,ad_w,ad_f) if is_mmgen_id(addr) else CoinAddr(addr)
				self.add_output(coin_addr,g.proto.coin_amt(amt or '0'),is_chg=not amt)
			else:
				die(2,f'{addr}: invalid {err_desc} {{!r}}'.format(f'{addr},{amt}' if amt else addr))

		if ',' in arg:
			addr,amt = arg.split(',',1)
			add_output_chk(addr,amt,'coin argument in command-line argument')
		else:
			add_output_chk(arg,None,'command-line argument')

	def process_cmd_args(self,cmd_args,ad_f,ad_w):

		for a in cmd_args:
			self.process_cmd_arg(a,ad_f,ad_w)

		if self.get_chg_output_idx() == None:
			die(2,( 'ERROR: No change output specified',
					self.msg_no_change_output.format(g.dcoin))[len(self.outputs) == 1])

		if not segwit_is_active() and self.has_segwit_outputs():
			rdie(2,f'{g.proj_name} Segwit address requested on the command line, '
					+ 'but Segwit is not active on this chain')

		if not self.outputs:
			die(2,'At least one output must be specified on the command line')

	async def get_outputs_from_cmdline(self,cmd_args):
		from .addr import AddrList,AddrData,TwAddrData
		addrfiles = [a for a in cmd_args if get_extension(a) == AddrList.ext]
		cmd_args = set(cmd_args) - set(addrfiles)

		ad_f = AddrData()
		for a in addrfiles:
			check_infile(a)
			ad_f.add(AddrList(a))

		ad_w = await TwAddrData(wallet=self.tw)

		self.process_cmd_args(cmd_args,ad_f,ad_w)

		self.add_mmaddrs_to_outputs(ad_w,ad_f)
		self.check_dup_addrs('outputs')

	def select_unspent(self,unspent):
		prompt = 'Enter a range or space-separated list of outputs to spend: '
		while True:
			reply = my_raw_input(prompt).strip()
			if reply:
				selected = AddrIdxList(fmt_str=','.join(reply.split()),on_fail='return')
				if selected:
					if selected[-1] <= len(unspent):
						return selected
					msg('Unspent output number must be <= {}'.format(len(unspent)))

	# we don't know fee yet, so perform preliminary check with fee == 0
	async def precheck_sufficient_funds(self,inputs_sum,sel_unspent):
		if self.twuo.total < self.send_amt:
			msg(self.msg_wallet_low_coin.format(self.send_amt-inputs_sum,g.dcoin))
			return False
		if inputs_sum < self.send_amt:
			msg(self.msg_low_coin.format(self.send_amt-inputs_sum,g.dcoin))
			return False
		return True

	async def get_change_amt(self):
		return self.sum_inputs() - self.send_amt - self.fee

	def warn_insufficient_chg(self,change_amt):
		msg(self.msg_low_coin.format(g.proto.coin_amt(-change_amt).hl(),g.coin))

	def final_inputs_ok_msg(self,change_amt):
		return f'Transaction produces {g.proto.coin_amt(change_amt).hl()} {g.coin} in change'

	def select_unspent_cmdline(self,unspent):

		def idx2num(idx):
			uo = unspent[idx]
			mmid_disp = f' ({uo.twmmid})' if uo.twmmid.type == 'mmgen' else ''
			msg(f'Adding input: {idx + 1} {uo.addr}{mmid_disp}')
			return idx + 1

		def get_uo_nums():
			for addr in opt.inputs.split(','):
				if is_mmgen_id(addr):
					attr = 'twmmid'
				elif is_coin_addr(addr):
					attr = 'addr'
				else:
					die(1,f'{addr!r}: not an MMGen ID or {g.coin} address')

				found = False
				for idx in range(len(unspent)):
					if getattr(unspent[idx],attr) == addr:
						yield idx2num(idx)
						found = True

				if not found:
					die(1,f'{addr!r}: address not found in tracking wallet')

		return set(get_uo_nums()) # silently discard duplicates

	async def get_cmdline_input_addrs(self):
		# Bitcoin full node, call doesn't go to the network, so just call listunspent with addrs=[]
		return []

	async def get_inputs_from_user(self):

		while True:
			us_f = self.select_unspent_cmdline if opt.inputs else self.select_unspent
			sel_nums = us_f(self.twuo.unspent)

			msg(f'Selected output{suf(sel_nums)}: {{}}'.format(' '.join(str(n) for n in sel_nums)))
			sel_unspent = self.twuo.MMGenTwOutputList([self.twuo.unspent[i-1] for i in sel_nums])

			inputs_sum = sum(s.amt for s in sel_unspent)
			if not await self.precheck_sufficient_funds(inputs_sum,sel_unspent):
				continue

			non_mmaddrs = [i for i in sel_unspent if i.twmmid.type == 'non-mmgen']
			if non_mmaddrs and self.caller != 'txdo':
				msg(self.msg_non_mmgen_inputs.format(
					', '.join(sorted({a.addr.hl() for a in non_mmaddrs}))))
				if not (opt.yes or keypress_confirm('Accept?')):
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

	def check_fee(self):
		assert self.sum_inputs() - self.sum_outputs() <= g.proto.max_tx_fee

	def update_send_amt(self,change_amt):
		if not self.send_amt:
			self.send_amt = change_amt

	async def set_token_params(self):
		pass

	async def create(self,cmd_args,locktime,do_info=False):
		assert isinstance(locktime,int),'locktime must be of type int'

		from .tw import TwUnspentOutputs

		if opt.comment_file:
			self.add_comment(opt.comment_file)

		twuo_addrs = await self.get_cmdline_input_addrs()

		self.twuo = await TwUnspentOutputs(minconf=opt.minconf,addrs=twuo_addrs)
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
		msg(f'{self.send_amt.hl()} {g.dcoin}' if self.send_amt else 'Unknown')

		change_amt = await self.get_inputs_from_user()

		self.update_change_output(change_amt)
		self.update_send_amt(change_amt)

		if g.proto.base_proto == 'Bitcoin':
			self.inputs.sort_bip69()
			self.outputs.sort_bip69()
			# do this only after inputs are sorted
			if opt.rbf:
				self.inputs[0].sequence = g.max_int - 2 # handles the locktime case too
			elif locktime:
				self.inputs[0].sequence = g.max_int - 1

		if not opt.yes:
			self.add_comment()  # edits an existing comment

		await self.create_raw()       # creates self.hex, self.txid

		if g.proto.base_proto == 'Bitcoin' and locktime:
			msg(f'Setting nlocktime to {strfmt_locktime(locktime)}!')
			self.set_hex_locktime(locktime)
			self.update_txid()
			self.locktime = locktime

		self.add_timestamp()
		self.add_blockcount()
		self.chain = g.chain

		self.check_fee()

		qmsg('Transaction successfully created')

		if not opt.yes:
			self.view_with_prompt('View decoded transaction?')

		del self.twuo.wallet

class MMGenTxForSigning(MMGenTX):

	hexdata_type = 'json'

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tx','MMGenTxForSigning'))

	async def sign(self,tx_num_str,keys): # return True or False; don't exit or raise exception

		if self.marked_signed():
			msg('Transaction is already signed!')
			return False

		try:
			self.check_correct_chain()
		except TransactionChainMismatch:
			return False

		if (self.has_segwit_inputs() or self.has_segwit_outputs()) and not g.proto.cap('segwit'):
			ymsg(f"TX has Segwit inputs or outputs, but {g.coin} doesn't support Segwit!")
			return False

		self.check_pubkey_scripts()

		qmsg(f'Passing {len(keys)} key{suf(keys)} to {g.proto.daemon_name}')

		if self.has_segwit_inputs():
			from .addr import KeyGenerator,AddrGenerator
			kg = KeyGenerator('std')
			ag = AddrGenerator('segwit')
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
				('signrawtransaction',       self.hex,sig_data,wifs,g.proto.sighash_type),
				('signrawtransactionwithkey',self.hex,wifs,sig_data,g.proto.sighash_type)
			)['sign_with_key' in g.rpc.caps]
			ret = await g.rpc.call(*args)
		except Exception as e:
			msg(yellow((
				e.args[0],
				'This is not the BCH chain.\nRe-run the script without the --coin=bch option.'
			)['Invalid sighash param' in e.args[0]]))
			return False

		try:
			self.hex = HexStr(ret['hex'])
			tx_decoded = await g.rpc.call('decoderawtransaction',ret['hex'])
			self.compare_size_and_estimated_size(tx_decoded)
			dt = DeserializedTX(self.hex)
			self.check_hex_tx_matches_mmgen_tx(dt)
			self.coin_txid = CoinTxID(dt['txid'],on_fail='raise')
			self.check_sigs(dt)
			if not self.coin_txid == tx_decoded['txid']:
				raise BadMMGenTxID('txid mismatch (after signing)')
			msg('OK')
			return True
		except Exception as e:
			try: m = '{}'.format(e.args[0])
			except: m = repr(e.args[0])
			msg('\n'+yellow(m))
			if g.traceback:
				import traceback
				ymsg('\n'+''.join(traceback.format_exception(*sys.exc_info())))
			return False

class MMGenBumpTX(MMGenTxForSigning):

	def __new__(cls,*args,**kwargs):
		return MMGenTX.__new__(altcoin_subclass(cls,'tx','MMGenBumpTX'),*args,**kwargs)

	min_fee = None
	bump_output_idx = None

	def __init__(self,filename,send=False,tw=None):
		super().__init__(filename,tw=tw)

		if not self.is_replaceable():
			die(1,f'Transaction {self.txid} is not replaceable')

		# If sending, require tx to be signed
		if send:
			if not self.marked_signed():
				die(1,'File {filename!r} is not a signed {g.proj_name} transaction file')
			if not self.coin_txid:
				die(1,'Transaction {self.txid!r} was not broadcast to the network')

		self.coin_txid = ''
		self.mark_raw()

	def check_bumpable(self):
		if not [o.amt for o in self.outputs if o.amt >= self.min_fee]:
			die(1,
				'Transaction cannot be bumped.\n' +
				f'All outputs contain less than the minimum fee ({self.min_fee} {g.coin})')

	def choose_output(self):
		chg_idx = self.get_chg_output_idx()
		init_reply = opt.output_to_reduce

		def check_sufficient_funds(o_amt):
			if o_amt < self.min_fee:
				msg(f'Minimum fee ({self.min_fee} {g.coin}) is greater than output amount ({o_amt} {g.coin})')
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
					prompt = f'Fee will be deducted from output {idx+1}{cm} ({o_amt} {g.coin})'
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
				c = g.coin ))
			return False
		output_amt = self.outputs[self.bump_output_idx].amt
		if ret >= output_amt:
			msg('{} {c}: {} fee too large. Maximum fee: <{} {c}'.format(
				ret.hl(),
				desc,
				output_amt.hl(),
				c = g.coin ))
			return False
		return ret

# NOT MAINTAINED
class MMGenSplitTX(MMGenTX):

	async def get_outputs_from_cmdline(self,mmid): # TODO: check that addr is empty

		from .addr import TwAddrData
		ad_w = await TwAddrData()

		if is_mmgen_id(mmid):
			coin_addr = mmaddr2coinaddr(mmid,ad_w,None) if is_mmgen_id(mmid) else CoinAddr(mmid)
			self.add_output(coin_addr,g.proto.coin_amt('0'),is_chg=True)
		else:
			die(2,'{}: invalid command-line argument'.format(mmid))

		self.add_mmaddrs_to_outputs(ad_w,None)

		if not segwit_is_active() and self.has_segwit_outputs():
			fs = '{} Segwit address requested on the command line, but Segwit is not active on this chain'
			rdie(2,fs.format(g.proj_name))

	def get_split_fee_from_user(self):
		if opt.rpc_host2:
			g.rpc_host = opt.rpc_host2
		if opt.tx_fees:
			opt.tx_fee = opt.tx_fees.split(',')[1]
		return super().get_fee_from_user()

	async def create_split(self,mmid):

		self.outputs = self.MMGenTxOutputList()
		await self.get_outputs_from_cmdline(mmid)

		while True:
			change_amt = self.sum_inputs() - self.get_split_fee_from_user()
			if change_amt >= 0:
				p = 'Transaction produces {} {} in change'.format(change_amt.hl(),g.coin)
				if opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
					if opt.yes:
						msg(p)
					break
			else:
				self.warn_insufficient_chg(change_amt)

		self.update_output_amt(0,change_amt)
		self.send_amt = change_amt

		if not opt.yes:
			self.add_comment()  # edits an existing comment

		await self.create_raw()       # creates self.hex, self.txid

		self.add_timestamp()
		self.add_blockcount() # TODO
		self.chain = g.chain

		assert self.sum_inputs() - self.sum_outputs() <= g.proto.max_tx_fee

		qmsg('Transaction successfully created')

		if not opt.yes:
			self.view_with_prompt('View decoded transaction?')
