#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
tw.addresses: Tracking wallet listaddresses class for the MMGen suite
"""

from ..util import suf
from ..objmethods import MMGenObject
from ..obj import MMGenListItem,ImmutableAttr,ListItemAttr,TwComment,NonNegativeInt
from ..addr import CoinAddr,MMGenID
from ..color import red,green
from .view import TwView
from .shared import TwMMGenID

class TwAddresses(TwView):

	hdr_lbl = 'tracking wallet addresses'
	desc = 'address list'
	item_desc = 'address'
	sort_key = 'twmmid'
	update_widths_on_age_toggle = True
	print_output_types = ('detail',)
	filters = ('showempty','showused','all_labels')
	showcoinaddrs = True
	showempty = True
	showused = 1 # tristate: 0:no, 1:yes, 2:all
	all_labels = False
	no_data_errmsg = 'No addresses in tracking wallet!'
	mod_subpath = 'tw.addresses'

	class display_type(TwView.display_type):

		class squeezed(TwView.display_type.squeezed):
			cols = ('num','mmid','used','addr','comment','amt','date')

		class detail(TwView.display_type.detail):
			cols = ('num','mmid','used','addr','comment','amt','block','date_time')

	class TwAddress(MMGenListItem):
		valid_attrs = {'twmmid','addr','al_id','confs','comment','amt','recvd','date','skip'}
		invalid_attrs = {'proto'}

		twmmid  = ImmutableAttr(TwMMGenID,include_proto=True) # contains confs,txid(unused),date(unused),al_id
		addr    = ImmutableAttr(CoinAddr,include_proto=True)
		al_id   = ImmutableAttr(str)                          # set to '_' for non-MMGen addresses
		confs   = ImmutableAttr(int,typeconv=False)
		comment = ListItemAttr(TwComment,reassign_ok=True)
		amt     = ImmutableAttr(None)
		recvd   = ImmutableAttr(None)
		date    = ListItemAttr(int,typeconv=False,reassign_ok=True)
		skip    = ListItemAttr(str,typeconv=False,reassign_ok=True)

		def __init__(self,proto,**kwargs):
			self.__dict__['proto'] = proto
			MMGenListItem.__init__(self,**kwargs)

		class conv_funcs:
			def amt(self,value):
				return self.proto.coin_amt(value)
			def recvd(self,value):
				return self.proto.coin_amt(value)

	@property
	def coinaddr_list(self):
		return [d.addr for d in self.data]

	async def __init__(self,proto,minconf=1,mmgen_addrs='',get_data=False):

		await super().__init__(proto)

		self.minconf = NonNegativeInt(minconf)

		if mmgen_addrs:
			a = mmgen_addrs.rsplit(':',1)
			if len(a) != 2:
				from ..util import die
				die(1,
					f'{mmgen_addrs}: invalid address list argument ' +
					'(must be in form <seed ID>:[<type>:]<idx list>)' )
			from ..addrlist import AddrIdxList
			self.usr_addr_list = [MMGenID(self.proto,f'{a[0]}:{i}') for i in AddrIdxList(a[1])]
		else:
			self.usr_addr_list = []

		if get_data:
			await self.get_data()

	@property
	def no_rpcdata_errmsg(self):
		return 'No addresses {}found!'.format(
			f'with {self.minconf} confirmations ' if self.minconf else '')

	async def gen_data(self,rpc_data,lbl_id):
		return (
			self.TwAddress(
					self.proto,
					twmmid  = twmmid,
					addr    = data['addr'],
					al_id   = getattr(twmmid.obj,'al_id','_'),
					confs   = data['confs'],
					comment = data['lbl'].comment,
					amt     = data['amt'],
					recvd   = data['recvd'],
					date    = 0,
					skip    = '' )
				for twmmid,data in rpc_data.items()
		)

	def filter_data(self):
		if self.usr_addr_list:
			return (d for d in self.data if d.twmmid.obj in self.usr_addr_list)
		else:
			return (d for d in self.data if
				(self.all_labels and d.comment) or
				(self.showused == 2 and d.recvd) or
				(not (d.recvd and not self.showused) and (d.amt or self.showempty))
			)

	def get_column_widths(self,data,wide=False):

		return self.compute_column_widths(
			widths = { # fixed cols
				'num':  max(2,len(str(len(data)))+1),
				'mmid': max(len(d.twmmid.disp) for d in data),
				'used': 4,
				'amt':  self.amt_widths['amt'],
				'date': self.age_w if self.has_age else 0,
				'block': self.age_col_params['block'][0] if wide and self.has_age else 0,
				'date_time': self.age_col_params['date_time'][0] if wide and self.has_age else 0,
				'spc':  7, # 6 spaces between cols + 1 leading space in fs
			},
			maxws = { # expandable cols
				'addr':    max(len(d.addr) for d in data) if self.showcoinaddrs else 0,
				'comment': max(d.comment.screen_width for d in data),
			},
			minws = {
				'addr': 12 if self.showcoinaddrs else 0,
				'comment': len('Comment'),
			},
			maxws_nice = {'addr': 18},
			wide = wide,
		)

	def subheader(self,color):
		if self.minconf:
			return f'Displaying balances with at least {self.minconf} confirmation{suf(self.minconf)}\n'
		else:
			return ''

	def gen_squeezed_display(self,data,cw,hdr_fs,fs,color):

		yield hdr_fs.format(
			n  = '',
			m  = 'MMGenID',
			u  = 'Used',
			a  = 'Address',
			c  = 'Comment',
			A  = 'Balance',
			d  = self.age_hdr )

		yes,no = (red('Yes '),green('No  ')) if color else ('Yes ','No  ')
		id_save = data[0].al_id

		for n,d in enumerate(data,1):
			if id_save != d.al_id:
				id_save = d.al_id
				yield ''
			yield fs.format(
				n = str(n) + ')',
				m = d.twmmid.fmt( width=cw.mmid, color=color ),
				u = yes if d.recvd else no,
				a = d.addr.fmt( color=color, width=cw.addr ),
				c = d.comment.fmt( width=cw.comment, color=color, nullrepl='-' ),
				A = d.amt.fmt( color=color, iwidth=cw.iwidth, prec=self.disp_prec ),
				d = self.age_disp( d, self.age_fmt )
			)

	def gen_detail_display(self,data,cw,hdr_fs,fs,color):

		yield hdr_fs.format(
			n  = '',
			m  = 'MMGenID',
			u  = 'Used',
			a  = 'Address',
			c  = 'Comment',
			A  = 'Balance',
			b  = 'Block',
			D  = 'Date/Time' )

		yes,no = (red('Yes '),green('No  ')) if color else ('Yes ','No  ')
		id_save = data[0].al_id

		for n,d in enumerate(data,1):
			if id_save != d.al_id:
				id_save = d.al_id
				yield ''
			yield fs.format(
				n = str(n) + ')',
				m = d.twmmid.fmt( width=cw.mmid, color=color ),
				u = yes if d.recvd else no,
				a = d.addr.fmt( color=color, width=cw.addr ),
				c = d.comment.fmt( width=cw.comment, color=color, nullrepl='-' ),
				A = d.amt.fmt( color=color, iwidth=cw.iwidth, prec=self.disp_prec ),
				b = self.age_disp( d, 'block' ),
				D = self.age_disp( d, 'date_time' ))

	async def set_dates(self,addrs):
		if not self.dates_set:
			bc = self.rpc.blockcount + 1
			caddrs = [addr for addr in addrs if addr.confs]
			hashes = await self.rpc.gathered_call('getblockhash',[(n,) for n in [bc - a.confs for a in caddrs]])
			dates = [d['time'] for d in await self.rpc.gathered_call('getblockheader',[(h,) for h in hashes])]
			for idx,addr in enumerate(caddrs):
				addr.date = dates[idx]
			self.dates_set = True

	sort_disp = {
		'age': 'AddrListID+Age',
		'amt': 'AddrListID+Amt',
		'twmmid': 'MMGenID',
	}

	sort_funcs = {
		'age': lambda d: '{}_{}_{}'.format(
			d.al_id,
			# Hack, but OK for the foreseeable future:
			('{:>012}'.format(1_000_000_000 - d.confs) if d.confs else '_'),
			d.twmmid.sort_key),
		'amt': lambda d: '{}_{}'.format(d.al_id,d.amt),
		'twmmid': lambda d: d.twmmid.sort_key,
	}

	@property
	def dump_fn_pfx(self):
		return 'listaddresses' + (f'-minconf-{self.minconf}' if self.minconf else '')

	def is_used(self,coinaddr):
		for e in self.data:
			if e.addr == coinaddr:
				return bool(e.recvd)
		else: # addr not in tracking wallet
			return None

	def get_change_address(self,al_id):
		"""
		Get lowest-indexed unused address in tracking wallet for requested AddrListID.
		Return values on failure:
		    None:  no addresses in wallet with requested AddrListID
		    False: no unused addresses in wallet with requested AddrListID
		"""

		def get_start():
			"""
			bisecting algorithm to find first entry with requested al_id

			Since 'btc' > 'F' and pre_target sorts below the first twmmid of the al_id
			stringwise, we can just search on raw twmmids.
			"""
			pre_target = al_id + ':0'
			bot = 0
			top = len(data) - 1
			n = top >> 1

			while True:

				if bot == top:
					return bot if data[bot].al_id == al_id else None

				if data[n].twmmid < pre_target:
					bot = n + 1
				else:
					top = n

				n = (top + bot) >> 1

		self.reverse = False
		self.do_sort('twmmid')

		data = self.data
		start = get_start()

		if start is not None:
			for d in data[start:]:
				if d.al_id == al_id:
					if not d.recvd:
						return d
				else:
					return False

	class action(TwView.action):

		def s_amt(self,parent):
			parent.do_sort('amt')

		def d_showempty(self,parent):
			parent.showempty = not parent.showempty

		def d_showused(self,parent):
			parent.showused = (parent.showused + 1) % 3

		def d_all_labels(self,parent):
			parent.all_labels = not parent.all_labels
