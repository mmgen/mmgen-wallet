#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
from binascii import unhexlify
from mmgen.common import *
from mmgen.obj import *

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
	if num >= 5 * 10**6:
		return ' '.join(time.strftime('%c',time.gmtime(num)).split()[1:])
	elif num > 0:
		return '{}{}'.format(('block height ','')[terse],num)
	elif num == None:
		return '(None)'
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
	d = g.rpch.getblockchaininfo()
	if d['chain'] == 'regtest':
		return True
	if 'segwit' in d['bip9_softforks'] and d['bip9_softforks']['segwit']['status'] == 'active':
		return True
	if g.skip_segwit_active_check:
		return True
	if exit_on_error:
		die(2,'Segwit not active on this chain.  Exiting')
	else:
		return False

def bytes2int(hex_bytes):
	r = hexlify(unhexlify(hex_bytes)[::-1])
	if r[0] in '89abcdef':
		die(3,"{}: Negative values not permitted in transaction!".format(hex_bytes))
	return int(r,16)

def bytes2coin_amt(hex_bytes):
	return g.proto.coin_amt(bytes2int(hex_bytes) * g.proto.coin_amt.min_coin_unit)

def scriptPubKey2addr(s):
	if len(s) == 50 and s[:6] == '76a914' and s[-4:] == '88ac':
		return g.proto.pubhash2addr(s[6:-4],p2sh=False),'p2pkh'
	elif len(s) == 46 and s[:4] == 'a914' and s[-2:] == '87':
		return g.proto.pubhash2addr(s[4:-2],p2sh=True),'p2sh'
	elif len(s) == 44 and s[:4] == g.proto.witness_vernum_hex + '14':
		return g.proto.pubhash2bech32addr(s[4:]),'bech32'
	else:
		raise NotImplementedError,'Unknown scriptPubKey ({})'.format(s)

from collections import OrderedDict
class DeserializedTX(OrderedDict,MMGenObject): # need to add MMGen types
	def __init__(self,txhex):
		tx = list(unhexlify(txhex))
		tx_copy = tx[:]
		d = { 'raw_tx':'' }

		def hshift(l,n,reverse=False,skip=False):
			ret = l[:n]
			if not skip: d['raw_tx'] += ''.join(ret)
			del l[:n]
			return hexlify(''.join(ret[::-1] if reverse else ret))

		# https://bitcoin.org/en/developer-reference#compactsize-unsigned-integers
		# For example, the number 515 is encoded as 0xfd0302.
		def readVInt(l,skip=False,sub_null=False):
			s = int(hexlify(l[0]),16)
			bytes_len = 1 if s < 0xfd else 2 if s == 0xfd else 4 if s == 0xfe else 8
			if bytes_len != 1: del l[0]
			ret = int(hexlify(''.join(l[:bytes_len][::-1])),16)
			if sub_null: d['raw_tx'] += '\0'
			elif not skip: d['raw_tx'] += ''.join(l[:bytes_len])
			del l[:bytes_len]
			return ret

		d['version'] = bytes2int(hshift(tx,4))
		has_witness = tx[0] == '\x00'
		if has_witness:
			u = hshift(tx,2,skip=True)[2:]
			if u != '01':
				raise IllegalWitnessFlagValue,"'{}': Illegal value for flag in transaction!".format(u)
			del tx_copy[-len(tx)-2:-len(tx)]

		d['num_txins'] = readVInt(tx)
		d['txins'] = MMGenList([OrderedDict((
			('txid',      hshift(tx,32,reverse=True)),
			('vout',      bytes2int(hshift(tx,4))),
			('scriptSig', hshift(tx,readVInt(tx,sub_null=True),skip=True)),
			('nSeq',      hshift(tx,4,reverse=True))
		)) for i in range(d['num_txins'])])

		d['num_txouts'] = readVInt(tx)
		d['txouts'] = MMGenList([OrderedDict((
			('amount',       bytes2coin_amt(hshift(tx,8))),
			('scriptPubKey', hshift(tx,readVInt(tx)))
		)) for i in range(d['num_txouts'])])

		for o in d['txouts']:
			o['address'] = scriptPubKey2addr(o['scriptPubKey'])[0]

		d['witness_size'] = 0
		if has_witness:
			# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
			# A non-witness program (defined hereinafter) txin MUST be associated with an empty
			# witness field, represented by a 0x00.
			del tx_copy[-len(tx):-4]
			wd,tx = tx[:-4],tx[-4:]
			d['witness_size'] = len(wd) + 2 # add marker and flag
			for i in range(len(d['txins'])):
				if hexlify(wd[0]) == '00':
					hshift(wd,1,skip=True)
					continue
				d['txins'][i]['witness'] = [
					hshift(wd,readVInt(wd,skip=True),skip=True) for item in range(readVInt(wd,skip=True))
				]
			if wd:
				raise WitnessSizeMismatch,'More witness data than inputs with witnesses!'

		d['lock_time'] = bytes2int(hshift(tx,4))
		d['txid'] = hexlify(sha256(sha256(''.join(tx_copy)).digest()).digest()[::-1])
		d['unsigned_hex'] = hexlify(d['raw_tx'])
		del d['raw_tx']

		keys = 'txid','version','lock_time','witness_size','num_txins','txins','num_txouts','txouts','unsigned_hex'
		return OrderedDict.__init__(self, ((k,d[k]) for k in keys))

txio_attrs = {
	'vout':  MMGenListItemAttr('vout',int,typeconv=False),
	'amt':   MMGenImmutableAttr('amt',g.proto.coin_amt,typeconv=False), # require amt to be of proper type
	'label': MMGenListItemAttr('label','TwComment',reassign_ok=True),
	'mmid':  MMGenListItemAttr('mmid','MMGenID'),
	'addr':  MMGenImmutableAttr('addr','CoinAddr'),
	'confs': MMGenListItemAttr('confs',int,typeconv=True), # long confs exist in the wild, so convert
	'txid':  MMGenListItemAttr('txid','CoinTxID'),
	'have_wif': MMGenListItemAttr('have_wif',bool,typeconv=False,delete_ok=True)
}

class MMGenTX(MMGenObject):

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tx','MMGenTX'),*args,**kwargs)

	ext      = 'rawtx'
	raw_ext  = 'rawtx'
	sig_ext  = 'sigtx'
	txid_ext = 'txid'
	desc     = 'transaction'
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

	msg_low_coin = 'Selected outputs insufficient to fund this transaction ({} {} needed)'
	msg_no_change_output = """
ERROR: No change address specified.  If you wish to create a transaction with
only one output, specify a single output address with no {} amount
""".strip()
	msg_non_mmgen_inputs = """
NOTE: This transaction includes non-{pnm} inputs, which makes the signing
process more complicated.  When signing the transaction, keys for non-{pnm}
inputs must be supplied to '{pnl}-txsign' in a file with the '--keys-from-file'
option.
Selected non-{pnm} inputs: {{}}""".strip().format(pnm=g.proj_name,pnl=g.proj_name.lower())

	class MMGenTxInput(MMGenListItem):
		for k in txio_attrs: locals()[k] = txio_attrs[k] # in lieu of inheritance
		scriptPubKey = MMGenListItemAttr('scriptPubKey','HexStr')
		sequence = MMGenListItemAttr('sequence',(int,long)[g.platform=='win'],typeconv=False)

	class MMGenTxOutput(MMGenListItem):
		for k in txio_attrs: locals()[k] = txio_attrs[k]
		is_chg = MMGenListItemAttr('is_chg',bool,typeconv=False)

	class MMGenTxInputList(list,MMGenObject):

		desc = 'transaction inputs'
		member_type = 'MMGenTxInput'

		def convert_coin(self,verbose=False):
			from mmgen.protocol import CoinProtocol
			io = getattr(MMGenTX,self.member_type)
			if verbose:
				msg('{}:'.format(self.desc.capitalize()))
			for i in self:
				d = i.__dict__
				d['amt'] = g.proto.coin_amt(d['amt'])
				i = io(**d)
				if verbose:
					pmsg(i.__dict__)

		def check_coin_mismatch(self):
			for i in self:
				if type(i.amt) != g.proto.coin_amt:
					die(2,'Coin mismatch in transaction: amount {} not of type {}!'.format(i.amt,g.proto.coin_amt))

	class MMGenTxOutputList(MMGenTxInputList):

		desc = 'transaction outputs'
		member_type = 'MMGenTxOutput'

	def __init__(self,filename=None,metadata_only=False,caller=None,silent_open=False):
		self.inputs      = self.MMGenTxInputList()
		self.outputs     = self.MMGenTxOutputList()
		self.send_amt    = g.proto.coin_amt('0')  # total amt minus change
		self.fee         = g.proto.coin_amt('0')
		self.hex         = ''           # raw serialized hex transaction
		self.label       = MMGenTXLabel('')
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

		if filename:
			self.parse_tx_file(filename,metadata_only=metadata_only,silent_open=silent_open)
			if metadata_only: return
			self.check_pubkey_scripts()
			self.check_sigs() # marks the tx as signed

		# repeat with sign and send, because coin daemon could be restarted
		self.check_correct_chain(on_fail='die')

	def check_correct_chain(self,on_fail='return'):
		assert on_fail in ('return','die'),"'{}': invalid value for 'on_fail'".format(on_fail)
		m = 'Transaction is for {}, but current chain is {}!'.format(self.chain,g.chain)
		bad = self.chain and g.chain and self.chain != g.chain
		if bad and hasattr(g.proto,'chain_name'):
			bad = self.chain != g.proto.chain_name
		if bad:
			msg(m) if on_fail == 'return' else die(2,m)
		return not bad

	def add_output(self,coinaddr,amt,is_chg=None):
		self.outputs.append(MMGenTX.MMGenTxOutput(addr=coinaddr,amt=amt,is_chg=is_chg))

	def get_chg_output_idx(self):
		try: return map(lambda x: x.is_chg,self.outputs).index(True)
		except ValueError: return None

	def update_output_amt(self,idx,amt):
		o = self.outputs[idx].__dict__
		o['amt'] = amt
		self.outputs[idx] = MMGenTX.MMGenTxOutput(**o)

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
		if not len(self.outputs): return g.proto.coin_amt(0)
		olist = self.outputs if exclude == None else \
			self.outputs[:exclude] + self.outputs[exclude+1:]
		return g.proto.coin_amt(sum(e.amt for e in olist))

	def add_mmaddrs_to_outputs(self,ad_w,ad_f):
		a = [e.addr for e in self.outputs]
		d = ad_w.make_reverse_dict(a)
		if ad_f:
			d.update(ad_f.make_reverse_dict(a))
		for e in self.outputs:
			if e.addr and e.addr in d:
				e.mmid,f = d[e.addr]
				if f: e.label = f

	def check_dup_addrs(self,io_str):
		assert io_str in ('inputs','outputs')
		io = getattr(self,io_str)
		for k in ('mmid','addr'):
			old_attr = None
			for attr in sorted(getattr(e,k) for e in io):
				if attr != None and attr == old_attr:
					die(2,'{}: duplicate address in transaction {}'.format(attr,io_str))
				old_attr = attr

	def update_txid(self):
		self.txid = MMGenTxID(make_chksum_6(unhexlify(self.hex)).upper())

	def create_raw(self):
		i = [{'txid':e.txid,'vout':e.vout} for e in self.inputs]
		if self.inputs[0].sequence:
			i[0]['sequence'] = self.inputs[0].sequence
		o = dict([(e.addr,e.amt) for e in self.outputs])
		self.hex = g.rpch.createrawtransaction(i,o)
		self.update_txid()

	# returns true if comment added or changed
	def add_comment(self,infile=None):
		if infile:
			self.label = MMGenTXLabel(get_data_from_file(infile,'transaction comment'))
		else: # get comment from user, or edit existing comment
			m = ('Add a comment to transaction?','Edit transaction comment?')[bool(self.label)]
			if keypress_confirm(m,default_yes=False):
				while True:
					s = MMGenTXLabel(my_raw_input('Comment: ',insert_txt=self.label))
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

	def compare_size_and_estimated_size(self):
		est_vsize = self.estimate_size()
		d = g.rpch.decoderawtransaction(self.hex)
		vsize = d['vsize'] if 'vsize' in d else d['size']
		vmsg('\nSize: {}, Vsize: {} (true) {} (estimated)'.format(d['size'],vsize,est_vsize))
		m1 = '\nERROR: Estimated transaction vsize is {:1.2f} times the true vsize\n'
		m2 = 'Your transaction fee estimates will be inaccurate\n'
		m3 = 'Please re-create and re-sign the transaction using the option --vsize-adj={:1.2f}'
		# allow for 5% error
		ratio = float(est_vsize) / vsize
		if not (0.95 < ratio < 1.05):
			raise BadTxSizeEstimate,(m1+m2+m3).format(ratio,1/ratio)

	# https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
	# 180: uncompressed, 148: compressed
	def estimate_size_old(self):
		if not self.inputs or not self.outputs: return None
		return len(self.inputs)*180 + len(self.outputs)*34 + 10

	# https://bitcoincore.org/en/segwit_wallet_dev/
	# vsize: 3 times of the size with original serialization, plus the size with new
	# serialization, divide the result by 4 and round up to the next integer.

	# TODO: results differ slightly from actual transaction size
	def estimate_size(self):
		if not self.inputs or not self.outputs: return None

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
			if not self.has_segwit_inputs(): return 0
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

		ret = (old_size * 3 + new_size) / 4

		dmsg('\nData from estimate_size():')
		dmsg('  inputs size: {}, outputs size: {}, witness size: {}'.format(isize,osize,wsize))
		dmsg('  size: {}, vsize: {}, old_size: {}'.format(new_size,ret,old_size))

		return int(ret * float(opt.vsize_adj)) if hasattr(opt,'vsize_adj') and opt.vsize_adj else ret

	# coin-specific fee routines
	def get_relay_fee(self):
		kb_fee = g.proto.coin_amt(g.rpch.getnetworkinfo()['relayfee'])
		ret = kb_fee * self.estimate_size() / 1024
		vmsg('Relay fee: {} {c}/kB, for transaction: {} {c}'.format(kb_fee,ret,c=g.coin))
		return ret

	# convert absolute BTC fee to satoshis-per-byte using estimated size
	def fee_abs2rel(self,abs_fee,to_unit=None):
		unit = getattr(g.proto.coin_amt,to_unit or 'min_coin_unit')
		return int(abs_fee / unit / self.estimate_size())

	def get_rel_fee_from_network(self): # rel_fee is in BTC/kB
		try:
			ret = g.rpch.estimatesmartfee(opt.tx_confs)
			rel_fee = ret['feerate'] if 'feerate' in ret else -2
			fe_type = 'estimatesmartfee'
		except:
			rel_fee = g.rpch.estimatefee(opt.tx_confs)
			fe_type = 'estimatefee'

		return rel_fee,fe_type

	# given tx size, rel fee and units, return absolute fee
	def convert_fee_spec(self,tx_size,units,amt,unit):
		self.usr_rel_fee = None # TODO
		return g.proto.coin_amt(int(amt)*tx_size*getattr(g.proto.coin_amt,units[unit])) \
			if tx_size else None

	# given network fee estimate in BTC/kB, return absolute fee using estimated tx size
	def fee_est2abs(self,rel_fee,fe_type=None):
		tx_size = self.estimate_size()
		ret = g.proto.coin_amt(rel_fee) * opt.tx_fee_adj * tx_size / 1024
		if opt.verbose:
			msg('{} fee for {} confirmations: {} {}/kB'.format(fe_type.upper(),opt.tx_confs,rel_fee,g.coin))
			msg('TX size (estimated): {}'.format(tx_size))
		return ret

	def convert_and_check_fee(self,tx_fee,desc='Missing description'):
		abs_fee = self.process_fee_spec(tx_fee,self.estimate_size(),on_fail='return')
		if abs_fee == None:
			# we shouldn't be calling this if tx size is unknown
			m = "'{}': cannot convert {} to {} because transaction size is unknown"
			assert False, m.format(tx_fee,self.rel_fee_desc,g.coin)
		elif abs_fee == False:
			m = "'{}': invalid TX fee (not a {} amount or {} specification)"
			msg(m.format(tx_fee,g.coin,self.rel_fee_desc))
			return False
		elif abs_fee > g.proto.max_tx_fee:
			m = '{} {c}: {} fee too large (maximum fee: {} {c})'
			msg(m.format(abs_fee,desc,g.proto.max_tx_fee,c=g.coin))
			return False
		elif abs_fee < self.get_relay_fee():
			m = '{} {c}: {} fee too small (below relay fee of {} {c})'
			msg(m.format(str(abs_fee),desc,str(self.get_relay_fee()),c=g.coin))
			return False
		else:
			return abs_fee

	# non-coin-specific fee routines

	# given tx size and absolute fee or fee spec, return absolute fee
	# relative fee is N+<first letter of unit name>
	def process_fee_spec(self,tx_fee,tx_size,on_fail='throw'):
		import re
		units = dict((u[0],u) for u in g.proto.coin_amt.units)
		pat = r'([1-9][0-9]*)({})'.format('|'.join(units.keys()))
		if g.proto.coin_amt(tx_fee,on_fail='silent'):
			return g.proto.coin_amt(tx_fee)
		elif re.match(pat,tx_fee):
			return self.convert_fee_spec(tx_size,units,*re.match(pat,tx_fee).groups())
		else:
			if on_fail == 'return':
				return False
			elif on_fail == 'throw':
				assert False, "'{}': invalid tx-fee argument".format(tx_fee)

	def get_usr_fee_interactive(self,tx_fee=None,desc='Starting'):
		abs_fee = None
		while True:
			if tx_fee:
				abs_fee = self.convert_and_check_fee(tx_fee,desc)
			if abs_fee:
				m = ('',' (after {}x adjustment)'.format(opt.tx_fee_adj))[opt.tx_fee_adj != 1]
				p = u'{} TX fee{}: {}{} {} ({} {})\n'.format(
						desc,
						m,
						('',u'≈')[self.fee_is_approximate],
						abs_fee.hl(),
						g.coin,
						pink(str(self.fee_abs2rel(abs_fee))),
						self.rel_fee_disp)
				if opt.yes or keypress_confirm(p+'OK?',default_yes=True):
					if opt.yes: msg(p)
					return abs_fee
			tx_fee = my_raw_input(self.usr_fee_prompt)
			desc = 'User-selected'

	def get_fee_from_user(self,have_estimate_fail=[]):

		if opt.tx_fee:
			desc = 'User-selected'
			start_fee = opt.tx_fee
		else:
			desc = 'Network-estimated'
			rel_fee,fe_type = self.get_rel_fee_from_network()

			if rel_fee < 0:
				if not have_estimate_fail:
					msg(self.fee_fail_fs.format(c=opt.tx_confs,t=fe_type))
					have_estimate_fail.append(True)
				start_fee = None
			else:
				start_fee = self.fee_est2abs(rel_fee,fe_type)

		return self.get_usr_fee_interactive(start_fee,desc=desc)

	def delete_attrs(self,desc,attr):
		for e in getattr(self,desc):
			if hasattr(e,attr): delattr(e,attr)

	def decode_io_oldfmt(self,data):
		tr = {'amount':'amt', 'address':'addr', 'confirmations':'confs','comment':'label'}
		tr_rev = dict(map(reversed,tr.items()))
		copy_keys = [tr_rev[k] if k in tr_rev else k for k in self.MMGenTxInput.__dict__]
		ret = MMGenList(self.MMGenTxInput(**dict([(tr[k] if k in tr else k,d[k])
					for k in copy_keys if k in d and d[k] != ''])) for d in data)
		for i in ret: i.sequence = int('0xffffffff',16)
		return ret

	# inputs methods
	def copy_inputs_from_tw(self,tw_unspent_data):
		txi,self.inputs = self.MMGenTxInput,self.MMGenTxInputList()
		for d in tw_unspent_data:
			t = txi(**dict([(attr,getattr(d,attr)) for attr in d.__dict__ if attr in txi.__dict__]))
			if d.twmmid.type == 'mmgen': t.mmid = d.twmmid # twmmid -> mmid
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
		return int(hexlify(unhexlify(self.hex[-8:])[::-1]),16)

	def set_hex_locktime(self,val):
		assert type(val) == int,'locktime value not an integer'
		self.hex = self.hex[:-8] + hexlify(unhexlify('{:08x}'.format(val))[::-1])

	def get_blockcount(self):
		return int(g.rpch.getblockcount())

	def add_blockcount(self):
		self.blockcount = self.get_blockcount()

	def format(self):
		self.inputs.check_coin_mismatch()
		self.outputs.check_coin_mismatch()
		def amt_to_str(d):
			return dict([(k,str(d[k]) if k == 'amt' else d[k]) for k in d])
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
			lines.append(baseconv.b58encode(self.label.encode('utf8')))
		if self.coin_txid:
			if not self.label: lines.append('-') # keep old tx files backwards compatible
			lines.append(self.coin_txid)
		self.chksum = make_chksum_6(' '.join(lines))
		self.fmt_data = '\n'.join([self.chksum] + lines)+'\n'

		assert len(self.fmt_data) <= g.max_tx_file_size,(
			'Transaction file size exceeds limit ({} bytes)'.format(g.max_tx_file_size))

	def get_non_mmaddrs(self,desc):
		return list(set(i.addr for i in getattr(self,desc) if not i.mmid))

	def sign(self,tx_num_str,keys): # return True or False; don't exit or raise exception

		if self.marked_signed():
			msg('Transaction is already signed!')
			return False

		if not self.check_correct_chain(on_fail='return'):
			return False

		if (self.has_segwit_inputs() or self.has_segwit_outputs()) and not g.proto.cap('segwit'):
			ymsg("TX has Segwit inputs or outputs, but {} doesn't support Segwit!".format(g.coin))
			return False

		self.check_pubkey_scripts()

		qmsg('Passing {} key{} to {}'.format(len(keys),suf(keys,'s'),g.proto.daemon_name))

		if self.has_segwit_inputs():
			from mmgen.addr import KeyGenerator,AddrGenerator
			kg = KeyGenerator('std')
			ag = AddrGenerator('segwit')
			keydict = MMGenDict([(d.addr,d.sec) for d in keys])

		sig_data = []
		for d in self.inputs:
			e = dict([(k,getattr(d,k)) for k in ('txid','vout','scriptPubKey','amt')])
			e['amount'] = e['amt']
			del e['amt']
			if d.mmid and d.mmid.mmtype == 'S':
				e['redeemScript'] = ag.to_segwit_redeem_script(kg.to_pubhex(keydict[d.addr]))
			sig_data.append(e)

		msg_r('Signing transaction{}...'.format(tx_num_str))
		wifs = [d.sec.wif for d in keys]

		try:
			ret = g.rpch.signrawtransactionwithkey(self.hex,wifs,sig_data,g.proto.sighash_type) \
				if 'sign_with_key' in g.rpch.caps else \
					g.rpch.signrawtransaction(self.hex,sig_data,wifs,g.proto.sighash_type)
		except Exception as e:
			msg(yellow('This is not the BCH chain.\nRe-run the script without the --coin=bch option.'
				if 'Invalid sighash param' in e.message else e.message))
			return False

		if not ret['complete']:
			msg('failed\n{} returned the following errors:'.format(g.proto.daemon_name.capitalize()))
			msg(repr(ret['errors']))
			return False

		try:
			self.hex = ret['hex']
			self.compare_size_and_estimated_size()
			dt = DeserializedTX(self.hex)
			self.check_hex_tx_matches_mmgen_tx(dt)
			self.coin_txid = CoinTxID(dt['txid'],on_fail='raise')
			self.check_sigs(dt)
			if not self.coin_txid == g.rpch.decoderawtransaction(self.hex)['txid']:
				raise BadMMGenTxID,'txid mismatch (after signing)'
			msg('OK')
			return True
		except Exception as e:
			msg(yellow(repr(e.message)))
			return False

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
		m = 'Fatal error: a malicious or malfunctioning coin daemon or other program may have altered your data!'

		lt = deserial_tx['lock_time']
		if lt != int(self.locktime or 0):
			m2 = '\nTransaction hex locktime ({}) does not match MMGen transaction locktime ({})\n{}'
			raise TxHexMismatch,m2.format(lt,self.locktime,m)

		def check_equal(desc,hexio,mmio):
			if mmio != hexio:
				msg('\nMMGen {}:\n{}'.format(desc,pformat(mmio)))
				msg('Hex {}:\n{}'.format(desc,pformat(hexio)))
				m2 = '{} in hex transaction data from coin daemon do not match those in MMGen transaction!\n'
				raise TxHexMismatch,(m2+m).format(desc.capitalize())

		seq_hex   = map(lambda i: int(i['nSeq'],16),deserial_tx['txins'])
		seq_mmgen = map(lambda i: i.sequence or g.max_int,self.inputs)
		check_equal('sequence numbers',seq_hex,seq_mmgen)

		d_hex   = sorted((i['txid'],i['vout']) for i in deserial_tx['txins'])
		d_mmgen = sorted((i.txid,i.vout) for i in self.inputs)
		check_equal('inputs',d_hex,d_mmgen)

		d_hex   = sorted((o['address'],g.proto.coin_amt(o['amount'])) for o in deserial_tx['txouts'])
		d_mmgen = sorted((o.addr,o.amt) for o in self.outputs)
		check_equal('outputs',d_hex,d_mmgen)

		uh = deserial_tx['unsigned_hex']
		if str(self.txid) != make_chksum_6(unhexlify(uh)).upper():
			raise TxHexMismatch,'MMGen TxID ({}) does not match hex transaction data!\n{}'.format(self.txid,m)

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
				assert mmti.mmid.mmtype == ('S','B')[ti['scriptSig']==''],fs.format('witness-type',mmti.mmid.mmtype)
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

	def is_in_mempool(self):
		return 'size' in g.rpch.getmempoolentry(self.coin_txid,on_fail='silent')

	def is_in_wallet(self):
		ret = g.rpch.gettransaction(self.coin_txid,on_fail='silent')
		if 'confirmations' in ret and ret['confirmations'] > 0:
			return ret['confirmations']
		else:
			return False

	def is_replaced(self):
		if self.is_in_mempool(): return False
		ret = g.rpch.gettransaction(self.coin_txid,on_fail='silent')
		if not 'bip125-replaceable' in ret or not 'confirmations' in ret or ret['confirmations'] > 0:
			return False
		return -ret['confirmations'] + 1,ret # 1: replacement in mempool, 2: replacement confirmed

	def is_in_utxos(self):
		return 'txid' in g.rpch.getrawtransaction(self.coin_txid,True,on_fail='silent')

	def get_status(self,status=False):
		if self.is_in_mempool():
			if status:
				d = g.rpch.gettransaction(self.coin_txid,on_fail='silent')
				brs = 'bip125-replaceable'
				r = '{}replaceable'.format(('NOT ','')[brs in d and d[brs]=='yes'])
				t = d['timereceived']
				m = 'Sent {} ({} h/m/s ago)'
				b = m.format(time.strftime('%c',time.gmtime(t)),secs_to_dhms(int(time.time()-t)))
				if opt.quiet:
					msg('Transaction is in mempool')
				else:
					msg('TX status: in mempool, {}\n{}'.format(r,b))
			else:
				msg('Warning: transaction is in mempool!')
		elif self.is_in_wallet():
			confs = self.is_in_wallet()
			die(0,'Transaction has {} confirmation{}'.format(confs,suf(confs,'s')))
		elif self.is_in_utxos():
			die(2,red('ERROR: transaction is in the blockchain (but not in the tracking wallet)!'))
		else:
			ret = self.is_replaced() # ret[0]==1: replacement in mempool, ret[0]==2: replacement confirmed
			if ret and ret[0]:
				m1 = 'Transaction has been replaced'
				m2 = ('',', and the replacement TX is confirmed')[ret[0]==2]
				msg('{}{}!'.format(m1,m2))
				if not opt.quiet:
					msg('Replacing transactions:')
					rt = ret[1]['walletconflicts']
					for t,s in [(tx,'size' in g.rpch.getmempoolentry(tx,on_fail='silent')) for tx in rt]:
						msg('  {}{}'.format(t,('',' in mempool')[s]))
				die(0,'')

	def confirm_send(self):
		m1 = ("Once this transaction is sent, there's no taking it back!",'')[bool(opt.quiet)]
		m2 = 'broadcast this transaction to the {} network'.format(g.chain.upper())
		m3 = ('YES, I REALLY WANT TO DO THIS','YES')[bool(opt.quiet or opt.yes)]
		confirm_or_raise(m1,m2,m3)
		msg('Sending transaction')

	def send(self,prompt_user=True,exit_on_fail=False):

		if not self.marked_signed():
			die(1,'Transaction is not signed!')

		self.check_correct_chain(on_fail='die')

		self.check_pubkey_scripts()

		self.check_hex_tx_matches_mmgen_tx(DeserializedTX(self.hex))

		bogus_send = os.getenv('MMGEN_BOGUS_SEND')

		if self.has_segwit_outputs() and not segwit_is_active() and not bogus_send:
			m = 'Transaction has MMGen Segwit outputs, but this blockchain does not support Segwit'
			die(2,m+' at the current height')

		if self.get_fee_from_tx() > g.proto.max_tx_fee:
			die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				self.get_fee_from_tx(),g.proto.name.capitalize(),g.proto.max_tx_fee,g.coin))

		self.get_status()

		if prompt_user: self.confirm_send()

		ret = None if bogus_send else g.rpch.sendrawtransaction(self.hex,on_fail='return')

		from mmgen.rpc import rpc_error,rpc_errmsg
		if rpc_error(ret):
			errmsg = rpc_errmsg(ret)
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
			if exit_on_fail: sys.exit(1)
			return False
		else:
			if bogus_send:
				m = 'BOGUS transaction NOT sent: {}'
			else:
				assert ret == self.coin_txid, 'txid mismatch (after sending)'
				m = 'Transaction sent: {}'
			self.desc = 'sent transaction'
			msg(m.format(self.coin_txid.hl()))
			self.add_timestamp()
			self.add_blockcount()
			return True

	def write_txid_to_file(self,ask_write=False,ask_write_default_yes=True):
		fn = '{}[{}].{}'.format(self.txid,self.send_amt,self.txid_ext)
		write_data_to_file(fn,self.coin_txid+'\n','transaction ID',
			ask_write=ask_write,
			ask_write_default_yes=ask_write_default_yes)

	def create_fn(self):
		tl = self.get_hex_locktime()
		tn = ('','.testnet')[g.proto.is_testnet()]
		self.fn = u'{}{}[{!s}{}{}]{x}{}.{}'.format(
			self.txid,
			('-'+g.dcoin,'')[g.coin=='BTC'],
			self.send_amt,
			('',',{}'.format(self.fee_abs2rel(
								self.get_fee_from_tx(),to_unit=self.fn_fee_unit))
							)[self.is_replaceable()],
			('',',tl={}'.format(tl))[bool(tl)],
			tn,self.ext,
			x=u'-α' if g.debug_utf8 else '')

	def write_to_file(  self,
						add_desc='',
						ask_write=True,
						ask_write_default_yes=False,
						ask_tty=True,
						ask_overwrite=True):

		if ask_write == False: ask_write_default_yes = True
		if not self.fmt_data:  self.format()
		if not self.fn:        self.create_fn()

		write_data_to_file(self.fn,self.fmt_data,self.desc+add_desc,
			ask_overwrite=ask_overwrite,
			ask_write=ask_write,
			ask_tty=ask_tty,
			ask_write_default_yes=ask_write_default_yes)

	def view_with_prompt(self,prompt=''):
		prompt += ' (y)es, (N)o, pager (v)iew, (t)erse view'
		reply = prompt_and_get_char(prompt,'YyNnVvTt',enter_ok=True)
		if reply and reply in 'YyVvTt':
			self.view(pager=reply in 'Vv',terse=reply in 'Tt')

	def view(self,pager=False,pause=True,terse=False):
		o = self.format_view(terse=terse)
		if pager: do_pager(o)
		else:
			msg_r(o)
			from mmgen.term import get_char
			if pause:
				get_char('Press any key to continue: ')
				msg('')

# 	def is_replaceable_from_rpc(self):
# 		dec_tx = g.rpch.decoderawtransaction(self.hex)
# 		return None < dec_tx['vin'][0]['sequence'] <= g.max_int - 2

	def is_replaceable(self):
		return self.inputs[0].sequence == g.max_int - 2

	def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse):

		def format_io(desc):
			io = getattr(self,desc)
			ip = desc == 'inputs'
			out = desc.capitalize() + ':\n' + enl
			addr_w = max(len(e.addr) for e in io)
			confs_per_day = 60*60*24 / g.proto.secs_per_block
			for n,e in enumerate(sorted(io,key=lambda o: o.mmid.sort_key if o.mmid else o.addr)):
				if ip and blockcount:
					confs = e.confs + blockcount - self.blockcount
					days = int(confs / confs_per_day)
				if e.mmid:
					mmid_fmt = e.mmid.fmt(
						width=max_mmwid,
						encl='()',
						color=True,
						append_chars=('',' (chg)')[bool(not ip and e.is_chg and terse)],
						append_color='green')
				else:
					mmid_fmt = MMGenID.fmtc(nonmm_str,width=max_mmwid,color=True)
				if terse:
					out += '{:3} {} {} {} {}\n'.format(n+1,
						e.addr.fmt(color=True,width=addr_w),
						mmid_fmt,e.amt.hl(),g.dcoin)
				else:
					icommon = [
						((n+1,'')[ip],'address:',e.addr.fmt(color=True,width=addr_w) + ' '+mmid_fmt),
						('','comment:',e.label.hl() if e.label else ''),
						('','amount:','{} {}'.format(e.amt.hl(),g.dcoin))]
					items = [(n+1, 'tx,vout:','{},{}'.format(e.txid,e.vout))] + icommon + [
						('','confirmations:','{} (around {} days)'.format(confs,days) if blockcount else '')
					] if ip else icommon + [
						('','change:',green('True') if e.is_chg else '')]
					out += '\n'.join([(u'{:>3} {:<8} {}'.format(*d)) for d in items if d[2]]) + '\n\n'
			return out

		return  format_io('inputs') + format_io('outputs')

	def format_view_rel_fee(self,terse):
		return ' ({} {})\n'.format(
			pink(str(self.fee_abs2rel(self.get_fee_from_tx()))),
			self.rel_fee_disp)

	def format_view_abs_fee(self):
		return g.proto.coin_amt(self.get_fee_from_tx()).hl()

	def format_view_verbose_footer(self):
		ts = len(self.hex)/2 if self.hex else 'unknown'
		out = 'Transaction size: Vsize {} (estimated), Total {}'.format(self.estimate_size(),ts)
		if self.marked_signed():
			ws = DeserializedTX(self.hex)['witness_size']
			out += ', Base {}, Witness {}'.format(ts-ws,ws)
		return out + '\n'

	def format_view(self,terse=False):
		try:
			rpc_init()
			blockcount = self.get_blockcount()
		except:
			blockcount = None

		def get_max_mmwid(io):
			if io == self.inputs:
				sel_f = lambda o: len(o.mmid) + 2 # len('()')
			else:
				sel_f = lambda o: len(o.mmid) + (2,8)[bool(o.is_chg)] # + len(' (chg)')
			return  max(max([sel_f(o) for o in io if o.mmid] or [0]),len(nonmm_str))

		nonmm_str = '(non-{} address)'.format(g.proj_name)
		max_mmwid = max(get_max_mmwid(self.inputs),get_max_mmwid(self.outputs))

		out = (self.txview_hdr_fs,self.txview_hdr_fs_short)[bool(terse)].format(
			i=self.txid.hl(),
			a=self.send_amt.hl(),
			c=g.dcoin,
			t=self.timestamp,
			r=(red('False'),green('True'))[self.is_replaceable()],
			s=self.marked_signed(color=True),
			l=(green('None'),orange(strfmt_locktime(self.locktime,terse=True)))[bool(self.locktime)])

		if self.chain != 'mainnet':
			out += green('Chain: {}\n'.format(self.chain.upper()))
		if self.coin_txid:
			out += '{} TxID: {}\n'.format(g.coin,self.coin_txid.hl())
		enl = ('\n','')[bool(terse)]
		out += enl
		if self.label:
			out += u'Comment: {}\n{}'.format(self.label.hl(),enl)

		out += self.format_view_body(blockcount,nonmm_str,max_mmwid,enl,terse=terse)

		out += (self.txview_ftr_fs,self.txview_ftr_fs_short)[bool(terse)].format(
			i=self.sum_inputs().hl(),
			o=self.sum_outputs().hl(),
			a=self.format_view_abs_fee(),
			r=self.format_view_rel_fee(terse),
			d=g.dcoin,c=g.coin)

		if opt.verbose: out += self.format_view_verbose_footer()

		return out # TX label might contain non-ascii chars

	def check_txfile_hex_data(self):
		self.hex = HexStr(self.hex,on_fail='raise')

	def parse_tx_file(self,infile,metadata_only=False,silent_open=False):

		def eval_io_data(raw_data,desc):
			from ast import literal_eval
			try:
				d = literal_eval(raw_data)
			except:
				if desc == 'inputs' and not silent_open:
					ymsg('Warning: transaction data appears to be in old format')
				import re
				d = literal_eval(re.sub(r"[A-Za-z]+?\(('.+?')\)",r'\1',raw_data))
			assert type(d) == list,'{} data not a list!'.format(desc)
			if not (desc == 'outputs' and g.proto.base_coin == 'ETH'): # ETH txs can have no outputs
				assert len(d),'no {}!'.format(desc)
			for e in d: e['amt'] = g.proto.coin_amt(e['amt'])
			io,io_list = (
				(MMGenTX.MMGenTxOutput,MMGenTX.MMGenTxOutputList),
				(MMGenTX.MMGenTxInput,MMGenTX.MMGenTxInputList)
			)[desc=='inputs']
			return io_list([io(**e) for e in d])

		tx_data = get_data_from_file(infile,self.desc+' data',silent=silent_open)

		try:
			desc = 'data'
			assert len(tx_data) <= g.max_tx_file_size,(
				'Transaction file size exceeds limit ({} bytes)'.format(g.max_tx_file_size))
			tx_data = tx_data.decode('ascii').splitlines()
			assert len(tx_data) >= 5,'number of lines less than 5'
			assert len(tx_data[0]) == 6,'invalid length of first line'
			self.chksum = HexStr(tx_data.pop(0),on_fail='raise')
			assert self.chksum == make_chksum_6(' '.join(tx_data)),'file data does not match checksum'

			if len(tx_data) == 6:
				assert len(tx_data[-1]) == 64,'invalid coin TxID length'
				desc = '{} TxID'.format(g.proto.name.capitalize())
				self.coin_txid = CoinTxID(tx_data.pop(-1),on_fail='raise')

			if len(tx_data) == 5:
				# rough check: allow for 4-byte utf8 characters + base58 (4 * 11 / 8 = 6 (rounded up))
				assert len(tx_data[-1]) < MMGenTXLabel.max_len*6,'invalid comment length'
				c = tx_data.pop(-1)
				if c != '-':
					desc = 'encoded comment (not base58)'
					comment = baseconv.b58decode(c).decode('utf8')
					assert comment != False,'invalid comment'
					desc = 'comment'
					self.label = MMGenTXLabel(comment,on_fail='raise')

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

			if metadata_only: return

			desc = 'send amount in metadata'
			self.send_amt = g.proto.coin_amt(send_amt,on_fail='raise')

			desc = 'transaction hex data'
			self.check_txfile_hex_data()
			# the following ops will all fail if g.coin doesn't match self.coin
			desc = 'coin type in metadata'
			assert self.coin == g.coin,self.coin
			desc = 'inputs data'
			self.inputs  = eval_io_data(inputs_data,'inputs')
			desc = 'outputs data'
			self.outputs = eval_io_data(outputs_data,'outputs')
		except Exception as e:
			die(2,'Invalid {} in transaction file: {}'.format(desc,e.message))

		# test doesn't work for Ethereum: test and mainnet addrs have same format
		if not self.chain and not self.inputs[0].addr.is_for_chain('testnet'):
			self.chain = 'mainnet'

		if self.dcoin: self.set_g_token()

	def process_cmd_arg(self,arg,ad_f,ad_w):

		def add_output_chk(addr,amt,err_desc):
			if not amt and self.get_chg_output_idx() != None:
				die(2,'ERROR: More than one change address listed on command line')
			if is_mmgen_id(addr) or is_coin_addr(addr):
				coin_addr = mmaddr2coinaddr(addr,ad_w,ad_f) if is_mmgen_id(addr) else CoinAddr(addr)
				self.add_output(coin_addr,g.proto.coin_amt(amt or '0'),is_chg=not amt)
			else:
				die(2,"{}: invalid {} '{}'".format(addr,err_desc,','.join((addr,amt)) if amt else addr))

		if ',' in arg:
			addr,amt = arg.split(',',1)
			add_output_chk(addr,amt,'coin argument in command-line argument')
		else:
			add_output_chk(arg,None,'command-line argument')

	def process_cmd_args(self,cmd_args,ad_f,ad_w):

		for a in cmd_args: self.process_cmd_arg(a,ad_f,ad_w)

		if self.get_chg_output_idx() == None:
			die(2,( 'ERROR: No change output specified',
					self.msg_no_change_output.format(g.dcoin))[len(self.outputs) == 1])

		if not segwit_is_active() and self.has_segwit_outputs():
			fs = '{} Segwit address requested on the command line, but Segwit is not active on this chain'
			rdie(2,fs.format(g.proj_name))

		if not self.outputs:
			die(2,'At least one output must be specified on the command line')

	def get_outputs_from_cmdline(self,cmd_args):
		from mmgen.addr import AddrList,AddrData
		addrfiles = [a for a in cmd_args if get_extension(a) == AddrList.ext]
		cmd_args = set(cmd_args) - set(addrfiles)

		ad_f = AddrData()
		for a in addrfiles:
			check_infile(a)
			ad_f.add(AddrList(a))

		ad_w = AddrData(source='tw')

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

	def check_sufficient_funds(self,inputs_sum,foo):
		if self.send_amt > inputs_sum:
			msg(self.msg_low_coin.format(self.send_amt-inputs_sum,g.coin))
			return False
		return True

	def get_change_amt(self):
		return self.sum_inputs() - self.send_amt - self.fee

	def warn_insufficient_chg(self,change_amt):
		msg(self.msg_low_coin.format(g.proto.coin_amt(-change_amt).hl(),g.coin))

	def final_inputs_ok_msg(self,change_amt):
		m = 'Transaction produces {} {} in change'
		return m.format(g.proto.coin_amt(change_amt).hl(),g.coin)

	def select_unspent_cmdline(self,unspent):
		sel_nums = []
		for i in opt.inputs.split(','):
			ls = len(sel_nums)
			if is_mmgen_id(i):
				for j in range(len(unspent)):
					if unspent[j].twmmid == i:
						sel_nums.append(j+1)
			elif is_coin_addr(i):
				for j in range(len(unspent)):
					if unspent[j].addr == i:
						sel_nums.append(j+1)
			else:
				die(1,"'{}': not an MMGen ID or coin address".format(i))

			ldiff = len(sel_nums) - ls
			if ldiff:
				sel_inputs = ','.join([str(i) for i in sel_nums[-ldiff:]])
				ul = unspent[sel_nums[-1]-1]
				mmid_disp = ' (' + ul.twmmid + ')' if ul.twmmid.type == 'mmgen' else ''
				msg('Adding input{}: {} {}{}'.format(suf(ldiff),sel_inputs,ul.addr,mmid_disp))
			else:
				die(1,"'{}': address not found in tracking wallet".format(i))

		return set(sel_nums) # silently discard duplicates

	def get_inputs_from_user(self,tw):

		while True:
			us_f = ('select_unspent','select_unspent_cmdline')[bool(opt.inputs)]
			sel_nums = getattr(self,us_f)(tw.unspent)

			msg('Selected output{}: {}'.format(suf(sel_nums,'s'),' '.join(map(str,sel_nums))))
			sel_unspent = tw.MMGenTwOutputList([tw.unspent[i-1] for i in sel_nums])

			inputs_sum = sum(s.amt for s in sel_unspent)
			if not self.check_sufficient_funds(inputs_sum,sel_unspent):
				continue

			non_mmaddrs = [i for i in sel_unspent if i.twmmid.type == 'non-mmgen']
			if non_mmaddrs and self.caller != 'txdo':
				msg(self.msg_non_mmgen_inputs.format(
					', '.join(set(sorted([a.addr.hl() for a in non_mmaddrs])))))
				if not (opt.yes or keypress_confirm('Accept?')):
					continue

			self.copy_inputs_from_tw(sel_unspent)  # makes self.inputs

			self.fee = self.get_fee_from_user()

			change_amt = self.get_change_amt()

			if change_amt >= 0: # TODO: show both ETH and token amts remaining
				p = self.final_inputs_ok_msg(change_amt)
				if opt.yes or keypress_confirm(p+'. OK?',default_yes=True):
					if opt.yes: msg(p)
					return change_amt
			else:
				self.warn_insufficient_chg(change_amt)

	def check_fee(self):
		assert self.sum_inputs() - self.sum_outputs() <= g.proto.max_tx_fee

	def update_send_amt(self,change_amt):
		if not self.send_amt:
			self.send_amt = change_amt

	def create(self,cmd_args,locktime,do_info=False):
		assert type(locktime) == int

		if opt.comment_file: self.add_comment(opt.comment_file)

		if not do_info: self.get_outputs_from_cmdline(cmd_args)

		do_license_msg()

		from mmgen.tw import TwUnspentOutputs
		tw = TwUnspentOutputs(minconf=opt.minconf)

		if not opt.inputs:
			tw.view_and_sort(self)

		tw.display_total()

		if do_info: sys.exit(0)

		self.send_amt = self.sum_outputs()

		msg('Total amount to spend: {}'.format(
			('Unknown','{} {}'.format(self.send_amt.hl(),g.dcoin))[bool(self.send_amt)]
		))

		change_amt = self.get_inputs_from_user(tw)

		# only after we have inputs
		if opt.rbf:  self.inputs[0].sequence = g.max_int - 2 # handles the locktime case too
		elif locktime: self.inputs[0].sequence = g.max_int - 1

		self.update_change_output(change_amt)
		self.update_send_amt(change_amt)

		if not opt.yes:
			self.add_comment()  # edits an existing comment
		self.create_raw()       # creates self.hex, self.txid

		if locktime:
			msg('Setting nlocktime to {}!'.format(strfmt_locktime(locktime)))
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

class MMGenBumpTX(MMGenTX):

	def __new__(cls,*args,**kwargs):
		return MMGenTX.__new__(altcoin_subclass(cls,'tx','MMGenBumpTX'),*args,**kwargs)

	min_fee = None
	bump_output_idx = None

	def __init__(self,filename,send=False):

		super(MMGenBumpTX,self).__init__(filename)

		if not self.is_replaceable():
			die(1,"Transaction '{}' is not replaceable".format(self.txid))

		# If sending, require tx to have been signed
		if send:
			if not self.marked_signed():
				die(1,"File '{}' is not a signed {} transaction file".format(filename,g.proj_name))
			if not self.coin_txid:
				die(1,"Transaction '{}' was not broadcast to the network".format(self.txid))

		self.coin_txid = ''
		self.mark_raw()

	def check_bumpable(self):
		if not [o.amt for o in self.outputs if o.amt >= self.min_fee]:
			die(1,'Transaction cannot be bumped.' +
			'\nAll outputs have less than the minimum fee ({} {})'.format(self.min_fee,g.coin))

	def choose_output(self):
		chg_idx = self.get_chg_output_idx()
		init_reply = opt.output_to_reduce
		while True:
			if init_reply == None:
				m = 'Choose an output to deduct the fee from (Hit ENTER for the change output): '
				reply = my_raw_input(m) or 'c'
			else:
				reply,init_reply = init_reply,None
			if chg_idx == None and not is_int(reply):
				msg("Output must be an integer")
			elif chg_idx != None and not is_int(reply) and reply != 'c':
				msg("Output must be an integer, or 'c' for the change output")
			else:
				idx = chg_idx if reply == 'c' else (int(reply) - 1)
				if idx < 0 or idx >= len(self.outputs):
					msg('Output must be in the range 1-{}'.format(len(self.outputs)))
				else:
					o_amt = self.outputs[idx].amt
					cs = ('',' (change output)')[chg_idx == idx]
					p = 'Fee will be deducted from output {}{} ({} {})'.format(idx+1,cs,o_amt,g.coin)
					if o_amt < self.min_fee:
						msg('Minimum fee ({} {c}) is greater than output amount ({} {c})'.format(
							self.min_fee,o_amt,c=g.coin))
					elif opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
						if opt.yes: msg(p)
						self.bump_output_idx = idx
						return idx

	def set_min_fee(self):
		self.min_fee = self.sum_inputs() - self.sum_outputs() + self.get_relay_fee()

	def update_fee(self,op_idx,fee):
		self.update_output_amt(op_idx,self.sum_inputs()-self.sum_outputs(exclude=op_idx)-fee)

	def convert_and_check_fee(self,tx_fee,desc):
		ret = super(MMGenBumpTX,self).convert_and_check_fee(tx_fee,desc)
		if ret < self.min_fee:
			msg('{} {c}: {} fee too small. Minimum fee: {} {c} ({} {})'.format(
				ret,desc,self.min_fee,self.fee_abs2rel(self.min_fee.hl()),self.rel_fee_desc,c=g.coin))
			return False
		output_amt = self.outputs[self.bump_output_idx].amt
		if ret >= output_amt:
			msg('{} {c}: {} fee too large. Maximum fee: <{} {c}'.format(ret.hl(),desc,output_amt.hl(),c=g.coin))
			return False
		return ret

class MMGenSplitTX(MMGenTX):

	def get_outputs_from_cmdline(self,mmid): # TODO: check that addr is empty

		from mmgen.addr import AddrData
		ad_w = AddrData(source='tw')

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
		try:
			rpc_init(reinit=True)
		except:
			ymsg('Connect to {} daemon failed.  Network fee estimation unavailable'.format(g.coin))
			return self.get_usr_fee_interactive(opt.tx_fee,'User-selected')
		return super(type(self),self).get_fee_from_user()

	def create_split(self,mmid):

		self.outputs = self.MMGenTxOutputList()
		self.get_outputs_from_cmdline(mmid)

		while True:
			change_amt = self.sum_inputs() - self.get_split_fee_from_user()
			if change_amt >= 0:
				p = 'Transaction produces {} {} in change'.format(change_amt.hl(),g.coin)
				if opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
					if opt.yes: msg(p)
					break
			else:
				self.warn_insufficient_chg(change_amt)

		self.update_output_amt(0,change_amt)
		self.send_amt = change_amt

		if not opt.yes:
			self.add_comment()  # edits an existing comment
		self.create_raw()       # creates self.hex, self.txid

		self.add_timestamp()
		self.add_blockcount() # TODO
		self.chain = g.chain

		assert self.sum_inputs() - self.sum_outputs() <= g.proto.max_tx_fee

		qmsg('Transaction successfully created')

		if not opt.yes:
			self.view_with_prompt('View decoded transaction?')
