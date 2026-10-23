# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet


"""
test.cmdtest_d.xmr_autosign: xmr autosigning tests for the cmdtest.py test suite
"""

import os, re, asyncio, json

from mmgen.color import blue, cyan, brown

from ..include.common import (
	imsg,
	oqmsg,
	silence,
	end_silence,
	strip_ansi_escapes,
	read_from_file)
from .include.common import get_file_with_ext, cleanup_env

from .xmrwallet import CmdTestXMRWallet
from .autosign import CmdTestAutosignThreaded

def make_burn_addr(cfg):
	from mmgen.tool.coin import tool_cmd
	return tool_cmd(
		cfg     = cfg,
		cmdname = 'privhex2addr',
		proto   = cfg._proto,
		mmtype  = 'monero').privhex2addr('beadcafe'*8)

class CmdTestXMRAutosign(CmdTestXMRWallet, CmdTestAutosignThreaded):
	"""
	Monero autosigning operations (xmrwallet compat mode)
	"""
	tmpdir_nums = [39]

	# xmrwallet attrs:
	tx_relay_user = 'miner'
	user_data = (
		# user    sid       autosign kal_range add_coind_args
		('miner', '98831F3A', False, '1',   []),
		('alice', 'FE3C6545', True,  '1-2', []))

	# autosign attrs:
	coins = ['xmr']
	compat = True
	user = 'alice'

	cmd_group = (
		('daemon_version',            'checking daemon version'),
		('create_tmp_wallets',        'creating temporary online wallets for user'),
		('new_account_user',          'adding an account to user’s tmp wallet'),
		('new_address_user',          'adding an address to user’s tmp wallet'),
		('new_address_user_label',    'adding an address to user’s tmp wallet (with label)'),
		('dump_tmp_wallets',          'dumping user’s tmp wallets'),
		('dump_tmp_wallets_json',     'dumping user’s tmp wallets to JSON format'),
		('delete_tmp_wallets',        'deleting user’s tmp wallets'),
		('gen_kafile_miner',          'generating key-address file for Miner'),
		('gen_vkafile_user',          'generating viewkey-address file for user'),
		('create_wallet_miner',       'creating Monero wallet for Miner'),
		('mine_initial_coins',        'mining initial coins'),
		('autosign_setup',            'autosign setup with user’s seed'),
		('autosign_xmr_setup',        'autosign setup (creation of Monero signing wallets)'),
		('restore_watchonly_wallets', 'creating watch-only wallets from user’s wallet dumps'),
		('delete_tmp_dump_files',     'deleting user’s dump files'),
		('fund_user1',                'sending funds to user (wallet #1)'),
		('check_bal_user1',           'mining, checking balance (wallet #1)'),
		('fund_user2',                'sending funds to user (wallet #2)'),
		('check_bal_user2',           'mining, checking balance (wallet #2)'),
		('wait_loop_start',           'starting autosign wait loop'),
		('export_outputs1',           'exporting outputs from user’s watch-only wallet #1'),
		('create_transfer_tx1',       'creating a transfer TX'),
		('submit_transfer_tx1',       'submitting the transfer TX'),
		('resubmit_transfer_tx1',     'resubmitting the transfer TX'),
		('export_outputs2',           'exporting outputs from user’s watch-only wallet #1'),
		('import_key_images1',        'importing signed key images into user’s online wallets'),
		('sync_chkbal1',              'syncing user’s wallet #1'),
		('abort_tx1',                 'aborting the current transaction (error)'),
		('create_transfer_tx2',       'creating a transfer TX (for relaying via proxy)'),
		('abort_tx2',                 'aborting the current transaction (OK, unsigned)'),
		('create_transfer_tx2a',      'creating the transfer TX again'),
		('submit_transfer_tx2',       'submitting the transfer TX (relaying via proxy)'),
		('sync_chkbal2',              'syncing user’s wallets and checking balance'),
		('dump_wallets',              'dumping user’s wallets'),
		('delete_wallets',            'deleting user’s wallets'),
		('restore_wallets',           'creating online (watch-only) wallets for user'),
		('delete_dump_files',         'deleting user’s dump files'),
		('export_outputs3',           'exporting outputs from user’s watch-only wallets'),
		('import_key_images2',        'importing signed key images into user’s online wallets'),
		('sync_chkbal3',              'syncing user’s wallets and checking balance'),
		('wait_loop_kill',            'stopping autosign wait loop'),
		('stop_daemons',              'stopping all wallet and coin daemons'),
		('view',                      'viewing user’s wallet in offline mode (wallet #1)'),
		('listview',                  'list-viewing user’s wallet in offline mode (wallet #2)'),
		('txlist',                    'listing user’s submitted transactions'),
		('txview',                    'viewing user’s submitted transactions'),
		('txview_all',                'viewing all raw, signed and submitted transactions'),
		('check_tx_dirs',             'cleaning and checking signable file directories'))

	def __init__(self, cfg, trunner, cfgs, spawn):

		CmdTestAutosignThreaded.__init__(self, cfg, trunner, cfgs, spawn)
		CmdTestXMRWallet.__init__(self, cfg, trunner, cfgs, spawn)

		if trunner is None:
			return

		self.user_cfg = self.users[self.user].cfg
		self.user_datadir = self.users[self.user].cfg._proto.network_datadir

		self.burn_addr = make_burn_addr(cfg)

		self.autosign_opts = ['--autosign'] # mmgen-xmrwallet opts
		self.autosign_setup_opts = ['--regtest=1', f'--xmrwallets={self.users[self.user].kal_range}']

	def create_tmp_wallets(self):
		self.spawn(msg_only=True)
		data = self.users[self.user]
		from mmgen.wallet import Wallet
		from mmgen.xmrwallet import op
		from mmgen.addrlist import KeyAddrList
		silence()
		kal = KeyAddrList(
			cfg       = self.user_cfg,
			proto     = self.proto,
			addr_idxs = '1-2',
			seed      = Wallet(self.user_cfg, fn=data.mmwords).seed,
			skip_chksum_msg = True,
			key_address_validity_check = False)
		kal.file.write(outdir=self.user_datadir, ask_overwrite=False)
		fn = get_file_with_ext(self.user_datadir, 'akeys')
		m = op('create', self.user_cfg, fn, '1-2')
		asyncio.run(m.main())
		asyncio.run(m.stop_wallet_daemon())
		end_silence()
		return 'ok'

	def _new_addr_user_autosign(self, *args):
		data = self.users[self.user]
		return self._new_addr_user(
			self.user,
			*args,
			kafile = get_file_with_ext(data.udir, 'akeys'))

	def new_account_user(self):
		return self._new_addr_user_autosign(
			'2',
			'start',
			r'Creating new account for wallet .*2.* with label '
			r'.*‘xmrwallet new account .*y/N\): ')

	def new_address_user(self):
		return self._new_addr_user_autosign(
			'2:1',
			'continue',
			r'Creating new address for wallet .*2.*, account .*#1.* with label '
			r'.*‘xmrwallet new address .*y/N\): ')

	def new_address_user_label(self):
		return self._new_addr_user_autosign(
			'2:1,user’s new address',
			'stop',
			r'Creating new address for wallet .*2.*, account .*#1.* with label '
			r'.*‘user’s new address .*y/N\): ')

	def dump_tmp_wallets(self):
		return self._dump_wallets(autosign=False)

	def dump_tmp_wallets_json(self):
		return self._dump_wallets(autosign=False, op='dump_json')

	def dump_wallets(self):
		return self._dump_wallets(autosign=True)

	def _dump_wallets(self, autosign, op='dump'):
		data = self.users[self.user]
		self.insert_device_online()
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ ([f'--{self.user}', '--compat'] if self.compat else [])
			+ [f'--daemon=localhost:{data.md.rpc_port}']
			+ (self.autosign_opts if autosign else [])
			+ [op]
			+ ([] if autosign else [get_file_with_ext(data.udir, 'akeys')]),
			env = cleanup_env(self.cfg))
		t.expect('2 wallets dumped')
		res = t.read()
		if op == 'dump_json':
			data = json.loads(re.sub('Stopping.*', '', strip_ansi_escapes(res)).strip())
		self.remove_device_online()
		return t

	def _delete_files(self, *ext_list):
		data = self.users[self.user]
		self.spawn(msg_only=True)
		wdir = data.wd.wallet_dir if self.compat else data.udir
		for ext in ext_list:
			get_file_with_ext(wdir, ext, no_dot=True, delete_all=True)
		return 'ok'

	def delete_tmp_wallets(self):
		return self._delete_files('MoneroWallet', 'MoneroWallet.keys', '.akeys')

	def delete_wallets(self):
		return self._delete_files('MoneroWatchOnlyWallet', '.keys', '.address.txt')

	def delete_tmp_dump_files(self):
		return self._delete_files('.dump')

	def gen_kafile_miner(self):
		return self._gen_kafiles(['miner'])

	def gen_vkafile_user(self):
		return self._gen_kafiles([self.user], add_opts=['--viewkeys'])

	def create_wallet_miner(self):
		return self.create_wallets_miner()

	def delete_dump_files(self):
		return self._delete_files('.dump')

	async def fund_user1(self):
		return await self._fund_user(self.user, wallet=1)

	fund_user1b = fund_user1

	async def check_bal_user1(self):
		return await self._check_bal_user(self.user, wallet=1)

	async def fund_user2(self):
		return await self._fund_user(self.user, wallet=2)

	async def check_bal_user2(self):
		return await self._check_bal_user(self.user, wallet=2)

	def autosign_setup(self):
		return self.run_setup(
			mn_type        = 'mmgen',
			mn_file        = self.users[self.user].mmwords,
			use_dfl_wallet = None,
			add_opts       = self.autosign_setup_opts,
			expect_args    = ['Continue with Monero setup? (Y/n): ', 'n'])

	def autosign_xmr_setup_redo(self):
		return self.autosign_xmr_setup(write_viewkeys=False)

	def autosign_xmr_setup(self, write_viewkeys=True):
		self.insert_device_online()
		self.do_mount_online()
		self.asi_online.xmr_dir.mkdir(exist_ok=True)
		(self.asi_online.xmr_dir / 'old.vkeys').touch()
		self.do_umount_online()
		self.remove_device_online()

		self.insert_device()
		t = self.spawn(
				'mmgen-autosign',
				self.opts + self.autosign_setup_opts + ['xmr_setup'],
				no_passthru_opts = True)
		if write_viewkeys:
			t.written_to_file('View keys')
		else:
			t.expect('already exists, skipping')
		t.read()
		self.remove_device()
		return t

	def restore_watchonly_wallets(self):
		return self._create_wallets('restore')

	def restore_wallets(self):
		return self._create_wallets('restore')

	def _create_wallets(self, op='create'):
		self.insert_device_online()
		t = self.create_wallets(self.user, op=op)
		t.read() # required!
		self.remove_device_online()
		return t

	def _create_transfer_tx(self, amt, add_opts=[]):
		self.insert_device_online()
		t = self.do_op(
			'transfer',
			self.user,
			f'1:0:{self.burn_addr},{amt}',
			no_relay = True,
			do_ret   = True,
			add_opts = add_opts)
		t.read() # required!
		self.remove_device_online()
		return t

	def create_transfer_tx1(self):
		return self._create_transfer_tx('0.124', add_opts=['--priority=2'])

	def create_transfer_tx2(self):
		return self._create_transfer_tx('0.257')

	create_transfer_tx2a = create_transfer_tx2

	def _abort_tx(self, expect, send=None, exit_val=None):
		self.insert_device_online()
		t = self.spawn('mmgen-xmrwallet', ['--autosign', 'abort'], exit_val=exit_val)
		t.expect(expect)
		if send:
			t.send(send)
		t.read() # required!
		self.remove_device_online()
		return t

	def abort_tx1(self):
		return self._abort_tx('No unsent transactions present', exit_val=2)

	def abort_tx2(self):
		return self._abort_tx('(y/N): ', 'y')

	def _xmr_autosign_op(
			self,
			op,
			desc          = None,
			signable_desc = None,
			ext           = None,
			wallet_arg    = None,
			add_opts      = [],
			wait_signed   = False):
		if wait_signed:
			self._wait_signed(signable_desc)
		data = self.users[self.user]
		args = (
			self.extra_opts
			+ self.autosign_opts
			+ ([f'--{self.user}', '--compat'] if self.compat else [])
			+ [f'--daemon=localhost:{data.md.rpc_port}']
			+ add_opts
			+ [op]
			+ ([get_file_with_ext(self.asi.xmr_tx_dir, ext)] if ext else [])
			+ ([wallet_arg] if wallet_arg else []))
		desc_pfx = f'{desc}, ' if desc else ''
		self.insert_device_online() # device must be removed by calling method
		return self.spawn('mmgen-xmrwallet', args, extra_desc=f'({desc_pfx}user)')

	def _sync_chkbal(self, wallet_arg, bal_chk_func):
		return self.sync_wallets(
			self.user,
			op           = 'sync',
			wallets      = wallet_arg,
			bal_chk_func = bal_chk_func)

	def sync_chkbal1(self):
		return self._sync_chkbal('1', lambda n, b, ub: b == ub and 1 < b < 1.12)
		# 1.234567891234 - 0.124 = 1.110567891234 (minus fees)

	def sync_chkbal2(self):
		return self._sync_chkbal('1', lambda n, b, ub: b == ub and 0.8 < b < 0.86)
		# 1.234567891234 - 0.124 - 0.257 = 0.853567891234 (minus fees)

	def sync_chkbal3(self):
		return self._sync_chkbal(
			'1-2',
			lambda n, b, ub: b == ub and ((n == 1 and 0.8 < b < 0.86) or (n == 2 and b > 1.23)))

	async def submit_transfer_tx1(self):
		return await self._submit_transfer_tx()

	async def resubmit_transfer_tx1(self):
		return await self._submit_transfer_tx(
			relay_parm = self.tx_relay_daemon_proxy_parm,
			op         = 'resubmit',
			check_bal  = False)

	async def submit_transfer_tx2(self):
		return await self._submit_transfer_tx(relay_parm=self.tx_relay_daemon_parm)

	async def _submit_transfer_tx(self, relay_parm=None, ext=None, op='submit', check_bal=True):
		t = self._xmr_autosign_op(
			op            = op,
			add_opts      = [f'--tx-relay-daemon={relay_parm}'] if relay_parm else [],
			ext           = ext,
			signable_desc = 'transaction',
			wait_signed   = op == 'submit')
		t.expect(f'{op.capitalize()} transaction? (y/N): ', 'y')
		t.written_to_file('Submitted transaction')
		t.read()
		self.remove_device_online() # device was inserted by _xmr_autosign_op()
		if check_bal:
			t.ok()
			return await self.mine_chk(
				self.user, 1, 0,
				lambda x: 0 < x.ub < 1.234567891234,
				'unlocked balance 0 < 1.234567891234')
		else:
			return t

	def _export_outputs(self, wallet_arg, op, add_opts=[]):
		t = self._xmr_autosign_op(
			op         = op,
			wallet_arg = wallet_arg,
			add_opts   = add_opts)
		t.written_to_file('Wallet outputs')
		t.read()
		self.remove_device_online() # device was inserted by _xmr_autosign_op()
		return t

	def export_outputs1(self):
		return self._export_outputs('1', op='export-outputs')

	def export_outputs2(self): # NB: --rescan-spent does not work with testnet/stagenet
		return self._export_outputs('1', op='export-outputs-sign', add_opts=['--rescan-blockchain'])

	def export_outputs3(self):
		return self._export_outputs('1-2', op='export-outputs-sign')

	def _import_key_images(self, wallet_arg):
		t = self._xmr_autosign_op(
			op            = 'import-key-images',
			wallet_arg    = wallet_arg,
			signable_desc = 'wallet outputs',
			wait_signed   = True)
		t.read()
		self.remove_device_online() # device was inserted by _xmr_autosign_op()
		return t

	def import_key_images1(self):
		return self._import_key_images(None)

	def import_key_images2(self):
		return self._import_key_images(None)

	def txlist(self):
		self.insert_device_online()
		t = self.spawn('mmgen-xmrwallet', self.autosign_opts + ['txlist'])
		t.match_expect_list([
			'SUBMITTED',
			'Network', 'Submitted',
			'transfer 1:0', '-> ext',
			'transfer 1:0', '-> ext'
		])
		t.read()
		self.remove_device_online()
		return t

	def txview(self):
		self.insert_device_online()
		t = self.spawn('mmgen-xmrwallet', self.autosign_opts + ['txview'])
		t.read()
		self.remove_device_online()
		return t

	def txview_all(self):
		self.spawn(msg_only=True)
		self.insert_device()
		self.do_mount()
		imsg(blue('Opening transaction directory: ') + cyan(f'{self.asi.xmr_tx_dir}'))
		for fn in self.asi.xmr_tx_dir.iterdir():
			imsg('\n' + brown(f'Viewing ‘{fn.name}’'))
			self.spawn('mmgen-xmrwallet', ['txview', str(fn)], no_msg=True).read()
		imsg('')
		self.do_umount()
		self.remove_device()
		return 'ok'

	def check_tx_dirs(self):

		self.insert_device()
		self.do_mount()
		before = '\n'.join(self._gen_listing())
		self.do_umount()
		self.remove_device()

		self.insert_device()
		t = self.spawn('mmgen-autosign', self.opts + ['clean'])
		t.read()
		self.remove_device()

		self.insert_device()
		self.do_mount()
		after = '\n'.join(self._gen_listing())
		self.do_umount()
		self.remove_device()

		imsg(f'\nBefore cleaning:\n{before}')
		imsg(f'\nAfter cleaning:\n{after}')
		pat = r'xmr/tx: \s*\S+\.subtx \S+\.subtx\s+xmr/outputs:\s*$'
		assert re.search(pat, after, re.DOTALL), f'regex search for {pat} failed'
		return t

	def view(self):
		return self.sync_wallets(self.user, op='view', wallets='1')

	def listview(self):
		return self.sync_wallets(self.user, op='listview', wallets='2')

class CmdTestXMRAutosignNoCompat(CmdTestXMRAutosign):
	"""
	Monero autosigning operations (non-xmrwallet compat mode)
	"""
	compat = False

class CmdTestXMRCompat(CmdTestXMRAutosign):
	"""
	Monero autosigning operations (compat mode)
	"""
	menu_prompt = 'efresh balances:\b'
	listaddresses_menu_prompt = 'efresh bals:\b'
	extra_daemons = ['ltc_rt']

	cmd_group = (
		('autosign_setup',          'autosign setup with user’s seed'),
		('autosign_xmr_setup',      'autosign setup (creation of Monero signing wallets)'),
		('addrimport_user',         'creating (importing) user’s watch-only wallets from key-address file'),
		('addrimport_user2',        'reimporting user’s watch-only wallets from key-address file'),
		('gen_kafile_miner',        'generating key-address file for Miner'),
		('gen_vkafile_user',        'generating viewkey-address file for user'),
		('create_wallet_miner',     'creating Monero wallet for Miner'),
		('mine_initial_coins',      'mining initial coins'),
		('fund_user2',              'sending funds to user (wallet #2)'),
		('check_bal_user2',         'mining, checking balance (wallet #2)'),
		('fund_user1',              'sending funds to user (wallet #1)'),
		('mine_blocks_10',          'mining some blocks'),
		('user_listaddresses_lbl',  'adding label to user’s tracking wallets (listaddresses)'),
		('fund_user1b',             'sending funds to user (wallet #1)'),
		('mine_blocks_10',          'mining some blocks'),
		('user_twview1',            'adding label to user’s tracking wallets (twview)'),
		('new_account_user',        'adding an account to user’s wallet'),
		('new_address_user',        'adding an address to user’s wallet'),
		('new_address_user_label',  'adding an address to user’s wallet (with label)'),
		('user_dump',               'dumping user’s wallets to JSON format'),
		('fund_user_sub1',          'sending funds to user’s subaddress #1 (wallet #2)'),
		('mine_blocks_1',           'mining a block'),
		('fund_user_sub2',          'sending funds to user’s subaddress #2 (wallet #2)'),
		('mine_blocks_1',           'mining a block'),
		('fund_user_sub3',          'sending funds to user’s subaddress #3 (wallet #2)'),
		('user_twview2',            'viewing user’s tracking wallets (reload, sort options)'),
		('user_twview_chk1',        'viewing user’s tracking wallets (check balances)'),
		('user_listaddresses_sort', 'listing user’s addresses (sort options)'),
		('wait_loop_start_compat',  'starting autosign wait loop in XMR compat mode [--coins=xmr]'),
		('user_txcreate1',          'creating a transaction'),
		('user_txabort1',           'aborting the transaction'),
		('user_txcreate2',          'recreating the transaction'),
		('wait_signed1',            'autosigning the transaction'),
		('wait_loop_kill',          'stopping autosign wait loop'),
		('user_txabort2',           'aborting the raw and signed transactions'),
		('user_txcreate3',          'recreating the transaction'),
		('wait_loop_start_ltc',     'starting autosign wait loop in XMR compat mode [--coins=ltc,xmr]'),
		('user_txsend1',            'sending the transaction'),
		('user_txstatus1',          'getting the transaction status (in mempool)'),
		('mine_blocks_10',          'mining some blocks'),
		('user_txstatus2',          'getting the transaction status (confirmations)'),
		('user_txstatus3',          'getting the transaction status (verbose)'),
		('user_twview_chk2',        'viewing user’s tracking wallets (check balances)'),
		('user_txcreate_sweep1',    'creating a sweep transaction (account sweep)'),
		('user_txsend2',            'sending the transaction'),
		('mine_blocks_10',          'mining some blocks'),
		('user_twview_chk3',        'viewing user’s tracking wallets (check balances)'),
		('user_txcreate_sweep2',    'creating a sweep transaction (address sweep)'),
		('user_txsend3',            'sending the transaction'),
		('mine_blocks_10',          'mining some blocks'),
		('user_twview_chk4',        'viewing user’s tracking wallets (check balances)'),
		('wait_loop_kill',          'stopping autosign wait loop'),
		('delete_offline_shmdir',   'deleting offline autosign wallet dir'),
		('autosign_setup',          'autosign setup with user’s seed'),
		('autosign_xmr_setup_redo', 'autosign setup (creation of Monero signing wallets, redo)'),
		('wait_loop_start_compat',  'starting autosign wait loop in XMR compat mode [--coins=xmr]'),
		('user_txcreate_sweep3',    'creating a sweep transaction (sweep to empty account)'),
		('user_txsend4',            'sending the transaction'),
		('mine_blocks_10',          'mining some blocks'),
		('user_twview_chk5',        'viewing user’s tracking wallets (check balances)'),
		('wait_loop_kill',          'stopping autosign wait loop'),
		('user_newacct1',           'adding account to user’s tracking wallet (dfl label)'),
		('user_newacct2',           'adding account to user’s tracking wallet (no timestr)'),
		('user_newacct3',           'adding account to user’s tracking wallet'),
		('user_newacct4',           'adding account to user’s tracking wallet (dfl label, no timestr)'),
		('user_newaddr1',           'adding address to user’s tracking wallet'),
		('user_newaddr2',           'adding address to user’s tracking wallet (no timestr)'),
		('user_newaddr3',           'adding address to user’s tracking wallet (dfl label)'),
		('user_newaddr4',           'adding address to user’s tracking wallet (dfl label, no timestr)'),
		('stop_daemons',            'stopping all wallet and coin daemons'))

	def __init__(self, cfg, trunner, cfgs, spawn):
		super().__init__(cfg, trunner, cfgs, spawn)
		if trunner is None:
			return
		data = self.users[self.user]
		self.user_dump_file = os.path.join(
			data.wd.wallet_dir,
			f'{data.sid}-2-MoneroWatchOnlyWallet.regtest.dump')
		self.user_daemon_opts = [
			f'--monero-daemon=localhost:{data.md.rpc_port}',
			'--monero-wallet-rpc-password=abc',
			'--regtest=1']
		self.user_opts = [f'--{self.user}', '--coin=xmr'] + self.user_daemon_opts

	def addrimport_user(self):
		return self._addrimport_user(create_address_files=True)

	def addrimport_user2(self):
		return self._addrimport_user(expect_str='Skipping.*Skipping')

	def _addrimport_user(self, *, expect_str=None, create_address_files=False):
		self.insert_device_online()
		t = self.spawn('mmgen-addrimport', self.user_opts + self.autosign_opts)
		if expect_str:
			t.expect(expect_str, regex=True)
		if create_address_files:
			self._create_address_files(t, self.user)
		t.read() # required!
		self.remove_device_online()
		return t

	async def mine_blocks_1(self):
		return await self._mine_blocks(1)

	async def mine_blocks_10(self):
		return await self._mine_blocks(10)

	async def _mine_blocks(self, n):
		self.spawn(msg_only=True)
		return await self.mine(n)

	def _new_addr_user_autosign(self, *args):
		return self._new_addr_user(self.user, *args, do_autosign=True)

	async def user_dump(self):
		t = self._xmr_autosign_op('dump')
		t.read()
		self.remove_device_online() # device was inserted by _xmr_autosign_op()
		return t

	async def fund_user_sub1(self):
		return await self._fund_user_autosign(1, 9876543210)

	async def fund_user_sub2(self):
		return await self._fund_user_autosign(2, 8765432109)

	async def fund_user_sub3(self):
		return await self._fund_user_autosign(3, 7654321098)

	async def _fund_user_autosign(self, addr_num, amt):
		data = json.loads(read_from_file(self.user_dump_file))
		addr_data = data['MoneroMMGenWalletDumpFile']['data']['wallet_metadata'][1]['addresses']
		return await self._fund_user(self.user, addr=addr_data[addr_num-1]['address'], amt=amt)

	def user_newacct1(self):
		return self._user_newacct(2, lbl_text='New Test Account', add_timestr=True)

	def user_newacct2(self):
		return self._user_newacct(1, lbl_text='New Test Account')

	def user_newacct3(self):
		return self._user_newacct(2, add_timestr=True)

	def user_newacct4(self):
		return self._user_newacct(2)

	def _user_newacct(self, wallet_num, lbl_text='', add_timestr=False):
		return self._user_twops(
			'listaddresses',
			newacct_wallet_num = wallet_num,
			lbl_text = lbl_text,
			add_timestr = add_timestr,
			expect_str = (lbl_text or 'new account ') + (r'.*\[20.*\]' if add_timestr else ''))

	def user_newaddr1(self):
		return self._user_newaddr(1, lbl_text='New Test Address', add_timestr=True)

	def user_newaddr2(self):
		return self._user_newaddr(1, lbl_text='New Test Address')

	def user_newaddr3(self):
		return self._user_newaddr(2, add_timestr=True)

	def user_newaddr4(self):
		return self._user_newaddr(2)

	def _user_newaddr(self, acct_num, lbl_text='', add_timestr=False):
		return self._user_twops(
			'listaddresses',
			newaddr_acct_num = acct_num,
			lbl_text = lbl_text,
			add_timestr = add_timestr,
			expect_str = (lbl_text or 'new address ') + (r'.*\[20.*\]' if add_timestr else ''))

	def user_listaddresses(self):
		return self._user_twops('listaddresses')

	def user_listaddresses_refresh(self):
		return self._user_twops('listaddresses', menu='R')

	def user_listaddresses_interact(self):
		return self._user_twops('listaddresses', pexpect_interact=True) # requires cmdtest.py -O

	def user_listaddresses_sort(self):
		return self._user_twops('listaddresses', menu='aAdMELLuuuraAdMeEuu')

	def user_listaddresses_lbl(self):
		return self._user_twops(
			'listaddresses',
			lbl_acct_num = 2,
			lbl_addr_idx = 0,
			lbl_text = 'New Test Label',
			add_timestr = True,
			menu = 'R',
			expect_str = r'Primary account.*1\.234567891234')

	def user_twview(self):
		return self._user_twops('twview')

	def user_twview1(self):
		return self._user_twops(
			'twview',
			lbl_acct_num = 1,
			lbl_addr_idx = 0,
			lbl_text = 'New Test Label',
			menu = 'R',
			expect_str = r'New Test Label.*2\.469135782468')

	def user_twview2(self):
		return self._user_twops('twview', menu='RaAdMraAdMe')

	def user_twview_chk1(self):
		return self._user_twview_chk([
			'Total XMR: 3.722345649021 [3.729999970119]',
			'1         0.026296296417',
			'0.007654321098'])

	def user_twview_chk2(self):
		return self._user_twview_chk(['Total XMR: 3.715053370119'], sync=True)

	def user_twview_chk3(self):
		return self._user_twview_chk(['Total XMR: 3.713242570119', '1.232757091234'], sync=True)

	def user_twview_chk4(self):
		return self._user_twview_chk(['Total XMR: 3.709050970119', '1.254861787651'], sync=True)

	def user_twview_chk5(self):
		return self._user_twview_chk(['Total XMR: 3.707234170119', '2.452375982468'], sync=True)

	def _user_twview_chk(self, expect_arr, sync=False):
		return self._user_twops(
			'twview',
			interactive = sync,
			menu = 'R' if sync else '',
			expect_arr = expect_arr)

	def _user_twops(
			self,
			op,
			*,
			lbl_acct_num = None,
			lbl_addr_idx = None,
			newacct_wallet_num = None,
			newaddr_acct_num = None,
			lbl_text = '',
			add_timestr = False,
			menu = '',
			interactive = True,
			pexpect_interact = False,
			expect_str = '',
			expect_arr = []):

		self.insert_device_online()
		t = self.spawn(
			'mmgen-tool',
			self.user_opts
			+ self.autosign_opts
			+ [op]
			+ (['interactive=1'] if interactive else []))
		menu_prompt = self.listaddresses_menu_prompt if op == 'listaddresses' else self.menu_prompt
		have_lbl = lbl_acct_num or newacct_wallet_num or newaddr_acct_num
		have_new_addr = newacct_wallet_num or newaddr_acct_num
		if pexpect_interact:
			t.p.interact() # pexpect interact() is currently broken
			self.remove_device_online()
			return t
		elif interactive:
			if lbl_acct_num:
				t.expect(menu_prompt, 'l')
				t.expect('main menu): ', str(lbl_acct_num))
				t.expect('main menu): ', str(lbl_addr_idx))
			elif newacct_wallet_num:
				t.expect(menu_prompt, 'N')
				t.expect('number, or ENTER to return to main menu> ', f'{newacct_wallet_num}\n')
			elif newaddr_acct_num:
				t.expect(menu_prompt, 'n')
				t.expect('main menu): ', str(newaddr_acct_num))
			if have_lbl:
				t.expect(': ', lbl_text + '\n')                    # add label
				t.expect('(y/N): ', ('y' if add_timestr else 'n')) # add timestr
			if have_new_addr:
				t.expect('(y/N): ', 'y')
			for ch in menu:
				t.expect(menu_prompt, ch)
			if expect_str:
				t.expect(expect_str, regex=True)
			t.expect(menu_prompt, 'q')
		elif expect_arr:
			text = strip_ansi_escapes(t.read())
			for s in expect_arr:
				assert s in text
		t.read()
		self.remove_device_online()
		return t

	def wait_loop_start_compat(self):
		return self.wait_loop_start(opts=['--xmrwallet-compat', '--coins=xmr'])

	def wait_loop_start_ltc(self):
		return self.wait_loop_start(opts=['--xmrwallet-compat', '--coins=ltc,xmr'])

	def user_txcreate1(self):
		return self._user_txops('txcreate', [f'{self.burn_addr},0.012345'], acct_num=1)

	def user_txcreate_sweep1(self):
		return self._user_txops('txcreate', menu='S', sweep_menu='23', sweep_type='sweep')

	def user_txcreate_sweep2(self):
		return self._user_txops('txcreate', menu='s', sweep_menu='3', sweep_type='sweep_all')

	def user_txcreate_sweep3(self):
		return self._user_txops('txcreate', menu='S', sweep_menu='12', sweep_type='sweep')

	user_txcreate3 = user_txcreate2 = user_txcreate1

	def _user_txabort(self):
		return self._user_txops('txsend', opts=[f'--{self.user}', '--abort'])

	user_txabort1 = user_txabort2 = _user_txabort

	def _user_txsend(self):
		return self._user_txops(
			'txsend',
			opts        = [f'--{self.user}', '--quiet'],
			add_opts    = self.user_daemon_opts,
			wait_signed = True)

	user_txsend1 = user_txsend2 = user_txsend3 = user_txsend4 = _user_txsend

	def user_txstatus1(self):
		return self._user_txstatus(expect_str='TxID: .* in mempool')

	def user_txstatus2(self):
		return self._user_txstatus(['--quiet'], expect_str='confirmations')

	def user_txstatus3(self):
		return self._user_txstatus(['--verbose'], expect_str='confirmations.*Info for transaction')

	def _user_txstatus(self, add_opts=[], expect_str=None):
		return self._user_txops(
			'txsend',
			opts     = [f'--{self.user}', '--status'],
			add_opts = self.user_daemon_opts + add_opts,
			expect_str = expect_str)

	def wait_signed1(self):
		self.spawn(msg_only=True)
		oqmsg('')
		self._wait_signed('transaction')
		return 'silent'

	def _user_txops(
			self,
			op,
			args = [],
			*,
			opts = [],
			add_opts = [],
			menu = '',
			acct_num = None,
			wait_signed = False,
			sweep_type = None,
			sweep_menu = '',
			signable_desc = 'transaction',
			expect_str = None,
			exit_val = 0):
		if wait_signed:
			self._wait_signed(signable_desc)
		self.insert_device_online()
		t = self.spawn(
			f'mmgen-{op}',
			(opts or self.user_opts)
			+ self.autosign_opts
			+ add_opts
			+ args,
			exit_val = exit_val)
		if exit_val:
			pass
		elif '--abort' in opts:
			t.expect('(y/N): ', 'y')
		elif op == 'txcreate':
			if sweep_type:
				t.expect(self.menu_prompt, menu)
				for ch in sweep_menu:
					t.expect('main menu): ', ch)
				t.expect('number> ', {'sweep': '1', 'sweep_all': '2'}[sweep_type])
				t.expect('(y/N): ', 'y') # create new address?
			else:
				for ch in menu + 'q':
					t.expect(self.menu_prompt, ch)
				t.expect('to spend from: ', f'{acct_num}\n')
			t.expect('(y/N): ', 'y') # save?
		elif op == 'txsend' and not '--status' in opts:
			t.expect('(y/N): ', 'y') # view?
		if expect_str:
			t.expect(expect_str, regex=True)
		t.read() # required!
		self.remove_device_online()
		return t
