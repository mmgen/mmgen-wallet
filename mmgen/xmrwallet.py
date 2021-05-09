#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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

import os,re
from collections import namedtuple
from .common import *
from .addr import KeyAddrList,AddrIdxList
from .rpc import MoneroRPCClientRaw, MoneroWalletRPCClient
from .daemon import MoneroWalletDaemon

xmrwallet_uarg_info = (
	lambda e,hp: {
		'daemon':          e('HOST:PORT', hp),
		'tx_relay_daemon': e('HOST:PORT[:PROXY_HOST:PROXY_PORT]', r'({p})(?::({p}))?'.format(p=hp)),
		'wallets_sweep':   e('SOURCE_WALLET_NUM:ACCOUNT[,DEST_WALLET_NUM]', r'(\d+):(\d+)(?:,(\d+))?'),
	})(
		namedtuple('uarg_info_entry',['annot','pat']),
		r'(?:[^:]+):(?:\d+)'
	)

class MoneroWalletOps:

	ops = ('create','sync','sweep')

	class base:

		class rpc:

			def __init__(self,parent,d):
				self.parent = parent
				self.c = parent.c
				self.d = d
				self.fn = parent.get_wallet_fn(d)

			async def open_wallet(self,desc):
				gmsg_r(f'\n  Opening {desc} wallet...')
				ret = await self.c.call( # returns {}
					'open_wallet',
					filename=os.path.basename(self.fn),
					password=self.d.wallet_passwd )
				gmsg('done')

			async def close_wallet(self,desc):
				gmsg_r(f'\n  Closing {desc} wallet...')
				await self.c.call('close_wallet')
				gmsg_r('done')

			def print_accts(self,data,addrs_data,indent='    '):
				d = data['subaddress_accounts']
				msg('\n' + indent + f'Accounts of wallet {os.path.basename(self.fn)}:')
				fs = indent + '  {:6}  {:18}  {:<6} {:%s}  {}' % max(len(e['label']) for e in d)
				msg(fs.format('Index ','Base Address','nAddrs','Label','Balance'))
				for i,e in enumerate(d):
					msg(fs.format(
						str(e['account_index']),
						e['base_address'][:15] + '...',
						len(addrs_data[i]['addresses']),
						e['label'],
						fmt_amt(e['balance']),
					))

			async def get_accts(self,print=True):
				data = await self.c.call('get_accounts')
				addrs_data = [
					await self.c.call('get_address',account_index=i)
						for i in range(len(data['subaddress_accounts']))
				]
				if print:
					self.print_accts(data,addrs_data)
				return ( data, addrs_data )

			async def create_acct(self):
				msg('\n    Creating new account...')
				ret = await self.c.call(
					'create_account',
					label = f'Sweep from {self.parent.source.idx}:{self.parent.account}'
				)
				msg('      Index:   {}'.format( pink(str(ret['account_index'])) ))
				msg('      Address: {}'.format( cyan(ret['address']) ))
				return ret['address']

			def get_last_acct(self,accts_data):
				msg('\n    Getting last account...')
				data = accts_data['subaddress_accounts'][-1]
				msg('      Index:   {}'.format( pink(str(data['account_index'])) ))
				msg('      Address: {}'.format( cyan(data['base_address']) ))
				return data['base_address']

			async def get_addrs(self,accts_data,account):
				ret = await self.c.call('get_address',account_index=account)
				d = ret['addresses']
				msg('\n      Addresses of account #{} ({}):'.format(
					account,
					accts_data['subaddress_accounts'][account]['label']))
				fs = '        {:6}  {:18}  {:%s}  {}' % max(len(e['label']) for e in d)
				msg(fs.format('Index ','Address','Label','Used'))
				for e in d:
					msg(fs.format(
						str(e['address_index']),
						e['address'][:15] + '...',
						e['label'],
						e['used']
					))
				return ret

			async def create_new_addr(self,account):
				msg_r('\n    Creating new address: ')
				ret = await self.c.call(
					'create_address',
					account_index = account,
					label         = 'Sweep from this account',
				)
				msg(cyan(ret['address']))
				return ret['address']

			async def get_last_addr(self,account):
				msg('\n    Getting last address:')
				ret = (await self.c.call(
					'get_address',
					account_index = account,
				))['addresses'][-1]['address']
				msg('      ' + cyan(ret))
				return ret

			def display_tx_relay_info(self):
				msg('\n    TX relay host: {}\n    Proxy:         {}'.format(
					blue(self.parent.wd2.daemon_addr),
					blue(self.parent.wd2.proxy)
				))

			def display_sweep_tx(self,data):
				from .obj import CoinTxID
				msg('    TxID:   {}\n    Amount: {}\n    Fee:    {}'.format(
					CoinTxID(data['tx_hash_list'][0]).hl(),
					hl_amt(data['amount_list'][0]),
					hl_amt(data['fee_list'][0]),
				))

			async def make_sweep_tx(self,account,addr):
				ret = await self.c.call(
					'sweep_all',
					address = addr,
					account_index = account,
					do_not_relay = True,
					get_tx_metadata = True
				)
				self.display_sweep_tx(ret)
				return ret

			def display_txid(self,data):
				from .obj import CoinTxID
				msg('\n    Relayed {}'.format( CoinTxID(data['tx_hash']).hl() ))

			async def relay_sweep_tx(self,tx_hex):
				ret = await self.c.call('relay_tx',hex=tx_hex)
				try:
					self.display_txid(ret)
				except:
					msg('\n'+str(ret))

		wallet_exists = True
		tx_relay = False

		def check_uargs(self):

			def check_host_arg(name):
				val = getattr(uarg,name)
				if not re.fullmatch(uarg_info[name].pat,val,re.ASCII):
					die(1,'{!r}: invalid {!r} parameter: it must have format {!r}'.format(
						val, name, uarg_info[name].annot ))

			if uarg.op != 'create' and uarg.restore_height != 0:
				die(1,"'restore_height' arg is supported only for create operation")

			if uarg.restore_height < 0:
				die(1,f"{uarg.restore_height}: invalid 'restore_height' arg (<0)")

			if uarg.daemon:
				check_host_arg('daemon')

			if uarg.tx_relay_daemon:
				if not self.tx_relay:
					die(1,f"'tx_relay_daemon' arg is not recognized for operation {uarg.op!r}")
				check_host_arg('tx_relay_daemon')

		def __init__(self,uarg_tuple):

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

			global uarg, uarg_info, fmt_amt, hl_amt

			uarg = uarg_tuple
			uarg_info = xmrwallet_uarg_info

			from .obj import XMRAmt
			def fmt_amt(amt):
				return XMRAmt(amt,from_unit='min_coin_unit').fmt(fs='5.12',color=True)
			def hl_amt(amt):
				return XMRAmt(amt,from_unit='min_coin_unit').hl()

			self.check_uargs()

			from .protocol import init_proto
			self.kal = KeyAddrList(init_proto('xmr',network='mainnet'),uarg.xmr_keyaddrfile)
			self.create_addr_data()

			check_wallets()

			self.wd = MoneroWalletDaemon(
				wallet_dir = opt.outdir or '.',
				test_suite = g.test_suite,
				daemon_addr = uarg.daemon or None,
			)

			if uarg.start_wallet_daemon:
				self.wd.restart()

			self.c = MoneroWalletRPCClient(
				host   = self.wd.host,
				port   = self.wd.rpc_port,
				user   = self.wd.user,
				passwd = self.wd.passwd
			)

			self.post_init()

		def create_addr_data(self):
			if uarg.wallets:
				idxs = AddrIdxList(uarg.wallets)
				self.addr_data = [d for d in self.kal.data if d.idx in idxs]
				if len(self.addr_data) != len(idxs):
					die(1,f'List {uarg.wallets!r} contains addresses not present in supplied key-address file')
			else:
				self.addr_data = self.kal.data

		def stop_daemons(self):
			if uarg.stop_wallet_daemon:
				self.wd.stop()
				if uarg.tx_relay_daemon:
					self.wd2.stop()

		def post_init(self): pass
		def post_process(self): pass

		def get_wallet_fn(self,d):
			return os.path.join(
				opt.outdir or '.','{}-{}-MoneroWallet{}'.format(
					self.kal.al_id.sid,
					d.idx,
					'-α' if g.debug_utf8 else ''))

		async def process_wallets(self):
			gmsg('\n{}ing {} wallet{}'.format(self.desc,len(self.addr_data),suf(self.addr_data)))
			processed = 0
			for n,d in enumerate(self.addr_data): # [d.sec,d.addr,d.wallet_passwd,d.viewkey]
				fn = self.get_wallet_fn(d)
				gmsg('\n{}ing wallet {}/{} ({})'.format(
					self.desc,
					n+1,
					len(self.addr_data),
					os.path.basename(fn),
				))
				processed += await self.run(d,fn)
			gmsg('\n{} wallet{} {}'.format(processed,suf(processed),self.past))
			return processed

	class create(base):
		name    = 'create'
		desc    = 'Creat'
		past    = 'created'
		wallet_exists = False

		async def run(self,d,fn):

			from .baseconv import baseconv
			ret = await self.c.call(
				'restore_deterministic_wallet',
				filename       = os.path.basename(fn),
				password       = d.wallet_passwd,
				seed           = baseconv.fromhex(d.sec,'xmrseed',tostr=True),
				restore_height = uarg.restore_height,
				language       = 'English' )

			pp_msg(ret) if opt.debug else msg('  Address: {}'.format(ret['address']))
			return True

	class sync(base):
		name    = 'sync'
		desc    = 'Sync'
		past    = 'synced'

		async def run(self,d,fn):

			chain_height = (await self.dc.call('get_height'))['height']
			msg(f'  Chain height: {chain_height}')

			import time
			t_start = time.time()

			msg_r('  Opening wallet...')
			await self.c.call(
				'open_wallet',
				filename=os.path.basename(fn),
				password=d.wallet_passwd )
			msg('done')

			msg_r('  Getting wallet height (be patient, this could take a long time)...')
			wallet_height = (await self.c.call('get_height'))['height']
			msg_r('\r' + ' '*68 + '\r')
			msg(f'  Wallet height: {wallet_height}        ')

			behind = chain_height - wallet_height
			if behind > 1000:
				msg_r(f'  Wallet is {behind} blocks behind chain tip.  Please be patient.  Syncing...')

			ret = await self.c.call('refresh')

			if behind > 1000:
				msg('done')

			if ret['received_money']:
				msg('  Wallet has received funds')

			t_elapsed = int(time.time() - t_start)

			bn = os.path.basename(fn)

			a,b = await self.rpc(self,d).get_accts(print=False)

			msg('  Balance: {} Unlocked balance: {}'.format(
				hl_amt(a['total_balance']),
				hl_amt(a['total_unlocked_balance']),
			))

			self.accts_data[bn] = { 'accts': a, 'addrs': b }

			msg('  Wallet height: {}'.format( (await self.c.call('get_height'))['height'] ))
			msg('  Sync time: {:02}:{:02}'.format( t_elapsed//60, t_elapsed%60 ))

			await self.c.call('close_wallet')
			return True

		def post_init(self):
			host,port = uarg.daemon.split(':') if uarg.daemon else ('localhost',self.wd.daemon_port)
			self.dc = MoneroRPCClientRaw(host=host, port=int(port), user=None, passwd=None)
			self.accts_data = {}

		def post_process(self):
			d = self.accts_data

			for n,k in enumerate(d):
				ad = self.addr_data[n]
				self.rpc(self,ad).print_accts( d[k]['accts'], d[k]['addrs'], indent='')

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

	class sweep(base):
		name    = 'sweep'
		desc    = 'Sweep'
		past    = 'swept'
		tx_relay = True

		def create_addr_data(self):
			m = re.fullmatch(uarg_info['wallets_sweep'].pat,uarg.wallets,re.ASCII)
			if not m:
				fs = "{!r}: invalid 'wallets' arg: for sweep operation, it must have format {!r}"
				die(1,fs.format( uarg.wallets, uarg_info['wallets_sweep'].annot ))

			def gen():
				for i,k in ( (1,'source'), (3,'dest') ):
					if m[i] == None:
						setattr(self,k,None)
					else:
						idx = int(m[i])
						try:
							res = [d for d in self.kal.data if d.idx == idx][0]
						except:
							die(1,'Supplied key-address file does not contain address {}:{}'.format(
								self.kal.al_id.sid,
								idx ))
						else:
							setattr(self,k,res)
							yield res

			self.addr_data = list(gen())
			self.account = int(m[2])

		def post_init(self):

			if uarg.tx_relay_daemon:
				m = re.fullmatch(uarg_info['tx_relay_daemon'].pat,uarg.tx_relay_daemon,re.ASCII)

				self.wd2 = MoneroWalletDaemon(
					wallet_dir = opt.outdir or '.',
					test_suite = g.test_suite,
					daemon_addr = m[1],
					proxy = m[2],
					port_shift = 16,
				)

				if uarg.start_wallet_daemon:
					self.wd2.restart()

				self.c2 = MoneroWalletRPCClient(
					host   = self.wd2.host,
					port   = self.wd2.rpc_port,
					user   = self.wd2.user,
					passwd = self.wd2.passwd
				)

		async def process_wallets(self):
			gmsg(f'\nSweeping account #{self.account} of wallet {self.source.idx}' + (
				' to new address' if self.dest is None else
				f' to new account in wallet {self.dest.idx}' ))

			h = self.rpc(self,self.source)

			await h.open_wallet('source')
			accts_data = (await h.get_accts())[0]

			max_acct = len(accts_data['subaddress_accounts']) - 1
			if self.account > max_acct:
				die(1,f'{self.account}: requested account index out of bounds (>{max_acct})')

			await h.get_addrs(accts_data,self.account)

			if self.dest == None:
				if keypress_confirm(f'\nCreate new address for account #{self.account}?'):
					new_addr = await h.create_new_addr(self.account)
				elif keypress_confirm(f'Sweep to last existing address of account #{self.account}?'):
					new_addr = await h.get_last_addr(self.account)
				else:
					die(1,'Exiting at user request')
				await h.get_addrs(accts_data,self.account)
			else:
				await h.close_wallet('source')
				bn = os.path.basename(self.get_wallet_fn(self.dest))
				h2 = self.rpc(self,self.dest)
				await h2.open_wallet('destination')
				accts_data = (await h2.get_accts())[0]

				if keypress_confirm(f'\nCreate new account for wallet {bn!r}?'):
					new_addr = await h2.create_acct()
					await h2.get_accts()
				elif keypress_confirm(f'Sweep to last existing account of wallet {bn!r}?'):
					new_addr = h2.get_last_acct(accts_data)
				else:
					die(1,'Exiting at user request')

				await h2.close_wallet('destination')
				await h.open_wallet('source')

			msg('\n    Creating sweep transaction: balance of wallet {}, account #{} => {}'.format(
				self.source.idx,
				self.account,
				cyan(new_addr),
			))
			sweep_tx = await h.make_sweep_tx(self.account,new_addr)

			if keypress_confirm('Relay sweep transaction?'):
				w_desc = 'source'
				if uarg.tx_relay_daemon:
					await h.close_wallet('source')
					self.c = self.c2
					h = self.rpc(self,self.source)
					w_desc = 'TX relay source'
					await h.open_wallet(w_desc)
				h.display_tx_relay_info()
				msg_r(f'    Relaying sweep transaction...')
				await h.relay_sweep_tx( sweep_tx['tx_metadata_list'][0] )
				await h.close_wallet(w_desc)

				gmsg('\n\nAll done')
			else:
				await h.close_wallet('source')
				die(1,'\nExiting at user request')

			return True