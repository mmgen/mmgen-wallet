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
ts_xmrwallet.py: xmrwallet tests for the test.py test suite
"""

import sys,os,atexit,asyncio,shutil
from subprocess import run,PIPE

from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.obj import MMGenRange
from mmgen.amt import XMRAmt
from mmgen.addrlist import KeyAddrList,AddrIdxList
from ..include.common import *
from .common import *

from .ts_base import *

class TestSuiteXMRWallet(TestSuiteBase):
	"""
	Monero wallet operations
	"""
	networks = ('xmr',)
	passthru_opts = ()
	tmpdir_nums = [29]
	dfl_random_txs = 3
	color = True
	cmd_group = (
		('gen_kafiles',               'generating key-address files'),
		('create_wallets_miner',      'creating Monero wallets (Miner)'),
		('mine_initial_coins',        'mining initial coins'),
		('create_wallets_alice',      'creating Monero wallets (Alice)'),
		('fund_alice',                'sending funds'),

		('sync_wallets_all',          'syncing all wallets'),
		('sync_wallets_selected',     'syncing selected wallets'),

		('sweep_to_address_proxy',    'sweeping to new address (via TX relay + proxy)'),
		('sweep_to_account',          'sweeping to new account'),
		('sweep_to_address_noproxy',  'sweeping to new address (via TX relay, no proxy)'),
		('transfer_to_miner_proxy',   'transferring funds to Miner (via TX relay + proxy)'),
		('transfer_to_miner_noproxy', 'transferring funds to Miner (via TX relay, no proxy)'),

		('transfer_to_miner_create1', 'transferring funds to Miner (create TX)'),
		('transfer_to_miner_send1',   'transferring funds to Miner (send TX via proxy)'),
		('transfer_to_miner_create2', 'transferring funds to Miner (create TX)'),
		('transfer_to_miner_send2',   'transferring funds to Miner (send TX, no proxy)'),

		('sweep_create_and_send',     'sweeping to new account (create TX + send TX, in stages)'),
	)

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return

		from mmgen.protocol import init_proto
		self.proto = init_proto('XMR',network='testnet')
		self.datadir_base  = os.path.join('test','daemons','xmrtest')
		self.extra_opts = ['--testnet=1', '--wallet-rpc-password=passw0rd']
		self.init_users()
		self.init_daemon_args()

		for v in self.users.values():
			run(['mkdir','-p',v.udir])

		self.init_proxy()

		self.tx_relay_daemon_parm = 'localhost:{}'.format( self.users['bob'].md.rpc_port )
		self.tx_relay_daemon_proxy_parm = (
			self.tx_relay_daemon_parm + f':127.0.0.1:{self.socks_port}' # proxy must be IP, not 'localhost'
			if self.use_proxy else None )

		if not opt.no_daemon_stop:
			atexit.register(self.stop_daemons)
			atexit.register(self.stop_miner_wallet_daemon)

		if not opt.no_daemon_autostart:
			self.stop_daemons()
			shutil.rmtree(self.datadir_base,ignore_errors=True)
			os.makedirs(self.datadir_base)
			self.start_daemons()

		self.balance = None

	# init methods

	def init_proxy(self):

		def port_in_use(port):
			import socket
			try: socket.create_connection(('localhost',port)).close()
			except: return False
			else: return True

		def start_proxy():
			if not opt.no_daemon_autostart:
				run(a+b2)
				omsg(f'SSH SOCKS server started, listening at localhost:{self.socks_port}')

		def kill_proxy():
			if g.platform == 'linux':
				omsg(f'Killing SSH SOCKS server at localhost:{self.socks_port}')
				cmd = [ 'pkill', '-f', ' '.join(a + b2) ]
				run(cmd)

		self.use_proxy = False
		self.socks_port = 9060
		a = ['ssh','-x','-o','ExitOnForwardFailure=True','-D',f'localhost:{self.socks_port}']
		b0 = ['-o','PasswordAuthentication=False']
		b1 = ['localhost','true']
		b2 = ['-fN','-E','txrelay-proxy.debug','localhost']

		if port_in_use(self.socks_port):
			omsg(f'Port {self.socks_port} already in use.  Assuming SSH SOCKS server is running')
			self.use_proxy = True
		else:
			cp = run(a+b0+b1,stdout=PIPE,stderr=PIPE)
			err = cp.stderr.decode()
			if err:
				omsg(err)

			if cp.returncode == 0:
				start_proxy()
				self.use_proxy = True
			elif 'onnection refused' in err:
				die(2,fmt("""
					The SSH daemon must be running and listening on localhost in order to test
					XMR TX relaying via SOCKS proxy.  If sshd is not running, please start it.
					Otherwise, add the line 'ListenAddress 127.0.0.1' to your sshd_config, and
					then restart the daemon.
				""",indent='    '))
			elif 'ermission denied' in err:
				msg(fmt(f"""
					In order to test XMR TX relaying via SOCKS proxy, it’s desirable to enable
					SSH to localhost without a password, which is not currently supported by
					your configuration.  Your possible courses of action:

					1. Continue by answering 'y' at this prompt, and enter your system password
					   at the following prompt;

					2. Exit the test here, add your user SSH public key to your user
					   'authorized_keys' file, and restart the test; or

					3. Exit the test here, start the SSH SOCKS proxy manually by entering the
					   following command, and restart the test:

					      {' '.join(a+b2)}
				""",indent='    ',strip_char='\t'))

				if keypress_confirm('Continue?'):
					start_proxy()
					self.use_proxy = True
				else:
					die(1,'Exiting at user request')
			else:
				die(2,fmt(f"""
					Please start the SSH SOCKS proxy by entering the following command:

						{' '.join(a+b2)}

					Then restart the test.
				""",indent='    '))

		if not opt.no_daemon_stop:
			atexit.register(kill_proxy)

	def init_users(self):
		from mmgen.daemon import CoinDaemon
		from mmgen.base_proto.monero.daemon import MoneroWalletDaemon
		from mmgen.base_proto.monero.rpc import MoneroRPCClient,MoneroRPCClientRaw,MoneroWalletRPCClient
		self.users = {}
		n = self.tmpdir_nums[0]
		ud = namedtuple('user_data',[
			'sid',
			'mmwords',
			'udir',
			'datadir',
			'kal_range',
			'kafile',
			'walletfile_fs',
			'addrfile_fs',
			'md',
			'md_rpc',
			'md_json_rpc',
			'wd',
			'wd_rpc',
		])
		for user,sid,shift,kal_range in ( # kal_range must be None, a single digit, or a single hyphenated range
				('miner', '98831F3A', 130,  '1-2'),
				('bob',   '1378FC64', 140, None),
				('alice', 'FE3C6545', 150, '1-4'),
			):
			udir = os.path.join('test',f'tmp{n}',user)
			datadir = os.path.join(self.datadir_base,user)
			md = CoinDaemon(
				proto      = self.proto,
				test_suite = True,
				port_shift = shift,
				opts       = ['online'],
				datadir    = datadir
			)
			md_rpc = MoneroRPCClientRaw(
				host   = md.host,
				port   = md.rpc_port,
				user   = None,
				passwd = None,
				test_connection = False,
				daemon = md,
			)
			md_json_rpc = MoneroRPCClient(
				host   = md.host,
				port   = md.rpc_port,
				user   = None,
				passwd = None,
				test_connection = False,
				daemon = md,
			)
			wd = MoneroWalletDaemon(
				proto      = self.proto,
				test_suite = True,
				wallet_dir = udir,
				user       = 'foo',
				passwd     = 'bar',
				port_shift = shift,
				datadir    = os.path.join('test','daemons'),
				daemon_addr = f'127.0.0.1:{md.rpc_port}',
			)
			wd_rpc = MoneroWalletRPCClient( daemon=wd, test_connection=False )
			self.users[user] = ud(
				sid           = sid,
				mmwords       = f'test/ref/{sid}.mmwords',
				udir          = udir,
				datadir       = datadir,
				kal_range     = kal_range,
				kafile        = f'{udir}/{sid}-XMR-M[{kal_range}].testnet.akeys',
				walletfile_fs = f'{udir}/{sid}-{{}}-MoneroWallet.testnet',
				addrfile_fs   = f'{udir}/{sid}-{{}}-MoneroWallet.testnet.address.txt',
				md            = md,
				md_rpc        = md_rpc,
				md_json_rpc   = md_json_rpc,
				wd            = wd,
				wd_rpc        = wd_rpc,
			)

	def init_daemon_args(self):
		common_args = ['--p2p-bind-ip=127.0.0.1','--fixed-difficulty=1'] # ,'--rpc-ssl-allow-any-cert']
		for u in self.users:
			other_ports = [self.users[u2].md.p2p_port for u2 in self.users if u2 != u]
			node_args = [f'--add-exclusive-node=127.0.0.1:{p}' for p in other_ports]
			self.users[u].md.usr_coind_args = common_args + node_args

	# cmd_group methods

	def gen_kafiles(self):
		for user,data in self.users.items():
			if not data.kal_range:
				continue
			run(['mkdir','-p',data.udir])
			run(f'rm -f {data.kafile}',shell=True)
			t = self.spawn(
				'mmgen-keygen', [
					'--testnet=1','-q', '--accept-defaults', '--coin=xmr',
					f'--outdir={data.udir}', data.mmwords, data.kal_range
				],
				extra_desc = f'({capfirst(user)})' )
			t.read()
			t.ok()
		t.skip_ok = True
		return t

	def create_wallets_miner(self): return self.create_wallets('miner')
	def create_wallets_alice(self): return self.create_wallets('alice')

	def create_wallets(self,user,wallet=None):
		assert wallet is None or is_int(wallet), 'wallet arg'
		data = self.users[user]
		run(
			'rm -f {}*'.format( data.walletfile_fs.format(wallet or '*') ),
			shell = True
		)
		dir_opt = [f'--wallet-dir={data.udir}']
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts + dir_opt + [ 'create', data.kafile, (wallet or data.kal_range) ] )
		t.expect('Check key-to-address validity? (y/N): ','n')
		for i in MMGenRange(wallet or data.kal_range).items:
			t.expect('Address: ')
		return t

	async def mine_initial_coins(self):
		await self.open_wallet_user('miner',1)
		return await self.mine_chk('miner',1,0,lambda x: x > 20,'unlocked balance > 20')

	async def fund_alice(self):
		await self.transfer(
			'miner',
			1234567891234,
			read_from_file(self.users['alice'].addrfile_fs.format(1)),
		)
		bal = '1.234567891234'
		return await self.mine_chk(
			'alice',1,0,
			lambda x: str(x) == bal,f'unlocked balance == {bal}',
			random_txs = self.dfl_random_txs
		)

	def sync_wallets_all(self):
		return self.sync_wallets('alice',add_opts=['--rescan-blockchain'])

	def sync_wallets_selected(self):
		return self.sync_wallets('alice',wallets='1-2,4')

	def sync_wallets(self,user,wallets=None,add_opts=None):
		data = self.users[user]
		cmd_opts = list_gen(
			[f'--wallet-dir={data.udir}'],
			[f'--daemon=localhost:{data.md.rpc_port}'],
		)
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts + cmd_opts + (add_opts or []) + [ 'sync', data.kafile ] + ([wallets] if wallets else []) )
		t.expect('Check key-to-address validity? (y/N): ','n')
		wlist = AddrIdxList(wallets) if wallets else MMGenRange(data.kal_range).items
		for n,wnum in enumerate(wlist):
			t.expect('Syncing wallet {}/{} ({})'.format(
				n+1,
				len(wlist),
				os.path.basename(data.walletfile_fs.format(wnum)),
			))
			t.expect('Chain height: ')
			t.expect('Wallet height: ')
			t.expect('Balance: ')
		return t

	def do_op(self, op, user, arg2,
			tx_relay_parm = None,
			do_not_relay  = False,
			return_amt    = False,
			reuse_acct    = False,
			add_desc      = None,
			do_ret        = False ):

		data = self.users[user]
		cmd_opts = list_gen(
			[f'--wallet-dir={data.udir}'],
			[f'--outdir={data.udir}'],
			[f'--daemon=localhost:{data.md.rpc_port}'],
			[f'--tx-relay-daemon={tx_relay_parm}', tx_relay_parm],
			['--do-not-relay', do_not_relay]
		)
		add_desc = (', ' + add_desc) if add_desc else ''

		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts + cmd_opts + [ op, data.kafile, arg2 ],
			extra_desc = f'({capfirst(user)}{add_desc})' )

		t.expect('Check key-to-address validity? (y/N): ','n')

		if op == 'sweep':
			t.expect(
				r'Create new {} .* \(y/N\): '.format(('address','account')[',' in arg2]),
				('y','n')[reuse_acct],
				regex=True )
			if reuse_acct:
				t.expect( r'to last existing account .* \(y/N\): ','y', regex=True )

		if return_amt:
			amt = XMRAmt(strip_ansi_escapes(t.expect_getend('Amt: ')).replace('XMR','').strip())

		if do_not_relay:
			t.expect('Save MoneroMMGenTX data? (y/N): ','y')
			t.written_to_file('MoneroMMGenTX data')
		else:
			t.expect(f'Relay {op} transaction? (y/N): ','y')

		t.read()

		return t if do_ret else amt if return_amt else t.ok()

	def sweep_to_address_proxy(self):
		self.do_op('sweep','alice','1:0',self.tx_relay_daemon_proxy_parm)
		return self.mine_chk('alice',1,0,lambda x: x > 1,'unlocked balance > 1')

	def sweep_to_account(self):
		self.do_op('sweep','alice','1:0,2')
		return self.mine_chk('alice',2,1,lambda x: x > 1,'unlocked balance > 1')

	def sweep_to_address_noproxy(self):
		self.do_op('sweep','alice','2:1',self.tx_relay_daemon_parm)
		return self.mine_chk('alice',2,1,lambda x: x > 0.9,'unlocked balance > 0.9')

	async def transfer_to_miner_proxy(self):
		addr = read_from_file(self.users['miner'].addrfile_fs.format(2))
		amt = '0.135'
		self.do_op('transfer','alice',f'2:1:{addr},{amt}',self.tx_relay_daemon_proxy_parm)
		await self.stop_wallet_user('miner')
		await self.open_wallet_user('miner',2)
		await self.mine_chk('miner',2,0,lambda x: str(x) == amt,f'unlocked balance == {amt}')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x > 0.9,'unlocked balance > 0.9')

	async def transfer_to_miner_noproxy(self):
		addr = read_from_file(self.users['miner'].addrfile_fs.format(2))
		self.do_op('transfer','alice',f'2:1:{addr},0.0995',self.tx_relay_daemon_parm)
		await self.mine_chk('miner',2,0,lambda x: str(x) == '0.2345','unlocked balance == 0.2345')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x > 0.9,'unlocked balance > 0.9')

	def transfer_to_miner_create(self,amt):
		get_file_with_ext(self.users['alice'].udir,'sigtx',delete_all=True)
		addr = read_from_file(self.users['miner'].addrfile_fs.format(2))
		return self.do_op('transfer','alice',f'2:1:{addr},{amt}',do_not_relay=True,do_ret=True)

	def transfer_to_miner_create1(self):
		return self.transfer_to_miner_create('0.0111')

	def transfer_to_miner_create2(self):
		return self.transfer_to_miner_create('0.0012')

	def relay_tx(self,relay_opt=None,add_desc=None):
		user = 'alice'
		data = self.users[user]
		fn = get_file_with_ext(data.udir,'sigtx')
		add_desc = (', ' + add_desc) if add_desc else ''
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ ([relay_opt] if relay_opt else [])
			+ [ 'relay', fn ],
			extra_desc = f'(relaying TX, {capfirst(user)}{add_desc})' )
		t.expect('Relay transaction? ','y')
		t.read()
		t.ok()

	async def transfer_to_miner_send1(self):
		self.relay_tx(f'--tx-relay-daemon={self.tx_relay_daemon_proxy_parm}',add_desc='via proxy')
		await self.mine_chk('miner',2,0,lambda x: str(x) == '0.2456','unlocked balance == 0.2456')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x > 0.9,'unlocked balance > 0.9')

	async def transfer_to_miner_send2(self):
		self.relay_tx(f'--tx-relay-daemon={self.tx_relay_daemon_parm}',add_desc='no proxy')
		await self.mine_chk('miner',2,0,lambda x: str(x) == '0.2468','unlocked balance == 0.2468')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x > 0.9,'unlocked balance > 0.9')

	async def sweep_create_and_send(self):
		bal = XMRAmt('0')
		min_bal = XMRAmt('0.9')

		for i in range(4):
			if i: ok()
			get_file_with_ext(self.users['alice'].udir,'sigtx',delete_all=True)
			send_amt = self.do_op(
				'sweep','alice','2:1,3', # '2:1,3'
				do_not_relay = True,
				reuse_acct   = True,
				add_desc     = f'TX #{i+1}',
				return_amt   = True )
			ok()
			self.relay_tx(f'--tx-relay-daemon={self.tx_relay_daemon_parm}',add_desc=f'send amt: {send_amt} XMR')
			await self.mine_chk('alice',2,1,lambda x: 'chk_bal_chg','balance has changed')
			ok()
			bal += await self.mine_chk('alice',3,0,lambda x,y=bal: x > y, f'bal > {bal}',return_amt=True)
			if bal >= min_bal:
				return 'ok'

		return False

	# wallet methods

	async def open_wallet_user(self,user,wnum):
		data = self.users[user]
		silence()
		kal = KeyAddrList(self.proto,data.kafile,skip_key_address_validity_check=True)
		end_silence()
		self.users[user].wd.start(silent=not (opt.exact_output or opt.verbose))
		return await data.wd_rpc.call(
			'open_wallet',
			filename = os.path.basename(data.walletfile_fs.format(wnum)),
			password = kal.entry(wnum).wallet_passwd )

	async def stop_wallet_user(self,user):
		await self.users[user].wd_rpc.stop_daemon(silent=not (opt.exact_output or opt.verbose))
		return 'ok'

	# mining methods

	async def start_mining(self):
		data = self.users['miner']
		addr = read_from_file(data.addrfile_fs.format(1)) # mine to wallet #1, account 0

		for i in range(20):
			ret = await data.md_rpc.call(
				'start_mining',
				do_background_mining = False, # run mining in background or foreground
				ignore_battery       = True,  # ignore battery state (on laptop)
				miner_address        = addr,  # account address to mine to
				threads_count        = 3 )    # number of mining threads to run
			status = self.get_status(ret)
			if status == 'OK':
				return True
			elif status == 'BUSY':
				await asyncio.sleep(5)
				omsg('Daemon busy.  Attempting to start mining...')
			else:
				die(2,f'Monerod returned status {status}')
		else:
			die(2,'Max retries exceeded')

	async def stop_mining(self):
		ret = await self.users['miner'].md_rpc.call('stop_mining')
		return self.get_status(ret)

	async def mine_chk(self,user,wnum,account,test,test_desc,random_txs=None,return_amt=False):
		"""
		- open destination wallet
		- optionally create and broadcast random TXs
		- start mining
		- mine until funds appear in wallet
		- stop mining
		- close wallet
		"""

		async def get_height():
			u = self.users['miner']
			for i in range(20):
				try:
					return (await u.md_json_rpc.call('get_last_block_header'))['block_header']['height']
				except Exception as e:
					if 'onnection refused' in str(e):
						omsg(f'{e}\nMonerod appears to have crashed. Attempting to restart...')
						await asyncio.sleep(5)
						u.md.restart()
						await asyncio.sleep(5)
						await self.start_mining()
					else:
						raise
			else:
				die(2,'Restart attempt limit exceeded')

		async def send_random_txs():
			from mmgen.tool.api import tool_api
			t = tool_api()
			t.init_coin('XMR','testnet')
			t.usr_randchars = 0
			imsg_r(f'Sending random transactions: ')
			for i in range(random_txs):
				await self.transfer(
					'miner',
					123456789,
					t.randpair()[1],
				)
				imsg_r(f'{i+1} ')
				oqmsg_r('+')
				await asyncio.sleep(0.5)
			imsg('')

		def print_balance(dest,ub):
			imsg('Total balance in {}’s wallet {}, account #{}: {}'.format(
				capfirst(dest.user),
				dest.wnum,
				dest.account,
				ub.hl()
			))

		async def get_balance(dest,count):
			data = self.users[dest.user]
			await data.wd_rpc.call('refresh')
			if count and not count % 20:
				await data.wd_rpc.call('rescan_blockchain')
			ret = await data.wd_rpc.call('get_accounts')
			return XMRAmt(ret['subaddress_accounts'][dest.account]['unlocked_balance'],from_unit='atomic')

		# start execution:

		self.do_msg(extra_desc =
			(f'sending {random_txs} random TXs, ' if random_txs else '') +
			f'mining, checking wallet {user}:{wnum}:{account}' )

		dest = namedtuple(
			'dest_info',['user','wnum','account','test','test_desc'])(user,wnum,account,test,test_desc)

		if dest.user != 'miner':
			await self.open_wallet_user(dest.user,dest.wnum)

		ub_start = await get_balance(dest,0)
		chk_bal_chg = dest.test(ub_start) == 'chk_bal_chg'

		if random_txs:
			await send_random_txs()

		await self.start_mining()

		h = await get_height()
		imsg_r(f'Chain height: {h} ')

		for count in range(500):
			ub = await get_balance(dest,count)
			if dest.test(ub) is True or ( chk_bal_chg and ub != ub_start ):
				imsg('')
				oqmsg_r('+')
				print_balance(dest,ub)
				break
			await asyncio.sleep(2)
			h = await get_height()
			imsg_r(f'{h} ')
			oqmsg_r('+')
		else:
			die(2,'Timeout exceeded, balance {ub!r}')

		await self.stop_mining()

		if user != 'miner':
			await self.stop_wallet_user(dest.user)

		return ub if return_amt else 'ok'

	# util methods

	def get_status(self,ret):
		if ret['status'] != 'OK':
			imsg( 'RPC status: {}'.format( ret['status'] ))
		return ret['status']

	def do_msg(self,extra_desc=None):
		self.spawn(
			'',
			msg_only = True,
			extra_desc = f'({extra_desc})' if extra_desc else None
		)

	async def transfer(self,user,amt,addr):
		return await self.users[user].wd_rpc.call('transfer',destinations=[{'amount':amt,'address':addr}])

	# daemon start/stop methods

	def start_daemons(self):
		for v in self.users.values():
			run(['mkdir','-p',v.datadir])
			v.md.start()

	def stop_daemons(self):
		for v in self.users.values():
			run_session(v.md_rpc.stop_daemon())

	def stop_miner_wallet_daemon(self):
		run_session(self.users['miner'].wd_rpc.stop_daemon())
