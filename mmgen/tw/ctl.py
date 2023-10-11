#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
tw.ctl: Tracking wallet control class for the MMGen suite
"""

import json
from collections import namedtuple

from ..util import msg,msg_r,suf,die
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import TwComment,get_obj
from ..addr import CoinAddr,is_mmgen_id,is_coin_addr
from ..rpc import rpc_init
from .shared import TwMMGenID,TwLabel

addr_info = namedtuple('addr_info',['twmmid','coinaddr'])

# decorator for TwCtl
def write_mode(orig_func):
	def f(self,*args,**kwargs):
		if self.mode != 'w':
			die(1,'{} opened in read-only mode: cannot execute method {}()'.format(
				type(self).__name__,
				locals()['orig_func'].__name__
			))
		return orig_func(self,*args,**kwargs)
	return f

class TwCtl(MMGenObject,metaclass=AsyncInit):

	caps = ('rescan','batch')
	data_key = 'addresses'
	use_tw_file = False
	aggressive_sync = False
	importing = False

	def __new__(cls,cfg,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,'tw.ctl'))

	async def __init__(
			self,
			cfg,
			proto,
			mode              = 'r',
			token_addr        = None,
			rpc_ignore_wallet = False):

		assert mode in ('r','w','i'), f"{mode!r}: wallet mode must be 'r','w' or 'i'"
		if mode == 'i':
			self.importing = True
			mode = 'w'

		# TODO: create on demand - only certain ops require RPC
		self.cfg = cfg
		self.rpc = await rpc_init( cfg, proto, ignore_wallet=rpc_ignore_wallet )
		self.proto = proto
		self.mode = mode
		self.desc = self.base_desc = f'{self.proto.name} tracking wallet'

		if self.use_tw_file:
			self.init_from_wallet_file()
		else:
			self.init_empty()

		if self.data['coin'] != self.proto.coin: # TODO remove?
			die( 'WalletFileError',
				f'Tracking wallet coin ({self.data["coin"]}) does not match current coin ({self.proto.coin})!')

		self.conv_types(self.data[self.data_key])
		self.cur_balances = {} # cache balances to prevent repeated lookups per program invocation

	def init_from_wallet_file(self):
		import os
		tw_dir = (
			os.path.join(self.cfg.data_dir) if self.proto.coin == 'BTC' else
			os.path.join(
				self.cfg.data_dir_root,
				'altcoins',
				self.proto.coin.lower(),
				('' if self.proto.network == 'mainnet' else 'testnet')
			))
		self.tw_fn = os.path.join(tw_dir,'tracking-wallet.json')

		from ..fileutil import check_or_create_dir,get_data_from_file
		check_or_create_dir(tw_dir)

		try:
			self.orig_data = get_data_from_file( self.cfg, self.tw_fn, quiet=True )
			self.data = json.loads(self.orig_data)
		except:
			try:
				os.stat(self.tw_fn)
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
			def del_twctl(twctl):
				self.cfg._util.dmsg(f'Running exit handler del_twctl() for {twctl!r}')
				del twctl
			atexit.register(del_twctl,self)

	def __del__(self):
		"""
		TwCtl instances opened in write or import mode must be explicitly destroyed with ‘del
		twuo.twctl’ and the like to ensure the instance is deleted and wallet is written before
		global vars are destroyed by the interpreter at shutdown.

		Not that this code can only be debugged by examining the program output, as exceptions
		are ignored within __del__():

			/usr/share/doc/python3.6-doc/html/reference/datamodel.html#object.__del__

		Since no exceptions are raised, errors will not be caught by the test suite.
		"""
		if getattr(self,'mode',None) == 'w': # mode attr might not exist in this state
			self.write()
		elif self.cfg.debug:
			msg('read-only wallet, doing nothing')

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
		if not self.cfg.cached_balances:
			return None
		if addr in data_root and 'balance' in data_root[addr]:
			return self.proto.coin_amt(data_root[addr]['balance'])

	async def get_balance(self,addr,force_rpc=False):
		ret = None if force_rpc else self.get_cached_balance(addr,self.cur_balances,self.data_root)
		if ret is None:
			ret = await self.rpc_get_balance(addr)
			self.cache_balance(addr,ret,self.cur_balances,self.data_root)
		return ret

	def force_write(self):
		mode_save = self.mode
		self.mode = 'w'
		self.write()
		self.mode = mode_save

	@write_mode
	def write_changed(self,data,quiet):
		from ..fileutil import write_data_to_file
		write_data_to_file(
			self.cfg,
			self.tw_fn,
			data,
			desc              = f'{self.base_desc} data',
			ask_overwrite     = False,
			ignore_opt_outdir = True,
			quiet             = quiet,
			check_data        = True, # die if wallet has been altered by another program
			cmp_data          = self.orig_data )

		self.orig_data = data

	def write(self,quiet=True):
		if not self.use_tw_file:
			self.cfg._util.dmsg("'use_tw_file' is False, doing nothing")
			return
		self.cfg._util.dmsg(f'write(): checking if {self.desc} data has changed')

		wdata = json.dumps(self.data)
		if self.orig_data != wdata:
			self.write_changed(wdata,quiet=quiet)
		elif self.cfg.debug:
			msg('Data is unchanged\n')

	async def resolve_address(self,addrspec):

		twmmid,coinaddr = (None,None)

		if is_coin_addr(self.proto,addrspec):
			coinaddr = get_obj(CoinAddr,proto=self.proto,addr=addrspec)
		elif is_mmgen_id(self.proto,addrspec):
			twmmid = TwMMGenID(self.proto,addrspec)
		else:
			msg(f'{addrspec!r}: invalid address for this network')
			return None

		from .rpc import TwRPC
		pairs = await TwRPC(proto=self.proto,rpc=self.rpc,twctl=self).get_addr_label_pairs(twmmid)

		if not pairs:
			msg(f'MMGen address {twmmid!r} not found in tracking wallet')
			return None

		pairs_data = dict((label.mmid,addr) for label,addr in pairs)

		if twmmid and not coinaddr:
			coinaddr = pairs_data[twmmid]

		# Allow for the possibility that BTC addr of MMGen addr was entered.
		# Do reverse lookup, so that MMGen addr will not be marked as non-MMGen.
		if not twmmid:
			for mmid,addr in pairs_data.items():
				if coinaddr == addr:
					twmmid = mmid
					break
			else:
				msg(f'Coin address {addrspec!r} not found in tracking wallet')
				return None

		return addr_info(twmmid,coinaddr)

	# returns on failure
	@write_mode
	async def set_comment(self,addrspec,comment='',trusted_coinaddr=None,silent=False):

		res = (
			addr_info(addrspec,trusted_coinaddr) if trusted_coinaddr
			else await self.resolve_address(addrspec) )

		if not res:
			return False

		comment = get_obj(TwComment,s=comment)

		if comment is False:
			return False

		lbl = get_obj(
			TwLabel,
			proto = self.proto,
			text = res.twmmid + (' ' + comment if comment else ''))

		if lbl is False:
			return False

		if await self.set_label(res.coinaddr,lbl):
			# redundant paranoia step:
			from .rpc import TwRPC
			pairs = await TwRPC(proto=self.proto,rpc=self.rpc,twctl=self).get_addr_label_pairs(res.twmmid)
			assert pairs[0][0].comment == comment, f'{pairs[0][0].comment!r} != {comment!r}'
			if not silent:
				desc = '{} address {} in tracking wallet'.format(
					res.twmmid.type.replace('mmgen','MMGen'),
					res.twmmid.addr.hl() )
				msg(
					'Added label {} to {}'.format(comment.hl2(encl='‘’'),desc) if comment else
					'Removed label from {}'.format(desc) )
			return True
		else:
			if not silent:
				msg( 'Label could not be {}'.format('added' if comment else 'removed') )
			return False

	@write_mode
	async def remove_comment(self,mmaddr):
		await self.set_comment(mmaddr,'')

	async def import_address_common(self,data,batch=False,gather=False):

		async def do_import(address,comment,message):
			try:
				res = await self.import_address( address, comment )
				self.cfg._util.qmsg(message)
				return res
			except Exception as e:
				die(2,f'\nImport of address {address!r} failed: {e.args[0]!r}')

		_d = namedtuple( 'formatted_import_data', data[0]._fields + ('mmid_disp',))
		pfx = self.proto.base_coin.lower() + ':'
		fdata = [ _d(*d, 'non-MMGen' if d.twmmid.startswith(pfx) else d.twmmid ) for d in data ]

		fs = '{:%s}: {:%s} {:%s} - OK' % (
			len(str(len(fdata))) * 2 + 1,
			max(len(d.addr) for d in fdata),
			max(len(d.mmid_disp) for d in fdata) + 2
		)

		nAddrs = len(data)
		out = [( # create list, not generator, so we know data is valid before starting import
				CoinAddr( self.proto, d.addr ),
				TwLabel( self.proto, d.twmmid + (f' {d.comment}' if d.comment else '') ),
				fs.format( f'{n}/{nAddrs}', d.addr, f'({d.mmid_disp})' )
			) for n,d in enumerate(fdata,1)]

		if batch:
			msg_r(f'Batch importing {len(out)} address{suf(data,"es")}...')
			ret = await self.batch_import_address((a,b) for a,b,c in out)
			msg(f'done\n{len(ret)} addresses imported')
		else:
			if gather: # this seems to provide little performance benefit
				import asyncio
				await asyncio.gather(*(do_import(*d) for d in out))
			else:
				for d in out:
					await do_import(*d)
			msg('Address import completed OK')
