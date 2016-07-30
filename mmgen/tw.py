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
from mmgen.term import get_char

def parse_tw_acct_label(s):
	ret = s.split(None,1)
	if ret and MMGenID(ret[0],on_fail='silent'):
		if len(ret) == 2:
			return tuple(ret)
		else:
			return ret[0],None
	else:
		return None,None

class MMGenTWOutput(MMGenListItem):
	attrs_reassign = 'label','skip'
	attrs = 'txid','vout','amt','label','mmid','addr','confs','scriptPubKey','days','skip'
	label = MMGenListItemAttr('label','MMGenAddrLabel')

class MMGenTrackingWallet(MMGenObject):
	wmsg = {
	'no_spendable_outputs': """
No spendable outputs found!  Import addresses with balances into your
watch-only wallet using '{}-addrimport' and then re-run this program.
""".strip().format(g.proj_name)
	}
	sort_keys = 'addr','age','amt','txid','mmid'

	def __init__(self):
		self.unspent      = []
		self.fmt_display  = ''
		self.fmt_print    = ''
		self.cols         = None
		self.reverse      = False
		self.group        = False
		self.show_days    = True
		self.show_mmid    = True
		self.get_data()
		self.sort_key     = 'age'
		self.do_sort()
		self.total        = self.get_total_btc()

	def get_total_btc(self):
		return sum([i.amt for i in self.unspent])

	def get_data(self):
		if g.bogus_wallet_data: # for debugging purposes only
			us_rpc = eval(get_data_from_file(g.bogus_wallet_data))
		else:
			us_rpc = bitcoin_connection().listunspent()
#		write_data_to_file('bogus_unspent.json', repr(us), 'bogus unspent data')
#		sys.exit()

		if not us_rpc: die(2,self.wmsg['no_spendable_outputs'])
		for o in us_rpc:
			o['mmid'],o['label'] = parse_tw_acct_label(o['account']) if 'account' in o else ('','')
			o['days'] = int(o['confirmations'] * g.mins_per_block / (60*24))
			o['amt'] = o['amount'] # TODO
			o['addr'] = o['address']
			o['confs'] = o['confirmations']
		self.unspent = [MMGenTWOutput(**dict([(k,v) for k,v in o.items() if k in MMGenTWOutput.attrs and o[k] not in (None,'')])) for o in us_rpc]
#		die(1,''.join([pp_format(i)+'\n' for i in us_rpc]))
#		die(1,''.join([str(i)+'\n' for i in self.unspent]))

	def s_addr(self,i):  return i.addr
	def s_age(self,i):   return 0 - i.confs
	def s_amt(self,i):   return i.amt
	def s_txid(self,i):  return '%s %03s' % (i.txid,i.vout)
	def s_mmid(self,i):
		if i.mmid:
			return '{}:{:>0{w}}'.format(
				*i.mmid.split(':'), w=AddrIdx.max_digits)
		else: return 'G' + (i.label or '')

	def do_sort(self,key=None,reverse=None):
		if not key: key = self.sort_key
		assert key
		self.sort_key = key
		if key not in self.sort_keys:
			fs = "'{}': invalid sort key.  Valid keys: [{}]"
			die(2,fs.format(key,' '.join(self.sort_keys)))
		if reverse == None: reverse = self.reverse
		self.unspent.sort(key=getattr(self,'s_'+key),reverse=reverse)

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(self.sort_key.capitalize().replace('Mmid','MMGenID'))
		if include_group and self.group and (self.sort_key in ('addr','txid','mmid')):
			ret.append('Grouped')
		return ret

	def set_term_columns(self):
		from mmgen.term import get_terminal_size
		while True:
			self.cols = get_terminal_size()[0]
			if self.cols >= g.min_screen_width: break
			m1 = 'Screen too narrow to display the tracking wallet'
			m2 = 'Please resize your screen to at least {} characters and hit ENTER '
			my_raw_input(m1+'\n'+m2.format(g.min_screen_width))

	def display(self):
		msg(self.format_for_display())

	def format_for_display(self):
		unsp = [MMGenTWOutput(**i.__dict__) for i in self.unspent]
		self.set_term_columns()

		for i in unsp:
			if i.label == None: i.label = ''
			i.skip = ''

		mmid_w = max(len(i.mmid or '') for i in unsp) or 10
		max_acct_len = max([len((i.mmid or '')+i.label)+1 for i in unsp])
		addr_w = min(34+((1+max_acct_len) if self.show_mmid else 0),self.cols-46) + 6
		acct_w   = min(max_acct_len, max(24,int(addr_w-10)))
		btaddr_w = addr_w - acct_w - 1
		label_w = acct_w - mmid_w - 1
		tx_w = max(11,min(64, self.cols-addr_w-32))
		txdots = ('','...')[tx_w < 64]
		fs = ' %-4s %-' + str(tx_w) + 's %-2s %s %s %s'
		table_hdr = fs % ('Num',
			'TX id'.ljust(tx_w - 5) + ' Vout',
			'',
			BTCAddr.fmtc('Address',width=addr_w+1),
			'Amt(BTC) ',
			('Conf.','Age(d)')[self.show_days])

		if self.group and (self.sort_key in ('addr','txid','mmid')):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				for k in ('addr','txid','mmid'):
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = (k,'addr')[k=='mmid']

		hdr_fmt   = 'UNSPENT OUTPUTS (sort order: %s)  Total BTC: %s'
		out  = [hdr_fmt % (' '.join(self.sort_info()), self.total.hl()), table_hdr]

		for n,i in enumerate(unsp):
			addr_dots = '|' + '.'*33
			mmid_disp = (MMGenID.hlc('.'*mmid_w) \
							if i.skip=='addr' else i.mmid.fmt(width=mmid_w,color=True)) \
								if i.mmid else ' ' * mmid_w
			if self.show_mmid and i.mmid:
				addr_out = '%s %s' % (
					type(i.addr).fmtc(addr_dots,width=btaddr_w,color=True) if i.skip == 'addr' \
						else i.addr.fmt(width=btaddr_w,color=True),
					'{} {}'.format(mmid_disp,i.label.fmt(width=label_w,color=True) if label_w > 0 else '')
				)
			else:
				addr_out = type(i.addr).fmtc(addr_dots,width=addr_w,color=True) if i.skip=='addr' \
								else i.addr.fmt(width=addr_w,color=True)

			tx = ' ' * (tx_w-4) + '|...' if i.skip == 'txid' \
					else i.txid[:tx_w-len(txdots)]+txdots

			out.append(fs % (str(n+1)+')',tx,i.vout,addr_out,i.amt.fmt(color=True),
						i.days if self.show_days else i.confs))

		self.fmt_display = '\n'.join(out) + '\n'
		return self.fmt_display

	def format_for_printing(self,color=False):

		fs  = ' %-4s %-67s %s %s %s %-8s %-6s %s'
		out = [fs % ('Num','Tx ID,Vout','Address'.ljust(34),'MMGen ID'.ljust(15),
			'Amount(BTC)','Conf.','Age(d)', 'Label')]

		max_lbl_len = max(len(i.label) for i in self.unspent if i.label) or 1
		for n,i in enumerate(self.unspent):
			addr = '=' if i.skip == 'addr' and self.group else i.addr.fmt(color=color)
			tx = ' ' * 63 + '=' if i.skip == 'txid' and self.group else str(i.txid)
			s = fs % (str(n+1)+')', tx+','+str(i.vout),addr,
					(i.mmid.fmt(width=14,color=color) if i.mmid else
						MMGenID.fmtc('',width=14,nullrepl='-',color=color)),
					i.amt.fmt(color=color),i.confs,i.days,
					i.label.hl(color=color) if i.label else
						MMGenAddrLabel.fmtc('',color=color,nullrepl='-',width=max_lbl_len))
			out.append(s.rstrip())

		fs = 'Unspent outputs ({} UTC)\nSort order: {}\n\n{}\n\nTotal BTC: {}\n'
		self.fmt_print = fs.format(
				make_timestr(),
				' '.join(self.sort_info(include_group=False)),
				'\n'.join(out),
				self.total.hl(color=color))
		return self.fmt_print

	def display_total(self):
		fs = '\nTotal unspent: %s BTC (%s outputs)'
		msg(fs % (self.total.hl(),len(self.unspent)))

	def get_idx_and_label_from_user(self):
		msg('')
		while True:
			ret = my_raw_input("Enter unspent output number (or 'q' to return to main menu): ")
			if ret == 'q': return None,None
			n = AddrIdx(ret,on_fail='silent') # hacky way to test and convert to integer
			if not n or n < 1 or n > len(self.unspent):
				msg('Choice must be a single number between 1 and %s' % len(self.unspent))
			elif not self.unspent[n-1].mmid:
				msg('Address #%s is not an %s address. No label can be added to it' %
						(n,g.proj_name))
			else:
				while True:
					s = my_raw_input("Enter label text (or 'q' to return to main menu): ")
					if s == 'q':
						return None,None
					elif s == '':
						if keypress_confirm(
							"Removing label for address #%s.  Is this what you want?" % n):
							return n,s
					elif s:
						if MMGenAddrLabel(s,on_fail='return'):
							return n,s

	def view_and_sort(self):
		from mmgen.term import do_pager
		prompt = """
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
	""".strip()
		self.display()
		msg(prompt)

		p = "'q'=quit view, 'p'=print to file, 'v'=pager view, 'w'=wide view, 'l'=add label:\b"
		while True:
			reply = get_char(p, immed_chars='atDdAMrgmeqpvw')
			if   reply == 'a': self.do_sort('amt')
			elif reply == 'A': self.do_sort('age')
			elif reply == 'd': self.do_sort('addr')
			elif reply == 'D': self.show_days = not self.show_days
			elif reply == 'e': msg('\n%s\n%s\n%s' % (self.fmt_display,prompt,p))
			elif reply == 'g': self.group = not self.group
			elif reply == 'l':
				idx,lbl = self.get_idx_and_label_from_user()
				if idx:
					e = self.unspent[idx-1]
					if type(self).add_label(e.mmid,lbl,addr=e.addr):
						self.get_data()
						self.do_sort()
						msg('%s\n%s\n%s' % (self.fmt_display,prompt,p))
					else:
						msg('Label could not be added\n%s\n%s' % (prompt,p))
			elif reply == 'M': self.do_sort('mmid'); self.show_mmid = True
			elif reply == 'm': self.show_mmid = not self.show_mmid
			elif reply == 'p':
				msg('')
				of = 'listunspent[%s].out' % ','.join(self.sort_info(include_group=False)).lower()
				write_data_to_file(of,self.format_for_printing(),'unspent outputs listing')
				m = yellow("Data written to '%s'" % of)
				msg('\n%s\n%s\n\n%s' % (self.fmt_display,m,prompt))
				continue
			elif reply == 'q': return self.unspent
			elif reply == 'r': self.unspent.reverse(); self.reverse = not self.reverse
			elif reply == 't': self.do_sort('txid')
			elif reply == 'v':
				do_pager(self.fmt_display)
				continue
			elif reply == 'w':
				do_pager(self.format_for_printing(color=True))
				continue
			else:
				msg('\nInvalid input')
				continue

			msg('\n')
			self.display()
			msg(prompt)

	# returns on failure
	@classmethod
	def add_label(cls,mmaddr,label='',addr=None):
		mmaddr = MMGenID(mmaddr)

		if addr: # called from view_and_sort()
			if not BTCAddr(addr,on_fail='return'): return False
		else:
			from mmgen.addr import AddrData
			addr = AddrData(source='tw').mmaddr2btcaddr(mmaddr)
			if not addr:
				msg('{} address {} not found in tracking wallet'.format(g.proj_name,mmaddr))
				return False

		label = MMGenAddrLabel(label,on_fail='return')
		if not label and label != '': return False

		acct = mmaddr + (' ' + label if label else '') # label is ASCII for now
		# return on failure - args: addr,label,rescan,p2sh
		ret = bitcoin_connection().importaddress(addr,acct,False,on_fail='return')
		from mmgen.rpc import rpc_error,rpc_errmsg
		if rpc_error(ret): msg('From bitcoind: ' + rpc_errmsg(ret))
		return not rpc_error(ret)

	@classmethod
	def remove_label(cls,mmaddr): cls.add_label(mmaddr,'')
