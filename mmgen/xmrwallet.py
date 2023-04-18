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
xmrwallet.py - MoneroWalletOps class
"""

import os,re,time,json
from collections import namedtuple
from .objmethods import MMGenObject,Hilite,InitErrors
from .obj import CoinTxID
from .color import red,yellow,green,blue,cyan,pink,orange
from .util import (
	msg,
	msg_r,
	gmsg,
	ymsg,
	gmsg_r,
	pp_msg,
	die,
	fmt,
	suf,
	async_run,
	make_timestr,
	make_chksum_6,
	capfirst,
)
from .seed import SeedID
from .protocol import init_proto
from .proto.btc.common import b58a
from .addr import CoinAddr,AddrIdx
from .addrlist import KeyAddrList,AddrIdxList
from .rpc import json_encoder
from .proto.xmr.rpc import MoneroRPCClient,MoneroWalletRPCClient
from .proto.xmr.daemon import MoneroWalletDaemon
from .ui import keypress_confirm

xmrwallet_uargs = namedtuple('xmrwallet_uargs',[
	'infile',
	'wallets',
	'spec',
])

xmrwallet_uarg_info = (
	lambda e,hp: {
		'daemon':          e('HOST:PORT', hp),
		'tx_relay_daemon': e('HOST:PORT[:PROXY_HOST:PROXY_PORT]', rf'({hp})(?::({hp}))?'),
		'newaddr_spec':    e('WALLET_NUM[:ACCOUNT][,"label text"]', rf'(\d+)(?::(\d+))?(?:,(.*))?'),
		'transfer_spec':   e('SOURCE_WALLET_NUM:ACCOUNT:ADDRESS,AMOUNT', rf'(\d+):(\d+):([{b58a}]+),([0-9.]+)'),
		'sweep_spec':      e('SOURCE_WALLET_NUM:ACCOUNT[,DEST_WALLET_NUM]', r'(\d+):(\d+)(?:,(\d+))?'),
		'label_spec':      e('WALLET_NUM:ACCOUNT:ADDRESS,"label text"', rf'(\d+):(\d+):(\d+),(.*)'),
	})(
		namedtuple('uarg_info_entry',['annot','pat']),
		r'(?:[^:]+):(?:\d+)'
	)

class XMRWalletAddrSpec(str,Hilite,InitErrors,MMGenObject):
	color = 'cyan'
	width = 0
	trunc_ok = False
	min_len = 5  # 1:0:0
	max_len = 14 # 9999:9999:9999
	def __new__(cls,arg1,arg2=None,arg3=None):
		if type(arg1) == cls:
			return arg1

		try:
			if isinstance(arg1,str):
				me = str.__new__(cls,arg1)
				m = re.fullmatch( '({n}):({n}):({n}|None)'.format(n=r'[0-9]{1,4}'), arg1 )
				assert m is not None, f'{arg1!r}: invalid XMRWalletAddrSpec'
				for e in m.groups():
					if len(e) != 1 and e[0] == '0':
						die(2,f'{e}: leading zeroes not permitted in XMRWalletAddrSpec element')
				me.wallet = AddrIdx(m[1])
				me.account = int(m[2])
				me.account_address = None if m[3] == 'None' else int(m[3])
			else:
				me = str.__new__(cls,f'{arg1}:{arg2}:{arg3}')
				for arg in [arg1,arg2] + ([] if arg3 is None else [arg3]):
					assert isinstance(arg,int), f'{arg}: XMRWalletAddrSpec component not of type int'
					assert arg is None or arg <= 9999, f'{arg}: XMRWalletAddrSpec component greater than 9999'
				me.wallet = AddrIdx(arg1)
				me.account = arg2
				me.account_address = arg3
			return me
		except Exception as e:
			return cls.init_fail(e,me)

def is_xmr_tx_file(cfg,fn):
	try:
		MoneroMMGenTX.Completed(cfg,fn)
		return True
	except Exception as e:
		if not 'MoneroMMGenTXFileParseError' in type(e).__name__:
			ymsg(f'\n{type(e).__name__}: {e}')
		return False

class MoneroMMGenTX:

	class Base:

		def __init__(self):
			self.name = type(self).__name__

		def make_chksum(self,keys=None):
			res = json.dumps(
				dict( (k,v) for k,v in self.data._asdict().items() if (not keys or k in keys) ),
				cls = json_encoder
			)
			return make_chksum_6(res)

		@property
		def base_chksum(self):
			return self.make_chksum(
				('op','create_time','network','seed_id','source','dest','amount')
			)

		@property
		def full_chksum(self):
			return self.make_chksum(set(self.data._fields) - {'metadata'})

		xmrwallet_tx_data = namedtuple('xmrwallet_tx_data',[
			'op',
			'create_time',
			'sign_time',
			'network',
			'seed_id',
			'source',
			'dest',
			'dest_address',
			'txid',
			'amount',
			'fee',
			'blob',
			'metadata',
		])

		def get_info(self,indent=''):
			d = self.data
			if d.dest:
				to_entry = f'\n{indent}  To:     ' + (
					'Wallet {}, account {}, address {}'.format(
						d.dest.wallet.hl(),
						red(f'#{d.dest.account}'),
						red(f'#{d.dest.account_address}')
					)
				)

			fs = """
				Info for transaction {a} [Seed ID: {b}. Network: {c}]:
				  TxID:    {d}
				  Created: {e:19} [{f}]
				  Signed:  {g:19} [{h}]
				  Type:    {i}
				  From:    Wallet {j}, account {k}{l}
				  Amount:  {m} XMR
				  Fee:     {n} XMR
				  Dest:    {o}
			"""

			pmid = d.dest_address.parsed.payment_id
			if pmid:
				fs += '  Payment ID: {pmid}'

			from .util2 import format_elapsed_hr
			return fmt(fs,strip_char='\t',indent=indent).format(
					a = orange(self.base_chksum.upper()),
					b = d.seed_id.hl(),
					c = yellow(d.network.upper()),
					d = d.txid.hl(),
					e = make_timestr(d.create_time),
					f = format_elapsed_hr(d.create_time),
					g = make_timestr(d.sign_time),
					h = format_elapsed_hr(d.sign_time),
					i = blue(capfirst(d.op)),
					j = d.source.wallet.hl(),
					k = red(f'#{d.source.account}'),
					l = to_entry if d.dest else '',
					m = d.amount.hl(),
					n = d.fee.hl(),
					o = d.dest_address.hl(),
					pmid = pink(pmid.hex()) if pmid else None
				)

		def write(self,delete_metadata=False,ask_write=True,ask_overwrite=True):
			dict_data = self.data._asdict()
			if delete_metadata:
				dict_data['metadata'] = None

			out = json.dumps(
				{ 'MoneroMMGenTX': {
						'base_chksum': self.base_chksum,
						'full_chksum': self.full_chksum,
						'data': dict_data,
					}
				},
				cls = json_encoder,
			)

			fn = '{a}{b}-XMR[{c!s}]{d}.{e}'.format(
				a = self.base_chksum.upper(),
				b = (lambda s: f'-{s.upper()}' if s else '')(self.full_chksum),
				c = self.data.amount,
				d = (lambda s: '' if s == 'mainnet' else f'.{s}')(self.data.network),
				e = self.ext
			)

			from .fileutil import write_data_to_file
			write_data_to_file(
				cfg                   = self.cfg,
				outfile               = fn,
				data                  = out,
				desc                  = self.desc,
				ask_write             = ask_write,
				ask_write_default_yes = not ask_write,
				ask_overwrite         = ask_overwrite )

	class New(Base):

		def __init__(self,*args,**kwargs):

			super().__init__()

			assert not args, 'Non-keyword args not permitted'

			d = namedtuple('kwargs_tuple',kwargs)(**kwargs)
			self.cfg = d.cfg

			proto = init_proto( self.cfg, 'xmr', network=d.network, need_amt=True )

			now = int(time.time())

			self.data = self.xmrwallet_tx_data(
				op             = d.op,
				create_time    = now,
				sign_time      = now,
				network        = d.network,
				seed_id        = SeedID(sid=d.seed_id),
				source         = XMRWalletAddrSpec(d.source),
				dest           = None if d.dest is None else XMRWalletAddrSpec(d.dest),
				dest_address   = CoinAddr(proto,d.dest_address),
				txid           = CoinTxID(d.txid),
				amount         = proto.coin_amt(d.amount,from_unit='atomic'),
				fee            = proto.coin_amt(d.fee,from_unit='atomic'),
				blob           = d.blob,
				metadata       = d.metadata,
			)

	class NewSigned(New):
		desc = 'signed transaction data'
		ext = 'sigtx'
		signed = True

	class Completed(Base):

		def __init__(self,cfg,fn):

			super().__init__()

			self.cfg = cfg
			self.fn = fn

			from .fileutil import get_data_from_file

			try:
				d_wrap = json.loads(get_data_from_file( cfg, fn ))['MoneroMMGenTX']
			except Exception as e:
				die( 'MoneroMMGenTXFileParseError', f'{type(e).__name__}: {e}\nCould not load transaction file' )

			d = self.xmrwallet_tx_data(**d_wrap['data'])

			if self.name != 'Completed':
				assert fn.endswith('.'+self.ext), 'TX filename {fn!r} has incorrect extension (not {self.ext!r})'
				assert getattr(d,self.req_field), f'{self.name} TX missing required field {self.req_field!r}'

			proto = init_proto( cfg, 'xmr', network=d.network, need_amt=True )

			self.data = self.xmrwallet_tx_data(
				op             = d.op,
				create_time    = d.create_time,
				sign_time      = d.sign_time,
				network        = d.network,
				seed_id        = SeedID(sid=d.seed_id),
				source         = XMRWalletAddrSpec(d.source),
				dest           = None if d.dest is None else XMRWalletAddrSpec(d.dest),
				dest_address   = CoinAddr(proto,d.dest_address),
				txid           = CoinTxID(d.txid),
				amount         = proto.coin_amt(d.amount),
				fee            = proto.coin_amt(d.fee),
				blob           = d.blob,
				metadata       = d.metadata,
			)

			for k in ('base_chksum','full_chksum'):
				a = getattr(self,k)
				b = d_wrap[k]
				assert a == b, f'{k} mismatch: {a} != {b}'

	class Signed(Completed):
		desc = 'signed transaction'
		ext = 'sigtx'
		signed = True
		req_field = 'blob'

class MoneroWalletOps:

	ops = (
		'create',
		'sync',
		'list',
		'new',
		'transfer',
		'sweep',
		'relay',
		'txview',
		'label' )

	opts = (
		'wallet_dir',
		'daemon',
		'tx_relay_daemon',
		'use_internal_keccak_module',
		'hash_preset',
		'restore_height',
		'no_start_wallet_daemon',
		'no_stop_wallet_daemon',
		'no_relay' )

	pat_opts = ('daemon','tx_relay_daemon')

	class base(MMGenObject):

		opts = ('wallet_dir',)

		def __init__(self,cfg,uarg_tuple):

			def gen_classes():
				for cls in type(self).__mro__:
					yield cls
					if cls.__name__ == 'base':
						break

			self.name = type(self).__name__
			self.cfg = cfg
			classes = tuple(gen_classes())
			self.opts = tuple(set(opt for cls in classes for opt in cls.opts))

			if not hasattr(self,'stem'):
				self.stem = self.name

			global uarg, uarg_info, fmt_amt, hl_amt

			uarg = uarg_tuple
			uarg_info = xmrwallet_uarg_info

			def fmt_amt(amt):
				return self.proto.coin_amt(amt,from_unit='atomic').fmt( iwidth=5, prec=12, color=True )
			def hl_amt(amt):
				return self.proto.coin_amt(amt,from_unit='atomic').hl()

			id_cur = None
			for cls in classes:
				if id(cls.check_uopts) != id_cur:
					cls.check_uopts(self)
					id_cur = id(cls.check_uopts)

			self.proto = init_proto( cfg, 'xmr', network=self.cfg.network, need_amt=True )

		def check_uopts(self):

			def check_pat_opt(name):
				val = getattr(self.cfg,name)
				if not re.fullmatch( uarg_info[name].pat, val, re.ASCII ):
					die(1,'{!r}: invalid value for --{}: it must have format {!r}'.format(
						val,
						name.replace('_','-'),
						uarg_info[name].annot
					))

			for attr in self.cfg.__dict__:
				if attr in MoneroWalletOps.opts and not attr in self.opts:
					die(1,'Option --{} not supported for {!r} operation'.format(
						attr.replace('_','-'),
						self.name,
					))

			for opt in MoneroWalletOps.pat_opts:
				if getattr(self.cfg,opt,None):
					check_pat_opt(opt)

		def display_tx_relay_info(self,indent=''):
			m = re.fullmatch(
				uarg_info['tx_relay_daemon'].pat,
				self.cfg.tx_relay_daemon,
				re.ASCII )
			msg(fmt(f"""
				TX relay info:
				  Host:  {blue(m[1])}
				  Proxy: {blue(m[2] or 'None')}
				""",strip_char='\t',indent=indent))

		def post_main(self):
			pass

		async def stop_wallet_daemon(self):
			pass

	class wallet(base):

		opts = (
			'use_internal_keccak_module',
			'hash_preset',
			'daemon',
			'no_start_wallet_daemon',
			'no_stop_wallet_daemon',
		)
		wallet_exists = True

		def __init__(self,cfg,uarg_tuple):

			def wallet_exists(fn):
				try: os.stat(fn)
				except: return False
				else: return True

			def check_wallets():
				for d in self.addr_data:
					fn = self.get_wallet_fn(d)
					exists = wallet_exists(fn)
					if exists and not self.wallet_exists:
						die(1,f'Wallet {fn!r} already exists!')
					elif not exists and self.wallet_exists:
						die(1,f'Wallet {fn!r} not found!')

			super().__init__(cfg,uarg_tuple)

			self.kal = KeyAddrList(
				cfg      = cfg,
				proto    = self.proto,
				addrfile = uarg.infile,
				key_address_validity_check = True )

			self.create_addr_data()

			check_wallets()

			self.wd = MoneroWalletDaemon(
				cfg         = self.cfg,
				proto       = self.proto,
				wallet_dir  = self.cfg.wallet_dir or '.',
				test_suite  = self.cfg.test_suite,
				daemon_addr = self.cfg.daemon or None,
			)

			self.c = MoneroWalletRPCClient(
				cfg             = self.cfg,
				daemon          = self.wd,
				test_connection = False,
			)

			if not self.cfg.no_start_wallet_daemon:
				async_run(self.c.restart_daemon())

		def create_addr_data(self):
			if uarg.wallets:
				idxs = AddrIdxList(uarg.wallets)
				self.addr_data = [d for d in self.kal.data if d.idx in idxs]
				if len(self.addr_data) != len(idxs):
					die(1,f'List {uarg.wallets!r} contains addresses not present in supplied key-address file')
			else:
				self.addr_data = self.kal.data

		async def stop_wallet_daemon(self):
			if not self.cfg.no_stop_wallet_daemon:
				await self.c.stop_daemon()

		def get_wallet_fn(self,data):
			return os.path.join(
				self.cfg.wallet_dir or '.','{a}-{b}-MoneroWallet{c}'.format(
					a = self.kal.al_id.sid,
					b = data.idx,
					c = f'.{self.cfg.network}' if self.cfg.network != 'mainnet' else ''))

		async def main(self):
			gmsg('\n{a}ing {b} wallet{c}'.format(
				a = self.stem.capitalize(),
				b = len(self.addr_data),
				c = suf(self.addr_data) ))
			processed = 0
			for n,d in enumerate(self.addr_data): # [d.sec,d.addr,d.wallet_passwd,d.viewkey]
				fn = self.get_wallet_fn(d)
				gmsg('\n{}ing wallet {}/{} ({})'.format(
					self.stem.capitalize(),
					n+1,
					len(self.addr_data),
					os.path.basename(fn),
				))
				processed += await self.process_wallet(
					d,
					fn,
					last = n == len(self.addr_data)-1 )
			gmsg(f'\n{processed} wallet{suf(processed)} {self.stem}ed')
			return processed

		class rpc:

			def __init__(self,parent,d):
				self.parent = parent
				self.cfg = parent.cfg
				self.c = parent.c
				self.d = d
				self.fn = parent.get_wallet_fn(d)

			def open_wallet(self,desc,refresh=True):
				gmsg_r(f'\n  Opening {desc} wallet...')
				self.c.call( # returns {}
					'open_wallet',
					filename=os.path.basename(self.fn),
					password=self.d.wallet_passwd )
				gmsg('done')

				if refresh:
					gmsg_r(f'  Refreshing {desc} wallet...')
					ret = self.c.call('refresh')
					gmsg('done')
					if ret['received_money']:
						msg('  Wallet has received funds')

			def close_wallet(self,desc):
				gmsg_r(f'\n  Closing {desc} wallet...')
				self.c.call('close_wallet')
				gmsg_r('done')

			async def stop_wallet(self,desc):
				msg(f'Stopping {self.c.daemon.desc} on port {self.c.daemon.bind_port}')
				gmsg_r(f'\n  Stopping {desc} wallet...')
				await self.c.stop_daemon(quiet=True) # closes wallet
				gmsg_r('done')

			def print_accts(self,data,addrs_data,indent='    '):
				d = data['subaddress_accounts']
				msg('\n' + indent + f'Accounts of wallet {os.path.basename(self.fn)}:')
				fs = indent + '  {:6}  {:18}  {:<6} {:%s}  {}' % max(len(e['label']) for e in d)
				msg(fs.format('Index ','Base Address','nAddrs','Label','Unlocked Balance'))
				for i,e in enumerate(d):
					msg(fs.format(
						str(e['account_index']),
						e['base_address'][:15] + '...',
						len(addrs_data[i]['addresses']),
						e['label'],
						fmt_amt(e['unlocked_balance']),
					))

			def get_accts(self,print=True):
				data = self.c.call('get_accounts')
				addrs_data = [
					self.c.call('get_address',account_index=i)
						for i in range(len(data['subaddress_accounts']))
				]
				if print:
					self.print_accts(data,addrs_data)
				return ( data, addrs_data )

			def create_acct(self,label=None):
				msg('\n    Creating new account...')
				ret = self.c.call(
					'create_account',
					label = label or 'Sweep from {}:{} [{}]'.format(
						self.parent.source.idx,
						self.parent.account,
						make_timestr() ))
				msg('      Index:   {}'.format( pink(str(ret['account_index'])) ))
				msg('      Address: {}'.format( cyan(ret['address']) ))
				return (ret['account_index'], ret['address'])

			def get_last_acct(self,accts_data):
				msg('\n    Getting last account...')
				ret = accts_data['subaddress_accounts'][-1]
				msg('      Index:   {}'.format( pink(str(ret['account_index'])) ))
				msg('      Address: {}'.format( cyan(ret['base_address']) ))
				return (ret['account_index'], ret['base_address'])

			def print_addrs(self,accts_data,account):
				ret = self.c.call('get_address',account_index=account)
				d = ret['addresses']
				msg('\n      Addresses of account #{} ({}):'.format(
					account,
					accts_data['subaddress_accounts'][account]['label']))
				fs = '        {:6}  {:18}  {:%s}  {}' % max( [len(e['label']) for e in d], default=0 )
				msg(fs.format('Index ','Address','Label','Used'))
				for e in d:
					msg(fs.format(
						str(e['address_index']),
						e['address'][:15] + '...',
						e['label'],
						e['used']
					))
				return ret

			def create_new_addr(self,account,label=None):
				msg_r('\n    Creating new address: ')
				ret = self.c.call(
					'create_address',
					account_index = account,
					label         = label or f'Sweep from this account [{make_timestr()}]',
				)
				msg(cyan(ret['address']))
				return ret['address']

			def get_last_addr(self,account,display=True):
				if display:
					msg('\n    Getting last address:')
				ret = self.c.call(
					'get_address',
					account_index = account,
				)['addresses']
				addr = ret[-1]['address']
				if display:
					msg('      ' + cyan(addr))
				return ( addr, len(ret) - 1 )

			def set_label(self,account,address_idx,label):
				return self.c.call(
					'label_address',
					index = { 'major': account, 'minor': address_idx },
					label = label
				)

			def make_transfer_tx(self,account,addr,amt):
				res = self.c.call(
					'transfer',
					account_index = account,
					destinations = [{
						'amount':  amt.to_unit('atomic'),
						'address': addr
					}],
					do_not_relay = True,
					get_tx_hex = True,
					get_tx_metadata = True
				)
				return MoneroMMGenTX.NewSigned(
					cfg            = self.cfg,
					op             = self.parent.name,
					network        = self.parent.proto.network,
					seed_id        = self.parent.kal.al_id.sid,
					source         = XMRWalletAddrSpec(self.parent.source.idx,self.parent.account,None),
					dest           = None,
					dest_address   = addr,
					txid           = res['tx_hash'],
					amount         = res['amount'],
					fee            = res['fee'],
					blob           = res['tx_blob'],
					metadata       = res['tx_metadata'],
				)

			def make_sweep_tx(self,account,dest_acct,dest_addr_idx,addr):
				res = self.c.call(
					'sweep_all',
					address = addr,
					account_index = account,
					do_not_relay = True,
					get_tx_hex = True,
					get_tx_metadata = True
				)

				if len(res['tx_hash_list']) > 1:
					die(3,'More than one TX required.  Cannot perform this sweep')

				return MoneroMMGenTX.NewSigned(
					cfg            = self.cfg,
					op             = self.parent.name,
					network        = self.parent.proto.network,
					seed_id        = self.parent.kal.al_id.sid,
					source         = XMRWalletAddrSpec(self.parent.source.idx,self.parent.account,None),
					dest           = XMRWalletAddrSpec(
										(self.parent.dest or self.parent.source).idx,
										dest_acct,
										dest_addr_idx),
					dest_address   = addr,
					txid           = res['tx_hash_list'][0],
					amount         = res['amount_list'][0],
					fee            = res['fee_list'][0],
					blob           = res['tx_blob_list'][0],
					metadata       = res['tx_metadata_list'][0],
				)

			def relay_tx(self,tx_hex):
				ret = self.c.call('relay_tx',hex=tx_hex)
				try:
					msg('\n    Relayed {}'.format( CoinTxID(ret['tx_hash']).hl() ))
				except:
					msg(f'\n   Server returned: {ret!s}')

	class create(wallet):
		stem    = 'creat'
		wallet_exists = False
		opts    = ('restore_height',)

		def check_uopts(self):
			if int(self.cfg.restore_height or 0) < 0:
				die(1,f'{self.cfg.restore_height}: invalid value for --restore-height (less than zero)')

		async def process_wallet(self,d,fn,last):
			msg_r('') # for pexpect

			from .xmrseed import xmrseed
			ret = self.c.call(
				'restore_deterministic_wallet',
				filename       = os.path.basename(fn),
				password       = d.wallet_passwd,
				seed           = xmrseed().fromhex(d.sec.wif,tostr=True),
				restore_height = self.cfg.restore_height,
				language       = 'English' )

			pp_msg(ret) if self.cfg.debug else msg('  Address: {}'.format( ret['address'] ))
			return True

	class sync(wallet):
		opts    = ('rescan_blockchain',)

		def __init__(self,cfg,uarg_tuple):

			super().__init__(cfg,uarg_tuple)

			host,port = self.cfg.daemon.split(':') if self.cfg.daemon else ('localhost',self.wd.daemon_port)

			from .daemon import CoinDaemon
			self.dc = MoneroRPCClient(
				cfg    = self.cfg,
				proto  = self.proto,
				daemon = CoinDaemon( self.cfg, 'xmr' ),
				host   = host,
				port   = int(port),
				user   = None,
				passwd = None )

			self.accts_data = {}

		async def process_wallet(self,d,fn,last):

			chain_height = self.dc.call_raw('get_height')['height']
			msg(f'  Chain height: {chain_height}')

			t_start = time.time()

			msg_r('  Opening wallet...')
			self.c.call(
				'open_wallet',
				filename=os.path.basename(fn),
				password=d.wallet_passwd )
			msg('done')

			msg_r('  Getting wallet height (be patient, this could take a long time)...')
			wallet_height = self.c.call('get_height')['height']
			msg_r('\r' + ' '*68 + '\r')
			msg(f'  Wallet height: {wallet_height}        ')

			behind = chain_height - wallet_height
			if behind > 1000:
				msg_r(f'  Wallet is {behind} blocks behind chain tip.  Please be patient.  Syncing...')

			ret = self.c.call('refresh')

			if behind > 1000:
				msg('done')

			if ret['received_money']:
				msg('  Wallet has received funds')

			for i in range(2):
				wallet_height = self.c.call('get_height')['height']
				if wallet_height >= chain_height:
					break
				ymsg(f'  Wallet failed to sync (wallet height [{wallet_height}] < chain height [{chain_height}])')
				if i or not self.cfg.rescan_blockchain:
					break
				msg_r('  Rescanning blockchain, please be patient...')
				self.c.call('rescan_blockchain')
				self.c.call('refresh')
				msg('done')

			t_elapsed = int(time.time() - t_start)

			bn = os.path.basename(fn)

			a,b = self.rpc(self,d).get_accts(print=False)

			msg('  Balance: {} Unlocked balance: {}'.format(
				hl_amt(a['total_balance']),
				hl_amt(a['total_unlocked_balance']),
			))

			self.accts_data[bn] = { 'accts': a, 'addrs': b }

			msg(f'  Wallet height: {wallet_height}')
			msg('  Sync time: {:02}:{:02}'.format(
				t_elapsed // 60,
				t_elapsed % 60 ))

			if not last:
				self.c.call('close_wallet')

			return wallet_height >= chain_height

		def post_main(self):
			d = self.accts_data

			for wnum,k in enumerate(d):
				if self.name == 'sync':
					self.rpc(self,self.addr_data[wnum]).print_accts( d[k]['accts'], d[k]['addrs'], indent='')
				elif self.name == 'list':
					fs = '  {:2} {} {} {}'
					msg('\n' + green(f'Wallet {k}:'))
					for acct_num,acct in enumerate(d[k]['addrs']):
						msg('\n  Account #{} [{} {}]'.format(
							acct_num,
							self.proto.coin_amt(
								d[k]['accts']['subaddress_accounts'][acct_num]['unlocked_balance'],
								from_unit='atomic').hl(),
							self.proto.coin_amt.hlc('XMR')
						))
						msg(fs.format('','Address'.ljust(95),'Used ','Label'))
						for addr in acct['addresses']:
							msg(fs.format(
								addr['address_index'],
								CoinAddr(self.proto,addr['address']).hl(),
								( yellow('True ') if addr['used'] else green('False') ),
								pink(addr['label']) ))

			col1_w = max(map(len,d)) + 1
			fs = '{:%s} {} {}' % col1_w
			tbals = [0,0]
			msg('\n'+fs.format('Wallet','Balance           ','Unlocked Balance'))

			for k in d:
				b  = d[k]['accts']['total_balance']
				ub = d[k]['accts']['total_unlocked_balance']
				msg(fs.format( k + ':', fmt_amt(b), fmt_amt(ub) ))
				tbals[0] += b
				tbals[1] += ub

			msg(fs.format( '-'*col1_w, '-'*18, '-'*18 ))
			msg(fs.format( 'TOTAL:', fmt_amt(tbals[0]), fmt_amt(tbals[1]) ))

	class list(sync):
		stem = 'sync'

	class spec(wallet): # virtual class

		def create_addr_data(self):
			m = re.fullmatch(uarg_info[self.spec_id].pat,uarg.spec,re.ASCII)
			if not m:
				fs = "{!r}: invalid {!r} arg: for {} operation, it must have format {!r}"
				die(1,fs.format( uarg.spec, self.spec_id, self.name, uarg_info[self.spec_id].annot ))

			def gen():
				for i,k in self.spec_key:
					if m[i] == None:
						setattr(self,k,None)
					else:
						idx = int(m[i])
						try:
							res = self.kal.entry(idx)
						except:
							die(1,'Supplied key-address file does not contain address {}:{}'.format(
								self.kal.al_id.sid,
								idx ))
						else:
							setattr(self,k,res)
							yield res

			self.addr_data = list(gen())
			self.account = None if m[2] is None else int(m[2])

			def strip_quotes(s):
				if s and s[0] in ("'",'"'):
					if s[-1] != s[0] or len(s) < 2:
						die(1,f'{s!r}: unbalanced quotes in label string!')
					return s[1:-1]
				else:
					return s # None or empty string

			if self.name == 'transfer':
				self.dest_addr = CoinAddr(self.proto,m[3])
				self.amount = self.proto.coin_amt(m[4])
			elif self.name == 'new':
				self.label = strip_quotes(m[3])
			elif self.name == 'label':
				self.address_idx = int(m[3])
				self.label = strip_quotes(m[4])

	class sweep(spec):
		spec_id  = 'sweep_spec'
		spec_key = ( (1,'source'), (3,'dest') )
		opts     = ('no_relay','tx_relay_daemon')

		def init_tx_relay_daemon(self):

			m = re.fullmatch(
				uarg_info['tx_relay_daemon'].pat,
				self.cfg.tx_relay_daemon,
				re.ASCII )

			wd2 = MoneroWalletDaemon(
				cfg         = self.cfg,
				proto       = self.proto,
				wallet_dir  = self.cfg.wallet_dir or '.',
				test_suite  = self.cfg.test_suite,
				daemon_addr = m[1],
				proxy       = m[2] )

			if self.cfg.test_suite:
				wd2.usr_daemon_args = ['--daemon-ssl-allow-any-cert']

			wd2.start()

			self.c = MoneroWalletRPCClient(
				cfg    = self.cfg,
				daemon = wd2 )

		async def main(self):

			gmsg(f'\n{self.stem.capitalize()}ing account #{self.account} of wallet {self.source.idx}' + (
				f': {self.amount} XMR to {self.dest_addr}' if self.name == 'transfer'
				else ' to new address' if self.dest == None
				else f' to new account in wallet {self.dest.idx}' ))

			h = self.rpc(self,self.source)

			h.open_wallet('source')
			accts_data = h.get_accts()[0]

			max_acct = len(accts_data['subaddress_accounts']) - 1
			if self.account > max_acct:
				die(1,f'{self.account}: requested account index out of bounds (>{max_acct})')

			h.print_addrs(accts_data,self.account)

			if self.name == 'transfer':
				dest_addr = self.dest_addr
			elif self.dest == None:
				dest_acct = self.account
				if keypress_confirm( self.cfg, f'\nCreate new address for account #{self.account}?' ):
					dest_addr_chk = h.create_new_addr(self.account)
				elif keypress_confirm( self.cfg, f'Sweep to last existing address of account #{self.account}?' ):
					dest_addr_chk = None
				else:
					die(1,'Exiting at user request')
				dest_addr,dest_addr_idx = h.get_last_addr(self.account,display=not dest_addr_chk)
				assert dest_addr_chk in (None,dest_addr), 'dest_addr_chk1'
				h.print_addrs(accts_data,self.account)
			else:
				h.close_wallet('source')
				bn = os.path.basename(self.get_wallet_fn(self.dest))
				h2 = self.rpc(self,self.dest)
				h2.open_wallet('destination')
				accts_data = h2.get_accts()[0]

				if keypress_confirm( self.cfg, f'\nCreate new account for wallet {bn!r}?' ):
					dest_acct,dest_addr = h2.create_acct()
					dest_addr_idx = 0
					h2.get_accts()
				elif keypress_confirm( self.cfg, f'Sweep to last existing account of wallet {bn!r}?' ):
					dest_acct,dest_addr_chk = h2.get_last_acct(accts_data)
					dest_addr,dest_addr_idx = h2.get_last_addr(dest_acct,display=False)
					assert dest_addr_chk == dest_addr, 'dest_addr_chk2'
				else:
					die(1,'Exiting at user request')

				h2.close_wallet('destination')
				h.open_wallet('source',refresh=False)

			msg(f'\n    Creating {self.name} transaction...')

			if self.name == 'transfer':
				new_tx = h.make_transfer_tx(self.account,dest_addr,self.amount)
			elif self.name == 'sweep':
				new_tx = h.make_sweep_tx(self.account,dest_acct,dest_addr_idx,dest_addr)

			msg('\n' + new_tx.get_info(indent='    '))

			if self.cfg.tx_relay_daemon:
				self.display_tx_relay_info(indent='    ')

			msg('Saving TX data to file')
			new_tx.write(delete_metadata=True)

			if self.cfg.no_relay:
				return True

			if keypress_confirm( self.cfg, f'Relay {self.name} transaction?' ):
				w_desc = 'source'
				if self.cfg.tx_relay_daemon:
					await h.stop_wallet('source')
					msg('')
					self.init_tx_relay_daemon()
					h = self.rpc(self,self.source)
					w_desc = 'TX relay source'
					h.open_wallet(w_desc,refresh=False)
				msg_r(f'\n    Relaying {self.name} transaction...')
				h.relay_tx(new_tx.data.metadata)
				gmsg('\nAll done')
				return True
			else:
				die(1,'\nExiting at user request')

	class transfer(sweep):
		stem    = 'transferr'
		spec_id = 'transfer_spec'
		spec_key = ( (1,'source'), )

	class new(spec):
		spec_id = 'newaddr_spec'
		spec_key = ( (1,'source'), )

		async def main(self):
			h = self.rpc(self,self.source)
			h.open_wallet('Monero',refresh=True)
			label = '{a} [{b}]'.format(
				a = self.label or f"xmrwallet new {'account' if self.account == None else 'address'}",
				b = make_timestr() )
			if self.account == None:
				acct,addr = h.create_acct(label=label)
			else:
				msg_r('\n    Account index: {}'.format( pink(str(self.account)) ))
				addr = h.create_new_addr(self.account,label=label)

			accts_data = h.get_accts()[0]

			if self.account != None:
				h.print_addrs(accts_data,self.account)

			# wallet must be left open: otherwise the 'stop_wallet' RPC call used to stop the daemon will fail
			if self.cfg.no_stop_wallet_daemon:
				h.close_wallet('Monero')

			msg('')

	class label(spec):
		spec_id  = 'label_spec'
		spec_key = ( (1,'source'), )
		opts     = ()

		async def main(self):

			gmsg('\n{} label for wallet {}, account #{}, address #{}'.format(
				'Setting' if self.label else 'Removing',
				self.source.idx,
				self.account,
				self.address_idx
			))
			h = self.rpc(self,self.source)

			h.open_wallet('source')
			accts_data = h.get_accts()[0]

			max_acct = len(accts_data['subaddress_accounts']) - 1
			if self.account > max_acct:
				die(1,f'{self.account}: requested account index out of bounds (>{max_acct})')

			ret = h.print_addrs(accts_data,self.account)

			if self.address_idx > len(ret['addresses']) - 1:
				die(1,'{}: requested address index out of bounds (>{})'.format(
					self.account,
					len(ret['addresses']) - 1 ))

			addr = ret['addresses'][self.address_idx]

			msg('\n  {} {}\n  {} {}\n  {} {}'.format(
					'Address:       ',
					cyan(addr['address'][:15] + '...'),
					'Existing label:',
					pink(addr['label']) if addr['label'] else '[none]',
					'New label:     ',
					pink(self.label) if self.label else '[none]' ))

			if addr['label'] == self.label:
				ymsg('\nLabel is unchanged, operation cancelled')
			elif keypress_confirm( self.cfg, '  {} label?'.format('Set' if self.label else 'Remove') ):
				h.set_label( self.account, self.address_idx, self.label )
				accts_data = h.get_accts(print=False)[0]
				ret = h.print_addrs(accts_data,self.account)
				new_label = ret['addresses'][self.address_idx]['label']
				if new_label != self.label:
					ymsg(f'Warning: new label {new_label!r} does not match requested value!')
					return False
				else:
					msg(cyan('\nLabel successfully {}'.format('set' if self.label else 'removed')))
			else:
				ymsg('\nOperation cancelled by user request')

	class relay(base):
		opts = ('tx_relay_daemon',)

		def __init__(self,cfg,uarg_tuple):

			super().__init__(cfg,uarg_tuple)

			self.tx = MoneroMMGenTX.Signed( self.cfg, uarg.infile )

			if self.cfg.tx_relay_daemon:
				m = re.fullmatch(
					uarg_info['tx_relay_daemon'].pat,
					self.cfg.tx_relay_daemon,
					re.ASCII )
				host,port = m[1].split(':')
				proxy = m[2]
				md = None
			else:
				from .daemon import CoinDaemon
				md = CoinDaemon( self.cfg, 'xmr', test_suite=self.cfg.test_suite )
				host,port = md.host,md.rpc_port
				proxy = None

			self.dc = MoneroRPCClient(
				cfg    = self.cfg,
				proto  = self.proto,
				daemon = md,
				host   = host,
				port   = int(port),
				user   = None,
				passwd = None,
				test_connection = False, # relay is presumably a public node, so avoid extra connections
				proxy  = proxy )

		async def main(self):
			msg('\n' + self.tx.get_info())

			if self.cfg.tx_relay_daemon:
				self.display_tx_relay_info()

			if keypress_confirm( self.cfg, 'Relay transaction?' ):
				res = self.dc.call_raw(
					'send_raw_transaction',
					tx_as_hex = self.tx.data.blob
				)
				if res['status'] == 'OK':
					msg('Status: ' + green('OK'))
					if res['not_relayed']:
						ymsg('Transaction not relayed')
					return True
				else:
					die( 'RPCFailure', repr(res) )
			else:
				die(1,'Exiting at user request')

	class txview(base):

		async def main(self):
			self.cfg._util.stdout_or_pager(
				'\n'.join(
					tx.get_info() for tx in
					sorted(
						(MoneroMMGenTX.Completed( self.cfg, fn ) for fn in uarg.infile),
						key = lambda x: x.data.sign_time )
			))
