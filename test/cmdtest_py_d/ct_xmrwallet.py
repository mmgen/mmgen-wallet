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
test.cmdtest_py_d.ct_xmrwallet: xmrwallet tests for the cmdtest.py test suite
"""

import sys,os,time,re,atexit,asyncio,shutil
from subprocess import run,PIPE
from collections import namedtuple

from mmgen.util import msg,fmt,async_run,capfirst,is_int,die,list_gen
from mmgen.obj import MMGenRange
from mmgen.amt import XMRAmt
from mmgen.addrlist import ViewKeyAddrList,KeyAddrList,AddrIdxList

from ..include.common import (
	cfg,
	omsg,
	oqmsg_r,
	ok,
	imsg,
	imsg_r,
	write_data_to_file,
	read_from_file,
	silence,
	end_silence,
	strip_ansi_escapes
)
from .common import get_file_with_ext
from .ct_base import CmdTestBase

# atexit functions:
def stop_daemons(self):
	for v in self.users.values():
		if '--restricted-rpc' in v.md.start_cmd:
			v.md.stop()
		else:
			async_run(v.md_rpc.stop_daemon())

def stop_miner_wallet_daemon(self):
	async_run(self.users['miner'].wd_rpc.stop_daemon())

def kill_proxy(cls,args):
	if sys.platform == 'linux':
		omsg(f'Killing SSH SOCKS server at localhost:{cls.socks_port}')
		cmd = [ 'pkill', '-f', ' '.join(args) ]
		run(cmd)

class CmdTestXMRWallet(CmdTestBase):
	"""
	Monero wallet operations
	"""

	networks = ('xmr',)
	passthru_opts = ()
	tmpdir_nums = [29]
	dfl_random_txs = 3
	color = True
	socks_port = 49237
	# Bob’s daemon is stopped via process kill, not RPC, so put Bob last in list:
	user_data = (
		('miner', '98831F3A', False, 130, '1-2', []),
		('alice', 'FE3C6545', False, 150, '1-4', []),
		('bob',   '1378FC64', False, 140, None,  ['--restricted-rpc']),
	)
	tx_relay_user = 'bob'
	datadir_base = os.path.join('test','daemons','xmrtest')

	cmd_group = (
		('daemon_version',            'checking daemon version'),
		('gen_kafiles',               'generating key-address files'),
		('create_wallets_miner',      'creating Monero wallets (Miner)'),
		('set_label_miner',           'setting an address label (Miner, primary account)'),
		('mine_initial_coins',        'mining initial coins'),
		('create_wallets_alice',      'creating Monero wallets (Alice)'),
		('fund_alice',                'sending funds'),

		('sync_wallets_all',          'syncing all wallets'),
		('new_account_alice',         'creating a new account (Alice)'),
		('new_account_alice_label',   'creating a new account (Alice, with label)'),
		('new_address_alice',         'creating a new address (Alice)'),
		('new_address_alice_label',   'creating a new address (Alice, with label)'),
		('remove_label_alice',        'removing an address label (Alice, subaddress)'),
		('set_label_alice',           'setting an address label (Alice, subaddress)'),
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
		('list_wallets_all',          'listing wallets'),
		('stop_daemons',              'stopping all wallet and coin daemons'),
	)

	def __init__(self,trunner,cfgs,spawn):
		CmdTestBase.__init__(self,trunner,cfgs,spawn)
		if trunner is None:
			return

		from mmgen.protocol import init_proto
		self.proto = init_proto( cfg, 'XMR', network='mainnet' )
		self.extra_opts = ['--wallet-rpc-password=passw0rd']
		self.autosign_mountpoint = os.path.join(self.tmpdir,'mmgen_autosign')
		self.autosign_xmr_dir = os.path.join(self.tmpdir,'mmgen_autosign','xmr')
		self.init_users()
		self.init_daemon_args()
		self.autosign_opts = []

		for v in self.users.values():
			run(['mkdir','-p',v.udir])

		self.tx_relay_daemon_parm = 'localhost:{}'.format( self.users[self.tx_relay_user].md.rpc_port )
		self.tx_relay_daemon_proxy_parm = (
			self.tx_relay_daemon_parm + f':127.0.0.1:{self.socks_port}' ) # must be IP, not 'localhost'

		if not cfg.no_daemon_stop:
			atexit.register(stop_daemons,self)
			atexit.register(stop_miner_wallet_daemon,self)

		if not cfg.no_daemon_autostart:
			stop_daemons(self)
			time.sleep(0.2)
			if os.path.exists(self.datadir_base):
				shutil.rmtree(self.datadir_base)
			os.makedirs(self.datadir_base)
			self.start_daemons()
			self.init_proxy()

		self.balance = None

	# init methods

	@classmethod
	def init_proxy(cls,external_call=False):

		def port_in_use(port):
			import socket
			try:
				socket.create_connection(('localhost',port)).close()
			except:
				return False
			else:
				return True

		def start_proxy():
			if external_call or not cfg.no_daemon_autostart:
				run(a+b2)
				omsg(f'SSH SOCKS server started, listening at localhost:{cls.socks_port}')

		debug_file = os.path.join('' if external_call else cls.datadir_base,'txrelay-proxy.debug')
		a = ['ssh','-x','-o','ExitOnForwardFailure=True','-D',f'localhost:{cls.socks_port}']
		b0 = ['-o','PasswordAuthentication=False']
		b1 = ['localhost','true']
		b2 = ['-fN','-E', debug_file, 'localhost']

		if port_in_use(cls.socks_port):
			omsg(f'Port {cls.socks_port} already in use.  Assuming SSH SOCKS server is running')
		else:
			cp = run(a+b0+b1,stdout=PIPE,stderr=PIPE)
			err = cp.stderr.decode()
			if err:
				omsg(err)

			if cp.returncode == 0:
				start_proxy()
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

				from mmgen.ui import keypress_confirm
				if keypress_confirm(cfg,'Continue?'):
					start_proxy()
				else:
					die(1,'Exiting at user request')
			else:
				die(2,fmt(f"""
					Please start the SSH SOCKS proxy by entering the following command:

						{' '.join(a+b2)}

					Then restart the test.
				""",indent='    '))

		if not (external_call or cfg.no_daemon_stop):
			atexit.unregister(kill_proxy)
			atexit.register(kill_proxy, cls, a + b2)

		return True

	def init_users(self):
		from mmgen.daemon import CoinDaemon
		from mmgen.proto.xmr.daemon import MoneroWalletDaemon
		from mmgen.proto.xmr.rpc import MoneroRPCClient,MoneroWalletRPCClient
		self.users = {}
		tmpdir_num = self.tmpdir_nums[0]
		ud = namedtuple('user_data',[
			'sid',
			'mmwords',
			'autosign',
			'udir',
			'datadir',
			'kal_range',
			'kafile',
			'walletfile_fs',
			'addrfile_fs',
			'md',
			'md_rpc',
			'wd',
			'wd_rpc',
			'add_coind_args',
		])
		# kal_range must be None, a single digit, or a single hyphenated range
		for (   user,
				sid,
				autosign,
				shift,
				kal_range,
				add_coind_args ) in self.user_data:
			tmpdir = os.path.join('test','tmp',str(tmpdir_num))
			udir = os.path.join(tmpdir,user)
			datadir = os.path.join(self.datadir_base,user)
			md = CoinDaemon(
				cfg        = cfg,
				proto      = self.proto,
				test_suite = True,
				port_shift = shift,
				opts       = ['online'],
				datadir    = datadir
			)
			md_rpc = MoneroRPCClient(
				cfg    = cfg,
				proto  = self.proto,
				host   = 'localhost',
				port   = md.rpc_port,
				user   = None,
				passwd = None,
				test_connection = False,
				daemon = md,
			)
			wd = MoneroWalletDaemon(
				cfg        = cfg,
				proto      = self.proto,
				test_suite = True,
				wallet_dir = udir,
				user       = 'foo',
				passwd     = 'bar',
				port_shift = shift,
				monerod_addr = f'127.0.0.1:{md.rpc_port}',
			)
			wd_rpc = MoneroWalletRPCClient(
				cfg             = cfg,
				daemon          = wd,
				test_connection = False,
			)
			if autosign:
				kafile_suf = 'vkeys'
				fn_stem    = 'MoneroWatchOnlyWallet'
				kafile_dir = self.autosign_xmr_dir
			else:
				kafile_suf = 'akeys'
				fn_stem    = 'MoneroWallet'
				kafile_dir = udir
			self.users[user] = ud(
				sid           = sid,
				mmwords       = f'test/ref/{sid}.mmwords',
				autosign      = autosign,
				udir          = udir,
				datadir       = datadir,
				kal_range     = kal_range,
				kafile        = f'{kafile_dir}/{sid}-XMR-M[{kal_range}].{kafile_suf}',
				walletfile_fs = f'{udir}/{sid}-{{}}-{fn_stem}',
				addrfile_fs   = f'{udir}/{sid}-{{}}-{fn_stem}.address.txt',
				md            = md,
				md_rpc        = md_rpc,
				wd            = wd,
				wd_rpc        = wd_rpc,
				add_coind_args = add_coind_args,
			)

	def init_daemon_args(self):
		common_args = ['--p2p-bind-ip=127.0.0.1','--fixed-difficulty=1','--regtest'] # ,'--rpc-ssl-allow-any-cert']
		for u in self.users:
			other_ports = [self.users[u2].md.p2p_port for u2 in self.users if u2 != u]
			node_args = [f'--add-exclusive-node=127.0.0.1:{p}' for p in other_ports]
			self.users[u].md.usr_coind_args = (
				common_args +
				node_args +
				self.users[u].add_coind_args )

	# cmd_group methods

	def daemon_version(self):
		rpc_port = self.users['miner'].md.rpc_port
		return self.spawn( 'mmgen-tool', ['--coin=xmr', f'--rpc-port={rpc_port}', 'daemon_version'] )

	def gen_kafiles(self):
		for user,data in self.users.items():
			if not data.kal_range:
				continue
			if data.autosign:
				continue
			run(['mkdir','-p',data.udir])
			run(f'rm -f {data.kafile}',shell=True)
			t = self.spawn(
				'mmgen-keygen', [
					'-q', '--accept-defaults', '--coin=xmr',
					f'--outdir={data.udir}', data.mmwords, data.kal_range
				],
				extra_desc = f'({capfirst(user)})' )
			t.read()
			t.ok()
		t.skip_ok = True
		return t

	def create_wallets_miner(self):
		return self.create_wallets('miner')
	def create_wallets_alice(self):
		return self.create_wallets('alice')

	def create_wallets(self,user,wallet=None,add_opts=[],op='create'):
		assert wallet is None or is_int(wallet), 'wallet arg'
		data = self.users[user]
		stem_glob = data.walletfile_fs.format(wallet or '*')
		for glob in (
				stem_glob,
				stem_glob + '.keys',
				stem_glob + '.address.txt' ):
			run( f'rm -f {glob}', shell=True )
		t = self.spawn(
			'mmgen-xmrwallet',
			[f'--wallet-dir={data.udir}']
			+ self.extra_opts
			+ (self.autosign_opts if data.autosign else [])
			+ add_opts
			+ [op]
			+ ([] if data.autosign else [data.kafile])
			+ [wallet or data.kal_range]
		)
		for i in MMGenRange(wallet or data.kal_range).items:
			write_data_to_file(
				cfg,
				self.users[user].addrfile_fs.format(i),
				t.expect_getend('Address: '),
				quiet = True
			)
		return t

	def new_addr_alice(self,spec,cfg,expect,kafile=None):
		data = self.users['alice']
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts +
			[f'--wallet-dir={data.udir}'] +
			[f'--daemon=localhost:{data.md.rpc_port}'] +
			(['--no-start-wallet-daemon'] if cfg in ('continue','stop') else []) +
			(['--no-stop-wallet-daemon'] if cfg in ('start','continue') else []) +
			['new', (kafile or data.kafile), spec] )
		m = re.search( expect, t.read(strip_color=True), re.DOTALL )
		assert m, f'no match found for {expect!r}'
		return t

	na_idx = 1

	def new_account_alice(self):
		return self.new_addr_alice(
			'4',
			'start',
			fr'Creating new account.*Index:\s+{self.na_idx}\s')

	def new_account_alice_label(self):
		return self.new_addr_alice(
			'4,Alice’s new account',
			'continue',
			fr'Creating new account.*Index:\s+{self.na_idx+1}\s.*Alice’s new account')

	def new_address_alice(self):
		return self.new_addr_alice(
			'4:2',
			'continue',
			r'Account index:\s+2\s+Creating new address' )

	def new_address_alice_label(self):
		return self.new_addr_alice(
			'4:2,Alice’s new address',
			'stop',
			r'Account index:\s+2\s+Creating new address.*Alice’s new address' )

	async def mine_initial_coins(self):
		self.spawn('', msg_only=True, extra_desc='(opening wallet)')
		await self.open_wallet_user('miner',1)
		ok()
		# NB: a large balance is required to avoid ‘insufficient outputs’ error
		return await self.mine_chk('miner',1,0,lambda x: x.ub > 2000,'unlocked balance > 2000')

	async def fund_alice(self,wallet=1,check_bal=True):
		self.spawn('', msg_only=True, extra_desc='(transferring funds from Miner wallet)')
		await self.transfer(
			'miner',
			1234567891234,
			read_from_file(self.users['alice'].addrfile_fs.format(wallet)),
		)
		if not check_bal:
			return 'ok'
		ok()
		bal = '1.234567891234'
		return await self.mine_chk(
			'alice',wallet,0,
			lambda x: str(x.ub) == bal,f'unlocked balance == {bal}',
			random_txs = self.dfl_random_txs
		)

	def set_label_miner(self):
		return self.set_label_user( 'miner', '1:0:0,"Miner’s new primary account label [1:0:0]"' )

	def remove_label_alice(self):
		return self.set_label_user( 'alice', '4:2:2,""' )

	def set_label_alice(self):
		return self.set_label_user( 'alice', '4:2:2,"Alice’s new subaddress label [4:2:2]"' )

	def set_label_user(self,user,label_spec):
		data = self.users[user]
		cmd_opts = [f'--wallet-dir={data.udir}', f'--daemon=localhost:{data.md.rpc_port}']
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts + cmd_opts + ['label', data.kafile, label_spec]
		)
		t.expect('(y/N): ','y')
		t.expect(['successfully set','successfully removed'])
		return t

	def sync_wallets_all(self):
		return self.sync_wallets('alice',add_opts=['--rescan-blockchain'])

	def sync_wallets_selected(self):
		return self.sync_wallets('alice',wallets='1-2,4')

	def list_wallets_all(self):
		return self.sync_wallets('alice',op='list')

	def sync_wallets(self,user,op='sync',wallets=None,add_opts=[],bal_chk_func=None):
		data = self.users[user]
		cmd_opts = list_gen(
			[f'--wallet-dir={data.udir}'],
			[f'--daemon=localhost:{data.md.rpc_port}'],
		)
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ cmd_opts
			+ self.autosign_opts
			+ add_opts
			+ [op]
			+ ([] if data.autosign else [data.kafile])
			+ ([wallets] if wallets else [])
		)
		wlist = AddrIdxList(wallets) if wallets else MMGenRange(data.kal_range).items
		for n,wnum in enumerate(wlist,1):
			t.expect('Syncing wallet {}/{} ({})'.format(
				n,
				len(wlist),
				os.path.basename(data.walletfile_fs.format(wnum)),
			))
			t.expect('Chain height: ')
			t.expect('Wallet height: ')
			res = strip_ansi_escapes(t.expect_getend('Balance: '))
			if bal_chk_func:
				m = re.match( r'(\S+) Unlocked balance: (\S+)', res, re.DOTALL )
				amts = [XMRAmt(amt) for amt in m.groups()]
				assert bal_chk_func(n,*amts), f'balance check for wallet {n} failed!'
		return t

	def do_op(
			self,
			op,
			user,
			arg2,
			tx_relay_parm = None,
			no_relay      = False,
			return_amt    = False,
			reuse_acct    = False,
			add_desc      = None,
			do_ret        = False):

		data = self.users[user]
		cmd_opts = list_gen(
			[f'--wallet-dir={data.udir}'],
			[f'--outdir={data.udir}', not data.autosign],
			[f'--daemon=localhost:{data.md.rpc_port}'],
			[f'--tx-relay-daemon={tx_relay_parm}', tx_relay_parm],
			['--no-relay', no_relay and not data.autosign],
			[f'--autosign-mountpoint={self.autosign_mountpoint}', data.autosign],
		)
		add_desc = (', ' + add_desc) if add_desc else ''

		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ cmd_opts
			+ [op]
			+ ([] if data.autosign else [data.kafile])
			+ [arg2],
			extra_desc = f'({capfirst(user)}{add_desc})' )

		if op == 'sign':
			return t

		if op == 'sweep':
			t.expect(
				r'Create new {} .* \(y/N\): '.format(('address','account')[',' in arg2]),
				('y','n')[reuse_acct],
				regex=True )
			if reuse_acct:
				t.expect( r'to last existing account .* \(y/N\): ','y', regex=True )

		if return_amt:
			amt = XMRAmt(strip_ansi_escapes(t.expect_getend('Amount: ')).replace('XMR','').strip())

		dtype = 'unsigned' if data.autosign else 'signed'
		t.expect(f'Save {dtype} transaction? (y/N): ','y')
		t.written_to_file(f'{dtype.capitalize()} transaction')

		if not no_relay:
			t.expect(f'Relay {op} transaction? (y/N): ','y')
			get_file_with_ext(self.users[user].udir,'sigtx',delete_all=True)

		t.read()

		return t if do_ret else amt if return_amt else t.ok()

	def sweep_to_address_proxy(self):
		self.do_op('sweep','alice','1:0',self.tx_relay_daemon_proxy_parm)
		return self.mine_chk('alice',1,0,lambda x: x.ub > 1,'unlocked balance > 1')

	def sweep_to_account(self):
		self.do_op('sweep','alice','1:0,2')
		return self.mine_chk('alice',2,1,lambda x: x.ub > 1,'unlocked balance > 1')

	def sweep_to_address_noproxy(self):
		self.do_op('sweep','alice','2:1',self.tx_relay_daemon_parm)
		return self.mine_chk('alice',2,1,lambda x: x.ub > 0.9,'unlocked balance > 0.9')

	async def transfer_to_miner_proxy(self):
		addr = read_from_file(self.users['miner'].addrfile_fs.format(2))
		amt = '0.135'
		self.do_op('transfer','alice',f'2:1:{addr},{amt}',self.tx_relay_daemon_proxy_parm)
		await self.stop_wallet_user('miner')
		await self.open_wallet_user('miner',2)
		await self.mine_chk('miner',2,0,lambda x: str(x.ub) == amt,f'unlocked balance == {amt}')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x.ub > 0.9,'unlocked balance > 0.9')

	async def transfer_to_miner_noproxy(self):
		addr = read_from_file(self.users['miner'].addrfile_fs.format(2))
		self.do_op('transfer','alice',f'2:1:{addr},0.0995',self.tx_relay_daemon_parm)
		await self.mine_chk('miner',2,0,lambda x: str(x.ub) == '0.2345','unlocked balance == 0.2345')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x.ub > 0.9,'unlocked balance > 0.9')

	def transfer_to_miner_create(self,amt):
		get_file_with_ext(self.users['alice'].udir,'sigtx',delete_all=True)
		addr = read_from_file(self.users['miner'].addrfile_fs.format(2))
		return self.do_op('transfer','alice',f'2:1:{addr},{amt}',no_relay=True,do_ret=True)

	def transfer_to_miner_create1(self):
		return self.transfer_to_miner_create('0.0111')

	def transfer_to_miner_create2(self):
		return self.transfer_to_miner_create('0.0012')

	def relay_tx(self,relay_opt,add_desc=None):
		user = 'alice'
		data = self.users[user]
		add_desc = (', ' + add_desc) if add_desc else ''
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ [ relay_opt, 'relay', get_file_with_ext(data.udir,'sigtx') ],
			extra_desc = f'(relaying TX, {capfirst(user)}{add_desc})' )
		t.expect('Relay transaction? ','y')
		t.read()
		t.ok()
		return t

	async def transfer_to_miner_send1(self):
		self.relay_tx(f'--tx-relay-daemon={self.tx_relay_daemon_proxy_parm}',add_desc='via proxy')
		await self.mine_chk('miner',2,0,lambda x: str(x.ub) == '0.2456','unlocked balance == 0.2456')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x.ub > 0.9,'unlocked balance > 0.9')

	async def transfer_to_miner_send2(self):
		self.relay_tx(f'--tx-relay-daemon={self.tx_relay_daemon_parm}',add_desc='no proxy')
		await self.mine_chk('miner',2,0,lambda x: str(x.ub) == '0.2468','unlocked balance == 0.2468')
		ok()
		return await self.mine_chk('alice',2,1,lambda x: x.ub > 0.9,'unlocked balance > 0.9')

	async def sweep_create_and_send(self):
		bal = XMRAmt('0')
		min_bal = XMRAmt('0.9')

		for i in range(4):
			if i:
				ok()
			get_file_with_ext(self.users['alice'].udir,'sigtx',delete_all=True)
			send_amt = self.do_op(
				'sweep','alice','2:1,3', # '2:1,3'
				no_relay     = True,
				reuse_acct   = True,
				add_desc     = f'TX #{i+1}',
				return_amt   = True )
			ok()
			self.relay_tx(f'--tx-relay-daemon={self.tx_relay_daemon_parm}',add_desc=f'send amt: {send_amt} XMR')
			await self.mine_chk('alice',2,1,lambda x: 'chk_bal_chg','balance has changed')
			ok()
			bal_info = await self.mine_chk('alice',3,0,lambda x,y=bal: x.ub > y, f'bal > {bal}',return_bal=True)
			bal += bal_info.ub
			if bal >= min_bal:
				return 'ok'

		return False

	# wallet methods

	async def open_wallet_user(self,user,wnum):
		data = self.users[user]
		silence()
		kal = (ViewKeyAddrList if data.autosign else KeyAddrList)(
			cfg      = cfg,
			proto    = self.proto,
			addrfile = data.kafile,
			skip_chksum_msg = True,
			key_address_validity_check = False )
		end_silence()
		self.users[user].wd.start(silent=not (cfg.exact_output or cfg.verbose))
		return data.wd_rpc.call(
			'open_wallet',
			filename = os.path.basename(data.walletfile_fs.format(wnum)),
			password = kal.entry(wnum).wallet_passwd )

	async def stop_wallet_user(self,user):
		await self.users[user].wd_rpc.stop_daemon(silent=not (cfg.exact_output or cfg.verbose))
		return 'ok'

	# mining methods

	async def mine5(self):
		return await self.mine(5)

	async def _get_height(self):
		u = self.users['miner']
		for _ in range(20):
			try:
				return u.md_rpc.call('get_last_block_header')['block_header']['height']
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

	async def mine10(self):
		return await self.mine(10)

	async def mine30(self):
		return await self.mine(30)

	async def mine100(self):
		return await self.mine(100)

	async def mine(self,nblks):
		start_height = height = await self._get_height()
		imsg(f'Height: {height}')
		imsg_r(f'Mining {nblks} blocks...')
		await self.start_mining()
		while height < start_height + nblks:
			await asyncio.sleep(2)
			height = await self._get_height()
			imsg_r('.')
		ret = await self.stop_mining()
		imsg('done')
		imsg(f'Height: {height}')
		return 'ok' if ret == 'OK' else False

	async def start_mining(self):
		data = self.users['miner']
		addr = read_from_file(data.addrfile_fs.format(1)) # mine to wallet #1, account 0

		for _ in range(20):
			# NB: threads_count > 1 provides no benefit and leads to connection errors with MSWin/MSYS2
			ret = data.md_rpc.call_raw(
				'start_mining',
				do_background_mining = False, # run mining in background or foreground
				ignore_battery       = True,  # ignore battery state (on laptop)
				miner_address        = addr,  # account address to mine to
				threads_count        = 1 )    # number of mining threads to run
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
		ret = self.users['miner'].md_rpc.call_raw('stop_mining')
		return self.get_status(ret)

	async def mine_chk(
			self,
			user,
			wnum,
			account,
			test,
			test_desc,
			test2      = None,
			test2_desc = None,
			random_txs = None,
			return_bal = False ):

		"""
		- open destination wallet
		- optionally create and broadcast random TXs
		- start mining
		- mine until funds appear in wallet
		- stop mining
		- close wallet
		"""

		async def send_random_txs():
			from mmgen.tool.api import tool_api
			t = tool_api(cfg)
			t.init_coin('XMR','mainnet')
			t.usr_randchars = 0
			imsg_r('Sending random transactions: ')
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

		def print_balance(dest,bal_info):
			imsg('Total balances in {}’s wallet {}, account #{}: {} (total), {} (unlocked)'.format(
				capfirst(dest.user),
				dest.wnum,
				dest.account,
				bal_info.b.hl(),
				bal_info.ub.hl(),
			))

		async def get_balance(dest,count):
			data = self.users[dest.user]
			data.wd_rpc.call('refresh')
			if count and not count % 20:
				data.wd_rpc.call('rescan_blockchain')
			ret = data.wd_rpc.call('get_accounts')['subaddress_accounts'][dest.account]
			d_tup = namedtuple('bal_info',['b','ub'])
			return d_tup(
				b  = XMRAmt(ret['balance'],from_unit='atomic'),
				ub = XMRAmt(ret['unlocked_balance'],from_unit='atomic')
			)

		# start execution:

		self.do_msg(extra_desc =
			(f'sending {random_txs} random TXs, ' if random_txs else '') +
			f'mining, checking wallet {user}:{wnum}:{account}' )

		dest = namedtuple(
			'dest_info',['user','wnum','account','test','test_desc','test2','test2_desc'])(
				user,wnum,account,test,test_desc,test2,test2_desc)

		if dest.user != 'miner':
			await self.open_wallet_user(dest.user,dest.wnum)

		bal_info_start = await get_balance(dest,0)
		chk_bal_chg = dest.test(bal_info_start) == 'chk_bal_chg'

		if random_txs:
			await send_random_txs()

		await self.start_mining()

		h = await self._get_height()
		imsg_r(f'Chain height: {h} ')

		max_iterations,min_height = (300,64) if sys.platform == 'win32' else (50,300)
		verbose = False

		for count in range(max_iterations):
			bal_info = await get_balance(dest,count)
			if h > min_height:
				if dest.test(bal_info) is True or (chk_bal_chg and bal_info.ub != bal_info_start.ub):
					imsg('')
					oqmsg_r('+')
					print_balance(dest,bal_info)
					if dest.test2:
						assert dest.test2(bal_info) is True, f'test failed: {dest.test2_desc} ({bal_info})'
					break
			await asyncio.sleep(2)
			h = await self._get_height()
			if count > 12: # something might have gone wrong, so be more verbose
				if not verbose:
					imsg('')
				imsg_r(f'Height: {h}, ')
				print_balance(dest,bal_info)
				verbose = True
			else:
				imsg_r(f'{h} ')
				oqmsg_r('+')
		else:
			die(2,f'Timeout exceeded, balance {bal_info.ub!r}')

		await self.stop_mining()

		if user != 'miner':
			await self.stop_wallet_user(dest.user)

		return bal_info if return_bal else 'ok'

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
		return self.users[user].wd_rpc.call('transfer',destinations=[{'amount':amt,'address':addr}])

	# daemon start/stop methods

	def start_daemons(self):
		for v in self.users.values():
			run(['mkdir','-p',v.datadir])
			v.md.start()

	def stop_daemons(self):
		self.spawn('', msg_only=True)
		if cfg.no_daemon_stop:
			omsg('[not stopping daemons at user request]')
		else:
			omsg('')
			stop_daemons(self)
			atexit.unregister(stop_daemons)

			stop_miner_wallet_daemon(self)
			atexit.unregister(stop_miner_wallet_daemon)
		return 'silent'
