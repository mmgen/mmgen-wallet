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
tw: Tracking wallet methods for the MMGen suite
"""

import json
from .exception import *
from .common import *
from .obj import *
from .tx import is_mmgen_id

CUR_HOME,ERASE_ALL = '\033[H','\033[0J'
def CUR_RIGHT(n): return '\033[{}C'.format(n)

def get_tw_label(s):
	try: return TwLabel(s,on_fail='raise')
	except BadTwComment: raise
	except: return None

_date_formatter = {
	'days':      lambda secs: (g.rpc.cur_date - secs) // 86400,
	'date':      lambda secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:],
	'date_time': lambda secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5]),
}

async def _set_dates(us):
	if us and us[0].date is None:
		# 'blocktime' differs from 'time', is same as getblockheader['time']
		dates = [o['blocktime'] for o in await g.rpc.gathered_call('gettransaction',[(o.txid,) for o in us])]
		for o,date in zip(us,dates):
			o.date = date

if os.getenv('MMGEN_BOGUS_WALLET_DATA'):
	# 1831006505 (09 Jan 2028) = projected time of block 1000000
	_date_formatter['days'] = lambda date: (1831006505 - date) // 86400
	async def _set_dates(us):
		for o in us:
			o.date = 1831006505 - int(9.7 * 60 * (o.confs - 1))

class TwUnspentOutputs(MMGenObject,metaclass=aInitMeta):

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tw','TwUnspentOutputs'))

	txid_w = 64
	disp_type = 'btc'
	can_group = True
	hdr_fmt = 'UNSPENT OUTPUTS (sort order: {}) Total {}: {}'
	desc = 'unspent outputs'
	item_desc = 'unspent output'
	dump_fn_pfx = 'listunspent'
	prompt_fs = 'Total to spend, excluding fees: {} {}\n\n'
	prompt = """
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: toggle [D]ays/date, show [g]roup, show [m]mgen addr, r[e]draw
Actions: [q]uit view, [p]rint to file, pager [v]iew, [w]ide view, add [l]abel:
"""
	key_mappings = {
		't':'s_txid','a':'s_amt','d':'s_addr','A':'s_age','r':'d_reverse','M':'s_twmmid',
		'D':'d_days','g':'d_group','m':'d_mmid','e':'d_redraw',
		'q':'a_quit','p':'a_print','v':'a_view','w':'a_view_wide','l':'a_lbl_add' }
	col_adj = 38
	age_fmts = ('confs','block','days','date','date_time')
	age_fmts_date_dependent = ('days','date','date_time')
	age_fmts_interactive = ('confs','block','days','date')
	_age_fmt = 'confs'

	class MMGenTwOutputList(list,MMGenObject): pass

	class MMGenTwUnspentOutput(MMGenListItem):
		txid         = ListItemAttr('CoinTxID')
		vout         = ListItemAttr(int,typeconv=False)
		amt          = ImmutableAttr(lambda:g.proto.coin_amt,typeconv=False)
		amt2         = ListItemAttr(lambda:g.proto.coin_amt,typeconv=False)
		label        = ListItemAttr('TwComment',reassign_ok=True)
		twmmid       = ImmutableAttr('TwMMGenID')
		addr         = ImmutableAttr('CoinAddr')
		confs        = ImmutableAttr(int,typeconv=False)
		date         = ListItemAttr(int,typeconv=False,reassign_ok=True)
		scriptPubKey = ImmutableAttr('HexStr')
		skip         = ListItemAttr(str,typeconv=False,reassign_ok=True)

	wmsg = {
	'no_spendable_outputs': """
No spendable outputs found!  Import addresses with balances into your
watch-only wallet using '{}-addrimport' and then re-run this program.
""".strip().format(g.proj_name.lower())
	}

	async def __ainit__(self,minconf=1,addrs=[]):
		self.unspent      = self.MMGenTwOutputList()
		self.fmt_display  = ''
		self.fmt_print    = ''
		self.cols         = None
		self.reverse      = False
		self.group        = False
		self.show_mmid    = True
		self.minconf      = minconf
		self.addrs        = addrs
		self.sort_key     = 'age'
		self.disp_prec    = self.get_display_precision()

		self.wallet = await TrackingWallet(mode='w')

	@property
	def age_fmt(self):
		return self._age_fmt

	@age_fmt.setter
	def age_fmt(self,val):
		if val not in self.age_fmts:
			raise BadAgeFormat("'{}': invalid age format (must be one of {!r})".format(val,self.age_fmts))
		self._age_fmt = val

	def get_display_precision(self):
		return g.proto.coin_amt.max_prec

	@property
	def total(self):
		return sum(i.amt for i in self.unspent)

	async def get_unspent_rpc(self):
		# bitcoin-cli help listunspent:
		# Arguments:
		# 1. minconf        (numeric, optional, default=1) The minimum confirmations to filter
		# 2. maxconf        (numeric, optional, default=9999999) The maximum confirmations to filter
		# 3. addresses      (json array, optional, default=empty array) A json array of bitcoin addresses
		# 4. include_unsafe (boolean, optional, default=true) Include outputs that are not safe to spend
		# 5. query_options  (json object, optional) JSON with query options

		# for now, self.addrs is just an empty list for Bitcoin and friends
		add_args = (9999999,self.addrs) if self.addrs else ()
		return await g.rpc.call('listunspent',self.minconf,*add_args)

	async def get_unspent_data(self,sort_key=None,reverse_sort=False):
		if g.bogus_wallet_data: # for debugging purposes only
			us_rpc = eval(get_data_from_file(g.bogus_wallet_data)) # testing, so ok
		else:
			us_rpc = await self.get_unspent_rpc()

		if not us_rpc:
			die(0,self.wmsg['no_spendable_outputs'])

		tr_rpc = []
		lbl_id = ('account','label')['label_api' in g.rpc.caps]

		for o in us_rpc:
			if not lbl_id in o:
				continue # coinbase outputs have no account field
			l = get_tw_label(o[lbl_id])
			if l:
				o.update({
					'twmmid': l.mmid,
					'label':  l.comment,
					'amt':    g.proto.coin_amt(o['amount']),
					'addr':   CoinAddr(o['address']),
					'confs':  o['confirmations']
				})
				tr_rpc.append(o)

		self.unspent = self.MMGenTwOutputList(
						self.MMGenTwUnspentOutput(
							**{k:v for k,v in o.items() if k in dir(self.MMGenTwUnspentOutput)}
						) for o in tr_rpc)
		for u in self.unspent:
			if u.label == None: u.label = ''
		if not self.unspent:
			die(1,'No tracked {}s in tracking wallet!'.format(self.item_desc))

		self.do_sort(key=sort_key,reverse=reverse_sort)

	def do_sort(self,key=None,reverse=False):
		sort_funcs = {
			'addr':  lambda i: i.addr,
			'age':   lambda i: 0 - i.confs,
			'amt':   lambda i: i.amt,
			'txid':  lambda i: '{} {:04}'.format(i.txid,i.vout),
			'twmmid':  lambda i: i.twmmid.sort_key
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
		from .term import get_terminal_size
		while True:
			self.cols = g.terminal_width or get_terminal_size().width
			if self.cols >= g.min_screen_width: break
			m1 = 'Screen too narrow to display the tracking wallet\n'
			m2 = 'Please resize your screen to at least {} characters and hit ENTER '
			my_raw_input((m1+m2).format(g.min_screen_width))

	async def format_for_display(self):
		unsp = self.unspent
		if self.age_fmt in self.age_fmts_date_dependent:
			await _set_dates(unsp)
		self.set_term_columns()

		# allow for 7-digit confirmation nums
		col1_w = max(3,len(str(len(unsp)))+1) # num + ')'
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in unsp) or 12 # DEADBEEF:S:1
		max_acct_w = max(i.label.screen_width for i in unsp) + mmid_w + 1
		max_btcaddr_w = max(len(i.addr) for i in unsp)
		min_addr_w = self.cols - self.col_adj
		addr_w = min(max_btcaddr_w + (0,1+max_acct_w)[self.show_mmid],min_addr_w)
		acct_w = min(max_acct_w, max(24,addr_w-10))
		btaddr_w = addr_w - acct_w - 1
		label_w = acct_w - mmid_w - 1
		tx_w = min(self.txid_w,self.cols-addr_w-29-col1_w) # min=6 TODO
		txdots = ('','..')[tx_w < self.txid_w]

		for i in unsp: i.skip = ''
		if self.group and (self.sort_key in ('addr','txid','twmmid')):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				for k in ('addr','txid','twmmid'):
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = (k,'addr')[k=='twmmid']

		out  = [self.hdr_fmt.format(' '.join(self.sort_info()),g.dcoin,self.total.hl())]
		if g.chain != 'mainnet': out += ['Chain: '+green(g.chain.upper())]
		fs = {  'btc':   ' {n:%s} {t:%s} {v:2} {a} {A} {c:<}' % (col1_w,tx_w),
				'eth':   ' {n:%s} {a} {A}' % col1_w,
				'token': ' {n:%s} {a} {A} {A2}' % col1_w }[self.disp_type]
		fs_hdr = ' {n:%s} {t:%s} {a} {A} {c:<}' % (col1_w,tx_w) if self.disp_type == 'btc' else fs
		date_hdr = {
			'confs':     'Confs',
			'block':     'Block',
			'days':      'Age(d)',
			'date':      'Date',
			'date_time': 'Date',
		}
		out += [fs_hdr.format(
							n='Num',
							t='TXid'.ljust(tx_w - 2) + ' Vout',
							a='Address'.ljust(addr_w),
							A='Amt({})'.format(g.dcoin).ljust(self.disp_prec+5),
							A2=' Amt({})'.format(g.coin).ljust(self.disp_prec+4),
							c = date_hdr[self.age_fmt],
						).rstrip()]

		for n,i in enumerate(unsp):
			addr_dots = '|' + '.'*(addr_w-1)
			mmid_disp = MMGenID.fmtc('.'*mmid_w if i.skip=='addr'
				else i.twmmid if i.twmmid.type=='mmgen'
					else 'Non-{}'.format(g.proj_name),width=mmid_w,color=True)
			if self.show_mmid:
				addr_out = '{} {}'.format(
					type(i.addr).fmtc(addr_dots,width=btaddr_w,color=True) if i.skip == 'addr' \
							else i.addr.fmt(width=btaddr_w,color=True),
					'{} {}'.format(mmid_disp,i.label.fmt(width=label_w,color=True) \
							if label_w > 0 else ''))
			else:
				addr_out = type(i.addr).fmtc(addr_dots,width=addr_w,color=True) \
					if i.skip=='addr' else i.addr.fmt(width=addr_w,color=True)

			out.append(fs.format(   n=str(n+1)+')',
									t='' if not i.txid else \
										' ' * (tx_w-4) + '|...' if i.skip == 'txid' \
											else i.txid[:tx_w-len(txdots)] + txdots,
									v=i.vout,
									a=addr_out,
									A=i.amt.fmt(color=True,prec=self.disp_prec),
									A2=(i.amt2.fmt(color=True,prec=self.disp_prec) if i.amt2 is not None else ''),
									c=self.age_disp(i,self.age_fmt),
									).rstrip())

		self.fmt_display = '\n'.join(out) + '\n'
		return self.fmt_display

	async def format_for_printing(self,color=False,show_confs=True):
		if self.age_fmt in self.age_fmts_date_dependent:
			await _set_dates(self.unspent)
		addr_w = max(len(i.addr) for i in self.unspent)
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in self.unspent) or 12 # DEADBEEF:S:1
		amt_w = g.proto.coin_amt.max_prec + 5
		cfs = '{c:<8} ' if show_confs else ''
		fs = {  'btc': (' {n:4} {t:%s} {a} {m} {A:%s} ' + cfs + '{b:<8} {D:<19} {l}') % (self.txid_w+3,amt_w),
				'eth':   ' {n:4} {a} {m} {A:%s} {l}' % amt_w,
				'token': ' {n:4} {a} {m} {A:%s} {A2:%s} {l}' % (amt_w,amt_w)
				}[self.disp_type]
		out = [fs.format(   n='Num',
							t='Tx ID,Vout',
							a='Address'.ljust(addr_w),
							m='MMGen ID'.ljust(mmid_w),
							A='Amount({})'.format(g.dcoin),
							A2='Amount({})'.format(g.coin),
							c='Confs',  # skipped for eth
							b='Block',  # skipped for eth
							D='Date',
							l='Label')]

		max_lbl_len = max([len(i.label) for i in self.unspent if i.label] or [2])
		for n,i in enumerate(self.unspent):
			addr = '|'+'.' * addr_w if i.skip == 'addr' and self.group else i.addr.fmt(color=color,width=addr_w)
			out.append(fs.format(
						n=str(n+1)+')',
						t='{},{}'.format('|'+'.'*63 if i.skip == 'txid' and self.group else i.txid,i.vout),
						a=addr,
						m=MMGenID.fmtc(i.twmmid if i.twmmid.type=='mmgen'
							else 'Non-{}'.format(g.proj_name),width=mmid_w,color=color),
						A=i.amt.fmt(color=color),
						A2=(i.amt2.fmt(color=color) if i.amt2 is not None else ''),
						c=i.confs,
						b=g.rpc.blockcount - (i.confs - 1),
						D=self.age_disp(i,'date_time'),
						l=i.label.hl(color=color) if i.label else
							TwComment.fmtc('',color=color,nullrepl='-',width=max_lbl_len)).rstrip())

		fs = '{} (block #{}, {} UTC)\nSort order: {}\n{}\n\nTotal {}: {}\n'
		self.fmt_print = fs.format(
				capfirst(self.desc),
				g.rpc.blockcount,
				make_timestr(g.rpc.cur_date),
				' '.join(self.sort_info(include_group=False)),
				'\n'.join(out),
				g.dcoin,
				self.total.hl(color=color))
		return self.fmt_print

	def display_total(self):
		fs = '\nTotal unspent: {} {} ({} output%s)' % suf(self.unspent)
		msg(fs.format(self.total.hl(),g.dcoin,len(self.unspent)))

	def get_idx_from_user(self,action):
		msg('')
		while True:
			ret = my_raw_input('Enter {} number (or RETURN to return to main menu): '.format(self.item_desc))
			if ret == '': return (None,None) if action == 'a_lbl_add' else None
			n = AddrIdx(ret,on_fail='silent')
			if not n or n < 1 or n > len(self.unspent):
				msg('Choice must be a single number between 1 and {}'.format(len(self.unspent)))
			else:
				if action == 'a_lbl_add':
					while True:
						s = my_raw_input("Enter label text (or 'q' to return to main menu): ")
						if s == 'q':
							return None,None
						elif s == '':
							fs = "Removing label for {} #{}.  Is this what you want?"
							if keypress_confirm(fs.format(self.item_desc,n)):
								return n,s
						elif s:
							if TwComment(s,on_fail='return'):
								return n,s
				else:
					if action == 'a_addr_delete':
						fs = "Removing {} #{} from tracking wallet.  Is this what you want?"
					elif action == 'a_balance_refresh':
						fs = "Refreshing tracking wallet {} #{}.  Is this what you want?"
					if keypress_confirm(fs.format(self.item_desc,n)):
						return n

	async def view_and_sort(self,tx):
		from .term import get_char
		prompt = self.prompt.strip() + '\b'
		no_output,oneshot_msg = False,None
		while True:
			msg_r('' if no_output else '\n\n' if opt.no_blank else CUR_HOME+ERASE_ALL)
			reply = get_char(
				'' if no_output else await self.format_for_display()+'\n'+(oneshot_msg or '')+prompt,
				immed_chars=''.join(self.key_mappings.keys())
			)
			no_output = False
			oneshot_msg = '' if oneshot_msg else None # tristate, saves previous state
			if reply not in self.key_mappings:
				msg_r('\ninvalid keypress ')
				time.sleep(0.5)
				continue

			action = self.key_mappings[reply]
			if action[:2] == 's_':
				self.do_sort(action[2:])
				if action == 's_twmmid': self.show_mmid = True
			elif action == 'd_days':
				af = self.age_fmts_interactive
				self.age_fmt = af[(af.index(self.age_fmt) + 1) % len(af)]
			elif action == 'd_mmid': self.show_mmid = not self.show_mmid
			elif action == 'd_group':
				if self.can_group:
					self.group = not self.group
			elif action == 'd_redraw': pass
			elif action == 'd_reverse': self.unspent.reverse(); self.reverse = not self.reverse
			elif action == 'a_quit': msg(''); return self.unspent
			elif action == 'a_balance_refresh':
				idx = self.get_idx_from_user(action)
				if idx:
					e = self.unspent[idx-1]
					bal = await self.wallet.get_balance(e.addr,force_rpc=True)
					await self.get_unspent_data()
					oneshot_msg = yellow('{} balance for account #{} refreshed\n\n'.format(g.dcoin,idx))
			elif action == 'a_lbl_add':
				idx,lbl = self.get_idx_from_user(action)
				if idx:
					e = self.unspent[idx-1]
					if await self.wallet.add_label(e.twmmid,lbl,addr=e.addr):
						await self.get_unspent_data()
						a = 'added to' if lbl else 'removed from'
						oneshot_msg = yellow("Label {} {} #{}\n\n".format(a,self.item_desc,idx))
					else:
						oneshot_msg = red('Label could not be added\n\n')
			elif action == 'a_addr_delete':
				idx = self.get_idx_from_user(action)
				if idx:
					e = self.unspent[idx-1]
					if await self.wallet.remove_address(e.addr):
						await self.get_unspent_data()
						oneshot_msg = yellow("{} #{} removed\n\n".format(capfirst(self.item_desc),idx))
					else:
						oneshot_msg = red('Address could not be removed\n\n')
			elif action == 'a_print':
				of = '{}-{}[{}].out'.format(self.dump_fn_pfx,g.dcoin,
										','.join(self.sort_info(include_group=False)).lower())
				msg('')
				try:
					write_data_to_file(of,await self.format_for_printing(),desc='{} listing'.format(self.desc))
				except UserNonConfirmation as e:
					oneshot_msg = red("File '{}' not overwritten by user request\n\n".format(of))
				else:
					oneshot_msg = yellow("Data written to '{}'\n\n".format(of))
			elif action in ('a_view','a_view_wide'):
				do_pager(self.fmt_display if action == 'a_view' else await self.format_for_printing(color=True))
				if g.platform == 'linux' and oneshot_msg == None:
					msg_r(CUR_RIGHT(len(prompt.split('\n')[-1])-2))
					no_output = True

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs
		elif age_fmt == 'block':
			return g.rpc.blockcount - (o.confs - 1)
		else:
			return _date_formatter[age_fmt](o.date)

class TwAddrList(MMGenDict,metaclass=aInitMeta):
	has_age = True
	age_fmts = TwUnspentOutputs.age_fmts
	age_disp = TwUnspentOutputs.age_disp

	def __new__(cls,*args,**kwargs):
		return MMGenDict.__new__(altcoin_subclass(cls,'tw','TwAddrList'),*args,**kwargs)

	def __init__(self,*args,**kwargs):
		pass

	async def __ainit__(self,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		def check_dup_mmid(acct_labels):
			mmid_prev,err = None,False
			for mmid in sorted(a.mmid for a in acct_labels if a):
				if mmid == mmid_prev:
					err = True
					msg('Duplicate MMGen ID ({}) discovered in tracking wallet!\n'.format(mmid))
				mmid_prev = mmid
			if err: rdie(3,'Tracking wallet is corrupted!')

		def check_addr_array_lens(acct_pairs):
			err = False
			for label,addrs in acct_pairs:
				if not label: continue
				if len(addrs) != 1:
					err = True
					if len(addrs) == 0:
						msg("Label '{}': has no associated address!".format(label))
					else:
						msg("'{}': more than one {} address in account!".format(addrs,g.coin))
			if err: rdie(3,'Tracking wallet is corrupted!')

		self.total = g.proto.coin_amt('0')

		lbl_id = ('account','label')['label_api' in g.rpc.caps]
		for d in await g.rpc.call('listunspent',0):
			if not lbl_id in d: continue  # skip coinbase outputs with missing account
			if d['confirmations'] < minconf: continue
			label = get_tw_label(d[lbl_id])
			if label:
				lm = label.mmid
				if usr_addr_list and (lm not in usr_addr_list):
					continue
				if lm in self:
					if self[lm]['addr'] != d['address']:
						die(2,'duplicate {} address ({}) for this MMGen address! ({})'.format(
								g.coin,d['address'],self[lm]['addr']))
				else:
					lm.confs = d['confirmations']
					lm.txid = d['txid']
					lm.date = None
					self[lm] = {'amt': g.proto.coin_amt('0'),
								'lbl': label,
								'addr': CoinAddr(d['address'])}
				self[lm]['amt'] += d['amount']
				self.total += d['amount']

		# We use listaccounts only for empty addresses, as it shows false positive balances
		if showempty or all_labels:
			# for compatibility with old mmids, must use raw RPC rather than native data for matching
			# args: minconf,watchonly, MUST use keys() so we get list, not dict
			if 'label_api' in g.rpc.caps:
				acct_list = await g.rpc.call('listlabels')
				aa = await g.rpc.batch_call('getaddressesbylabel',[(k,) for k in acct_list])
				acct_addrs = [list(a.keys()) for a in aa]
			else:
				acct_list = list((await g.rpc.call('listaccounts',0,True)).keys()) # raw list, no 'L'
				acct_addrs = await g.rpc.batch_call('getaddressesbyaccount',[(a,) for a in acct_list]) # use raw list here
			acct_labels = MMGenList([get_tw_label(a) for a in acct_list])
			check_dup_mmid(acct_labels)
			assert len(acct_list) == len(acct_addrs),(
				'listaccounts() and getaddressesbyaccount() not equal in length')
			addr_pairs = list(zip(acct_labels,acct_addrs))
			check_addr_array_lens(addr_pairs)
			for label,addr_arr in addr_pairs:
				if not label: continue
				if all_labels and not showempty and not label.comment: continue
				if usr_addr_list and (label.mmid not in usr_addr_list): continue
				if label.mmid not in self:
					self[label.mmid] = { 'amt':g.proto.coin_amt('0'), 'lbl':label, 'addr':'' }
					if showbtcaddrs:
						self[label.mmid]['addr'] = CoinAddr(addr_arr[0])

	def raw_list(self):
		return [((k if k.type == 'mmgen' else 'Non-MMGen'),self[k]['addr'],self[k]['amt']) for k in self]

	def coinaddr_list(self): return [self[k]['addr'] for k in self]

	async def format(self,showbtcaddrs,sort,show_age,age_fmt):
		if not self.has_age:
			show_age = False
		if age_fmt not in self.age_fmts:
			raise BadAgeFormat("'{}': invalid age format (must be one of {!r})".format(age_fmt,self.age_fmts))
		out = ['Chain: '+green(g.chain.upper())] if g.chain != 'mainnet' else []
		fs = '{mid}' + ('',' {addr}')[showbtcaddrs] + ' {cmt} {amt}' + ('',' {age}')[show_age]
		mmaddrs = [k for k in self.keys() if k.type == 'mmgen']
		max_mmid_len = max(len(k) for k in mmaddrs) + 2 if mmaddrs else 10
		max_cmt_width = max(max(v['lbl'].comment.screen_width for v in self.values()),7)
		addr_width = max(len(self[mmid]['addr']) for mmid in self)

		# fp: fractional part
		max_fp_len = max([len(a.split('.')[1]) for a in [str(v['amt']) for v in self.values()] if '.' in a] or [1])
		out += [fs.format(
				mid=MMGenID.fmtc('MMGenID',width=max_mmid_len),
				addr=(CoinAddr.fmtc('ADDRESS',width=addr_width) if showbtcaddrs else None),
				cmt=TwComment.fmtc('COMMENT',width=max_cmt_width+1),
				amt='BALANCE'.ljust(max_fp_len+4),
				age=age_fmt.upper(),
				).rstrip()]

		def sort_algo(j):
			if sort and 'age' in sort:
				return '{}_{:>012}_{}'.format(
					j.obj.rsplit(':',1)[0],
					# Hack, but OK for the foreseeable future:
					(1000000000-(j.confs or 0) if hasattr(j,'confs') else 0),
					j.sort_key)
			else:
				return j.sort_key

		al_id_save = None
		mmids = sorted(self,key=sort_algo,reverse=bool(sort and 'reverse' in sort))
		if show_age:
			await _set_dates([o for o in mmids if hasattr(o,'confs')])
		for mmid in mmids:
			if mmid.type == 'mmgen':
				if al_id_save and al_id_save != mmid.obj.al_id:
					out.append('')
				al_id_save = mmid.obj.al_id
				mmid_disp = mmid
			else:
				if al_id_save:
					out.append('')
					al_id_save = None
				mmid_disp = 'Non-MMGen'
			e = self[mmid]
			out.append(fs.format(
				mid=MMGenID.fmtc(mmid_disp,width=max_mmid_len,color=True),
				addr=(e['addr'].fmt(color=True,width=addr_width) if showbtcaddrs else None),
				cmt=e['lbl'].comment.fmt(width=max_cmt_width,color=True,nullrepl='-'),
				amt=e['amt'].fmt('4.{}'.format(max(max_fp_len,3)),color=True),
				age=self.age_disp(mmid,age_fmt) if show_age and hasattr(mmid,'confs') else '-'
				).rstrip())

		return '\n'.join(out + ['\nTOTAL: {} {}'.format(self.total.hl(color=True),g.dcoin)])

class TrackingWallet(MMGenObject,metaclass=aInitMeta):

	caps = ('rescan','batch')
	data_key = 'addresses'
	use_tw_file = False
	aggressive_sync = False
	importing = False

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tw','TrackingWallet'))

	async def __ainit__(self,mode='r'):

		assert mode in ('r','w','i'), "{!r}: wallet mode must be 'r','w' or 'i'".format(mode)
		if mode == 'i':
			self.importing = True
			mode = 'w'

		if g.debug:
			print_stack_trace('TW INIT {!r} {!r}'.format(mode,self))

		self.mode = mode
		self.desc = self.base_desc = '{} tracking wallet'.format(capfirst(g.proto.name))

		if self.use_tw_file:
			self.init_from_wallet_file()
		else:
			self.init_empty()

		if self.data['coin'] != g.coin:
			m = 'Tracking wallet coin ({}) does not match current coin ({})!'
			raise WalletFileError(m.format(self.data['coin'],g.coin))

		self.conv_types(self.data[self.data_key])
		self.cur_balances = {} # cache balances to prevent repeated lookups per program invocation

	def init_empty(self):
		self.data = { 'coin': g.coin, 'addresses': {} }

	def init_from_wallet_file(self):

		tw_dir = (
			os.path.join(g.data_dir,g.proto.data_subdir) if g.coin == 'BTC' else
			os.path.join(g.data_dir_root,'altcoins',g.coin.lower(),g.proto.data_subdir) )
		self.tw_fn = os.path.join(tw_dir,'tracking-wallet.json')

		check_or_create_dir(tw_dir)

		try:
			self.orig_data = get_data_from_file(self.tw_fn,quiet=True)
			self.data = json.loads(self.orig_data)
		except:
			try: os.stat(self.tw_fn)
			except:
				self.orig_data = ''
				self.init_empty()
				self.force_write()
			else:
				m = "File '{}' exists but does not contain valid json data"
				raise WalletFileError(m.format(self.tw_fn))
		else:
			self.upgrade_wallet_maybe()

		# ensure that wallet file is written when user exits via KeyboardInterrupt:
		if self.mode == 'w':
			import atexit
			def del_tw(tw):
				dmsg('Running exit handler del_tw() for {!r}'.format(tw))
				del tw
			atexit.register(del_tw,self)

	def __del__(self):
		"""
		TrackingWallet instances opened in write or import mode must be explicitly destroyed
		with 'del tw', 'del twuo.wallet' and the like to ensure the instance is deleted and
		wallet is written before global vars are destroyed by the interpreter at shutdown.

		Not that this code can only be debugged by examining the program output, as exceptions
		are ignored within __del__():

			/usr/share/doc/python3.6-doc/html/reference/datamodel.html#object.__del__

		Since no exceptions are raised, errors will not be caught by the test suite.
		"""
		if g.debug:
			print_stack_trace('TW DEL {!r}'.format(self))

		if self.mode == 'w':
			self.write()
		elif g.debug:
			msg('read-only wallet, doing nothing')

	def upgrade_wallet_maybe(self):
		pass

	@staticmethod
	def conv_types(ad):
		for k,v in ad.items():
			if k not in ('params','coin'):
				v['mmid'] = TwMMGenID(v['mmid'],on_fail='raise')
				v['comment'] = TwComment(v['comment'],on_fail='raise')

	@property
	def data_root(self):
		return self.data[self.data_key]

	@property
	def data_root_desc(self):
		return self.data_key

	def cache_balance(self,addr,bal,session_cache,data_root,force=False):
		if force or addr not in session_cache:
			session_cache[addr] = str(bal)
			if addr in data_root:
				data_root[addr]['balance'] = str(bal)
				if self.aggressive_sync:
					self.write()

	def get_cached_balance(self,addr,session_cache,data_root):
		if addr in session_cache:
			return g.proto.coin_amt(session_cache[addr])
		if not g.use_cached_balances:
			return None
		if addr in data_root and 'balance' in data_root[addr]:
			return g.proto.coin_amt(data_root[addr]['balance'])

	async def get_balance(self,addr,force_rpc=False):
		ret = None if force_rpc else self.get_cached_balance(addr,self.cur_balances,self.data_root)
		if ret == None:
			ret = await self.rpc_get_balance(addr)
			self.cache_balance(addr,ret,self.cur_balances,self.data_root)
		return ret

	async def rpc_get_balance(self,addr):
		raise NotImplementedError('not implemented')

	@property
	def sorted_list(self):
		return sorted(
			[ { 'addr':x[0],
				'mmid':x[1]['mmid'],
				'comment':x[1]['comment'] }
					for x in self.data_root.items() if x[0] not in ('params','coin') ],
			key=lambda x: x['mmid'].sort_key+x['addr'] )

	@property
	def mmid_ordered_dict(self):
		return dict((x['mmid'],{'addr':x['addr'],'comment':x['comment']}) for x in self.sorted_list)

	@write_mode
	async def import_address(self,addr,label,rescan):
		return await g.rpc.call('importaddress',addr,label,rescan,timeout=(False,3600)[rescan])

	@write_mode
	def batch_import_address(self,arg_list):
		return g.rpc.batch_call('importaddress',arg_list)

	def force_write(self):
		mode_save = self.mode
		self.mode = 'w'
		self.write()
		self.mode = mode_save

	@write_mode
	def write_changed(self,data):
		write_data_to_file(
			self.tw_fn,data,
			desc='{} data'.format(self.base_desc),
			ask_overwrite=False,ignore_opt_outdir=True,quiet=True,
			check_data=True,cmp_data=self.orig_data)
		self.orig_data = data

	def write(self): # use 'check_data' to check wallet hasn't been altered by another program
		if not self.use_tw_file:
			dmsg("'use_tw_file' is False, doing nothing")
			return
		dmsg('write(): checking if {} data has changed'.format(self.desc))
		wdata = json.dumps(self.data)

		if self.orig_data != wdata:
			if g.debug:
				print_stack_trace('TW DATA CHANGED {!r}'.format(self))
				print_diff(self.orig_data,wdata,from_json=True)
			self.write_changed(wdata)
		elif g.debug:
			msg('Data is unchanged\n')

	async def is_in_wallet(self,addr):
		return addr in (await TwAddrList([],0,True,True,True,wallet=self)).coinaddr_list()

	@write_mode
	async def set_label(self,coinaddr,lbl):
		# bitcoin-abc 'setlabel' RPC is broken, so use old 'importaddress' method to set label
		# broken behavior: new label is set OK, but old label gets attached to another address
		if 'label_api' in g.rpc.caps and g.coin != 'BCH':
			args = ('setlabel',coinaddr,lbl)
		else:
			# NOTE: this works because importaddress() removes the old account before
			# associating the new account with the address.
			# RPC args: addr,label,rescan[=true],p2sh[=none]
			args = ('importaddress',coinaddr,lbl,False)

		try:
			return await g.rpc.call(*args)
		except Exception as e:
			rmsg(e.args[0])
			return False

	# returns on failure
	@write_mode
	async def add_label(self,arg1,label='',addr=None,silent=False,on_fail='return'):
		from .tx import is_mmgen_id,is_coin_addr
		mmaddr,coinaddr = None,None
		if is_coin_addr(addr or arg1):
			coinaddr = CoinAddr(addr or arg1,on_fail='return')
		if is_mmgen_id(arg1):
			mmaddr = TwMMGenID(arg1)

		if mmaddr and not coinaddr:
			from .addr import TwAddrData
			coinaddr = (await TwAddrData()).mmaddr2coinaddr(mmaddr)

		try:
			if not is_mmgen_id(arg1):
				assert coinaddr,"Invalid coin address for this chain: {}".format(arg1)
			assert coinaddr,"{pn} address '{ma}' not found in tracking wallet"
			assert await self.is_in_wallet(coinaddr),"Address '{ca}' not found in tracking wallet"
		except Exception as e:
			msg(e.args[0].format(pn=g.proj_name,ma=mmaddr,ca=coinaddr))
			return False

		# Allow for the possibility that BTC addr of MMGen addr was entered.
		# Do reverse lookup, so that MMGen addr will not be marked as non-MMGen.
		if not mmaddr:
			from .addr import TwAddrData
			mmaddr = (await TwAddrData()).coinaddr2mmaddr(coinaddr)

		if not mmaddr:
			mmaddr = '{}:{}'.format(g.proto.base_coin.lower(),coinaddr)

		mmaddr = TwMMGenID(mmaddr)

		cmt = TwComment(label,on_fail=on_fail)
		if cmt in (False,None):
			return False

		lbl = TwLabel(mmaddr + ('',' '+cmt)[bool(cmt)],on_fail=on_fail)

		if await self.set_label(coinaddr,lbl) == False:
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

	@write_mode
	async def remove_label(self,mmaddr):
		await self.add_label(mmaddr,'')

	@write_mode
	async def remove_address(self,addr):
		raise NotImplementedError('address removal not implemented for coin {}'.format(g.coin))

class TwGetBalance(MMGenObject,metaclass=aInitMeta):

	fs = '{w:13} {u:<16} {p:<16} {c}\n'

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tw','TwGetBalance'))

	async def __ainit__(self,minconf,quiet):

		self.minconf = minconf
		self.quiet = quiet
		self.data = {k:[g.proto.coin_amt('0')] * 4 for k in ('TOTAL','Non-MMGen','Non-wallet')}
		await self.create_data()

	async def create_data(self):
		# 0: unconfirmed, 1: below minconf, 2: confirmed, 3: spendable (privkey in wallet)
		lbl_id = ('account','label')['label_api' in g.rpc.caps]
		for d in await g.rpc.call('listunspent',0):
			lbl = get_tw_label(d[lbl_id])
			if lbl:
				if lbl.mmid.type == 'mmgen':
					key = lbl.mmid.obj.sid
					if key not in self.data:
						self.data[key] = [g.proto.coin_amt('0')] * 4
				else:
					key = 'Non-MMGen'
			else:
				lbl,key = None,'Non-wallet'

			if not d['confirmations']:
				self.data['TOTAL'][0] += d['amount']
				self.data[key][0] += d['amount']

			conf_level = (1,2)[d['confirmations'] >= self.minconf]

			self.data['TOTAL'][conf_level] += d['amount']
			self.data[key][conf_level] += d['amount']

			if d['spendable']:
				self.data[key][3] += d['amount']

	def format(self):
		if self.quiet:
			o = str(self.data['TOTAL'][2] if self.data else 0) + '\n'
		else:
			o = self.fs.format( w='Wallet',
								u=' Unconfirmed',
								p=' <{} confirms'.format(self.minconf),
								c=' >={} confirms'.format(self.minconf))
			for key in sorted(self.data):
				if not any(self.data[key]): continue
				o += self.fs.format(**dict(zip(
							('w','u','p','c'),
							[key+':'] + [a.fmt(color=True,suf=' '+g.dcoin) for a in self.data[key]]
							)))

		for key,vals in list(self.data.items()):
			if key == 'TOTAL': continue
			if vals[3]:
				o += red('Warning: this wallet contains PRIVATE KEYS for {} outputs!\n'.format(key))
		return o.rstrip()
