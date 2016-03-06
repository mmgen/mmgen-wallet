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
from binascii import unhexlify
from decimal import Decimal
from collections import OrderedDict

from mmgen.common import *
from mmgen.term import do_pager

def trim_exponent(n):
	'''Remove exponent and trailing zeros.
	'''
	d = Decimal(n)
	return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

def normalize_btc_amt(amt):
	# amt must be a string!

	from decimal import Decimal
	try:
		ret = Decimal(amt)
	except:
		msg('%s: Invalid amount' % amt)
		return False

	dmsg('Decimal(amt): %s\nAs tuple: %s' % (amt,repr(ret.as_tuple())))

	if ret.as_tuple()[-1] < -8:
		msg('%s: Too many decimal places in amount' % amt)
		return False

	if ret == 0:
		msg('Requested zero BTC amount')
		return False

	return trim_exponent(ret)

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

def prompt_and_view_tx_data(c,prompt,inputs_data,tx_hex,adata,comment,metadata):

	prompt += ' (y)es, (N)o, pager (v)iew, (t)erse view'

	reply = prompt_and_get_char(prompt,'YyNnVvTt',enter_ok=True)

	if reply and reply in 'YyVvTt':
		view_tx_data(c,inputs_data,tx_hex,adata,comment,metadata,
				pager=reply in 'Vv',terse=reply in 'Tt')


def view_tx_data(c,inputs_data,tx_hex,b2m_map,comment,metadata,pager=False,pause=True,terse=False):

	td = c.decoderawtransaction(tx_hex)

	fs = (
		'TRANSACTION DATA\n\nHeader: [Tx ID: {}] [Amount: {} BTC] [Time: {}]\n\n',
		'Transaction {} - {} BTC - {} GMT\n'
	)[bool(terse)]

	out = fs.format(*metadata)

	enl = ('\n','')[bool(terse)]
	if comment: out += 'Comment: %s\n%s' % (comment,enl)
	out += 'Inputs:\n' + enl

	nonmm_str = 'non-{pnm} address'.format(pnm=g.proj_name)

	total_in = 0
	for n,i in enumerate(td['vin']):
		for j in inputs_data:
			if j['txid'] == i['txid'] and j['vout'] == i['vout']:
				days = int(j['confirmations'] * g.mins_per_block / (60*24))
				total_in += j['amount']
				if not j['mmid']: j['mmid'] = nonmm_str
				mmid_fmt = ' ({:>{l}})'.format(j['mmid'],l=34-len(j['address']))
				if terse:
					out += '  %s: %-54s %s BTC' % (n+1,j['address'] + mmid_fmt,
							trim_exponent(j['amount']))
				else:
					for d in (
	(n+1, 'tx,vout:',       '%s,%s' % (i['txid'], i['vout'])),
	('',  'address:',       j['address'] + mmid_fmt),
	('',  'comment:',       j['comment']),
	('',  'amount:',        '%s BTC' % trim_exponent(j['amount'])),
	('',  'confirmations:', '%s (around %s days)' % (j['confirmations'], days))
					):
						if d[2]: out += ('%3s %-8s %s\n' % d)
				out += '\n'

				break
	total_out = 0
	out += 'Outputs:\n' + enl
	for n,i in enumerate(td['vout']):
		btcaddr = i['scriptPubKey']['addresses'][0]
		mmid,comment=b2m_map[btcaddr] if btcaddr in b2m_map else (nonmm_str,'')
		mmid_fmt = ' ({:>{l}})'.format(mmid,l=34-len(j['address']))
		total_out += i['value']
		if terse:
			out += '  %s: %-54s %s BTC' % (n+1,btcaddr + mmid_fmt,
					trim_exponent(i['value']))
		else:
			for d in (
					(n+1, 'address:',  btcaddr + mmid_fmt),
					('',  'comment:',  comment),
					('',  'amount:',   trim_exponent(i['value']))
				):
				if d[2]: out += ('%3s %-8s %s\n' % d)
		out += '\n'

	fs = (
		'Total input:  %s BTC\nTotal output: %s BTC\nTX fee:       %s BTC\n',
		'In %s BTC - Out %s BTC - Fee %s BTC\n'
	)[bool(terse)]

	out += fs % (
		trim_exponent(total_in),
		trim_exponent(total_out),
		trim_exponent(total_in-total_out)
	)

	o = out.encode('utf8')
	if pager: do_pager(o)
	else:
		sys.stdout.write(o)
		from mmgen.term import get_char
		if pause:
			get_char('Press any key to continue: ')
			msg('')


def parse_tx_file(tx_data,infile):

	err_str,err_fmt = '','Invalid %s in transaction file'

	if len(tx_data) == 5:
		metadata,tx_hex,inputs_data,outputs_data,comment = tx_data
	elif len(tx_data) == 4:
		metadata,tx_hex,inputs_data,outputs_data = tx_data
		comment = ''
	else:
		err_str = 'number of lines'

	if not err_str:
		if len(metadata.split()) != 3:
			err_str = 'metadata'
		else:
			try: unhexlify(tx_hex)
			except: err_str = 'hex data'
			else:
				try: inputs_data = eval(inputs_data)
				except: err_str = 'inputs data'
				else:
					try: outputs_data = eval(outputs_data)
					except: err_str = 'mmgen-to-btc address map data'
					else:
						if comment:
							from mmgen.bitcoin import b58decode
							comment = b58decode(comment)
							if comment == False:
								err_str = 'encoded comment (not base58)'
							else:
								if is_valid_tx_comment(comment):
									comment = comment.decode('utf8')
								else:
									err_str = 'comment'

	if err_str:
		msg(err_fmt % err_str)
		sys.exit(2)
	else:
		return metadata.split(),tx_hex,inputs_data,outputs_data,comment


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


def get_tx_comment_from_file(infile):
	s = get_data_from_file(infile,'transaction comment')
	if is_valid_tx_comment(s):
		return s.decode('utf8').strip()
	else:
		sys.exit(2)

def get_tx_comment_from_user(comment=''):
	try:
		while True:
			s = my_raw_input('Comment: ',insert_txt=comment.encode('utf8'))
			if s == '': return False
			if is_valid_tx_comment(s):
				return s.decode('utf8')
	except KeyboardInterrupt:
		msg('User interrupt')
		return False

def make_tx_data(metadata_fmt, tx_hex, inputs_data, b2m_map, comment):
	from mmgen.bitcoin import b58encode
	s = (b58encode(comment.encode('utf8')),) if comment else ()
	lines = (metadata_fmt, tx_hex, repr(inputs_data), repr(b2m_map)) + s
	return '\n'.join(lines)+'\n'

def mmaddr2btcaddr_addrdata(mmaddr,addr_data,source=''):
	seed_id,idx = mmaddr.split(':')
	if seed_id in addr_data:
		if idx in addr_data[seed_id]:
			vmsg('%s -> %s%s' % (mmaddr,addr_data[seed_id][idx][0],
				' (from %s)' % source if source else ''))
			return addr_data[seed_id][idx]

	return '',''
