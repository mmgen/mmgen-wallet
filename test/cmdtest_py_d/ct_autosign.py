#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
test.cmdtest_py_d.ct_autosign: Autosign tests for the cmdtest.py test suite
"""

import sys,os,shutil
from subprocess import run,DEVNULL
from pathlib import Path

from mmgen.cfg import Config
from mmgen.color import red,green,blue,purple
from mmgen.util import msg,suf,die
from mmgen.led import LEDControl
from mmgen.autosign import Autosign

from ..include.common import (
	cfg,
	omsg,
	omsg_r,
	start_test_daemons,
	stop_test_daemons,
	joinpath,
	imsg,
	read_from_file
)
from .common import ref_dir,dfl_words_file,dfl_bip39_file

from .ct_base import CmdTestBase
from .input import stealth_mnemonic_entry

filedir_map = (
	('btc',''),
	('bch',''),
	('ltc','litecoin'),
	('eth','ethereum'),
	('mm1','ethereum'),
	('etc','ethereum_classic'),
)

def init_led(simulate):
	try:
		cf = LEDControl(enabled=True,simulate=simulate)
	except Exception as e:
		msg(str(e))
		die(2,'LEDControl initialization failed')
	for fn in (cf.board.status,cf.board.trigger):
		if fn:
			run(['sudo','chmod','0666',fn],check=True)

class CmdTestAutosignBase(CmdTestBase):
	networks     = ('btc',)
	tmpdir_nums  = [18]
	color        = True
	no_insert_check = True
	win_skip = True
	have_online = False

	def __init__(self,trunner,cfgs,spawn):

		super().__init__(trunner,cfgs,spawn)

		if trunner is None:
			return

		self.silent_mount = self.live or not (cfg.exact_output or cfg.verbose)
		self.network_ids = [c+'_tn' for c in self.daemon_coins] + self.daemon_coins

		self._create_autosign_instances(create_dirs=not cfg.skipping_deps)

		if not (cfg.skipping_deps or self.live):
			self._create_removable_device()

		if self.simulate_led and not cfg.exact_output:
			die(1,red('This command must be run with --exact-output enabled!'))

		if self.simulate_led or not self.live:
			LEDControl.create_dummy_control_files()
			self.spawn_env['MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE'] = '1'

		self.opts = ['--coins='+','.join(self.coins)]

		if self.live:
			init_led(self.simulate_led)
		elif self.no_insert_check:
			self.opts.append('--no-insert-check')

		self.tx_file_ops('set_count') # initialize tx_count here so we can resume anywhere

		def gen_msg_fns():
			fmap = dict(filedir_map)
			for coin in self.coins:
				if coin == 'xmr':
					continue
				sdir = os.path.join('test','ref',fmap[coin])
				for fn in os.listdir(sdir):
					if fn.endswith(f'[{coin.upper()}].rawmsg.json'):
						yield os.path.join(sdir,fn)

		self.ref_msgfiles = tuple(gen_msg_fns())
		self.good_msg_count = 0
		self.bad_msg_count = 0

		if not self.live:
			self.spawn_env['MMGEN_TEST_SUITE_ROOT_PFX'] = self.tmpdir

	def _create_autosign_instances(self,create_dirs):
		d = {'offline': {'name':'asi'}}
		if self.have_online:
			d['online'] =  {'name':'asi_online'}
		for subdir,data in d.items():
			if create_dirs and not self.live:
				for k in ('mountpoint','wallet_dir','dev_label_dir'):
					if k == 'wallet_dir' and subdir == 'online':
						continue
					(Path(self.tmpdir) / (subdir + getattr(Autosign,'dfl_'+k))).mkdir(parents=True,exist_ok=True)
			setattr(self,data['name'],
				Autosign(
					Config({
						'coins': ','.join(self.coins),
						'test_suite': True,
						'test_suite_xmr_autosign': self.name == 'CmdTestXMRAutosign',
						'test_suite_root_pfx': None if self.live else self.tmpdir,
						'online': subdir == 'online',
					})))

	def _create_removable_device(self):
		redir = DEVNULL
		img_file = str(self.asi.fs_image_path)
		run(['truncate', '--size=10M', img_file], check=True)
		run(['/sbin/mkfs.ext2', '-E', f'root_owner={os.getuid()}:{os.getgid()}', img_file],
			stdout=redir, stderr=redir, check=True)
		self.do_mount(no_dir_chk=True)
		(self.asi.mountpoint / 'tx').mkdir()
		self.do_umount()

	def __del__(self):
		if sys.platform == 'win32' or self.tr is None:
			return
		if self.simulate_led or not self.live:
			LEDControl.delete_dummy_control_files()

	def start_daemons(self):
		self.spawn('',msg_only=True)
		start_test_daemons(*self.network_ids)
		return 'ok'

	def stop_daemons(self):
		self.spawn('',msg_only=True)
		stop_test_daemons(*self.network_ids)
		return 'ok'

	def gen_key(self):
		t = self.spawn( 'mmgen-autosign', self.opts + ['gen_key'] )
		t.expect_getend('Wrote key file ')
		return t

	def create_dfl_wallet(self):
		t = self.spawn( 'mmgen-walletconv', [
				f'--outdir={cfg.data_dir}',
				'--usr-randchars=0', '--quiet', '--hash-preset=1', '--label=foo',
				'test/ref/98831F3A.hex'
			]
		)
		t.passphrase_new('new MMGen wallet','abc')
		t.written_to_file('MMGen wallet')
		return t

	def run_setup_dfl_wallet(self):
		return self.run_setup(mn_type='default',use_dfl_wallet=True)

	def run_setup_bip39(self):
		return self.run_setup(mn_type='bip39')

	def run_setup(self,mn_type=None,mn_file=None,use_dfl_wallet=False):
		mn_desc = mn_type or 'default'
		mn_type = mn_type or 'mmgen'

		t = self.spawn(
			'mmgen-autosign',
			self.opts +
			([] if mn_desc == 'default' else [f'--mnemonic-fmt={mn_type}']) +
			['setup'] )

		if use_dfl_wallet:
			t.expect( 'Use default wallet for autosigning? (Y/n): ', 'y' )
			t.passphrase( 'MMGen wallet', 'abc' )
		else:
			if use_dfl_wallet is not None: # None => no dfl wallet present
				t.expect( 'Use default wallet for autosigning? (Y/n): ', 'n' )
			mn_file = mn_file or { 'mmgen': dfl_words_file, 'bip39': dfl_bip39_file }[mn_type]
			mn = read_from_file(mn_file).strip().split()
			from mmgen.mn_entry import mn_entry
			entry_mode = 'full'
			mne = mn_entry( cfg, mn_type, entry_mode )

			t.expect('words: ',{ 12:'1', 18:'2', 24:'3' }[len(mn)])
			t.expect('OK? (Y/n): ','\n')
			t.expect('Type a number.*: ',str(mne.entry_modes.index(entry_mode)+1),regex=True)
			stealth_mnemonic_entry(t,mne,mn,entry_mode)

		t.written_to_file('Autosign wallet')
		return t

	def copy_tx_files(self):
		self.spawn('',msg_only=True)
		return self.tx_file_ops('copy')

	def remove_signed_txfiles(self):
		self.tx_file_ops('remove_signed')
		return 'skip'

	def remove_signed_txfiles_btc(self):
		self.tx_file_ops('remove_signed',txfile_coins=['btc'])
		return 'skip'

	def tx_file_ops(self,op,txfile_coins=[]):

		assert op in ('copy','set_count','remove_signed')

		from .ct_ref import CmdTestRef
		def gen():
			d = CmdTestRef.sources['ref_tx_file']
			dirmap = [e for e in filedir_map if e[0] in (txfile_coins or self.txfile_coins)]
			for coin,coindir in dirmap:
				for network in (0,1):
					fn = d[coin][network]
					if fn:
						yield (coindir,fn)

		data = list(gen()) + [('','25EFA3[2.34].testnet.rawtx')] # TX with 2 non-MMGen outputs

		self.tx_count = len(data)
		if op == 'set_count':
			return

		self.do_mount()

		for coindir,fn in data:
			src = joinpath(ref_dir,coindir,fn)
			if cfg.debug_utf8:
				ext = '.testnet.rawtx' if fn.endswith('.testnet.rawtx') else '.rawtx'
				fn = fn[:-len(ext)] + '-α' + ext
			target = joinpath(self.asi.mountpoint,'tx',fn)
			if not op == 'remove_signed':
				shutil.copyfile(src,target)
			try:
				os.unlink(target.replace('.rawtx','.sigtx'))
			except:
				pass

		self.do_umount()

		return 'ok'

	def create_bad_txfiles(self):
		return self.bad_txfiles('create')

	def remove_bad_txfiles(self):
		return self.bad_txfiles('remove')

	create_bad_txfiles2 = create_bad_txfiles
	remove_bad_txfiles2 = remove_bad_txfiles

	def bad_txfiles(self,op):
		self.do_mount()
		# create or delete 2 bad tx files
		self.spawn('',msg_only=True)
		fns = [joinpath(self.asi.mountpoint,'tx',f'bad{n}.rawtx') for n in (1,2)]
		if op == 'create':
			for fn in fns:
				with open(fn,'w') as fp:
					fp.write('bad tx data\n')
			self.bad_tx_count = 2
		elif op == 'remove':
			for fn in fns:
				try:
					os.unlink(fn)
				except:
					pass
			self.bad_tx_count = 0
		self.do_umount()
		return 'ok'

	def copy_msgfiles(self):
		return self.msgfile_ops('copy')

	def remove_signed_msgfiles(self):
		return self.msgfile_ops('remove_signed')

	def create_invalid_msgfile(self):
		return self.msgfile_ops('create_invalid')

	def remove_invalid_msgfile(self):
		return self.msgfile_ops('remove_invalid')

	def msgfile_ops(self,op):
		self.spawn('',msg_only=True)
		destdir = joinpath(self.asi.mountpoint,'msg')
		self.do_mount()
		os.makedirs(destdir,exist_ok=True)
		if op.endswith('_invalid'):
			fn = os.path.join(destdir,'DEADBE[BTC].rawmsg.json')
			if op == 'create_invalid':
				with open(fn,'w') as fp:
					fp.write('bad data\n')
				self.bad_msg_count += 1
			elif op == 'remove_invalid':
				os.unlink(fn)
				self.bad_msg_count -= 1
		else:
			for fn in self.ref_msgfiles:
				if op == 'copy':
					if os.path.basename(fn) == 'ED405C[BTC].rawmsg.json': # contains bad Seed ID
						self.bad_msg_count += 1
					else:
						self.good_msg_count += 1
					imsg(f'Copying: {fn} -> {destdir}')
					shutil.copy2(fn,destdir)
				elif op == 'remove_signed':
					os.unlink(os.path.join( destdir, os.path.basename(fn).replace('rawmsg','sigmsg') ))
		self.do_umount()
		return 'ok'

	def do_sign(self,args,have_msg=False,tx_name='transaction'):
		t = self.spawn('mmgen-autosign', self.opts + args )
		t.expect(
			f'{self.tx_count} {tx_name}{suf(self.tx_count)} signed' if self.tx_count else
			'No unsigned transactions' )

		if self.bad_tx_count:
			t.expect(f'{self.bad_tx_count} {tx_name}{suf(self.bad_tx_count)} failed to sign')
			t.req_exit_val = 1

		if have_msg:
			t.expect(
				f'{self.good_msg_count} message file{suf(self.good_msg_count)}{{0,1}} signed'
					if self.good_msg_count else
				'No unsigned message files', regex=True )

			if self.bad_msg_count:
				t.expect(
					f'{self.bad_msg_count} message file{suf(self.bad_msg_count)}{{0,1}} failed to sign',
					regex = True )
				t.req_exit_val = 1

		if 'wait' in args:
			t.expect('Waiting')
			imsg(purple('\nKilling wait loop!'))
			t.kill(2)
			t.req_exit_val = 1
		else:
			t.read()

		imsg('')
		return t

	@property
	def device_inserted(self):
		return self.asi.dev_label_path.exists()

	@property
	def device_inserted_ts(self):
		return self.asi_online.dev_label_path.exists()

	def insert_device(self):
		self.asi.dev_label_path.touch()

	def insert_device_ts(self):
		self.asi_online.dev_label_path.touch()

	def remove_device(self):
		if self.asi.dev_label_path.exists():
			self.asi.dev_label_path.unlink()

	def remove_device_ts(self):
		if self.asi_online.dev_label_path.exists():
			self.asi_online.dev_label_path.unlink()

	def _mount_ops(self, loc, cmd, *args, **kwargs):
		return getattr(getattr(self,loc),cmd)(*args, silent=self.silent_mount, **kwargs)

	def do_mount(self, *args, **kwargs):
		return self._mount_ops('asi', 'do_mount', *args, **kwargs)

	def do_umount(self, *args, **kwargs):
		return self._mount_ops('asi', 'do_umount', *args, **kwargs)

	def do_mount_online(self, *args, **kwargs):
		return self._mount_ops('asi_online', 'do_mount', *args, **kwargs)

	def do_umount_online(self, *args, **kwargs):
		return self._mount_ops('asi_online', 'do_umount', *args, **kwargs)

class CmdTestAutosign(CmdTestAutosignBase):
	'autosigning transactions for all supported coins'
	coins        = ['btc','bch','ltc','eth']
	daemon_coins = ['btc','bch','ltc']
	txfile_coins = ['btc','bch','ltc','eth','mm1','etc']
	live         = False
	simulate_led = False
	bad_tx_count = 0
	cmd_group = (
		('start_daemons',            'starting daemons'),
		('copy_tx_files',            'copying transaction files'),
		('gen_key',                  'generating key'),
		('create_dfl_wallet',        'creating default MMGen wallet'),
		('run_setup_dfl_wallet',     'running ‘autosign setup’ (with default wallet)'),
		('sign_quiet',               'signing transactions (--quiet)'),
		('remove_signed_txfiles',    'removing signed transaction files'),
		('run_setup_bip39',          'running ‘autosign setup’ (BIP39 mnemonic)'),
		('create_bad_txfiles',       'creating bad transaction files'),
		('sign_full_summary',        'signing transactions (--full-summary)'),
		('remove_signed_txfiles_btc','removing transaction files (BTC only)'),
		('remove_bad_txfiles',       'removing bad transaction files'),
		('sign_led',                 'signing transactions (--led - BTC files only)'),
		('remove_signed_txfiles',    'removing signed transaction files'),
		('sign_stealth_led',         'signing transactions (--stealth-led)'),
		('remove_signed_txfiles',    'removing signed transaction files'),
		('copy_msgfiles',            'copying message files'),
		('sign_quiet_msg',           'signing transactions and messages (--quiet)'),
		('remove_signed_txfiles',    'removing signed transaction files'),
		('create_bad_txfiles2',      'creating bad transaction files'),
		('remove_signed_msgfiles',   'removing signed message files'),
		('create_invalid_msgfile',   'creating invalid message file'),
		('sign_full_summary_msg',    'signing transactions and messages (--full-summary)'),
		('remove_invalid_msgfile',   'removing invalid message file'),
		('remove_bad_txfiles2',      'removing bad transaction files'),
		('sign_no_unsigned_msg',     'signing transactions and messages (nothing to sign)'),
		('stop_daemons',             'stopping daemons'),
	)

	def sign_quiet(self):
		return self.do_sign(['--quiet','wait'])

	def sign_full_summary(self):
		return self.do_sign(['--full-summary','wait'])

	def sign_led(self):
		return self.do_sign(['--quiet','--led'])

	def sign_stealth_led(self):
		return self.do_sign(['--quiet','--stealth-led','wait'])

	def sign_quiet_msg(self):
		return self.do_sign(['--quiet','wait'],have_msg=True)

	def sign_full_summary_msg(self):
		return self.do_sign(['--full-summary','wait'],have_msg=True)

	def sign_no_unsigned_msg(self):
		self.tx_count = 0
		self.good_msg_count = 0
		self.bad_msg_count = 0
		return self.do_sign(['--quiet','wait'],have_msg=True)

class CmdTestAutosignBTC(CmdTestAutosign):
	'autosigning BTC transactions'
	coins        = ['btc']
	daemon_coins = ['btc']
	txfile_coins = ['btc']

class CmdTestAutosignLive(CmdTestAutosignBTC):
	'live autosigning BTC transactions'
	live = True
	cmd_group = (
		('start_daemons',        'starting daemons'),
		('copy_tx_files',        'copying transaction files'),
		('gen_key',              'generating key'),
		('run_setup_mmgen',      'running ‘autosign setup’ (MMGen native mnemonic)'),
		('sign_live',            'signing transactions'),
		('create_bad_txfiles',   'creating bad transaction files'),
		('sign_live_led',        'signing transactions (--led)'),
		('remove_bad_txfiles',   'removing bad transaction files'),
		('sign_live_stealth_led','signing transactions (--stealth-led)'),
		('stop_daemons',         'stopping daemons'),
	)

	def run_setup_mmgen(self):
		return self.run_setup(mn_type='mmgen',use_dfl_wallet=None)

	def sign_live(self):
		return self.do_sign_live([])

	def sign_live_led(self):
		return self.do_sign_live(['--led'])

	def sign_live_stealth_led(self):
		return self.do_sign_live(['--stealth-led'])

	def do_sign_live(self,led_opts):

		def prompt_remove():
			omsg_r(blue('\nRemove removable device and then hit ENTER '))
			input()

		def prompt_insert_sign(t):
			omsg(blue(insert_msg))
			t.expect(f'{self.tx_count} transactions signed')
			if self.bad_tx_count:
				t.expect(f'{self.bad_tx_count} transactions failed to sign')
			t.expect('Waiting')

		if led_opts:
			opts_msg = "'" + ' '.join(led_opts) + "'"
			info_msg = f"Running 'mmgen-autosign wait' with {led_opts[0]}. " + {
						'--led':         "The LED should start blinking slowly now",
						'--stealth-led': "You should see no LED activity now"
					}[led_opts[0]]
			insert_msg = 'Insert removable device and watch for fast LED activity during signing'
		else:
			opts_msg = 'no LED'
			info_msg = "Running 'mmgen-autosign wait'"
			insert_msg = 'Insert removable device '

		omsg(purple(f'Running autosign test with {opts_msg}'))

		self.do_umount_online()
		prompt_remove()
		omsg(green(info_msg))
		t = self.spawn(
			'mmgen-autosign',
			self.opts + led_opts + ['--quiet','--no-summary','wait'])
		if not cfg.exact_output:
			omsg('')
		prompt_insert_sign(t)

		self.do_mount_online() # race condition due to device insertion detection
		self.remove_signed_txfiles()
		self.do_umount_online()

		imsg(purple('\nKilling wait loop!'))
		t.kill(2) # 2 = SIGINT
		t.req_exit_val = 1
		if self.simulate_led and led_opts:
			t.expect("Stopping LED")
		return t

class CmdTestAutosignLiveSimulate(CmdTestAutosignLive):
	'live autosigning BTC transactions with simulated LED support'
	simulate_led = True
