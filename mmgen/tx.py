#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
tx.py:  Bitcoin transaction routines
"""

import sys,os
from stat import *
from binascii import unhexlify
from mmgen.common import *
from mmgen.obj import *
from mmgen.term import do_pager

def is_mmgen_seed_id(s): return SeedID(sid=s,on_fail='silent')
def is_mmgen_idx(s):     return AddrIdx(s,on_fail='silent')
def is_mmgen_id(s):      return MMGenID(s,on_fail='silent')
def is_btc_addr(s):      return BTCAddr(s,on_fail='silent')

def is_b58_str(s):
	from mmgen.bitcoin import b58a
	return set(list(s)) <= set(b58a)

def is_wif(s):
	if s == '': return False
	compressed = not s[0] == '5'
	from mmgen.bitcoin import wiftohex
	return wiftohex(s,compressed) is not False

def _wiftoaddr(s):
	if s == '': return False
	compressed = not s[0] == '5'
	from mmgen.bitcoin import wiftohex,privnum2addr
	hex_key = wiftohex(s,compressed)
	if not hex_key: return False
	return privnum2addr(int(hex_key,16),compressed)

def _wiftoaddr_keyconv(wif):
	if wif[0] == '5':
		from subprocess import check_output
		return check_output(['keyconv', wif]).split()[1]
	else:
		return _wiftoaddr(wif)

def get_wif2addr_f():
	if opt.no_keyconv: return _wiftoaddr
	from mmgen.addr import test_for_keyconv
	return (_wiftoaddr,_wiftoaddr_keyconv)[bool(test_for_keyconv())]

class MMGenTxInputOldFmt(MMGenListItem):  # for converting old tx files only
	tr = {'amount':'amt', 'address':'addr', 'confirmations':'confs','comment':'label'}
	attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','wif'
	attrs_priv = 'tr',

class MMGenTxInput(MMGenListItem):
	attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','have_wif'
	label = MMGenListItemAttr('label','MMGenAddrLabel')

class MMGenTxOutput(MMGenListItem):
	attrs = 'txid','vout','amt','label','mmid','addr','have_wif'
	label = MMGenListItemAttr('label','MMGenAddrLabel')

class MMGenTX(MMGenObject):
	ext      = 'rawtx'
	raw_ext  = 'rawtx'
	sig_ext  = 'sigtx'
	txid_ext = 'txid'
	desc = 'transaction'

	max_fee = BTCAmt('0.01')

	def __init__(self,filename=None):
		self.inputs      = []
		self.inputs_enc  = []
		self.outputs     = []
		self.outputs_enc = []
		self.change_addr = ''
		self.size        = 0             # size of raw serialized tx
		self.fee         = BTCAmt('0')
		self.send_amt    = BTCAmt('0')  # total amt minus change
		self.hex         = ''            # raw serialized hex transaction
		self.label       = MMGenTXLabel('')
		self.txid        = ''
		self.btc_txid    = ''
		self.timestamp   = ''
		self.chksum      = ''
		self.fmt_data    = ''
		self.blockcount  = 0
		if filename:
			if get_extension(filename) == self.sig_ext:
				self.mark_signed()
			self.parse_tx_file(filename)

	def add_output(self,btcaddr,amt): # 'txid','vout','amount','label','mmid','address'
		self.outputs.append(MMGenTxOutput(addr=btcaddr,amt=amt))

	def del_output(self,btcaddr):
		for i in range(len(self.outputs)):
			if self.outputs[i].addr == btcaddr:
				self.outputs.pop(i); return
		raise ValueError

	def sum_outputs(self):
		return BTCAmt(sum([e.amt for e in self.outputs]))

	def add_mmaddrs_to_outputs(self,ad_w,ad_f):
		a = [e.addr for e in self.outputs]
		d = ad_w.make_reverse_dict(a)
		d.update(ad_f.make_reverse_dict(a))
		for e in self.outputs:
			if e.addr and e.addr in d:
				e.mmid,f = d[e.addr]
				if f: e.label = f

#	def encode_io(self,desc):
# 		tr = getattr((MMGenTxOutput,MMGenTxInput)[desc=='inputs'],'tr')
# 		tr_rev = dict([(v,k) for k,v in tr.items()])
# 		return [dict([(tr_rev[e] if e in tr_rev else e,getattr(d,e)) for e in d.__dict__])
# 					for d in getattr(self,desc)]
#
	def create_raw(self,c):
		i = [{'txid':e.txid,'vout':e.vout} for e in self.inputs]
		o = dict([(e.addr,e.amt) for e in self.outputs])
		self.hex = c.createrawtransaction(i,o)
		self.txid = make_chksum_6(unhexlify(self.hex)).upper()

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

	# https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
	def calculate_size_and_fee(self,fee_estimate):
		self.size = len(self.inputs)*180 + len(self.outputs)*34 + 10
		if fee_estimate:
			ftype,fee = 'Calculated',fee_estimate*opt.tx_fee_adj*self.size / 1024
		else:
			ftype,fee = 'User-selected',opt.tx_fee

		ufee = None
		if not keypress_confirm('{} TX fee is {} BTC.  OK?'.format(ftype,fee.hl()),default_yes=True):
			while True:
				ufee = my_raw_input('Enter transaction fee: ')
				if BTCAmt(ufee,on_fail='return'):
					ufee = BTCAmt(ufee)
					if ufee > self.max_fee:
						msg('{} BTC: fee too large (maximum fee: {} BTC)'.format(ufee,self.max_fee))
					else:
						fee = ufee
						break
		self.fee = fee
		vmsg('Inputs:{}  Outputs:{}  TX size:{}'.format(
				len(self.inputs),len(self.outputs),self.size))
		vmsg('Fee estimate: {} (1024 bytes, {} confs)'.format(fee_estimate,opt.tx_confs))
		m = ('',' (after %sx adjustment)' % opt.tx_fee_adj)[opt.tx_fee_adj != 1 and not ufee]
		vmsg('TX fee:       {}{}'.format(self.fee,m))

	# inputs methods
	def list_wifs(self,desc,mmaddrs_only=False):
		return [e.wif for e in getattr(self,desc) if e.mmid] if mmaddrs_only \
			else [e.wif for e in getattr(self,desc)]

	def delete_attrs(self,desc,attr):
		for e in getattr(self,desc):
			if hasattr(e,attr): delattr(e,attr)

	def decode_io(self,desc,data):
		io = (MMGenTxOutput,MMGenTxInput)[desc=='inputs']
		return [io(**dict([(k,d[k]) for k in io.attrs
					if k in d and d[k] not in ('',None)])) for d in data]

	def decode_io_oldfmt(self,data):
		io = MMGenTxInputOldFmt
		tr_rev = dict([(v,k) for k,v in io.tr.items()])
		copy_keys = [tr_rev[k] if k in tr_rev else k for k in io.attrs]
		return [io(**dict([(io.tr[k] if k in io.tr else k,d[k])
					for k in copy_keys if k in d and d[k] != ''])) for d in data]

	def copy_inputs_from_tw(self,data):
		self.inputs = self.decode_io('inputs',[e.__dict__ for e in data])

	def get_input_sids(self):
		return set([e.mmid[:8] for e in self.inputs if e.mmid])

	def sum_inputs(self):
		return sum([e.amt for e in self.inputs])

	def add_timestamp(self):
		self.timestamp = make_timestamp()

	def add_blockcount(self,c):
		self.blockcount = int(c.getblockcount())

	def format(self):
		from mmgen.bitcoin import b58encode
		lines = (
			'{} {} {} {}'.format(
				self.txid,
				self.send_amt,
				self.timestamp,
				self.blockcount
			),
			self.hex,
			repr([e.__dict__ for e in self.inputs]),
			repr([e.__dict__ for e in self.outputs])
		) + ((b58encode(self.label.encode('utf8')),) if self.label else ())
		self.chksum = make_chksum_6(' '.join(lines))
		self.fmt_data = '\n'.join((self.chksum,) + lines)+'\n'


	def get_non_mmaddrs(self,desc):
		return list(set([i.addr for i in getattr(self,desc) if not i.mmid]))

	# return true or false, don't exit
	def sign(self,c,tx_num_str,keys):

		if not keys:
			msg('No keys. Cannot sign!')
			return False

		qmsg('Passing %s key%s to bitcoind' % (len(keys),suf(keys,'k')))
		dmsg('Keys:\n  %s' % '\n  '.join(keys))

		sig_data = [dict([(k,getattr(d,k)) for k in 'txid','vout','scriptPubKey'])
						for d in self.inputs]
		dmsg('Sig data:\n%s' % pp_format(sig_data))
		dmsg('Raw hex:\n%s' % self.hex)

		msg_r('Signing transaction{}...'.format(tx_num_str))
		sig_tx = c.signrawtransaction(self.hex,sig_data,keys)

		if sig_tx['complete']:
			msg('OK')
			self.hex = sig_tx['hex']
			self.mark_signed()
			return True
		else:
			msg('failed\nBitcoind returned the following errors:')
			pp_msg(sig_tx['errors'])
			return False

	def mark_signed(self):
		self.desc = 'signed transaction'
		self.ext = self.sig_ext

	def check_signed(self,c):
		d = c.decoderawtransaction(self.hex)
		ret = bool(d['vin'][0]['scriptSig']['hex'])
		if ret: self.mark_signed()
		return ret

	def send(self,c,bogus=False):
		if bogus:
			self.btc_txid = 'deadbeef' * 8
			m = 'BOGUS transaction NOT sent: %s'
		else:
			self.btc_txid = c.sendrawtransaction(self.hex) # exits on failure?
			m = 'Transaction sent: %s'
		msg(m % self.btc_txid)

	def write_txid_to_file(self,ask_write=False,ask_write_default_yes=True):
		fn = '%s[%s].%s' % (self.txid,self.send_amt,self.txid_ext)
		write_data_to_file(fn,self.btc_txid+'\n','transaction ID',
			ask_write=ask_write,
			ask_write_default_yes=ask_write_default_yes)

	def write_to_file(self,add_desc='',ask_write=True,ask_write_default_yes=False):
		if ask_write == False:
			ask_write_default_yes=True
		self.format()
		fn = '%s[%s].%s' % (self.txid,self.send_amt,self.ext)
		write_data_to_file(fn,self.fmt_data,self.desc+add_desc,
			ask_write=ask_write,
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
			sys.stdout.write(o)
			from mmgen.term import get_char
			if pause:
				get_char('Press any key to continue: ')
				msg('')

	def format_view(self,terse=False):
		try:
			blockcount = bitcoin_connection().getblockcount()
		except:
			blockcount = None

		fs = (
			'TRANSACTION DATA\n\nHeader: [Tx ID: {}] [Amount: {} BTC] [Time: {}]\n\n',
			'Transaction {} - {} BTC - {} UTC\n'
		)[bool(terse)]

		out = fs.format(self.txid,self.send_amt.hl(),self.timestamp)

		enl = ('\n','')[bool(terse)]
		if self.label:
			out += 'Comment: %s\n%s' % (self.label.hl(),enl)
		out += 'Inputs:\n' + enl

		nonmm_str = '(non-{pnm} address)'.format(pnm=g.proj_name)
#		for i in self.inputs: print i #DEBUG
		for n,e in enumerate(self.inputs):
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
		for n,e in enumerate(self.outputs):
			mmid_fmt = e.mmid.fmt(width=len(nonmm_str),encl='()',color=True) if e.mmid \
						else MMGenID.hlc(nonmm_str)
			if terse:
				out += '%3s: %s %s %s BTC' % (n+1, e.addr.fmt(color=True),mmid_fmt, e.amt.hl())
			else:
				for d in (
						(n+1, 'address:',  e.addr.fmt(color=True) + ' ' + mmid_fmt),
						('',  'comment:',  e.label.hl() if e.label else ''),
						('',  'amount:',   '%s BTC' % e.amt.hl())
					):
					if d[2]: out += ('%3s %-8s %s\n' % d)
			out += '\n'

		fs = (
			'Total input:  %s BTC\nTotal output: %s BTC\nTX fee:       %s BTC\n',
			'In %s BTC - Out %s BTC - Fee %s BTC\n'
		)[bool(terse)]

		total_in  = self.sum_inputs()
		total_out = self.sum_outputs()
		out += fs % (
			total_in.hl(),
			total_out.hl(),
			(total_in-total_out).hl()
		)

		return out

	def parse_tx_file(self,infile):

		self.parse_tx_data(get_lines_from_file(infile,self.desc+' data'))

	def parse_tx_data(self,tx_data):

		err_str,err_fmt = '','Invalid %s in transaction file'

		if len(tx_data) == 6:
			self.chksum,metadata,self.hex,inputs_data,outputs_data,comment = tx_data
		elif len(tx_data) == 5:
			self.chksum,metadata,self.hex,inputs_data,outputs_data = tx_data
			comment = ''
		else:
			err_str = 'number of lines'

		if not err_str:
			if self.chksum != make_chksum_6(' '.join(tx_data[1:])):
				err_str = 'checksum'
			elif len(metadata.split()) != 4:
				err_str = 'metadata'
			else:
				self.txid,send_amt,self.timestamp,blockcount = metadata.split()
				self.send_amt = BTCAmt(send_amt)
				self.blockcount = int(blockcount)
				try: unhexlify(self.hex)
				except: err_str = 'hex data'
				else:
					try: self.inputs = self.decode_io('inputs',eval(inputs_data))
					except: err_str = 'inputs data'
					else:
						try: self.outputs = self.decode_io('outputs',eval(outputs_data))
						except: err_str = 'btc-to-mmgen address map data'
						else:
							if comment:
								from mmgen.bitcoin import b58decode
								comment = b58decode(comment)
								if comment == False:
									err_str = 'encoded comment (not base58)'
								else:
									self.label = MMGenTXLabel(comment,on_fail='return')
									if not self.label:
										err_str = 'comment'

		if err_str:
			msg(err_fmt % err_str)
			sys.exit(2)
