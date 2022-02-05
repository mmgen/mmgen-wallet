#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
twctl: Tracking wallet control class for the MMGen suite
"""

from .globalvars import g
from .util import msg,dmsg,write_mode,base_proto_subclass,die
from .base_obj import AsyncInit
from .objmethods import MMGenObject
from .obj import TwComment,get_obj
from .addr import CoinAddr,is_mmgen_id,is_coin_addr
from .rpc import rpc_init
from .tw import TwMMGenID,TwLabel

class TrackingWallet(MMGenObject,metaclass=AsyncInit):

	caps = ('rescan','batch')
	data_key = 'addresses'
	use_tw_file = False
	aggressive_sync = False
	importing = False

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(base_proto_subclass(cls,proto,'twctl'))

	async def __init__(self,proto,mode='r',token_addr=None):

		assert mode in ('r','w','i'), f"{mode!r}: wallet mode must be 'r','w' or 'i'"
		if mode == 'i':
			self.importing = True
			mode = 'w'

		if g.debug:
			print_stack_trace(f'TW INIT {mode!r} {self!r}')

		self.rpc = await rpc_init(proto) # TODO: create on demand - only certain ops require RPC
		self.proto = proto
		self.mode = mode
		self.desc = self.base_desc = f'{self.proto.name} tracking wallet'

		if self.use_tw_file:
			self.init_from_wallet_file()
		else:
			self.init_empty()

		if self.data['coin'] != self.proto.coin: # TODO remove?
			die( 'WalletFileError',
				'Tracking wallet coin ({}) does not match current coin ({})!'.format(
					self.data['coin'],
					self.proto.coin ))

		self.conv_types(self.data[self.data_key])
		self.cur_balances = {} # cache balances to prevent repeated lookups per program invocation

	def init_empty(self):
		self.data = { 'coin': self.proto.coin, 'addresses': {} }

	def init_from_wallet_file(self):
		import os,json
		tw_dir = (
			os.path.join(g.data_dir) if self.proto.coin == 'BTC' else
			os.path.join(
				g.data_dir_root,
				'altcoins',
				self.proto.coin.lower(),
				('' if self.proto.network == 'mainnet' else 'testnet')
			))
		self.tw_fn = os.path.join(tw_dir,'tracking-wallet.json')

		from .fileutil import check_or_create_dir,get_data_from_file
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
				die( 'WalletFileError', f'File {self.tw_fn!r} exists but does not contain valid json data' )
		else:
			self.upgrade_wallet_maybe()

		# ensure that wallet file is written when user exits via KeyboardInterrupt:
		if self.mode == 'w':
			import atexit
			def del_tw(tw):
				dmsg(f'Running exit handler del_tw() for {tw!r}')
				del tw
			atexit.register(del_tw,self)

	def __del__(self):
		"""
		TrackingWallet instances opened in write or import mode must be explicitly destroyed
		with 'del twctl', 'del twuo.wallet' and the like to ensure the instance is deleted and
		wallet is written before global vars are destroyed by the interpreter at shutdown.

		Not that this code can only be debugged by examining the program output, as exceptions
		are ignored within __del__():

			/usr/share/doc/python3.6-doc/html/reference/datamodel.html#object.__del__

		Since no exceptions are raised, errors will not be caught by the test suite.
		"""
		if g.debug:
			print_stack_trace(f'TW DEL {self!r}')

		if getattr(self,'mode',None) == 'w': # mode attr might not exist in this state
			self.write()
		elif g.debug:
			msg('read-only wallet, doing nothing')

	def upgrade_wallet_maybe(self):
		pass

	def conv_types(self,ad):
		for k,v in ad.items():
			if k not in ('params','coin'):
				v['mmid'] = TwMMGenID(self.proto,v['mmid'])
				v['comment'] = TwComment(v['comment'])

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
			return self.proto.coin_amt(session_cache[addr])
		if not g.cached_balances:
			return None
		if addr in data_root and 'balance' in data_root[addr]:
			return self.proto.coin_amt(data_root[addr]['balance'])

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
		return await self.rpc.call('importaddress',addr,label,rescan,timeout=(False,3600)[rescan])

	@write_mode
	def batch_import_address(self,arg_list):
		return self.rpc.batch_call('importaddress',arg_list)

	def force_write(self):
		mode_save = self.mode
		self.mode = 'w'
		self.write()
		self.mode = mode_save

	@write_mode
	def write_changed(self,data):
		from .fileutil import write_data_to_file
		write_data_to_file(
			self.tw_fn,
			data,
			desc              = f'{self.base_desc} data',
			ask_overwrite     = False,
			ignore_opt_outdir = True,
			quiet             = True,
			check_data        = True,
			cmp_data          = self.orig_data )

		self.orig_data = data

	def write(self): # use 'check_data' to check wallet hasn't been altered by another program
		if not self.use_tw_file:
			dmsg("'use_tw_file' is False, doing nothing")
			return
		dmsg(f'write(): checking if {self.desc} data has changed')

		import json
		wdata = json.dumps(self.data)

		if self.orig_data != wdata:
			if g.debug:
				print_stack_trace(f'TW DATA CHANGED {self!r}')
				print_diff(self.orig_data,wdata,from_json=True)
			self.write_changed(wdata)
		elif g.debug:
			msg('Data is unchanged\n')

	async def is_in_wallet(self,addr):
		from .twaddrs import TwAddrList
		return addr in (await TwAddrList(self.proto,[],0,True,True,True,wallet=self)).coinaddr_list()

	@write_mode
	async def set_label(self,coinaddr,lbl):
		args = self.rpc.daemon.set_label_args( self.rpc, coinaddr, lbl )
		try:
			return await self.rpc.call(*args)
		except Exception as e:
			rmsg(e.args[0])
			return False

	# returns on failure
	@write_mode
	async def add_label(self,arg1,label='',addr=None,silent=False,on_fail='return'):
		assert on_fail in ('return','raise'), 'add_label_chk1'
		mmaddr,coinaddr = None,None
		if is_coin_addr(self.proto,addr or arg1):
			coinaddr = get_obj(CoinAddr,proto=self.proto,addr=addr or arg1)
		if is_mmgen_id(self.proto,arg1):
			mmaddr = TwMMGenID(self.proto,arg1)

		if mmaddr and not coinaddr:
			from .addrdata import TwAddrData
			coinaddr = (await TwAddrData(self.proto)).mmaddr2coinaddr(mmaddr)

		try:
			if not is_mmgen_id(self.proto,arg1):
				assert coinaddr, f'Invalid coin address for this chain: {arg1}'
			assert coinaddr, f'{g.proj_name} address {mmaddr!r} not found in tracking wallet'
			assert await self.is_in_wallet(coinaddr), f'Address {coinaddr!r} not found in tracking wallet'
		except Exception as e:
			msg(str(e))
			return False

		# Allow for the possibility that BTC addr of MMGen addr was entered.
		# Do reverse lookup, so that MMGen addr will not be marked as non-MMGen.
		if not mmaddr:
			from .addrdata import TwAddrData
			mmaddr = (await TwAddrData(proto=self.proto)).coinaddr2mmaddr(coinaddr)

		if not mmaddr:
			mmaddr = f'{self.proto.base_coin.lower()}:{coinaddr}'

		mmaddr = TwMMGenID(self.proto,mmaddr)

		cmt = TwComment(label) if on_fail=='raise' else get_obj(TwComment,s=label)
		if cmt in (False,None):
			return False

		lbl_txt = mmaddr + (' ' + cmt if cmt else '')
		lbl = (
			TwLabel(self.proto,lbl_txt) if on_fail == 'raise' else
			get_obj(TwLabel,proto=self.proto,text=lbl_txt) )

		if await self.set_label(coinaddr,lbl) == False:
			if not silent:
				msg( 'Label could not be {}'.format('added' if label else 'removed') )
			return False
		else:
			desc = '{} address {} in tracking wallet'.format(
				mmaddr.type.replace('mmg','MMG'),
				mmaddr.replace(self.proto.base_coin.lower()+':','') )
			if label:
				msg(f'Added label {label!r} to {desc}')
			else:
				msg(f'Removed label from {desc}')
			return True

	@write_mode
	async def remove_label(self,mmaddr):
		await self.add_label(mmaddr,'')

	@write_mode
	async def remove_address(self,addr):
		raise NotImplementedError(f'address removal not implemented for coin {self.proto.coin}')
