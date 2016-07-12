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

import sys, os
from stat import *
from binascii import hexlify,unhexlify
from decimal import Decimal
from collections import OrderedDict

from mmgen.common import *
from mmgen.term import do_pager

def normalize_btc_amt(amt):
	'''Remove exponent and trailing zeros.
	'''
	# to_integral() needed to keep ints > 9 from being shown in exp. notation
	if is_btc_amt(amt):
		return amt.quantize(Decimal(1)) if amt == amt.to_integral() else amt.normalize()
	else:
		die(2,'%s: not a BTC amount' % amt)

def is_btc_amt(amt):

	if type(amt) is not Decimal:
		msg('%s: not a decimal number' % amt)
		return False

	if amt.as_tuple()[-1] < -g.btc_amt_decimal_places:
		msg('%s: Too many decimal places in amount' % amt)
		return False

	return True

def convert_to_btc_amt(amt,return_on_fail=False):
	# amt must be a string!

	from decimal import Decimal
	try:
		ret = Decimal(amt)
	except:
		m = '%s: amount cannot be converted to decimal' % amt
		if return_on_fail:
			msg(m); return False
		else:
			die(2,m)

	dmsg('Decimal(amt): %s' % repr(amt))

	if ret.as_tuple()[-1] < -g.btc_amt_decimal_places:
		m = '%s: Too many decimal places in amount' % amt
		if return_on_fail:
			msg(m); return False
		else:
			die(2,m)

	if ret == 0:
		msg('WARNING: BTC amount is zero')

	return ret


def parse_mmgen_label(s,check_label_len=False):
	l = split2(s)
	if not is_mmgen_addr(l[0]): return '',s
	if check_label_len: check_addr_label(l[1])
	return tuple(l)

def is_mmgen_seed_id(s):
	import re
	return re.match(r'^[0123456789ABCDEF]{8}$',s) is not None

def is_mmgen_idx(s):
	try: int(s)
	except: return False
	return len(s) <= g.mmgen_idx_max_digits

def is_mmgen_addr(s):
	seed_id,idx = split2(s,':')
	return is_mmgen_seed_id(seed_id) and is_mmgen_idx(idx)

def is_btc_addr(s):
	from mmgen.bitcoin import verify_addr
	return verify_addr(s)

def is_b58_str(s):
	from mmgen.bitcoin import b58a
	return set(list(s)) <= set(b58a)

def is_wif(s):
	if s == '': return False
	compressed = not s[0] == '5'
	from mmgen.bitcoin import wiftohex
	return wiftohex(s,compressed) is not False

def wiftoaddr(s):
	if s == '': return False
	compressed = not s[0] == '5'
	from mmgen.bitcoin import wiftohex,privnum2addr
	hex_key = wiftohex(s,compressed)
	if not hex_key: return False
	return privnum2addr(int(hex_key,16),compressed)


def is_valid_tx_comment(s):

	try: s = s.decode('utf8')
	except:
		msg('Invalid transaction comment (not UTF-8)')
		return False

	if len(s) > g.max_tx_comment_len:
		msg('Invalid transaction comment (longer than %s characters)' %
				g.max_tx_comment_len)
		return False

	return True


def check_addr_label(label):

	if len(label) > g.max_addr_label_len:
		msg("'%s': overlong label (length must be <=%s)" %
				(label,g.max_addr_label_len))
		sys.exit(3)

	for ch in label:
		if ch not in g.addr_label_symbols:
			msg("""
'%s': illegal character in label '%s'.
Only ASCII printable characters are permitted.
""".strip() % (ch,label))
			sys.exit(3)

def wiftoaddr_keyconv(wif):
	if wif[0] == '5':
		from subprocess import check_output
		return check_output(['keyconv', wif]).split()[1]
	else:
		return wiftoaddr(wif)

def get_wif2addr_f():
	if opt.no_keyconv: return wiftoaddr
	from mmgen.addr import test_for_keyconv
	return (wiftoaddr,wiftoaddr_keyconv)[bool(test_for_keyconv())]


def mmaddr2btcaddr_addrdata(mmaddr,addr_data,source=''):
	seed_id,idx = mmaddr.split(':')
	if seed_id in addr_data:
		if idx in addr_data[seed_id]:
			vmsg('%s -> %s%s' % (mmaddr,addr_data[seed_id][idx][0],
				' (from %s)' % source if source else ''))
			return addr_data[seed_id][idx]

	return '',''

from mmgen.obj import *

class MMGenTX(MMGenObject):
	ext  = g.rawtx_ext
	desc = 'transaction'

	def __init__(self,filename=None):
		self.inputs      = []
		self.outputs     = {}
		self.change_addr = ''
		self.size        = 0             # size of raw serialized tx
		self.fee         = Decimal('0')
		self.send_amt    = Decimal('0')  # total amt minus change
		self.hex         = ''            # raw serialized hex transaction
		self.comment     = ''
		self.txid        = ''
		self.btc_txid    = ''
		self.timestamp   = ''
		self.chksum      = ''
		self.fmt_data    = ''
		self.blockcount  = 0
		if filename:
			if get_extension(filename) == g.sigtx_ext:
				self.mark_signed()
			self.parse_tx_file(filename)

	def add_output(self,btcaddr,amt):
		self.outputs[btcaddr] = (amt,)

	def del_output(self,btcaddr):
		del self.outputs[btcaddr]

	def sum_outputs(self):
		return sum([self.outputs[k][0] for k in self.outputs])

	# returns true if comment added or changed
	def add_comment(self,infile=None):
		if infile:
			s = get_data_from_file(infile,'transaction comment')
			if is_valid_tx_comment(s):
				self.comment = s.decode('utf8').strip()
				return True
			else:
				sys.exit(2)
		else: # get comment from user, or edit existing comment
			m = ('Add a comment to transaction?','Edit transaction comment?')[bool(self.comment)]
			if keypress_confirm(m,default_yes=False):
				while True:
					s = my_raw_input('Comment: ',insert_txt=self.comment.encode('utf8'))
					if is_valid_tx_comment(s):
						csave = self.comment
						self.comment = s.decode('utf8').strip()
						return (True,False)[csave == self.comment]
					else:
						msg('Invalid comment')
			return False

	def edit_comment(self):
		return self.add_comment(self)

	# https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending
	def calculate_size_and_fee(self,fee_estimate):
		self.size = len(self.inputs)*180 + len(self.outputs)*34 + 10
		if fee_estimate:
			ftype,fee = 'Calculated','{:.8f}'.format(fee_estimate*opt.tx_fee_adj*self.size / 1024)
		else:
			ftype,fee = 'User-selected',opt.tx_fee

		ufee = None
		if not keypress_confirm('{} TX fee: {} BTC.  OK?'.format(ftype,fee),default_yes=True):
			while True:
				ufee = my_raw_input('Enter transaction fee: ')
				if convert_to_btc_amt(ufee,return_on_fail=True):
					if Decimal(ufee) > g.max_tx_fee:
						msg('{} BTC: fee too large (maximum fee: {} BTC)'.format(ufee,g.max_tx_fee))
					else:
						fee = ufee
						break
		self.fee = convert_to_btc_amt(fee)
		vmsg('Inputs:{}  Outputs:{}  TX size:{}'.format(
				len(self.inputs),len(self.outputs),self.size))
		vmsg('Fee estimate: {} (1024 bytes, {} confs)'.format(fee_estimate,opt.tx_confs))
		m = ('',' (after %sx adjustment)' % opt.tx_fee_adj)[opt.tx_fee_adj != 1 and not ufee]
		vmsg('TX fee:       {}{}'.format(self.fee,m))

	def copy_inputs(self,source):
		copy_keys = 'txid','vout','amount','comment','mmid','address',\
					'confirmations','scriptPubKey'
		self.inputs = [dict([(k,d[k] if k in d else '') for k in copy_keys]) for d in source]

	def sum_inputs(self):
		return sum([i['amount'] for i in self.inputs])

	def create_raw(self,c):
		o = dict([(k,v[0]) for k,v in self.outputs.items()])
		self.hex = c.createrawtransaction(self.inputs,o)
		self.txid = make_chksum_6(unhexlify(self.hex)).upper()

# 	def make_b2m_map(self,ail_w,ail_f):
# 		d = dict([(d['address'], (d['mmid'],d['comment']))
# 					for d in self.inputs if d['mmid']])
# 		d = ail_w.make_reverse_dict(self.outputs.keys())
# 		d.update(ail_f.make_reverse_dict(self.outputs.keys()))
# 		self.b2m_map = d

	def add_mmaddrs_to_outputs(self,ail_w,ail_f):
		d = ail_w.make_reverse_dict(self.outputs.keys())
		d.update(ail_f.make_reverse_dict(self.outputs.keys()))
		for k in self.outputs:
			if k in d:
				self.outputs[k] += d[k]

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
				(self.blockcount or 'None')
			),
			self.hex,
			repr(self.inputs),
			repr(self.outputs)
		) + ((b58encode(self.comment.encode('utf8')),) if self.comment else ())
		self.chksum = make_chksum_6(' '.join(lines))
		self.fmt_data = '\n'.join((self.chksum,) + lines)+'\n'

	# return true or false, don't exit
	def sign(self,c,tx_num_str,keys=None):

		if keys:
			qmsg('Passing %s key%s to bitcoind' % (len(keys),suf(keys,'k')))
			dmsg('Keys:\n  %s' % '\n  '.join(keys))

		sig_data = [dict([(k,d[k]) for k in 'txid','vout','scriptPubKey']) for d in self.inputs]
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
		self.ext = g.sigtx_ext

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
		fn = '%s[%s].%s' % (self.txid,self.send_amt,g.txid_ext)
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

		out = fs.format(self.txid,self.send_amt,self.timestamp)

		enl = ('\n','')[bool(terse)]
		if self.comment:
			out += 'Comment: %s\n%s' % (self.comment,enl)
		out += 'Inputs:\n' + enl

		nonmm_str = 'non-{pnm} address'.format(pnm=g.proj_name)

		for n,i in enumerate(self.inputs):
			if blockcount:
				confirmations = i['confirmations'] + blockcount - self.blockcount
				days = int(confirmations * g.mins_per_block / (60*24))
			if not i['mmid']:
				i['mmid'] = nonmm_str
			mmid_fmt = ' ({:>{l}})'.format(i['mmid'],l=34-len(i['address']))
			if terse:
				out += '  %s: %-54s %s BTC' % (n+1,i['address'] + mmid_fmt,
						normalize_btc_amt(i['amount']))
			else:
				for d in (
	(n+1, 'tx,vout:',       '%s,%s' % (i['txid'], i['vout'])),
	('',  'address:',       i['address'] + mmid_fmt),
	('',  'comment:',       i['comment']),
	('',  'amount:',        '%s BTC' % normalize_btc_amt(i['amount'])),
	('',  'confirmations:', '%s (around %s days)' % (confirmations,days) if blockcount else '')
				):
					if d[2]: out += ('%3s %-8s %s\n' % d)
			out += '\n'

		out += 'Outputs:\n' + enl
		for n,k in enumerate(self.outputs):
			btcaddr = k
			v = self.outputs[k]
			btc_amt,mmid,comment = (v[0],'Non-MMGen address','') if len(v) == 1 else v
			mmid_fmt = ' ({:>{l}})'.format(mmid,l=34-len(btcaddr))
			if terse:
				out += '  %s: %-54s %s BTC' % (n+1, btcaddr+mmid_fmt, normalize_btc_amt(btc_amt))
			else:
				for d in (
						(n+1, 'address:',  btcaddr + mmid_fmt),
						('',  'comment:',  comment),
						('',  'amount:',   '%s BTC' % normalize_btc_amt(btc_amt))
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
			normalize_btc_amt(total_in),
			normalize_btc_amt(total_out),
			normalize_btc_amt(total_in-total_out)
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
				self.send_amt = Decimal(send_amt)
				self.blockcount = int(blockcount)
				try: unhexlify(self.hex)
				except: err_str = 'hex data'
				else:
					try: self.inputs = eval(inputs_data)
					except: err_str = 'inputs data'
					else:
						try: self.outputs = eval(outputs_data)
						except: err_str = 'btc-to-mmgen address map data'
						else:
							if comment:
								from mmgen.bitcoin import b58decode
								comment = b58decode(comment)
								if comment == False:
									err_str = 'encoded comment (not base58)'
								else:
									if is_valid_tx_comment(comment):
										self.comment = comment.decode('utf8')
									else:
										err_str = 'comment'

		if err_str:
			msg(err_fmt % err_str)
			sys.exit(2)


