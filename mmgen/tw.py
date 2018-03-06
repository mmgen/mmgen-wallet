#!/usr/bin/env python
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
tw: Tracking wallet methods for the MMGen suite
"""

from mmgen.common import *
from mmgen.obj import *
from mmgen.tx import is_mmgen_id

CUR_HOME,ERASE_ALL = '\033[H','\033[0J'

class MMGenTrackingWallet(MMGenObject):

	class MMGenTwOutputList(list,MMGenObject): pass

	class MMGenTwUnspentOutput(MMGenListItem):
	#	attrs = 'txid','vout','amt','label','twmmid','addr','confs','scriptPubKey','days','skip'
		txid     = MMGenImmutableAttr('txid','CoinTxID')
		vout     = MMGenImmutableAttr('vout',int,typeconv=False),
		amt      = MMGenImmutableAttr('amt',g.proto.coin_amt.__name__),
		label    = MMGenListItemAttr('label','TwComment',reassign_ok=True),
		twmmid   = MMGenImmutableAttr('twmmid','TwMMGenID')
		addr     = MMGenImmutableAttr('addr','CoinAddr'),
		confs    = MMGenImmutableAttr('confs',int,typeconv=False),
		scriptPubKey = MMGenImmutableAttr('scriptPubKey','HexStr')
		days    = MMGenListItemAttr('days',int,typeconv=False),
		skip    = MMGenListItemAttr('skip',bool,typeconv=False,reassign_ok=True),

	wmsg = {
	'no_spendable_outputs': """
No spendable outputs found!  Import addresses with balances into your
watch-only wallet using '{}-addrimport' and then re-run this program.
""".strip().format(g.proj_name.lower())
	}

	def __init__(self,minconf=1):
		self.unspent      = self.MMGenTwOutputList()
		self.fmt_display  = ''
		self.fmt_print    = ''
		self.cols         = None
		self.reverse      = False
		self.group        = False
		self.show_days    = True
		self.show_mmid    = True
		self.minconf      = minconf
		self.get_unspent_data()
		self.sort_key     = 'age'
		self.do_sort()
		self.total        = self.get_total_coin()

	def get_total_coin(self):
		return sum(i.amt for i in self.unspent)

	def get_unspent_data(self):
		if g.bogus_wallet_data: # for debugging purposes only
			us_rpc = eval(get_data_from_file(g.bogus_wallet_data)) # testing, so ok
		else:
			us_rpc = g.rpch.listunspent(self.minconf)
#		write_data_to_file('bogus_unspent.json', repr(us), 'bogus unspent data')
#		sys.exit(0)

		if not us_rpc: die(0,self.wmsg['no_spendable_outputs'])
		mm_rpc = self.MMGenTwOutputList()
		confs_per_day = 60*60*24 / g.proto.secs_per_block
		for o in us_rpc:
			if not 'account' in o: continue          # coinbase outputs have no account field
			l = TwLabel(o['account'],on_fail='silent')
			if l:
				o.update({
					'twmmid': l.mmid,
					'label':  l.comment,
					'days':   int(o['confirmations'] / confs_per_day),
					'amt':    g.proto.coin_amt(o['amount']), # TODO
					'addr':   CoinAddr(o['address']), # TODO
					'confs':  o['confirmations']
				})
				mm_rpc.append(o)
		self.unspent = self.MMGenTwOutputList([self.MMGenTwUnspentOutput(**dict([(k,v) for k,v in o.items() if k in self.MMGenTwUnspentOutput.__dict__])) for o in mm_rpc])
		for u in self.unspent:
			if u.label == None: u.label = ''
		if not self.unspent:
			die(1,'No tracked unspent outputs in tracking wallet!')

	def do_sort(self,key=None,reverse=False):
		sort_funcs = {
			'addr':  lambda i: i.addr,
			'age':   lambda i: 0 - i.confs,
			'amt':   lambda i: i.amt,
			'txid':  lambda i: '%s %03s' % (i.txid,i.vout),
			'mmid':  lambda i: i.twmmid.sort_key
		}
		key = key or self.sort_key
		if key not in sort_funcs:
			die(1,"'{}': invalid sort key.  Valid options: {}".format(key,' '.join(sort_funcs.keys())))
		self.sort_key = key
		assert type(reverse) == bool
		self.unspent.sort(key=sort_funcs[key],reverse=reverse or self.reverse)

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(capfirst(self.sort_key).replace('Twmmid','MMGenID'))
		if include_group and self.group and (self.sort_key in ('addr','txid','twmmid')):
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
		if not opt.no_blank: msg(CUR_HOME+ERASE_ALL)
		msg(self.format_for_display())

	def format_for_display(self):
		unsp = self.unspent
# 		unsp.pdie()
		self.set_term_columns()

		# allow for 7-digit confirmation nums
		col1_w = max(3,len(str(len(unsp)))+1) # num + ')'
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in unsp) or 12 # DEADBEEF:S:1
		max_acct_w = max(len(i.label) for i in unsp) + mmid_w + 1
		addr_w = min(max(len(i.addr) for i in unsp)+(0,1+max_acct_w)[self.show_mmid],self.cols-45)
		acct_w = min(max_acct_w, max(24,int(addr_w-10)))
		btaddr_w = addr_w - acct_w - 1
		label_w = acct_w - mmid_w - 1
		tx_w = max(11,min(64, self.cols-addr_w-28-col1_w))
		txdots = ('','...')[tx_w < 64]

		for i in unsp: i.skip = None
		if self.group and (self.sort_key in ('addr','txid','twmmid')):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				for k in ('addr','txid','twmmid'):
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = (k,'addr')[k=='twmmid']

		hdr_fmt = 'UNSPENT OUTPUTS (sort order: {})  Total {}: {}'
		out  = [hdr_fmt.format(' '.join(self.sort_info()),g.coin,self.total.hl())]
		if g.chain in ('testnet','regtest'):
			out += [green('Chain: {}'.format(g.chain.upper()))]
		fs = ' {:%s} {:%s} {:2} {} {} {:<}' % (col1_w,tx_w)
		out += [fs.format('Num',
				'TX id'.ljust(tx_w - 5) + ' Vout', '',
				'Address'.ljust(addr_w+3),
				'Amt({})'.format(g.coin).ljust(10),
				('Confs','Age(d)')[self.show_days])]

		for n,i in enumerate(unsp):
			addr_dots = '|' + '.'*33
			mmid_disp = MMGenID.fmtc('.'*mmid_w if i.skip=='addr'
				else i.twmmid if i.twmmid.type=='mmgen'
					else 'Non-{}'.format(g.proj_name),width=mmid_w,color=True)
			if self.show_mmid:
				addr_out = '%s %s' % (
					type(i.addr).fmtc(addr_dots,width=btaddr_w,color=True) if i.skip == 'addr' \
						else i.addr.fmt(width=btaddr_w,color=True),
					'{} {}'.format(mmid_disp,i.label.fmt(width=label_w,color=True) \
							if label_w > 0 else '')
				)
			else:
				addr_out = type(i.addr).fmtc(addr_dots,width=addr_w,color=True) \
					if i.skip=='addr' else i.addr.fmt(width=addr_w,color=True)

			tx = ' ' * (tx_w-4) + '|...' if i.skip == 'txid' \
					else i.txid[:tx_w-len(txdots)]+txdots

			out.append(fs.format(str(n+1)+')',tx,i.vout,addr_out,i.amt.fmt(color=True),
						i.days if self.show_days else i.confs))

		self.fmt_display = '\n'.join(out) + '\n'
#		unsp.pdie()
		return self.fmt_display

	def format_for_printing(self,color=False):

		addr_w = max(len(i.addr) for i in self.unspent)
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in self.unspent) or 12 # DEADBEEF:S:1
		fs  = ' {:4} {:67} {} {} {:12} {:<8} {:<6} {}'
		out = [fs.format('Num','Tx ID,Vout',
				'Address'.ljust(addr_w),
				'MMGen ID'.ljust(mmid_w+1),
				'Amount({})'.format(g.coin),
				'Confs','Age(d)',
				'Label')]

		max_lbl_len = max([len(i.label) for i in self.unspent if i.label] or [1])
		for n,i in enumerate(self.unspent):
			addr = '|'+'.' * addr_w if i.skip == 'addr' and self.group else i.addr.fmt(color=color,width=addr_w)
			tx = '|'+'.' * 63 if i.skip == 'txid' and self.group else str(i.txid)
			out.append(
				fs.format(str(n+1)+')', tx+','+str(i.vout),
					addr,
					MMGenID.fmtc(i.twmmid if i.twmmid.type=='mmgen'
						else 'Non-{}'.format(g.proj_name),width=mmid_w,color=color),
					i.amt.fmt(color=color),
					i.confs,i.days,
					i.label.hl(color=color) if i.label else
						TwComment.fmtc('',color=color,nullrepl='-',width=max_lbl_len)).rstrip())

		fs = 'Unspent outputs ({} UTC)\nSort order: {}\n\n{}\n\nTotal {}: {}\n'
		self.fmt_print = fs.format(
				make_timestr(),
				' '.join(self.sort_info(include_group=False)),
				'\n'.join(out),
				g.coin,
				self.total.hl(color=color))
		return self.fmt_print

	def display_total(self):
		fs = '\nTotal unspent: {} {} ({} outputs)'
		msg(fs.format(self.total.hl(),g.coin,len(self.unspent)))

	def get_idx_and_label_from_user(self):
		msg('')
		while True:
			ret = my_raw_input("Enter unspent output number (or 'q' to return to main menu): ")
			if ret == 'q': return None,None
			n = AddrIdx(ret,on_fail='silent') # hacky way to test and convert to integer
			if not n or n < 1 or n > len(self.unspent):
				msg('Choice must be a single number between 1 and %s' % len(self.unspent))
# 			elif not self.unspent[n-1].mmid:
# 				msg('Address #%s is not an %s address. No label can be added to it' %
# 						(n,g.proj_name))
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
						if TwComment(s,on_fail='return'):
							return n,s

	def view_and_sort(self,tx):
		fs = 'Total to spend, excluding fees: {} {}\n\n'
		txos = fs.format(tx.sum_outputs().hl(),g.coin) if tx.outputs else ''
		prompt = """
{}Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
	""".format(txos).strip()
		self.display()
		msg(prompt)

		from mmgen.term import get_char
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
					if type(self).add_label(e.twmmid,lbl,addr=e.addr):
						self.get_unspent_data()
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
	def add_label(cls,arg1,label='',addr=None,silent=False):
		from mmgen.tx import is_mmgen_id,is_coin_addr
		mmaddr,coinaddr = None,None
		if is_coin_addr(addr or arg1):
			coinaddr = CoinAddr(addr or arg1,on_fail='return')
		if is_mmgen_id(arg1):
			mmaddr = TwMMGenID(arg1)

		if mmaddr and not coinaddr:
			from mmgen.addr import AddrData
			coinaddr = AddrData(source='tw').mmaddr2coinaddr(mmaddr)

		try:
			if not is_mmgen_id(arg1):
				assert coinaddr,"Invalid coin address for this chain: {}".format(arg1)
			assert coinaddr,"{pn} address '{ma}' not found in tracking wallet"
			assert coinaddr.is_in_tracking_wallet(),"Address '{ca}' not found in tracking wallet"
		except Exception as e:
			msg(e[0].format(pn=g.proj_name,ma=mmaddr,ca=coinaddr))
			return False

		# Allow for the possibility that BTC addr of MMGen addr was entered.
		# Do reverse lookup, so that MMGen addr will not be marked as non-MMGen.
		if not mmaddr:
			from mmgen.addr import AddrData
			mmaddr = AddrData(source='tw').coinaddr2mmaddr(coinaddr)

		if not mmaddr: mmaddr = '{}:{}'.format(g.proto.base_coin.lower(),coinaddr)

		mmaddr = TwMMGenID(mmaddr)

		cmt = TwComment(label,on_fail='return')
		if cmt in (False,None): return False

		lbl = TwLabel(mmaddr + ('',' '+cmt)[bool(cmt)]) # label is ASCII for now

		# NOTE: this works because importaddress() removes the old account before
		# associating the new account with the address.
		# Will be replaced by setlabel() with new RPC label API
		# RPC args: addr,label,rescan[=true],p2sh[=none]
		ret = g.rpch.importaddress(coinaddr,lbl,False,on_fail='return')

		from mmgen.rpc import rpc_error,rpc_errmsg
		if rpc_error(ret):
			msg('From {}: {}'.format(g.proto.daemon_name,rpc_errmsg(ret)))
			if not silent:
				msg('Label could not be {}'.format(('removed','added')[bool(label)]))
			return False
		else:
			m = mmaddr.type.replace('mmg','MMG')
			a = mmaddr.replace(g.proto.base_coin.lower()+':','')
			s = '{} address {} in tracking wallet'.format(m,a)
			if label: msg("Added label '{}' to {}".format(label,s))
			else:     msg('Removed label from {}'.format(s))
			return True

	@classmethod
	def remove_label(cls,mmaddr): cls.add_label(mmaddr,'')
