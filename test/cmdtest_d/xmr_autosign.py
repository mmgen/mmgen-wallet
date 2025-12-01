#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
	# user sid autosign port_shift kal_range add_coind_args
	user_data = (
		('miner', '98831F3A', False, 130, '1', []),
		('alice', 'FE3C6545', True,  150, '1-2', []))

	# autosign attrs:
	coins = ['xmr']
	compat = True

	cmd_group = (
		('daemon_version',           'checking daemon version'),
		('create_tmp_wallets',       'creating temporary online wallets for Alice'),
		('new_account_alice',        'adding an account to Alice’s tmp wallet'),
		('new_address_alice',        'adding an address to Alice’s tmp wallet'),
		('new_address_alice_label',  'adding an address to Alice’s tmp wallet (with label)'),
		('dump_tmp_wallets',         'dumping Alice’s tmp wallets'),
		('dump_tmp_wallets_json',    'dumping Alice’s tmp wallets to JSON format'),
		('delete_tmp_wallets',       'deleting Alice’s tmp wallets'),
		('gen_kafile_miner',         'generating key-address file for Miner'),
		('create_wallet_miner',      'creating Monero wallet for Miner'),
		('mine_initial_coins',       'mining initial coins'),
		('autosign_setup',           'autosign setup with Alice’s seed'),
		('autosign_xmr_setup',       'autosign setup (creation of Monero signing wallets)'),
		('restore_watchonly_wallets', 'creating watch-only wallets from Alice’s wallet dumps'),
		('delete_tmp_dump_files',    'deleting Alice’s dump files'),
		('fund_alice1',              'sending funds to Alice (wallet #1)'),
		('check_bal_alice1',         'mining, checking balance (wallet #1)'),
		('fund_alice2',              'sending funds to Alice (wallet #2)'),
		('check_bal_alice2',         'mining, checking balance (wallet #2)'),
		('wait_loop_start',          'starting autosign wait loop'),
		('export_outputs1',          'exporting outputs from Alice’s watch-only wallet #1'),
		('create_transfer_tx1',      'creating a transfer TX'),
		('submit_transfer_tx1',      'submitting the transfer TX'),
		('resubmit_transfer_tx1',    'resubmitting the transfer TX'),
		('export_outputs2',          'exporting outputs from Alice’s watch-only wallet #1'),
		('import_key_images1',       'importing signed key images into Alice’s online wallets'),
		('sync_chkbal1',             'syncing Alice’s wallet #1'),
		('abort_tx1',                'aborting the current transaction (error)'),
		('create_transfer_tx2',      'creating a transfer TX (for relaying via proxy)'),
		('abort_tx2',                'aborting the current transaction (OK, unsigned)'),
		('create_transfer_tx2a',     'creating the transfer TX again'),
		('submit_transfer_tx2',      'submitting the transfer TX (relaying via proxy)'),
		('sync_chkbal2',             'syncing Alice’s wallets and checking balance'),
		('dump_wallets',             'dumping Alice’s wallets'),
		('delete_wallets',           'deleting Alice’s wallets'),
		('restore_wallets',          'creating online (watch-only) wallets for Alice'),
		('delete_dump_files',        'deleting Alice’s dump files'),
		('export_outputs3',          'exporting outputs from Alice’s watch-only wallets'),
		('import_key_images2',       'importing signed key images into Alice’s online wallets'),
		('sync_chkbal3',             'syncing Alice’s wallets and checking balance'),
		('wait_loop_kill',           'stopping autosign wait loop'),
		('stop_daemons',             'stopping all wallet and coin daemons'),
		('view',                     'viewing Alice’s wallet in offline mode (wallet #1)'),
		('listview',                 'list-viewing Alice’s wallet in offline mode (wallet #2)'),
		('txlist',                   'listing Alice’s submitted transactions'),
		('txview',                   'viewing Alice’s submitted transactions'),
		('txview_all',               'viewing all raw, signed and submitted transactions'),
		('check_tx_dirs',            'cleaning and checking signable file directories'),
	)

	def __init__(self, cfg, trunner, cfgs, spawn):

		CmdTestAutosignThreaded.__init__(self, cfg, trunner, cfgs, spawn)
		CmdTestXMRWallet.__init__(self, cfg, trunner, cfgs, spawn)

		if trunner is None:
			return

		from mmgen.cfg import Config
		self.alice_cfg = Config({
			'coin': 'XMR',
			'outdir': self.users['alice'].udir,
			'wallet_rpc_password': 'passwOrd',
			'test_suite': True,
		} | ({
			'alice': True,
			'compat': True
		} if self.compat else {
			'wallet_dir': self.users['alice'].udir
		}))

		self.burn_addr = make_burn_addr(cfg)

		self.opts.append('--xmrwallets={}'.format(self.users['alice'].kal_range)) # mmgen-autosign opts
		self.autosign_opts = ['--autosign']                                       # mmgen-xmrwallet opts
		self.spawn_env['MMGEN_TEST_SUITE_XMR_AUTOSIGN'] = '1'

	def create_tmp_wallets(self):
		self.spawn(msg_only=True)
		data = self.users['alice']
		from mmgen.wallet import Wallet
		from mmgen.xmrwallet import op
		from mmgen.addrlist import KeyAddrList
		silence()
		kal = KeyAddrList(
			cfg       = self.alice_cfg,
			proto     = self.proto,
			addr_idxs = '1-2',
			seed      = Wallet(self.alice_cfg, fn=data.mmwords).seed,
			skip_chksum_msg = True,
			key_address_validity_check = False)
		kal.file.write(ask_overwrite=False)
		fn = get_file_with_ext(data.udir, 'akeys')
		m = op('create', self.alice_cfg, fn, '1-2')
		asyncio.run(m.main())
		asyncio.run(m.stop_wallet_daemon())
		end_silence()
		return 'ok'

	def _new_addr_alice(self, *args):
		data = self.users['alice']
		return self.new_addr_alice(
			*args,
			kafile = get_file_with_ext(data.udir, 'akeys'))

	def new_account_alice(self):
		return self._new_addr_alice(
			'2',
			'start',
			r'Creating new account for wallet .*2.* with label '
			r'.*‘xmrwallet new account .*y/N\): ')

	def new_address_alice(self):
		return self._new_addr_alice(
			'2:1',
			'continue',
			r'Creating new address for wallet .*2.*, account .*#1.* with label '
			r'.*‘xmrwallet new address .*y/N\): ')

	def new_address_alice_label(self):
		return self._new_addr_alice(
			'2:1,Alice’s new address',
			'stop',
			r'Creating new address for wallet .*2.*, account .*#1.* with label '
			r'.*‘Alice’s new address .*y/N\): ')

	def dump_tmp_wallets(self):
		return self._dump_wallets(autosign=False)

	def dump_tmp_wallets_json(self):
		return self._dump_wallets(autosign=False, op='dump_json')

	def dump_wallets(self):
		return self._dump_wallets(autosign=True)

	def _dump_wallets(self, autosign, op='dump'):
		data = self.users['alice']
		self.insert_device_online()
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ (['--alice', '--compat'] if self.compat else [f'--wallet-dir={data.udir}'])
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
		data = self.users['alice']
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
		return self.gen_kafiles(['miner'])

	def create_wallet_miner(self):
		return self.create_wallets_miner()

	def delete_dump_files(self):
		return self._delete_files('.dump')

	async def fund_alice1(self):
		return await self.fund_alice(wallet=1)

	fund_alice1b = fund_alice1

	async def check_bal_alice1(self):
		return await self.check_bal_alice(wallet=1)

	async def fund_alice2(self):
		return await self.fund_alice(wallet=2)

	async def check_bal_alice2(self):
		return await self.check_bal_alice(wallet=2)

	def autosign_setup(self):
		return self.run_setup(
			mn_type        = 'mmgen',
			mn_file        = self.users['alice'].mmwords,
			use_dfl_wallet = None,
			expect_args    = ['Continue with Monero setup? (Y/n): ', 'n'])

	def autosign_xmr_setup(self):
		self.insert_device_online()
		self.do_mount_online()
		self.asi_online.xmr_dir.mkdir(exist_ok=True)
		(self.asi_online.xmr_dir / 'old.vkeys').touch()
		self.do_umount_online()
		self.remove_device_online()

		self.insert_device()
		t = self.spawn('mmgen-autosign', self.opts + ['xmr_setup'], no_passthru_opts=True)
		t.written_to_file('View keys')
		t.read()
		self.remove_device()
		return t

	def restore_watchonly_wallets(self):
		return self._create_wallets('restore')

	def restore_wallets(self):
		return self._create_wallets('restore')

	def _create_wallets(self, op='create'):
		self.insert_device_online()
		t = self.create_wallets('alice', op=op)
		t.read() # required!
		self.remove_device_online()
		return t

	def _create_transfer_tx(self, amt, add_opts=[]):
		self.insert_device_online()
		t = self.do_op(
			'transfer',
			'alice',
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
		data = self.users['alice']
		args = (
			self.extra_opts
			+ self.autosign_opts
			+ (['--alice', '--compat'] if self.compat else [f'--wallet-dir={data.udir}'])
			+ [f'--daemon=localhost:{data.md.rpc_port}']
			+ add_opts
			+ [op]
			+ ([get_file_with_ext(self.asi.xmr_tx_dir, ext)] if ext else [])
			+ ([wallet_arg] if wallet_arg else []))
		desc_pfx = f'{desc}, ' if desc else ''
		self.insert_device_online() # device must be removed by calling method
		return self.spawn('mmgen-xmrwallet', args, extra_desc=f'({desc_pfx}Alice)')

	def _sync_chkbal(self, wallet_arg, bal_chk_func):
		return self.sync_wallets(
			'alice',
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
				'alice', 1, 0,
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
		return self.sync_wallets('alice', op='view', wallets='1')

	def listview(self):
		return self.sync_wallets('alice', op='listview', wallets='2')

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
	extra_daemons = ['ltc']

	cmd_group = (
		('autosign_setup',           'autosign setup with Alice’s seed'),
		('autosign_xmr_setup',       'autosign setup (creation of Monero signing wallets)'),
		('create_watchonly_wallets', 'creating Alice’s watch-only wallets'),
		('gen_kafile_miner',         'generating key-address file for Miner'),
		('create_wallet_miner',      'creating Monero wallet for Miner'),
		('mine_initial_coins',       'mining initial coins'),
		('fund_alice2',              'sending funds to Alice (wallet #2)'),
		('check_bal_alice2',         'mining, checking balance (wallet #2)'),
		('fund_alice1',              'sending funds to Alice (wallet #1)'),
		('mine_blocks_10',           'mining some blocks'),
		('alice_listaddresses1',     'adding label to Alice’s tracking wallets (listaddresses)'),
		('fund_alice1b',             'sending funds to Alice (wallet #1)'),
		('mine_blocks_10',           'mining some blocks'),
		('alice_twview1',            'adding label to Alice’s tracking wallets (twview)'),
		('new_account_alice',        'adding an account to Alice’s wallet'),
		('new_address_alice',        'adding an address to Alice’s wallet'),
		('new_address_alice_label',  'adding an address to Alice’s wallet (with label)'),
		('alice_dump',               'dumping alice’s wallets to JSON format'),
		('fund_alice_sub1',          'sending funds to Alice’s subaddress #1 (wallet #2)'),
		('mine_blocks_1',            'mining a block'),
		('fund_alice_sub2',          'sending funds to Alice’s subaddress #2 (wallet #2)'),
		('mine_blocks_1',            'mining a block'),
		('fund_alice_sub3',          'sending funds to Alice’s subaddress #3 (wallet #2)'),
		('alice_twview2',            'viewing Alice’s tracking wallets (reload, sort options)'),
		('alice_twview3',            'viewing Alice’s tracking wallets (check balances)'),
		('alice_listaddresses2',     'listing Alice’s addresses (sort options)'),
		('wait_loop_start_compat',   'starting autosign wait loop in XMR compat mode [--coins=xmr]'),
		('alice_txcreate1',          'creating a transaction'),
		('alice_txabort1',           'aborting the transaction'),
		('alice_txcreate2',          'recreating the transaction'),
		('wait_signed1',             'autosigning the transaction'),
		('wait_loop_kill',           'stopping autosign wait loop'),
		('alice_txabort2',           'aborting the raw and signed transactions'),
		('alice_txcreate3',          'recreating the transaction'),
		('wait_loop_start_ltc',      'starting autosign wait loop in XMR compat mode [--coins=ltc,xmr]'),
		('alice_txsend1',            'sending the transaction'),
		('wait_loop_kill',           'stopping autosign wait loop'),
		('stop_daemons',             'stopping all wallet and coin daemons'),
	)

	def __init__(self, cfg, trunner, cfgs, spawn):
		super().__init__(cfg, trunner, cfgs, spawn)
		if trunner is None:
			return
		self.alice_tw_dir = os.path.join(self.tr.data_dir, 'alice', 'altcoins', 'xmr', 'tracking-wallets')
		self.alice_dump_file = os.path.join(
			self.alice_tw_dir,
			'{}-2-MoneroWatchOnlyWallet.dump'.format(self.users['alice'].sid))
		self.alice_daemon_opts = [
			f'--monero-daemon=localhost:{self.users["alice"].md.rpc_port}',
			'--monero-wallet-rpc-password=passwOrd']
		self.alice_opts = ['--alice', '--coin=xmr'] + self.alice_daemon_opts

	def create_watchonly_wallets(self):
		return self._create_wallets()

	async def mine_blocks_1(self):
		return await self._mine_blocks(1)

	async def mine_blocks_10(self):
		return await self._mine_blocks(10)

	async def _mine_blocks(self, n):
		self.spawn(msg_only=True)
		return await self.mine(n)

	def _new_addr_alice(self, *args):
		return self.new_addr_alice(*args, do_autosign=True)

	async def alice_dump(self):
		t = self._xmr_autosign_op('dump')
		t.read()
		self.remove_device_online() # device was inserted by _xmr_autosign_op()
		return t

	async def fund_alice_sub1(self):
		return await self._fund_alice(1, 9876543210)

	async def fund_alice_sub2(self):
		return await self._fund_alice(2, 8765432109)

	async def fund_alice_sub3(self):
		return await self._fund_alice(3, 7654321098)

	async def _fund_alice(self, addr_num, amt):
		data = json.loads(read_from_file(self.alice_dump_file))
		addr_data = data['MoneroMMGenWalletDumpFile']['data']['wallet_metadata'][1]['addresses']
		return await self.fund_alice(addr=addr_data[addr_num-1]['address'], amt=amt)

	def alice_listaddresses1(self):
		return self._alice_twops(
			'listaddresses',
			lbl_addr_num = 2,
			lbl_addr_idx_num = 0,
			lbl_add_timestr = True,
			menu = 'R',
			expect_str = r'Primary account.*1\.234567891234')

	def alice_twview(self):
		return self._alice_twops('twview')

	def alice_twview1(self):
		return self._alice_twops(
			'twview',
			lbl_addr_num = 1,
			lbl_addr_idx_num = 0,
			menu = 'R',
			expect_str = r'New Label.*2\.469135782468')

	def alice_twview2(self):
		return self._alice_twops('twview', menu='RaAdMraAdMe')

	def alice_twview3(self):
		return self._alice_twops(
			'twview',
			expect_arr = [
				'Total XMR: 3.722345649021 [3.729999970119]',
				'1         0.026296296417',
				'0.007654321098'])

	def alice_listaddresses2(self):
		return self._alice_twops('listaddresses', menu='aAdMELLuuuraAdMeEuu')

	def _alice_twops(
			self,
			op,
			*,
			lbl_addr_num = None,
			lbl_addr_idx_num = None,
			lbl_add_timestr = False,
			menu = '',
			expect_str = '',
			expect_arr = []):

		interactive = not expect_arr
		self.insert_device_online()
		t = self.spawn(
			'mmgen-tool',
			self.alice_opts
			+ self.autosign_opts
			+ [op]
			+ (['interactive=1'] if interactive else []))
		if interactive:
			if lbl_addr_num:
				t.expect(self.menu_prompt, 'l')
				t.expect('main menu): ', str(lbl_addr_num))
				if lbl_addr_idx_num is not None:
					t.expect('main menu): ', str(lbl_addr_idx_num))
				t.expect(': ', 'New Label\n')
				t.expect('(y/N): ', 'y' if lbl_add_timestr else 'n')
			for ch in menu:
				t.expect(self.menu_prompt, ch)
			if expect_str:
				t.expect(expect_str, regex=True)
			t.expect(self.menu_prompt, 'q')
		elif expect_arr:
			text = strip_ansi_escapes(t.read())
			for s in expect_arr:
				assert s in text
		self.remove_device_online()
		return t

	def wait_loop_start_compat(self):
		return self.wait_loop_start(opts=['--xmrwallet-compat', '--coins=xmr'])

	def wait_loop_start_ltc(self):
		return self.wait_loop_start(opts=['--xmrwallet-compat', '--coins=ltc,xmr'])

	def alice_txcreate1(self):
		return self._alice_txops('txcreate', [f'{self.burn_addr},0.012345'], acct_num=1)

	alice_txcreate3 = alice_txcreate2 = alice_txcreate1

	def alice_txabort1(self):
		return self._alice_txops('txsend', opts=['--alice', '--abort'])

	alice_txabort2 = alice_txabort1

	def alice_txsend1(self):
		return self._alice_txops(
			'txsend',
			opts        = ['--alice', '--quiet'],
			add_opts    = self.alice_daemon_opts,
			acct_num    = 1,
			wait_signed = True)

	def wait_signed1(self):
		self.spawn(msg_only=True)
		oqmsg('')
		self._wait_signed('transaction')
		return 'silent'

	def _alice_txops(
			self,
			op,
			args = [],
			*,
			opts = [],
			add_opts = [],
			menu = '',
			acct_num = None,
			wait_signed = False,
			signable_desc = 'transaction'):
		if wait_signed:
			self._wait_signed(signable_desc)
		self.insert_device_online()
		t = self.spawn(f'mmgen-{op}', (opts or self.alice_opts) + self.autosign_opts + add_opts + args)
		if '--abort' in opts:
			t.expect('(y/N): ', 'y')
		elif op == 'txcreate':
			for ch in menu + 'q':
				t.expect(self.menu_prompt, ch)
			t.expect('to spend from: ', f'{acct_num}\n')
			t.expect('(y/N): ', 'y') # save?
		elif op == 'txsend':
			t.expect('(y/N): ', 'y') # view?
		t.read() # required!
		self.remove_device_online()
		return t
