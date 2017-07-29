#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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

import sys,os
from stat import *
from binascii import unhexlify
from mmgen.common import *
from mmgen.obj import *

def is_mmgen_seed_id(s): return SeedID(sid=s,on_fail='silent')
def is_mmgen_idx(s):     return AddrIdx(s,on_fail='silent')
def is_mmgen_id(s):      return MMGenID(s,on_fail='silent')
def is_btc_addr(s):      return BTCAddr(s,on_fail='silent')
def is_addrlist_id(s):   return AddrListID(s,on_fail='silent')
def is_tw_label(s):      return TwLabel(s,on_fail='silent')

def is_wif(s):
	if s == '': return False
	from mmgen.bitcoin import wif2hex
	return bool(wif2hex(s))

def segwit_is_active(exit_on_error=False):
	d = bitcoin_connection().getblockchaininfo()
	if d['chain'] == 'regtest' or d['bip9_softforks']['segwit']['status'] == 'active':
		return True
	if g.skip_segwit_active_check: return True
	if exit_on_error:
		die(2,'Segwit not active on this chain.  Exiting')
	else:
		return False

def bytes2int(hex_bytes):
	r = hexlify(unhexlify(hex_bytes)[::-1])
	if r[0] in '89abcdef':
		die(3,"{}: Negative values not permitted in transaction!".format(hex_bytes))
	return int(r,16)

def bytes2btc(hex_bytes):
	return bytes2int(hex_bytes) * g.satoshi

from collections import OrderedDict
class DeserializedTX(OrderedDict,MMGenObject): # need to add MMGen types
	def __init__(self,txhex):
		tx = list(unhexlify(txhex))
		tx_copy = tx[:]

		def hshift(l,n,reverse=False):
			ret = l[:n]
			del l[:n]
			return hexlify(''.join(ret[::-1] if reverse else ret))

		# https://bitcoin.org/en/developer-reference#compactsize-unsigned-integers
		# For example, the number 515 is encoded as 0xfd0302.
		def readVInt(l):
			s = int(hexlify(l[0]),16)
			bytes_len = 1 if s < 0xfd else 2 if s == 0xfd else 4 if s == 0xfe else 8
			if bytes_len != 1: del l[0]
			ret = int(hexlify(''.join(l[:bytes_len][::-1])),16)
			del l[:bytes_len]
			return ret

		d = { 'version': bytes2int(hshift(tx,4)) }
		has_witness = (False,True)[hexlify(tx[0])=='00']
		if has_witness:
			u = hshift(tx,2)[2:]
			if u != '01':
				die(2,"'{}': Illegal value for flag in transaction!".format(u))
			del tx_copy[-len(tx)-2:-len(tx)]

		d['num_txins'] = readVInt(tx)
		d['txins'] = MMGenList([OrderedDict((
			('txid',      hshift(tx,32,reverse=True)),
			('vout',      bytes2int(hshift(tx,4))),
			('scriptSig', hshift(tx,readVInt(tx))),
			('nSeq',      hshift(tx,4,reverse=True))
		)) for i in range(d['num_txins'])])

		d['num_txouts'] = readVInt(tx)
		d['txouts'] = MMGenList([OrderedDict((
			('amount',       bytes2btc(hshift(tx,8))),
			('scriptPubKey', hshift(tx,readVInt(tx)))
		)) for i in range(d['num_txouts'])])

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
					hshift(wd,1)
					continue
				d['txins'][i]['witness'] = [hshift(wd,readVInt(wd)) for item in range(readVInt(wd))]
			if wd:
				die(3,'More witness data than inputs with witnesses!')

		d['lock_time'] = bytes2int(hshift(tx,4))
		d['txid'] = hexlify(sha256(sha256(''.join(tx_copy)).digest()).digest()[::-1])

		keys = 'txid','version','lock_time','witness_size','num_txins','txins','num_txouts','txouts'
		return OrderedDict.__init__(self, ((k,d[k]) for k in keys))

class MMGenTX(MMGenObject):
	ext      = 'rawtx'
	raw_ext  = 'rawtx'
	sig_ext  = 'sigtx'
	txid_ext = 'txid'
	desc = 'transaction'

	class MMGenTxInput(MMGenListItem):
		attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','have_wif','sequence'
		txid = MMGenListItemAttr('txid','BitcoinTxID')
		scriptPubKey = MMGenListItemAttr('scriptPubKey','HexStr')

	class MMGenTxOutput(MMGenListItem):
		attrs = 'txid','vout','amt','label','mmid','addr','have_wif','is_chg'

	class MMGenTxInputOldFmt(MMGenListItem):  # for converting old tx files only
		tr = {'amount':'amt', 'address':'addr', 'confirmations':'confs','comment':'label'}
		attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','wif'
		attrs_priv = 'tr',

	class MMGenTxInputList(list,MMGenObject): pass
	class MMGenTxOutputList(list,MMGenObject): pass

	def __init__(self,filename=None):
		self.inputs      = self.MMGenTxInputList()
		self.outputs     = self.MMGenTxOutputList()
		self.send_amt    = BTCAmt('0')  # total amt minus change
		self.hex         = ''           # raw serialized hex transaction
		self.label       = MMGenTXLabel('')
		self.txid        = ''
		self.btc_txid    = ''
		self.timestamp   = ''
		self.chksum      = ''
		self.fmt_data    = ''
		self.blockcount  = 0
		self.chain       = None

		if filename:
			self.parse_tx_file(filename)
			self.check_sigs() # marks the tx as signed

		# repeat with sign and send, because bitcoind could be restarted
		self.die_if_incorrect_chain()

	def die_if_incorrect_chain(self):
		if self.chain and g.chain and self.chain != g.chain:
			die(2,'Transaction is for {}, but current chain is {}!'.format(self.chain,g.chain))

	def add_output(self,btcaddr,amt,is_chg=None):
		self.outputs.append(self.MMGenTxOutput(addr=btcaddr,amt=amt,is_chg=is_chg))

	def get_chg_output_idx(self):
		for i in range(len(self.outputs)):
			if self.outputs[i].is_chg == True:
				return i
		return None

	def update_output_amt(self,idx,amt):
		o = self.outputs[idx].__dict__
		o['amt'] = amt
		self.outputs[idx] = self.MMGenTxOutput(**o)

	def del_output(self,idx):
		self.outputs.pop(idx)

	def sum_outputs(self,exclude=None):
		olist = self.outputs if exclude == None else \
			self.outputs[:exclude] + self.outputs[exclude+1:]
		return BTCAmt(sum(e.amt for e in olist))

	def add_mmaddrs_to_outputs(self,ad_w,ad_f):
		a = [e.addr for e in self.outputs]
		d = ad_w.make_reverse_dict(a)
		d.update(ad_f.make_reverse_dict(a))
		for e in self.outputs:
			if e.addr and e.addr in d:
				e.mmid,f = d[e.addr]
				if f: e.label = f

#	def encode_io(self,desc):
# 		tr = getattr((self.MMGenTxOutput,self.MMGenTxInput)[desc=='inputs'],'tr')
# 		tr_rev = dict([(v,k) for k,v in tr.items()])
# 		return [dict([(tr_rev[e] if e in tr_rev else e,getattr(d,e)) for e in d.__dict__])
# 					for d in getattr(self,desc)]
#
	def create_raw(self,c):
		i = [{'txid':e.txid,'vout':e.vout} for e in self.inputs]
		if self.inputs[0].sequence:
			i[0]['sequence'] = self.inputs[0].sequence
		o = dict([(e.addr,e.amt) for e in self.outputs])
		self.hex = c.createrawtransaction(i,o)
		self.txid = MMGenTxID(make_chksum_6(unhexlify(self.hex)).upper())

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

	def has_segwit_inputs(self):
		return any(i.mmid and i.mmid.mmtype == 'S' for i in self.inputs)

	# https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
	# 180: uncompressed, 148: compressed
	def estimate_size_old(self):
		if not self.inputs or not self.outputs: return None
		return len(self.inputs)*180 + len(self.outputs)*34 + 10

	# https://bitcoincore.org/en/segwit_wallet_dev/
	# vsize: 3 times of the size with original serialization, plus the size with new
	# serialization, divide the result by 4 and round up to the next integer.

	# TODO: results differ slightly from actual transaction size
	def estimate_vsize(self):
		if not self.inputs or not self.outputs: return None

		sig_size = 72 # sig in DER format
		pubkey_size = { 'compressed':33, 'uncompressed':65 }
		outpoint_size = 36 # txid + vout

		def get_inputs_size():
			segwit_isize = outpoint_size + 1 + 23 + 4 # (txid,vout) [scriptSig size] scriptSig nSeq # = 64
			# txid vout [scriptSig size] scriptSig (<sig> <pubkey>) nSeq
			legacy_isize = outpoint_size + 1 + 2 + sig_size + pubkey_size['uncompressed'] + 4 # = 180
			compressed_isize = outpoint_size + 1 + 2 + sig_size + pubkey_size['compressed'] + 4 # = 148
			ret = sum((legacy_isize,segwit_isize)[i.mmid.mmtype=='S'] for i in self.inputs if i.mmid)
			# assume all non-MMGen pubkeys are compressed (we have no way of knowing
			# until we see the key).  TODO: add user option to specify this?
			return ret + sum(compressed_isize for i in self.inputs if not i.mmid)

		def get_outputs_size():
			return sum((34,32)[o.addr.addr_fmt=='p2sh'] for o in self.outputs)

		# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
		# The witness is a serialization of all witness data of the transaction. Each txin is
		# associated with a witness field. A witness field starts with a var_int to indicate the
		# number of stack items for the txin. It is followed by stack items, with each item starts
		# with a var_int to indicate the length. Witness data is NOT script.

		# A non-witness program txin MUST be associated with an empty witness field, represented
		# by a 0x00. If all txins are not witness program, a transaction's wtxid is equal to its txid.
		def get_witness_size():
			if not self.has_segwit_inputs(): return 0
			wf_size = 1 + 1 + sig_size + 1 + pubkey_size['compressed'] # vInt vInt sig vInt pubkey = 108
			return sum((1,wf_size)[bool(i.mmid) and i.mmid.mmtype=='S'] for i in self.inputs)

		isize = get_inputs_size()
		osize = get_outputs_size()
		wsize = get_witness_size()
#  		pmsg([i.mmid and i.mmid.mmtype == 'S' for i in self.inputs])
#  		pmsg([i.mmid for i in self.inputs])
#  		pmsg([i.mmid for i in self.outputs])
#  		pmsg('isize',isize)
#  		pmsg('osize',osize)
#  		pmsg('wsize',wsize)

		# TODO: compute real varInt sizes instead of assuming 1 byte
		# old serialization: [nVersion]              [vInt][txins][vInt][txouts]         [nLockTime]
		old_size =           4                     + 1   + isize + 1  + osize          + 4
		# new serialization: [nVersion][marker][flag][vInt][txins][vInt][txouts][witness][nLockTime]
		new_size =           4       + 1     + 1   + 1   + isize + 1  + osize + wsize  + 4 \
				if wsize else old_size

		ret = (old_size * 3 + new_size) / 4
# 		pmsg('old_size',old_size) # This should be equal to the size of serialized signed tx
# 		pmsg('ret',ret)
# 		pmsg('estimate_size_old',self.estimate_size_old())
		return ret

	estimate_size = estimate_vsize

	def get_fee(self):
		return self.sum_inputs() - self.sum_outputs()

	def btc2spb(self,btc_fee):
		return int(btc_fee/g.satoshi/self.estimate_size())

	def get_relay_fee(self):
		assert self.estimate_size()
		kb_fee = BTCAmt(bitcoin_connection().getnetworkinfo()['relayfee'])
		vmsg('Relay fee: {} BTC/kB'.format(kb_fee))
		return kb_fee * self.estimate_size() / 1024

	def convert_fee_spec(self,tx_fee,tx_size,on_fail='throw'):
		if BTCAmt(tx_fee,on_fail='silent'):
			return BTCAmt(tx_fee)
		elif len(tx_fee) >= 2 and tx_fee[-1] == 's' and is_int(tx_fee[:-1]) and int(tx_fee[:-1]) >= 1:
			if tx_size:
				return BTCAmt(int(tx_fee[:-1]) * tx_size * g.satoshi)
			else:
				return None
		else:
			if on_fail == 'return':
				return False
			elif on_fail == 'throw':
				assert False, "'{}': invalid tx-fee argument".format(tx_fee)

	def get_usr_fee(self,tx_fee,desc='Missing description'):
		btc_fee = self.convert_fee_spec(tx_fee,self.estimate_size(),on_fail='return')
		if btc_fee == None:
			msg("'{}': cannot convert satoshis-per-byte to BTC because transaction size is unknown".format(tx_fee))
			assert False  # because we shouldn't be calling this if tx size is unknown
		elif btc_fee == False:
			msg("'{}': invalid TX fee (not a BTC amount or satoshis-per-byte specification)".format(tx_fee))
			return False
		elif btc_fee > g.max_tx_fee:
			msg('{} BTC: {} fee too large (maximum fee: {} BTC)'.format(btc_fee,desc,g.max_tx_fee))
			return False
		elif btc_fee < self.get_relay_fee():
			msg('{} BTC: {} fee too small (below relay fee of {} BTC)'.format(str(btc_fee),desc,str(self.get_relay_fee())))
			return False
		else:
			return btc_fee

	def get_usr_fee_interactive(self,tx_fee=None,desc='Starting'):
		btc_fee = None
		while True:
			if tx_fee:
				btc_fee = self.get_usr_fee(tx_fee,desc)
			if btc_fee:
				m = ('',' (after {}x adjustment)'.format(opt.tx_fee_adj))[opt.tx_fee_adj != 1]
				p = '{} TX fee{}: {} BTC ({} satoshis per byte)'.format(desc,m,
					btc_fee.hl(),pink(str(self.btc2spb(btc_fee))))
				if opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
					if opt.yes: msg(p)
					return btc_fee
			tx_fee = my_raw_input('Enter transaction fee: ')
			desc = 'User-selected'

	# inputs methods
	def list_wifs(self,desc,mmaddrs_only=False):
		return [e.wif for e in getattr(self,desc) if e.mmid] if mmaddrs_only \
			else [e.wif for e in getattr(self,desc)]

	def delete_attrs(self,desc,attr):
		for e in getattr(self,desc):
			if hasattr(e,attr): delattr(e,attr)

	def decode_io(self,desc,data):
		io,il = (
			(self.MMGenTxOutput,self.MMGenTxOutputList),
			(self.MMGenTxInput,self.MMGenTxInputList)
		)[desc=='inputs']
		return il([io(**dict([(k,d[k]) for k in io.attrs
					if k in d and d[k] not in ('',None)])) for d in data])

	def decode_io_oldfmt(self,data):
		io = self.MMGenTxInputOldFmt
		tr_rev = dict([(v,k) for k,v in io.tr.items()])
		copy_keys = [tr_rev[k] if k in tr_rev else k for k in io.attrs]
		return [io(**dict([(io.tr[k] if k in io.tr else k,d[k])
					for k in copy_keys if k in d and d[k] != ''])) for d in data]

	def copy_inputs_from_tw(self,tw_unspent_data):
		txi,self.inputs = self.MMGenTxInput,self.MMGenTxInputList()
		for d in tw_unspent_data:
			t = txi(**dict([(attr,getattr(d,attr)) for attr in d.__dict__ if attr in txi.attrs]))
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

	def add_blockcount(self,c):
		self.blockcount = int(c.getblockcount())

	def format(self):
		from mmgen.bitcoin import b58encode
		lines = [
			'{} {} {} {} {}'.format(
				self.chain.upper() if self.chain else 'Unknown',
				self.txid,
				self.send_amt,
				self.timestamp,
				self.blockcount
			),
			self.hex,
			repr([e.__dict__ for e in self.inputs]),
			repr([e.__dict__ for e in self.outputs])
		]
		if self.label:
			lines.append(b58encode(self.label.encode('utf8')))
		if self.btc_txid:
			if not self.label: lines.append('-') # keep old tx files backwards compatible
			lines.append(self.btc_txid)
		self.chksum = make_chksum_6(' '.join(lines))
		self.fmt_data = '\n'.join([self.chksum] + lines)+'\n'

	def get_non_mmaddrs(self,desc):
		return list(set(i.addr for i in getattr(self,desc) if not i.mmid))

	# return true or false, don't exit
	def sign(self,c,tx_num_str,keys):

		self.die_if_incorrect_chain()

		if not keys:
			msg('No keys. Cannot sign!')
			return False

		qmsg('Passing %s key%s to bitcoind' % (len(keys),suf(keys,'s')))

		sig_data = []
		for d in self.inputs:
			e = dict([(k,getattr(d,k)) for k in ('txid','vout','scriptPubKey','amt')])
			e['amount'] = e['amt']
			del e['amt']
			wif = keys[d.addr]
			if d.mmid and d.mmid.mmtype == 'S':
				from mmgen.bitcoin import pubhex2redeem_script
				from mmgen.addr import keygen_wif2pubhex,keygen_selector
				pubhex = keygen_wif2pubhex(wif,keygen_selector())
				e['redeemScript'] = pubhex2redeem_script(pubhex)
			sig_data.append(e)

		from mmgen.bitcoin import hash256
		msg_r('Signing transaction{}...'.format(tx_num_str))
		# sighashtype defaults to 'ALL'
		sig_tx = c.signrawtransaction(self.hex,sig_data,keys.values())

		if sig_tx['complete']:
			self.hex = sig_tx['hex']
			vmsg('Signed transaction size: {}'.format(len(self.hex)/2))
			dt = DeserializedTX(self.hex)
			txid = dt['txid']
			self.check_sigs(dt)
			assert txid == c.decoderawtransaction(self.hex)['txid'], 'txid mismatch (after signing)'
			self.btc_txid = BitcoinTxID(txid,on_fail='return')
			msg('OK')
			return True
		else:
			msg('failed\nBitcoind returned the following errors:')
			msg(repr(sig_tx['errors']))
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

	def check_sigs(self,deserial_tx=None): # return False if no sigs, die on error
		txins = (deserial_tx or DeserializedTX(self.hex))['txins']
		has_ss = any(ti['scriptSig'] for ti in txins)
		has_witness = any('witness' in ti and ti['witness'] for ti in txins)
		if not (has_ss or has_witness):
			return False
		for ti in txins:
			if ti['scriptSig'][:6] == '160014' and len(ti['scriptSig']) == 46: # P2SH-P2WPKH
				assert 'witness' in ti, 'missing witness'
				assert type(ti['witness']) == list and len(ti['witness']) == 2, 'malformed witness'
				assert len(ti['witness'][1]) == 66, 'incorrect witness pubkey length'
			elif ti['scriptSig'] == '': # native P2WPKH
				die(3,('TX has missing signature','Native P2WPKH not implemented')['witness' in ti])
			else: # non-witness
				assert not 'witness' in ti, 'non-witness input has witness'
				# sig_size 72 (DER format), pubkey_size 'compressed':33, 'uncompressed':65
				assert (200 < len(ti['scriptSig']) < 300), 'malformed scriptSig' # VERY rough check
		self.mark_signed()
		return True

	def has_segwit_outputs(self):
		return any(o.mmid and o.mmid.mmtype == 'S' for o in self.outputs)

	def is_in_mempool(self,c):
		return 'size' in c.getmempoolentry(self.btc_txid,on_fail='silent')

	def is_in_wallet(self,c):
		ret = c.gettransaction(self.btc_txid,on_fail='silent')
		return 'confirmations' in ret and ret['confirmations'] > 0

	def is_replaced(self,c):
		if self.is_in_mempool(c): return False
		ret = c.gettransaction(self.btc_txid,on_fail='silent')
		if not 'bip125-replaceable' in ret or not 'confirmations' in ret or ret['confirmations'] > 0:
			return False
		return -ret['confirmations'] + 1 # 1: replacement in mempool, 2: replacement confirmed

	def is_in_utxos(self,c):
		return 'txid' in c.getrawtransaction(self.btc_txid,True,on_fail='silent')

	def send(self,c,prompt_user=True):

		self.die_if_incorrect_chain()

		bogus_send = os.getenv('MMGEN_BOGUS_SEND')

		if self.has_segwit_outputs() and not segwit_is_active() and not bogus_send:
			m = 'Transaction has MMGen Segwit outputs, but this blockchain does not support Segwit'
			die(2,m+' at the current height')

		if self.get_fee() > g.max_tx_fee:
			die(2,'Transaction fee ({}) greater than max_tx_fee ({})!'.format(self.get_fee(),g.max_tx_fee))

		if self.is_in_mempool(c):
			msg('Warning: transaction is in mempool!')
		elif self.is_in_wallet(c):
			die(1,'Transaction has been confirmed!')
		elif self.is_in_utxos(c):
			die(2,red('ERROR: transaction is in the blockchain (but not in the tracking wallet)!'))

		ret = self.is_replaced(c) # 1: replacement in mempool, 2: replacement confirmed
		if ret:
			die(1,'Transaction has been replaced'+('',', and the replacement TX is confirmed')[ret==2]+'!')

		if prompt_user:
			m1 = ("Once this transaction is sent, there's no taking it back!",'')[bool(opt.quiet)]
			m2 = 'broadcast this transaction to the {} network'.format(g.chain.upper())
			m3 = ('YES, I REALLY WANT TO DO THIS','YES')[bool(opt.quiet or opt.yes)]
			confirm_or_exit(m1,m2,m3)

		msg('Sending transaction')
		if bogus_send:
			ret = 'deadbeef' * 8
			m = 'BOGUS transaction NOT sent: %s'
		else:
			ret = c.sendrawtransaction(self.hex) # exits on failure
			m = 'Transaction sent: %s'

		if ret:
			if not bogus_send:
				assert ret == self.btc_txid, 'txid mismatch (after sending)'
			self.desc = 'sent transaction'
			msg(m % self.btc_txid.hl())
			self.add_timestamp()
			self.add_blockcount(c)
			return True

		# rpc call exits on failure, so we won't get here
		msg('Sending of transaction {} failed'.format(self.txid))
		return False

	def write_txid_to_file(self,ask_write=False,ask_write_default_yes=True):
		fn = '%s[%s].%s' % (self.txid,self.send_amt,self.txid_ext)
		write_data_to_file(fn,self.btc_txid+'\n','transaction ID',
			ask_write=ask_write,
			ask_write_default_yes=ask_write_default_yes)

	def write_to_file(self,add_desc='',ask_write=True,ask_write_default_yes=False,ask_tty=True,ask_overwrite=True):
		if ask_write == False:
			ask_write_default_yes=True
		self.format()
		spbs = ('',',{}'.format(self.btc2spb(self.get_fee())))[self.is_rbf()]
		fn = '{}[{}{}].{}'.format(self.txid,self.send_amt,spbs,self.ext)
		write_data_to_file(fn,self.fmt_data,self.desc+add_desc,
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
		o = self.format_view(terse=terse).encode('utf8')
		if pager: do_pager(o)
		else:
			Msg_r(o)
			from mmgen.term import get_char
			if pause:
				get_char('Press any key to continue: ')
				msg('')

# 	def is_rbf_fromhex(self,color=False):
# 		try:
# 			dec_tx = bitcoin_connection().decoderawtransaction(self.hex)
# 		except:
# 			return yellow('Unknown') if color else None
# 		rbf = bool(dec_tx['vin'][0]['sequence'] == g.max_int - 2)
# 		return (red,green)[rbf](str(rbf)) if color else rbf

	def is_rbf(self,color=False):
		ret = None < self.inputs[0].sequence <= g.max_int - 2
		return (red,green)[ret](str(ret)) if color else ret

	def signal_for_rbf(self):
		self.inputs[0].sequence = g.max_int - 2

	def format_view(self,terse=False):
#		self.pdie()
		try:
			blockcount = bitcoin_connection().getblockcount()
		except:
			blockcount = None

		hdr_fs = (
			'TRANSACTION DATA\n\nHeader: [ID:{}] [{} BTC] [{} UTC] [RBF:{}] [Signed:{}]\n',
			'Transaction {} {} BTC ({} UTC) RBF={} Signed={}\n'
		)[bool(terse)]

		out = hdr_fs.format(self.txid.hl(),self.send_amt.hl(),self.timestamp,
				self.is_rbf(color=True),self.marked_signed(color=True))

		enl = ('\n','')[bool(terse)]
		if self.chain in ('testnet','regtest'): out += green('Chain: {}\n'.format(self.chain.upper()))
		if self.btc_txid: out += 'Bitcoin TxID: {}\n'.format(self.btc_txid.hl())
		out += enl

		if self.label:
			out += 'Comment: %s\n%s' % (self.label.hl(),enl)
		out += 'Inputs:\n' + enl

		nonmm_str = '(non-{pnm} address){s}  '.format(pnm=g.proj_name,s=('',' ')[terse])
		for n,e in enumerate(sorted(self.inputs,key=lambda o: o.mmid.sort_key if o.mmid else o.addr)):
			if blockcount:
				confs = e.confs + blockcount - self.blockcount
				days = int(confs * g.mins_per_block / (60*24))
			mmid_fmt = e.mmid.fmt(width=len(nonmm_str),encl='()',color=True) if e.mmid \
						else MMGenID.hlc(nonmm_str)
			if terse:
				out += '%3s: %s %s %s BTC' % (n+1, e.addr.fmt(color=True),mmid_fmt, e.amt.hl())
			else:
				for d in (
	(n+1, 'tx,vout:',       '%s,%s' % (e.txid, e.vout)),
	('',  'address:',       e.addr.fmt(color=True) + ' ' + mmid_fmt),
	('',  'comment:',       e.label.hl() if e.label else ''),
	('',  'amount:',        '%s BTC' % e.amt.hl()),
	('',  'confirmations:', '%s (around %s days)' % (confs,days) if blockcount else '')
				):
					if d[2]: out += ('%3s %-8s %s\n' % d)
			out += '\n'

		out += 'Outputs:\n' + enl
		for n,e in enumerate(sorted(self.outputs,key=lambda o: o.mmid.sort_key if o.mmid else o.addr)):
			if e.mmid:
				app=('',' (chg)')[bool(e.is_chg and terse)]
				mmid_fmt = e.mmid.fmt(width=len(nonmm_str),encl='()',color=True,
										app=app,appcolor='green')
			else:
				mmid_fmt = MMGenID.hlc(nonmm_str)
			if terse:
				out += '%3s: %s %s %s BTC' % (n+1, e.addr.fmt(color=True),mmid_fmt, e.amt.hl())
			else:
				for d in (
						(n+1, 'address:',  e.addr.fmt(color=True) + ' ' + mmid_fmt),
						('',  'comment:',  e.label.hl() if e.label else ''),
						('',  'amount:',   '%s BTC' % e.amt.hl()),
						('',  'change:',   green('True') if e.is_chg else '')
					):
					if d[2]: out += ('%3s %-8s %s\n' % d)
			out += '\n'

		fs = (
			'Total input:  %s BTC\nTotal output: %s BTC\nTX fee:       %s BTC (%s satoshis per byte)\n',
			'In %s BTC - Out %s BTC - Fee %s BTC (%s satoshis/byte)\n'
		)[bool(terse)]

		total_in  = self.sum_inputs()
		total_out = self.sum_outputs()
		out += fs % (
			total_in.hl(),
			total_out.hl(),
			(total_in-total_out).hl(),
			pink(str(self.btc2spb(total_in-total_out))),
		)
		if opt.verbose:
			ts = len(self.hex)/2 if self.hex else 'unknown'
			out += 'Transaction size: Vsize={} Actual={}'.format(self.estimate_size(),ts)
			if self.marked_signed():
				ws = DeserializedTX(self.hex)['witness_size']
				out += ' Base={} Witness={}'.format(ts-ws,ws)
			out += '\n'

		# TX label might contain non-ascii chars
		return out

	def parse_tx_file(self,infile):

		self.parse_tx_data(get_lines_from_file(infile,self.desc+' data'))

	def parse_tx_data(self,tx_data):

		def do_err(s): die(2,'Invalid %s in transaction file' % s)

		if len(tx_data) < 5: do_err('number of lines')

		self.chksum = HexStr(tx_data.pop(0))
		if self.chksum != make_chksum_6(' '.join(tx_data)):
			do_err('checksum')

		if len(tx_data) == 6:
			self.btc_txid = BitcoinTxID(tx_data.pop(-1),on_fail='return')
			if not self.btc_txid:
				do_err('Bitcoin TxID')

		if len(tx_data) == 5:
			c = tx_data.pop(-1)
			if c != '-':
				from mmgen.bitcoin import b58decode
				comment = b58decode(c)
				if comment == False:
					do_err('encoded comment (not base58)')
				else:
					self.label = MMGenTXLabel(comment,on_fail='return')
					if not self.label:
						do_err('comment')
		else:
			comment = ''

		if len(tx_data) == 4:
			metadata,self.hex,inputs_data,outputs_data = tx_data
		else:
			do_err('number of lines')

		metadata = metadata.split()
		if len(metadata) not in (4,5): do_err('metadata')
		if len(metadata) == 5:
			t = metadata.pop(0)
			self.chain = (t.lower(),None)[t=='Unknown']

		self.txid,send_amt,self.timestamp,blockcount = metadata
		self.txid = MMGenTxID(self.txid)
		self.send_amt = BTCAmt(send_amt)
		self.blockcount = int(blockcount)
		self.hex = HexStr(self.hex)

		try: unhexlify(self.hex)
		except: do_err('hex data')

		try: self.inputs = self.decode_io('inputs',eval(inputs_data))
		except: do_err('inputs data')

		if not self.chain and not self.inputs[0].addr.testnet:
			self.chain = 'mainnet'

		try: self.outputs = self.decode_io('outputs',eval(outputs_data))
		except: do_err('btc-to-mmgen address map data')

class MMGenBumpTX(MMGenTX):

	min_fee = None
	bump_output_idx = None

	def __init__(self,filename,send=False):

		super(type(self),self).__init__(filename)

		if not self.is_rbf():
			die(1,"Transaction '{}' is not replaceable (RBF)".format(self.txid))

		# If sending, require tx to have been signed
		if send:
			if not self.marked_signed():
				die(1,"File '{}' is not a signed {} transaction file".format(filename,g.proj_name))
			if not self.btc_txid:
				die(1,"Transaction '{}' was not broadcast to the network".format(self.txid,g.proj_name))

		self.btc_txid = ''
		self.mark_raw()

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
					p = 'Fee will be deducted from output {}{} ({} BTC)'.format(idx+1,cs,o_amt)
					if o_amt < self.min_fee:
						msg('Minimum fee ({} BTC) is greater than output amount ({} BTC)'.format(
							self.min_fee,o_amt))
					elif opt.yes or keypress_confirm(p+'.  OK?',default_yes=True):
						if opt.yes: msg(p)
						self.bump_output_idx = idx
						return idx

	def set_min_fee(self):
		self.min_fee = self.sum_inputs() - self.sum_outputs() + self.get_relay_fee()

	def get_usr_fee(self,tx_fee,desc):
		ret = super(type(self),self).get_usr_fee(tx_fee,desc)
		if ret < self.min_fee:
			msg('{} BTC: {} fee too small. Minimum fee: {} BTC ({} satoshis per byte)'.format(
				ret,desc,self.min_fee,self.btc2spb(self.min_fee)))
			return False
		output_amt = self.outputs[self.bump_output_idx].amt
		if ret >= output_amt:
			msg('{} BTC: {} fee too large. Maximum fee: <{} BTC'.format(ret,desc,output_amt))
			return False
		return ret
