#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet


"""
test.cmdtest_d.ct_xmr_autosign: xmr autosigning tests for the cmdtest.py test suite
"""

import re

from mmgen.color import blue, cyan, brown
from mmgen.util import async_run

from ..include.common import cfg, imsg, silence, end_silence
from .common import get_file_with_ext

from .ct_xmrwallet import CmdTestXMRWallet
from .ct_autosign import CmdTestAutosignThreaded

def make_burn_addr():
	from mmgen.tool.coin import tool_cmd
	return tool_cmd(
		cfg     = cfg,
		cmdname = 'privhex2addr',
		proto   = cfg._proto,
		mmtype  = 'monero').privhex2addr('beadcafe'*8)

class CmdTestXMRAutosign(CmdTestXMRWallet, CmdTestAutosignThreaded):
	"""
	Monero autosigning operations
	"""
	tmpdir_nums = [39]

	# ct_xmrwallet attrs:
	tx_relay_user = 'miner'
	#    user     sid      autosign  shift kal_range add_coind_args
	user_data = (
		('miner', '98831F3A', False, 130, '1', []),
		('alice', 'FE3C6545', True,  150, '1-2', []),
	)

	# ct_autosign attrs:
	coins = ['xmr']

	cmd_group = (
		('daemon_version',           'checking daemon version'),
		('gen_kafile_miner',         'generating key-address file for Miner'),
		('create_wallet_miner',      'creating Monero wallet for Miner'),
		('mine_initial_coins',       'mining initial coins'),
		('create_tmp_wallets',       'creating temporary online wallets for Alice'),
		('new_account_alice',        'adding an account to Alice’s tmp wallet'),
		('new_address_alice',        'adding an address to Alice’s tmp wallet'),
		('new_address_alice_label',  'adding an address to Alice’s tmp wallet (with label)'),
		('dump_tmp_wallets',         'dumping Alice’s tmp wallets'),
		('delete_tmp_wallets',       'deleting Alice’s tmp wallets'),
		('autosign_setup',           'autosign setup with Alice’s seed'),
		('autosign_xmr_setup',       'autosign setup (creation of Monero signing wallets)'),
		('create_watchonly_wallets', 'creating watch-only wallets from Alice’s wallet dumps'),
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

	def __init__(self, trunner, cfgs, spawn):

		CmdTestAutosignThreaded.__init__(self, trunner, cfgs, spawn)
		CmdTestXMRWallet.__init__(self, trunner, cfgs, spawn)

		if trunner is None:
			return

		from mmgen.cfg import Config
		self.cfg = Config({
			'coin': 'XMR',
			'outdir': self.users['alice'].udir,
			'wallet_dir': self.users['alice'].udir,
			'wallet_rpc_password': 'passwOrd',
			'test_suite': True,
		})

		self.burn_addr = make_burn_addr()

		self.opts.append('--xmrwallets={}'.format(self.users['alice'].kal_range)) # mmgen-autosign opts
		self.autosign_opts = ['--autosign']                                       # mmgen-xmrwallet opts
		self.spawn_env['MMGEN_TEST_SUITE_XMR_AUTOSIGN'] = '1'

	def create_tmp_wallets(self):
		self.spawn('', msg_only=True)
		data = self.users['alice']
		from mmgen.wallet import Wallet
		from mmgen.xmrwallet import op
		from mmgen.addrlist import KeyAddrList
		silence()
		kal = KeyAddrList(
			cfg       = self.cfg,
			proto     = self.proto,
			addr_idxs = '1-2',
			seed      = Wallet(cfg, data.mmwords).seed,
			skip_chksum_msg = True,
			key_address_validity_check = False)
		kal.file.write(ask_overwrite=False)
		fn = get_file_with_ext(data.udir, 'akeys')
		m = op('create', self.cfg, fn, '1-2')
		async_run(m.main())
		async_run(m.stop_wallet_daemon())
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
			r'Creating new account for wallet .*2.* with label .*‘xmrwallet new account .*y/N\): ')

	def new_address_alice(self):
		return self._new_addr_alice(
			'2:1',
			'continue',
			r'Creating new address for wallet .*2.*, account .*#1.* with label .*‘xmrwallet new address .*y/N\): ')

	def new_address_alice_label(self):
		return self._new_addr_alice(
			'2:1,Alice’s new address',
			'stop',
			r'Creating new address for wallet .*2.*, account .*#1.* with label .*‘Alice’s new address .*y/N\): ')

	def dump_tmp_wallets(self):
		return self._dump_wallets(autosign=False)

	def dump_wallets(self):
		return self._dump_wallets(autosign=True)

	def _dump_wallets(self, autosign):
		data = self.users['alice']
		self.insert_device_online()
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ [f'--wallet-dir={data.udir}', f'--daemon=localhost:{data.md.rpc_port}']
			+ (self.autosign_opts if autosign else [])
			+ ['dump']
			+ ([] if autosign else [get_file_with_ext(data.udir, 'akeys')]))
		t.expect('2 wallets dumped')
		t.read()
		self.remove_device_online()
		return t

	def _delete_files(self, *ext_list):
		data = self.users['alice']
		self.spawn('', msg_only=True)
		for ext in ext_list:
			get_file_with_ext(data.udir, ext, no_dot=True, delete_all=True)
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

	def fund_alice1(self):
		return self.fund_alice(wallet=1)

	def check_bal_alice1(self):
		return self.check_bal_alice(wallet=1)

	def fund_alice2(self):
		return self.fund_alice(wallet=2)

	def check_bal_alice2(self):
		return self.check_bal_alice(wallet=2)

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

	def create_watchonly_wallets(self):
		return self.restore_wallets()

	def restore_wallets(self):
		self.insert_device_online()
		t = self.create_wallets('alice', op='restore')
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
			+ [f'--wallet-dir={data.udir}', f'--daemon=localhost:{data.md.rpc_port}']
			+ add_opts
			+ [op]
			+ ([get_file_with_ext(self.asi.xmr_tx_dir, ext)] if ext else [])
			+ ([wallet_arg] if wallet_arg else [])
		)
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

	def _mine_chk(self, desc):
		bal_type = {'locked':'b', 'unlocked':'ub'}[desc]
		return self.mine_chk(
			'alice', 1, 0,
			lambda x: 0 < getattr(x, bal_type) < 1.234567891234,
			f'{desc} balance 0 < 1.234567891234')

	def submit_transfer_tx1(self):
		return self._submit_transfer_tx()

	def resubmit_transfer_tx1(self):
		return self._submit_transfer_tx(
				relay_parm = self.tx_relay_daemon_proxy_parm,
				op         = 'resubmit',
				check_bal  = False)

	def submit_transfer_tx2(self):
		return self._submit_transfer_tx(relay_parm=self.tx_relay_daemon_parm)

	def _submit_transfer_tx(self, relay_parm=None, ext=None, op='submit', check_bal=True):
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
			return self._mine_chk('unlocked')
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
		self.spawn('', msg_only=True)
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
