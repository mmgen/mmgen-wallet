#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen


"""
test.test_py_d.ts_xmr_autosign: xmr autosigning tests for the test.py test suite
"""

from .ts_xmrwallet import *
from .ts_autosign import TestSuiteAutosignBase

def make_burn_addr():
	from mmgen.tool.coin import tool_cmd
	return tool_cmd(
		cfg     = cfg,
		cmdname = 'privhex2addr',
		proto   = cfg._proto,
		mmtype  = 'monero' ).privhex2addr('beadcafe'*8)

class TestSuiteXMRAutosign(TestSuiteXMRWallet,TestSuiteAutosignBase):
	"""
	Monero autosigning operations
	"""

	tmpdir_nums = [39]

	# ts_xmrwallet attrs:
	user_data = (
		('miner', '98831F3A', False, 130, '1', []),
		('alice', 'FE3C6545', True,  150, '1-2', []),
	)

	# ts_autosign attrs:
	coins        = ['xmr']
	daemon_coins = []
	txfile_coins = []
	live         = False
	simulate     = False
	bad_tx_count = 0
	tx_relay_user = 'miner'

	cmd_group = (
		('daemon_version',           'checking daemon version'),
		('create_tmp_wallets',       'creating temporary online wallets for Alice'),
		('new_account_alice',        'adding an account to Alice’s tmp wallet'),
		('new_address_alice',        'adding an address to Alice’s tmp wallet'),
		('new_address_alice_label',  'adding an address to Alice’s tmp wallet (with label)'),
		('dump_tmp_wallets',         'dumping Alice’s tmp wallets'),
		('delete_tmp_wallets',       'deleting Alice’s tmp wallets'),
		('autosign_setup',           'autosign setup with Alice’s seed'),
		('create_watchonly_wallets', 'creating online (watch-only) wallets for Alice'),
		('delete_tmp_dump_files',    'deleting Alice’s dump files'),
		('gen_kafiles',              'generating key-address files for Miner'),
		('create_wallets_miner',     'creating Monero wallets for Miner'),
		('mine_initial_coins',       'mining initial coins'),
		('fund_alice',               'sending funds to Alice'),
		('create_transfer_tx1',      'creating a transfer TX'),
		('sign_transfer_tx1',        'signing the transfer TX'),
		('submit_transfer_tx1',      'submitting the transfer TX'),
		('create_transfer_tx2',      'creating a transfer TX (for relaying via proxy)'),
		('sign_transfer_tx2',        'signing the transfer TX (for relaying via proxy)'),
		('submit_transfer_tx2',      'submitting the transfer TX (relaying via proxy)'),
		('list_wallets',             'listing Alice’s wallets and checking balance'),
		('dump_wallets',             'dumping Alice’s wallets'),
		('delete_wallets',           'deleting Alice’s wallets'),
		('restore_wallets',          'creating online (watch-only) wallets for Alice'),
		('delete_dump_files',        'deleting Alice’s dump files'),
		('export_outputs',           'exporting outputs from Alice’s watch-only wallets'),
		('export_key_images',        'exporting signed key images from Alice’s offline wallets'),
		('import_key_images',        'importing signed key images into Alice’s online wallets'),
		('list_wallets',             'listing Alice’s wallets and checking balance'),
	)

	def __init__(self,trunner,cfgs,spawn):

		TestSuiteXMRWallet.__init__(self,trunner,cfgs,spawn)
		TestSuiteAutosignBase.__init__(self,trunner,cfgs,spawn)

		if trunner == None:
			return

		from mmgen.cfg import Config
		self.cfg = Config({
			'coin': 'XMR',
			'outdir': self.users['alice'].udir,
			'wallet_dir': self.users['alice'].udir,
			'wallet_rpc_password': 'passwOrd',
		})

		self.burn_addr = make_burn_addr()

		self.opts.append('--xmrwallets={}'.format( self.users['alice'].kal_range )) # mmgen-autosign opts
		self.autosign_opts = [f'--autosign-mountpoint={self.mountpoint}']           # mmgen-xmrwallet opts
		self.tx_count = 1

	def create_tmp_wallets(self):
		self.spawn('',msg_only=True)
		data = self.users['alice']
		from mmgen.wallet import Wallet
		from mmgen.xmrwallet import MoneroWalletOps,xmrwallet_uargs
		silence()
		kal = KeyAddrList(
			cfg       = self.cfg,
			proto     = self.proto,
			addr_idxs = '1-2',
			seed      = Wallet(cfg,data.mmwords).seed )
		kal.file.write(ask_overwrite=False)
		fn = get_file_with_ext(data.udir,'akeys')
		m = MoneroWalletOps.create(
			self.cfg,
			xmrwallet_uargs(fn, '1-2', None))
		async_run(m.main())
		async_run(m.stop_wallet_daemon())
		end_silence()
		return 'ok'

	def _new_addr_alice(self,*args):
		data = self.users['alice']
		return self.new_addr_alice(
			*args,
			kafile = get_file_with_ext(data.udir,'akeys') )

	def new_account_alice(self):
		return self._new_addr_alice(
			'2',
			'start',
			fr'Creating new account.*Index:\s+{self.na_idx}\s')

	def new_address_alice(self):
		return self._new_addr_alice(
			'2:1',
			'continue',
			fr'Account index:\s+1\s+Creating new address' )

	def new_address_alice_label(self):
		return self._new_addr_alice(
			'2:1,Alice’s new address',
			'stop',
			fr'Account index:\s+1\s+Creating new address.*Alice’s new address' )

	def dump_tmp_wallets(self):
		return self._dump_wallets(autosign=False)

	def dump_wallets(self):
		return self._dump_wallets(autosign=True)

	def _dump_wallets(self,autosign):
		data = self.users['alice']
		t = self.spawn(
			'mmgen-xmrwallet',
			self.extra_opts
			+ [f'--wallet-dir={data.udir}', f'--daemon=localhost:{data.md.rpc_port}']
			+ (self.autosign_opts if autosign else [])
			+ ['dump']
			+ ([] if autosign else [get_file_with_ext(data.udir,'akeys')]) )
		t.expect('2 wallets dumped')
		return t

	def _delete_files(self,*ext_list):
		data = self.users['alice']
		self.spawn('',msg_only=True)
		for ext in ext_list:
			get_file_with_ext(data.udir,ext,no_dot=True,delete_all=True)
		return 'ok'

	def delete_tmp_wallets(self):
		return self._delete_files( 'MoneroWallet', 'MoneroWallet.keys', '.akeys' )

	def delete_wallets(self):
		return self._delete_files( 'MoneroWatchOnlyWallet', '.keys', '.address.txt' )

	def delete_tmp_dump_files(self):
		return self._delete_files( '.dump' )

	def delete_dump_files(self):
		return self._delete_files( '.dump' )

	def autosign_setup(self):
		from pathlib import Path
		Path(self.autosign_xmr_dir).mkdir(parents=True,exist_ok=True)
		Path(self.autosign_xmr_dir,'old.vkeys').touch()
		t = self.run_setup(
			mn_type        = 'mmgen',
			mn_file        = self.users['alice'].mmwords,
			use_dfl_wallet = None )
		t.expect('Continue with Monero setup? (Y/n): ','y')
		t.written_to_file('View keys')
		return t

	def create_watchonly_wallets(self):
		return self.create_wallets( 'alice', op='restore' )

	def restore_wallets(self):
		return self.create_wallets( 'alice', op='restore' )

	def list_wallets(self):
		return self.sync_wallets(
			'alice',
			op           = 'list',
			bal_chk_func = lambda n,bal: (0.83 < bal < 0.8536) if n == 0 else True )
			# 1.234567891234 - 0.124 - 0.257 = 0.853567891234 (minus fees)

	def _create_transfer_tx(self,amt):
		return self.do_op('transfer','alice',f'1:0:{self.burn_addr},{amt}',no_relay=True,do_ret=True)

	def create_transfer_tx1(self):
		return self._create_transfer_tx('0.124')

	def create_transfer_tx2(self):
		get_file_with_ext(self.asi.xmr_tx_dir,'rawtx',delete_all=True)
		get_file_with_ext(self.asi.xmr_tx_dir,'sigtx',delete_all=True)
		return self._create_transfer_tx('0.257')

	def _sign_transfer_tx(self):
		return self.do_sign(['--full-summary'],tx_name='Monero transaction')

	def sign_transfer_tx1(self):
		return self._sign_transfer_tx()

	def sign_transfer_tx2(self):
		return self._sign_transfer_tx()

	def _xmr_autosign_op(self,op,desc,dtype=None,ext=None,wallet_arg=None,add_opts=[]):
		data = self.users['alice']
		args = (
			self.extra_opts
			+ self.autosign_opts
			+ [f'--wallet-dir={data.udir}']
			+ ([f'--daemon=localhost:{data.md.rpc_port}'] if not op == 'submit' else [])
			+ add_opts
			+ [ op ]
			+ ([get_file_with_ext(self.asi.xmr_tx_dir,ext)] if ext else [])
			+ ([wallet_arg] if wallet_arg else [])
		)
		t = self.spawn( 'mmgen-xmrwallet', args, extra_desc=f'({desc}, Alice)' )
		if dtype:
			t.written_to_file(dtype.capitalize())
		return t

	def submit_transfer_tx1(self):
		return self._submit_transfer_tx( self.tx_relay_daemon_parm, ext='sigtx' )

	def submit_transfer_tx2(self):
		return self._submit_transfer_tx( self.tx_relay_daemon_proxy_parm, ext=None )

	def _submit_transfer_tx(self,relay_parm,ext):
		t = self._xmr_autosign_op(
			op       = 'submit',
			desc     = 'submitting TX',
			add_opts = [f'--tx-relay-daemon={relay_parm}'],
			ext      = ext )
		t.expect( 'Submit transaction? (y/N): ', 'y' )
		t.written_to_file('Submitted transaction')
		t.ok()
		return self.mine_chk(
			'alice', 1, 0,
			lambda x: 0 < x < 1.234567891234,
			'unlocked balance 0 < 1.234567891234' )

	def export_outputs(self):
		return self._xmr_autosign_op(
			op    = 'export-outputs',
			desc  = 'exporting outputs',
			dtype = 'wallet outputs',
			wallet_arg = '1-2' )

	def export_key_images(self):
		self.tx_count = 2
		return self.do_sign(['--full-summary'],tx_name='Monero wallet outputs file')

	def import_key_images(self):
		return self._xmr_autosign_op(
			op    = 'import-key-images',
			desc  = 'importing key images' )
