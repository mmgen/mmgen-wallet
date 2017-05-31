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
tx.py:  Bitcoin transaction routines
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

def is_b58_str(s):
	from mmgen.bitcoin import b58a
	return set(list(s)) <= set(b58a)

def is_wif(s):
	if s == '': return False
	from mmgen.bitcoin import wif2hex
	return bool(wif2hex(s))

class MMGenTxInputOldFmt(MMGenListItem):  # for converting old tx files only
	tr = {'amount':'amt', 'address':'addr', 'confirmations':'confs','comment':'label'}
	attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','wif'
	attrs_priv = 'tr',

class MMGenTxInput(MMGenListItem):
	attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','have_wif','sequence'
	label = MMGenListItemAttr('label','MMGenAddrLabel')

class MMGenTxOutput(MMGenListItem):
	attrs = 'txid','vout','amt','label','mmid','addr','have_wif','is_chg'
	label = MMGenListItemAttr('label','MMGenAddrLabel')

class MMGenTX(MMGenObject):
	ext      = 'rawtx'
	raw_ext  = 'rawtx'
	sig_ext  = 'sigtx'
	txid_ext = 'txid'
	desc = 'transaction'

	def __init__(self,filename=None):
		self.inputs      = []
		self.inputs_enc  = []
		self.outputs     = []
		self.outputs_enc = []
		self.send_amt    = BTCAmt('0')  # total amt minus change
		self.hex         = ''           # raw serialized hex transaction
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

	def add_output(self,btcaddr,amt,is_chg=None):
		self.outputs.append(MMGenTxOutput(addr=btcaddr,amt=amt,is_chg=is_chg))

	def get_chg_output_idx(self):
		for i in range(len(self.outputs)):
			if self.outputs[i].is_chg == True:
				return i
		return None

	def update_output_amt(self,idx,amt):
		o = self.outputs[idx].__dict__
		o['amt'] = amt
		self.outputs[idx] = MMGenTxOutput(**o)

	def del_output(self,idx):
		self.outputs.pop(idx)

	def sum_outputs(self,exclude=None):
		olist = self.outputs if exclude == None else \
			self.outputs[:exclude] + self.outputs[exclude+1:]
		return BTCAmt(sum([e.amt for e in olist]))

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

	# https://bitcoin.stackexchange.com/questions/1195/
	# how-to-calculate-transaction-size-before-sending
	# 180: uncompressed, 148: compressed
	def get_size(self):
		if not self.inputs or not self.outputs: return None
		return len(self.inputs)*180 + len(self.outputs)*34 + 10

	def get_fee(self):
		return self.sum_inputs() - self.sum_outputs()

	def btc2spb(self,btc_fee):
		return int(btc_fee/g.satoshi/self.get_size())

	def get_relay_fee(self):
		assert self.get_size()
		kb_fee = BTCAmt(bitcoin_connection().getinfo()['relayfee'])
		vmsg('Relay fee: {} BTC/kB'.format(kb_fee))
		return kb_fee * self.get_size() / 1024

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
		btc_fee = self.convert_fee_spec(tx_fee,self.get_size(),on_fail='return')
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

	def get_output_sids(self):
		return set([e.mmid[:8] for e in self.outputs if e.mmid])

	def sum_inputs(self):
		return sum([e.amt for e in self.inputs])

	def add_timestamp(self):
		self.timestamp = make_timestamp()

	def add_blockcount(self,c):
		self.blockcount = int(c.getblockcount())

	def format(self):
		from mmgen.bitcoin import b58encode
		lines = [
			'{} {} {} {}'.format(
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
			vmsg('Signed transaction size: {}'.format(len(self.hex)/2))
			return True
		else:
			msg('failed\nBitcoind returned the following errors:')
			pp_msg(sig_tx['errors'])
			return False

	def mark_raw(self):
		self.desc = 'transaction'
		self.ext = self.raw_ext

	def mark_signed(self):
		self.desc = 'signed transaction'
		self.ext = self.sig_ext

	def is_signed(self,color=False):
		ret = self.desc == 'signed transaction'
		return (red,green)[ret](str(ret)) if color else ret

	def check_signed(self,c):
		d = c.decoderawtransaction(self.hex)
		ret = bool(d['vin'][0]['scriptSig']['hex'])
		if ret: self.mark_signed()
		return ret

	def send(self,c,prompt_user=True):

		if self.get_fee() > g.max_tx_fee:
			die(2,'Transaction fee ({}) greater than max_tx_fee ({})!'.format(self.get_fee(),g.max_tx_fee))

		if prompt_user:
			m1 = ("Once this transaction is sent, there's no taking it back!",'')[bool(opt.quiet)]
			m2 = 'broadcast this transaction to the network'
			m3 = ('YES, I REALLY WANT TO DO THIS','YES')[bool(opt.quiet or opt.yes)]
			confirm_or_exit(m1,m2,m3)

		msg('Sending transaction')
		if os.getenv('MMGEN_BOGUS_SEND'):
			ret = 'deadbeef' * 8
			m = 'BOGUS transaction NOT sent: %s'
		else:
			ret = c.sendrawtransaction(self.hex) # exits on failure
			m = 'Transaction sent: %s'

		if ret:
			self.btc_txid = BitcoinTxID(ret,on_fail='return')
			if self.btc_txid:
				self.desc = 'sent transaction'
				msg(m % self.btc_txid.hl())
				self.add_timestamp()
				self.add_blockcount(c)
				return True

		# rpc implementation exits on failure, so we won't get here
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
		o = self.format_view(terse=terse)
		if pager: do_pager(o)
		else:
			sys.stdout.write(o)
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
		try:
			blockcount = bitcoin_connection().getblockcount()
		except:
			blockcount = None

		hdr_fs = (
			'TRANSACTION DATA\n\nHeader: [ID:{}] [{} BTC] [{} UTC] [RBF:{}] [Signed:{}]\n',
			'Transaction {} {} BTC ({} UTC) RBF={} Signed={}\n'
		)[bool(terse)]

		out = hdr_fs.format(self.txid.hl(),self.send_amt.hl(),self.timestamp,
				self.is_rbf(color=True),self.is_signed(color=True))

		enl = ('\n','')[bool(terse)]
		if self.btc_txid: out += 'Bitcoin TxID: {}\n'.format(self.btc_txid.hl())
		out += enl

		if self.label:
			out += 'Comment: %s\n%s' % (self.label.hl(),enl)
		out += 'Inputs:\n' + enl

		nonmm_str = '(non-{pnm} address){s}'.format(pnm=g.proj_name,s=('',' ')[terse])
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
			out += 'Transaction size: estimated - {}, actual - {}\n'.format(self.get_size(),ts)

		# only tx label may contain non-ascii chars
		# encode() is necessary for test suite with PopenSpawn
		return out.encode('utf8')

	def parse_tx_file(self,infile):

		self.parse_tx_data(get_lines_from_file(infile,self.desc+' data'))

	def parse_tx_data(self,tx_data):

		def do_err(s): die(2,'Invalid %s in transaction file' % s)

		if len(tx_data) < 5: do_err('number of lines')

		self.chksum = tx_data.pop(0)
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

		if len(metadata.split()) != 4: do_err('metadata')

		self.txid,send_amt,self.timestamp,blockcount = metadata.split()
		self.txid = MMGenTxID(self.txid)
		self.send_amt = BTCAmt(send_amt)
		self.blockcount = int(blockcount)

		try: unhexlify(self.hex)
		except: do_err('hex data')

		try: self.inputs = self.decode_io('inputs',eval(inputs_data))
		except: do_err('inputs data')

		try: self.outputs = self.decode_io('outputs',eval(outputs_data))
		except: do_err('btc-to-mmgen address map data')

class MMGenBumpTX(MMGenTX):

	min_fee = None
	bump_output_idx = None

	def __init__(self,filename,send=False):

		super(type(self),self).__init__(filename)

		if not self.is_rbf():
			die(1,"Transaction '{}' is not replaceable (RBF)".format(self.txid))

		# If sending, require tx to have been signed and broadcast
		if send:
			if not self.is_signed():
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
				reply = my_raw_input('Which output do you wish to deduct the fee from? ')
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
