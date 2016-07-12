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
tw: Tracking wallet methods for the MMGen suite
"""

from mmgen.common import *
from mmgen.obj import *
from mmgen.tx import parse_mmgen_label,normalize_btc_amt
from mmgen.term import get_char

class MMGenTrackingWallet(MMGenObject):

	wmsg = {
	'no_spendable_outputs': """
No spendable outputs found!  Import addresses with balances into your
watch-only wallet using '{}-addrimport' and then re-run this program.
""".strip().format(g.proj_name)
	}

	sort_keys = 'address','age','amount','txid','mmaddr'
	def s_address(self,i):  return i['address']
	def s_age(self,i):      return 0 - i['confirmations']
	def s_amount(self,i):   return i['amount']
	def s_txid(self,i):     return '%s %03s' % (i['txid'],i['vout'])
	def s_mmaddr(self,i):
		if i['mmid']:
			return '{}:{:>0{w}}'.format(
				*i['mmid'].split(':'), w=g.mmgen_idx_max_digits)
		else: return 'G' + i['comment']

	def do_sort(self,key,reverse=None):
		if key not in self.sort_keys:
			fs = "'{}': invalid sort key.  Valid keys: [{}]"
			die(2,fs.format(key,' '.join(self.sort_keys)))
		if reverse == None: reverse = self.reverse
		self.sort = key
		self.unspent.sort(key=getattr(self,'s_'+key),reverse=reverse)

	def sort_info(self,include_group=True):
		ret = ([],['reverse'])[self.reverse]
		ret.append(self.sort)
		if include_group and self.group and (self.sort in ('address','txid')):
			ret.append('grouped')
		return ret

	def __init__(self):
		if g.bogus_wallet_data: # for debugging purposes only
			us = eval(get_data_from_file(g.bogus_wallet_data))
		else:
			us = bitcoin_connection().listunspent()
#		write_data_to_file('bogus_unspent.json', repr(us), 'bogus unspent data')
#		sys.exit()

		if not us: die(2,self.wmsg['no_spendable_outputs'])
		for o in us:
			o['mmid'],o['comment'] = parse_mmgen_label(o['account'])
			del o['account']
			o['skip'] = ''
			amt = str(normalize_btc_amt(o['amount']))
			lfill = 3 - len(amt.split('.')[0]) if '.' in amt else 3 - len(amt)
			o['amt_fmt'] = ' '*lfill + amt
			o['days'] = int(o['confirmations'] * g.mins_per_block / (60*24))

		self.unspent  = us
		self.fmt_display  = ''
		self.fmt_print    = ''
		self.cols         = None
		self.reverse      = False
		self.group        = False
		self.show_days    = True
		self.show_mmaddr  = True
		self.do_sort('age')
		self.total = sum([i['amount'] for i in self.unspent])

	def set_cols(self):
		from mmgen.term import get_terminal_size
		self.cols = get_terminal_size()[0]
		if self.cols < g.min_screen_width:
			m = 'A screen at least {} characters wide is required to display the tracking wallet'
			die(2,m.format(g.min_screen_width))

	def display(self):
		msg(self.format_for_display())

	def format(self,wide=False):
		return self.format_for_printing() if wide else self.format_for_display()

	def format_for_display(self):
		unspent = self.unspent
		total = sum([i['amount'] for i in unspent])
		mmid_w = max(len(i['mmid']) for i in unspent)
		self.set_cols()

		max_acct_len = max([len(i['mmid']+i['comment'])+1 for i in self.unspent])
		addr_w = min(34+((1+max_acct_len) if self.show_mmaddr else 0),self.cols-46)
		acct_w   = min(max_acct_len, max(24,int(addr_w-10)))
		btaddr_w = addr_w - acct_w - 1
		tx_w = max(11,min(64, self.cols-addr_w-32))
		txdots = ('','...')[tx_w < 64]
		fs = ' %-4s %-' + str(tx_w) + 's %-2s %-' + str(addr_w) + 's %-13s %-s'
		table_hdr = fs % ('Num','TX id  Vout','','Address','Amount (BTC)',
							('Conf.','Age(d)')[self.show_days])

		from copy import deepcopy
		unsp = deepcopy(unspent)
		for i in unsp: i['skip'] = ''
		if self.group and (self.sort in ('address','txid')):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				if self.sort == 'address' and a['address'] == b['address']: b['skip'] = 'addr'
				elif self.sort == 'txid' and a['txid'] == b['txid']:        b['skip'] = 'txid'

		for i in unsp:
			addr_disp = (i['address'],'|' + '.'*33)[i['skip']=='addr']
			mmid_disp = (i['mmid'],'.'*len(i['mmid']))[i['skip']=='addr']
			if self.show_mmaddr:
				dots = ('','..')[btaddr_w < len(i['address'])]
				i['addr'] = '%s%s %s' % (
					addr_disp[:btaddr_w-len(dots)],
					dots, (
					('{:<{w}} '.format(mmid_disp,w=mmid_w) if i['mmid'] else '')
						+ i['comment'])[:acct_w]
					)
			else:
				i['addr'] = addr_disp

			i['tx'] = ' ' * (tx_w-4) + '|...' if i['skip'] == 'txid' \
					else i['txid'][:tx_w-len(txdots)]+txdots

		hdr_fmt   = 'UNSPENT OUTPUTS (sort order: %s)  Total BTC: %s'
		out  = [hdr_fmt % (' '.join(self.sort_info()), normalize_btc_amt(total)), table_hdr]
		out += [fs % (str(n+1)+')',i['tx'],i['vout'],i['addr'],i['amt_fmt'],
					i['days'] if self.show_days else i['confirmations'])
						for n,i in enumerate(unsp)]
		self.fmt_display = '\n'.join(out)
		return self.fmt_display

	def format_for_printing(self):

		total = sum([i['amount'] for i in self.unspent])
		fs  = ' %-4s %-67s %-34s %-14s %-12s %-8s %-6s %s'
		out = [fs % ('Num','Tx ID,Vout','Address','{} ID'.format(g.proj_name),
			'Amount(BTC)','Conf.','Age(d)', 'Comment')]

		for n,i in enumerate(self.unspent):
			addr = '=' if i['skip'] == 'addr' and self.group else i['address']
			tx = ' ' * 63 + '=' if i['skip'] == 'txid' and self.group else str(i['txid'])
			s = fs % (str(n+1)+')', tx+','+str(i['vout']),addr,
					i['mmid'],i['amt_fmt'].strip(),i['confirmations'],i['days'],i['comment'])
			out.append(s.rstrip())

		fs = 'Unspent outputs ({} UTC)\nSort order: {}\n\n{}\n\nTotal BTC: {}\n'
		self.fmt_print = fs.format(
				make_timestr(),
				' '.join(self.sort_info(include_group=False)),
				'\n'.join(out),
				normalize_btc_amt(total))
		return self.fmt_print

	def display_total(self):
		fs = '\nTotal unspent: %s BTC (%s outputs)'
		msg(fs % (normalize_btc_amt(self.total), len(self.unspent)))

	def view_and_sort(self):
		from mmgen.term import do_pager
		s = """
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
	""".strip()
		self.display()
		msg(s)

		p = "('q' = quit sorting, 'p' = print to file, 'v' = pager view, 'w' = wide view): "
		while True:
			reply = get_char(p, immed_chars='atDdAMrgmeqpvw')
			if   reply == 'a': self.do_sort('amount')
			elif reply == 't': self.do_sort('txid')
			elif reply == 'D': self.show_days = not self.show_days
			elif reply == 'd': self.do_sort('address')
			elif reply == 'A': self.do_sort('age')
			elif reply == 'M': self.do_sort('mmaddr'); self.show_mmaddr = True
			elif reply == 'r': self.unspent.reverse(); self.reverse = not self.reverse
			elif reply == 'g': self.group = not self.group
			elif reply == 'm': self.show_mmaddr = not self.show_mmaddr
			elif reply == 'e': msg("\n%s\n%s\n%s" % (self.fmt_display,s,p))
			elif reply == 'q': return self.unspent
			elif reply == 'p':
				of = 'listunspent[%s].out' % ','.join(self.sort_info(include_group=False))
				write_data_to_file(of,self.format_for_printing(),'unspent outputs listing')
				m = yellow("Data written to '%s'" % of)
				msg('\n%s\n\n%s\n\n%s' % (self.fmt_display,m,s))
				continue
			elif reply == 'v':
				do_pager(self.fmt_display)
				continue
			elif reply == 'w':
				do_pager(self.format_for_printing())
				continue
			else:
				msg('\nInvalid input')
				continue

			self.display()
			msg(s)
