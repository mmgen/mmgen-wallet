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

import os,time,re,shutil
from pathlib import Path

from mmgen.color import yellow,purple,gray
from mmgen.util import fmt,async_run

from ..include.common import (
	cfg,
	oqmsg,
	oqmsg_r,
	imsg,
	silence,
	end_silence
)
from .common import get_file_with_ext

from .ts_xmrwallet import TestSuiteXMRWallet
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
	no_insert_check = False
	win_skip = True

	cmd_group = (
		('daemon_version',           'checking daemon version'),
		('create_tmp_wallets',       'creating temporary online wallets for Alice'),
		('new_account_alice',        'adding an account to Alice’s tmp wallet'),
		('new_address_alice',        'adding an address to Alice’s tmp wallet'),
		('new_address_alice_label',  'adding an address to Alice’s tmp wallet (with label)'),
		('dump_tmp_wallets',         'dumping Alice’s tmp wallets'),
		('delete_tmp_wallets',       'deleting Alice’s tmp wallets'),
		('autosign_clean',           'cleaning signable file directories'),
		('autosign_setup',           'autosign setup with Alice’s seed'),
		('create_watchonly_wallets', 'creating online (watch-only) wallets for Alice'),
		('delete_tmp_dump_files',    'deleting Alice’s dump files'),
		('gen_kafiles',              'generating key-address files for Miner'),
		('create_wallets_miner',     'creating Monero wallets for Miner'),
		('mine_initial_coins',       'mining initial coins'),
		('fund_alice1',              'sending funds to Alice (wallet #1)'),
		('fund_alice2',              'sending funds to Alice (wallet #2)'),
		('autosign_start_thread',    'starting autosign wait loop'),
		('create_transfer_tx1',      'creating a transfer TX'),
		('submit_transfer_tx1',      'submitting the transfer TX'),
		('resubmit_transfer_tx1',    'resubmitting the transfer TX'),
		('export_outputs1',          'exporting outputs from Alice’s watch-only wallet #1'),
		('import_key_images1',       'importing signed key images into Alice’s online wallets'),
		('sync_chkbal1',             'syncing Alice’s wallet #1'),
		('create_transfer_tx2',      'creating a transfer TX (for relaying via proxy)'),
		('submit_transfer_tx2',      'submitting the transfer TX (relaying via proxy)'),
		('sync_chkbal2',             'syncing Alice’s wallets and checking balance'),
		('dump_wallets',             'dumping Alice’s wallets'),
		('delete_wallets',           'deleting Alice’s wallets'),
		('restore_wallets',          'creating online (watch-only) wallets for Alice'),
		('delete_dump_files',        'deleting Alice’s dump files'),
		('export_outputs2',          'exporting outputs from Alice’s watch-only wallets'),
		('import_key_images2',       'importing signed key images into Alice’s online wallets'),
		('sync_chkbal3',             'syncing Alice’s wallets and checking balance'),
		('txlist',                   'listing Alice’s submitted transactions'),
		('check_tx_dirs',            'cleaning and checking signable file directories'),
		('autosign_kill_thread',     'stopping autosign wait loop'),
		('stop_daemons',             'stopping all wallet and coin daemons'),
	)

	def __init__(self,trunner,cfgs,spawn):

		TestSuiteXMRWallet.__init__(self,trunner,cfgs,spawn)
		TestSuiteAutosignBase.__init__(self,trunner,cfgs,spawn)

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

		self.opts.append('--xmrwallets={}'.format( self.users['alice'].kal_range )) # mmgen-autosign opts
		self.autosign_opts = [f'--autosign-mountpoint={self.mountpoint}']           # mmgen-xmrwallet opts
		self.tx_count = 1
		self.spawn_env['MMGEN_TEST_SUITE_XMR_AUTOSIGN'] = '1'

	def create_tmp_wallets(self):
		self.spawn('',msg_only=True)
		data = self.users['alice']
		from mmgen.wallet import Wallet
		from mmgen.xmrwallet import MoneroWalletOps,xmrwallet_uargs
		from mmgen.addrlist import KeyAddrList
		silence()
		kal = KeyAddrList(
			cfg       = self.cfg,
			proto     = self.proto,
			addr_idxs = '1-2',
			seed      = Wallet(cfg,data.mmwords).seed,
			skip_chksum_msg = True,
			key_address_validity_check = False )
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
			r'Account index:\s+1\s+Creating new address' )

	def new_address_alice_label(self):
		return self._new_addr_alice(
			'2:1,Alice’s new address',
			'stop',
			r'Account index:\s+1\s+Creating new address.*Alice’s new address' )

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

	def fund_alice1(self):
		return self.fund_alice(wallet=1,check_bal=False)

	def fund_alice2(self):
		return self.fund_alice(wallet=2)

	def insert_device(self):
		self.asi.dev_disk_path.touch()

	def autosign_setup(self):
		self.insert_device()
		Path(self.autosign_xmr_dir).mkdir(parents=True,exist_ok=True)
		Path(self.autosign_xmr_dir,'old.vkeys').touch()
		t = self.run_setup(
			mn_type        = 'mmgen',
			mn_file        = self.users['alice'].mmwords,
			use_dfl_wallet = None )
		t.expect('Continue with Monero setup? (Y/n): ','y')
		t.written_to_file('View keys')
		return t

	def autosign_start_thread(self):
		if self.asi.dev_disk_path.exists():
			self.asi.dev_disk_path.unlink()
		def run():
			t = self.spawn('mmgen-autosign', self.opts + ['wait'], direct_exec=True )
			self.write_to_tmpfile('autosign_thread_pid',str(t.ep.pid))
		import threading
		threading.Thread( target=run, name='Autosign wait loop' ).start()
		time.sleep(0.2)
		return 'silent'

	def autosign_kill_thread(self):
		self.spawn('',msg_only=True)
		pid = int(self.read_from_tmpfile('autosign_thread_pid'))
		self.delete_tmpfile('autosign_thread_pid')
		from signal import SIGTERM
		imsg(purple(f'Killing autosign wait loop [PID {pid}]'))
		try:
			os.kill(pid,SIGTERM)
		except:
			imsg(yellow(f'{pid}: no such process'))
		return 'ok'

	def create_watchonly_wallets(self):
		return self.create_wallets( 'alice', op='restore' )

	def restore_wallets(self):
		return self.create_wallets( 'alice', op='restore' )

	def _create_transfer_tx(self,amt):
		t = self.do_op('transfer','alice',f'1:0:{self.burn_addr},{amt}',no_relay=True,do_ret=True)
		t.read() # required!
		self.insert_device()
		return t

	def create_transfer_tx1(self):
		return self._create_transfer_tx('0.124')

	def create_transfer_tx2(self):
		get_file_with_ext(self.asi.xmr_tx_dir,'rawtx',delete_all=True)
		get_file_with_ext(self.asi.xmr_tx_dir,'sigtx',delete_all=True)
		return self._create_transfer_tx('0.257')

	def _xmr_autosign_op(
			self,
			op,
			desc        = None,
			dtype       = None,
			ext         = None,
			wallet_arg  = None,
			add_opts    = [],
			wait_signed = False):
		if wait_signed:
			oqmsg_r(gray(f'→ offline wallet{"s" if dtype.endswith("s") else ""} signing {dtype}'))
			while True:
				oqmsg_r(gray('.'))
				if not self.asi.dev_disk_path.exists():
					break
				time.sleep(0.5)
			oqmsg(gray('done'))
		data = self.users['alice']
		args = (
			self.extra_opts
			+ self.autosign_opts
			+ [f'--wallet-dir={data.udir}', f'--daemon=localhost:{data.md.rpc_port}']
			+ add_opts
			+ [ op ]
			+ ([get_file_with_ext(self.asi.xmr_tx_dir,ext)] if ext else [])
			+ ([wallet_arg] if wallet_arg else [])
		)
		desc_pfx = f'{desc}, ' if desc else ''
		return self.spawn( 'mmgen-xmrwallet', args, extra_desc=f'({desc_pfx}Alice)' )

	def _sync_chkbal(self,wallet_arg,bal_chk_func):
		return self.sync_wallets(
			'alice',
			op           = 'sync',
			wallets      = wallet_arg,
			bal_chk_func = bal_chk_func )

	def sync_chkbal1(self):
		return self._sync_chkbal( '1', lambda n,b,ub: b == ub and 1 < b < 1.12 )
		# 1.234567891234 - 0.124 = 1.110567891234 (minus fees)

	def sync_chkbal2(self):
		return self._sync_chkbal( '1', lambda n,b,ub: b == ub and 0.8 < b < 0.86 )
		# 1.234567891234 - 0.124 - 0.257 = 0.853567891234 (minus fees)

	def sync_chkbal3(self):
		return self._sync_chkbal(
			'1-2',
			lambda n,b,ub: b == ub and ((n == 1 and 0.8 < b < 0.86) or (n == 2 and b > 1.23)) )

	def _mine_chk(self,desc):
		bal_type = {'locked':'b','unlocked':'ub'}[desc]
		return self.mine_chk(
			'alice', 1, 0,
			lambda x: 0 < getattr(x,bal_type) < 1.234567891234,
			f'{desc} balance 0 < 1.234567891234' )

	def submit_transfer_tx1(self):
		return self._submit_transfer_tx( ext='sigtx' )

	def resubmit_transfer_tx1(self):
		return self._submit_transfer_tx(
				relay_parm = self.tx_relay_daemon_proxy_parm,
				op         = 'resubmit',
				check_bal  = False)

	def submit_transfer_tx2(self):
		return self._submit_transfer_tx( relay_parm=self.tx_relay_daemon_parm )

	def _submit_transfer_tx(self,relay_parm=None,ext=None,op='submit',check_bal=True):
		t = self._xmr_autosign_op(
			op       = op,
			add_opts = [f'--tx-relay-daemon={relay_parm}'] if relay_parm else [],
			ext      = ext,
			dtype    = 'transaction',
			wait_signed = op == 'submit' )
		t.expect( f'{op.capitalize()} transaction? (y/N): ', 'y' )
		t.written_to_file('Submitted transaction')
		if check_bal:
			t.ok()
			return self._mine_chk('unlocked')
		else:
			return t

	def _export_outputs(self,wallet_arg,add_opts=[]):
		t = self._xmr_autosign_op(
			op    = 'export-outputs',
			wallet_arg = wallet_arg,
			add_opts = add_opts )
		t.written_to_file('Wallet outputs')
		t.read() # required!
		self.insert_device()
		return t

	def export_outputs1(self):
		return self._export_outputs('1',['--rescan-blockchain'])

	def export_outputs2(self):
		return self._export_outputs('1-2')

	def _import_key_images(self,wallet_arg):
		return self._xmr_autosign_op(
			op    = 'import-key-images',
			wallet_arg = wallet_arg,
			dtype = 'wallet outputs',
			wait_signed = True )

	def import_key_images1(self):
		return self._import_key_images(None)

	def import_key_images2(self):
		return self._import_key_images(None)

	def create_fake_tx_files(self):
		imsg('Creating fake transaction files')

		self.asi.msg_dir.mkdir(exist_ok=True)
		self.asi.xmr_dir.mkdir(exist_ok=True)
		self.asi.xmr_tx_dir.mkdir(exist_ok=True)
		self.asi.xmr_outputs_dir.mkdir(exist_ok=True)

		for fn in (
			'a.rawtx', 'a.sigtx',
			'b.rawtx', 'b.sigtx',
			'c.rawtx',
			'd.sigtx',
		):
			(self.asi.tx_dir / fn).touch()

		for fn in (
			'a.rawmsg.json', 'a.sigmsg.json',
			'b.rawmsg.json',
			'c.sigmsg.json',
			'd.rawmsg.json', 'd.sigmsg.json',
		):
			(self.asi.msg_dir / fn).touch()

		for fn in (
			'a.rawtx', 'a.sigtx', 'a.subtx',
			'b.rawtx', 'b.sigtx',
			'c.subtx',
			'd.rawtx', 'd.subtx',
			'e.rawtx',
			'f.sigtx','f.subtx',
		):
			(self.asi.xmr_tx_dir / fn).touch()

		for fn in (
			'a.raw', 'a.sig',
			'b.raw',
			'c.sig',
		):
			(self.asi.xmr_outputs_dir / fn).touch()

		return 'ok'

	def _gen_listing(self):
		for k in ('tx_dir','msg_dir','xmr_tx_dir','xmr_outputs_dir'):
			d = getattr(self.asi,k)
			if d.is_dir():
				yield '{:12} {}'.format(
					str(Path(*d.parts[4:])) + ':',
					' '.join(sorted(i.name for i in d.iterdir()))).strip()

	def autosign_clean(self):

		self.create_fake_tx_files()
		before = '\n'.join(self._gen_listing())

		t = self.spawn( 'mmgen-autosign', [f'--mountpoint={self.mountpoint}','clean'] )
		out = t.read()

		after = '\n'.join(self._gen_listing())
		chk = """
			tx:          a.sigtx b.sigtx c.rawtx d.sigtx
			msg:         a.sigmsg.json b.rawmsg.json c.sigmsg.json d.sigmsg.json
			xmr/tx:      a.subtx b.sigtx c.subtx d.subtx e.rawtx f.subtx
			xmr/outputs:
		"""

		shutil.rmtree(self.asi.mountpoint)
		self.asi.tx_dir.mkdir(parents=True)

		imsg(f'\nBefore cleaning:\n{before}')
		imsg(f'\nAfter cleaning:\n{after}')

		assert '13 files shredded' in out
		assert after + '\n' == fmt(chk), f'\n{after}\n!=\n{fmt(chk)}'

		return t

	def txlist(self):
		t = self.spawn( 'mmgen-xmrwallet', self.autosign_opts + ['txlist'] )
		t.match_expect_list([
			'SUBMITTED',
			'Network','Submitted',
			'Transfer 1:0','-> ext',
			'Transfer 1:0','-> ext'
		])
		return t

	def check_tx_dirs(self):
		before = '\n'.join(self._gen_listing())
		t = self.spawn( 'mmgen-autosign', [f'--mountpoint={self.mountpoint}','clean'] )
		t.read()
		after = '\n'.join(self._gen_listing())
		imsg(f'\nBefore cleaning:\n{before}')
		imsg(f'\nAfter cleaning:\n{after}')
		pat = r'xmr/tx: \s*\S+\.subtx \S+\.subtx\s+xmr/outputs:\s*$'
		assert re.search( pat, after, re.DOTALL ), f'regex search for {pat} failed'
		return t
