#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
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
test.cmdtest_d.ct_autosign: Autosign tests for the cmdtest.py test suite
"""

import sys, os, time, shutil, atexit
from subprocess import run, DEVNULL
from pathlib import Path

from mmgen.cfg import Config
from mmgen.color import red, blue, yellow, cyan, orange, purple, gray
from mmgen.util import msg, suf, die, indent, fmt
from mmgen.led import LEDControl
from mmgen.autosign import Autosign, Signable

from ..include.common import (
	cfg,
	omsg,
	omsg_r,
	oqmsg,
	oqmsg_r,
	start_test_daemons,
	stop_test_daemons,
	joinpath,
	imsg,
	read_from_file,
	silence,
	end_silence,
	VirtBlockDevice,
)
from .common import ref_dir, dfl_words_file, dfl_bip39_file

from .ct_base import CmdTestBase
from .input import stealth_mnemonic_entry

class CmdTestAutosignBase(CmdTestBase):
	networks     = ('btc',)
	tmpdir_nums  = [18]
	color        = True
	platform_skip = ('win32',)
	threaded     = False
	daemon_coins = []

	def __init__(self, trunner, cfgs, spawn):

		CmdTestBase.__init__(self, trunner, cfgs, spawn)

		if trunner is None:
			return

		self.silent_mount = self.live or not (cfg.exact_output or cfg.verbose)
		self.network_ids = [c+'_tn' for c in self.daemon_coins] + self.daemon_coins

		self._create_autosign_instances(create_dirs=not cfg.skipping_deps)
		self.fs_image_path = Path(self.tmpdir).absolute() / 'removable_device_image'

		if sys.platform == 'linux':
			self.txdev = VirtBlockDevice(self.fs_image_path, '10M')

		if not (cfg.skipping_deps or self.live):
			self._create_removable_device()

		if sys.platform == 'darwin' and not cfg.no_daemon_stop:
			atexit.register(self._macOS_eject_disk, self.asi.dev_label)

		self.opts = ['--coins='+','.join(self.coins)]

		if not self.live:
			self.spawn_env['MMGEN_TEST_SUITE_ROOT_PFX'] = self.tmpdir

		if self.threaded:
			self.spawn_env['MMGEN_TEST_SUITE_AUTOSIGN_THREADED'] = '1'

	def __del__(self):
		if hasattr(self, 'have_dummy_control_files'):
			db = LEDControl.boards['dummy']
			for fn in (db.status, db.trigger):
				run(f'sudo rm -f {fn}'.split(), check=True)

		if hasattr(self, 'txdev'):
			del self.txdev

		if not cfg.no_daemon_stop:
			if sys.platform == 'darwin':
				for label in (self.asi.dev_label, self.asi.ramdisk.label):
					self._macOS_eject_disk(label)

	def _create_autosign_instances(self, create_dirs):
		d = {'offline': {'name':'asi'}}

		if self.have_online:
			d['online'] =  {'name':'asi_online'}

		for subdir, data in d.items():
			asi = Autosign(
				Config({
					'coins': ','.join(self.coins),
					'test_suite': True,
					'test_suite_xmr_autosign': self.name == 'CmdTestXMRAutosign',
					'test_suite_autosign_threaded': self.threaded,
					'test_suite_root_pfx': None if self.live else self.tmpdir,
					'online': subdir == 'online',
				}))

			if create_dirs and not self.live:
				for k in ('mountpoint', 'shm_dir', 'wallet_dir'):
					if subdir == 'online' and k in ('shm_dir', 'wallet_dir'):
						continue
					if sys.platform == 'darwin' and k != 'mountpoint':
						continue
					getattr(asi, k).mkdir(parents=True, exist_ok=True)
					if sys.platform == 'darwin' and k == 'mountpoint':
						asi.mountpoint.rmdir()
						continue

			setattr(self, data['name'], asi)

	def _set_e2label(self, label):
		imsg(f'Setting label to {label}')
		run(['/sbin/e2label', str(self.txdev.img_path), label], check=True)

	def _create_removable_device(self):
		if sys.platform == 'linux':
			self.txdev.create()
			self.txdev.attach(silent=True)
			cmd = [
				'/sbin/mkfs.ext2',
				'-E', 'root_owner={}:{}'.format(os.getuid(), os.getgid()),
				'-L', self.asi.dev_label,
				str(self.txdev.img_path)]
			redir = DEVNULL
			run(cmd, stdout=redir, stderr=redir, check=True)
			self.txdev.detach(silent=True)
		elif sys.platform == 'darwin':
			cmd = [
				'hdiutil', 'create', '-size', '10M', '-fs', 'exFAT',
				'-volname', self.asi.dev_label,
				str(self.fs_image_path)]
			redir = None if cfg.exact_output or cfg.verbose else DEVNULL
			run(cmd, stdout=redir, check=True)

	def _macOS_mount_fs_image(self, loc):
		time.sleep(0.2)
		run(
			['hdiutil', 'attach', '-mountpoint', str(loc.mountpoint), f'{self.fs_image_path}.dmg'],
			stdout=DEVNULL, check=True)

	def _macOS_eject_disk(self, label):
		try:
			run(['diskutil' , 'eject', label], stdout=DEVNULL, stderr=DEVNULL)
		except:
			pass

	def start_daemons(self):
		self.spawn('', msg_only=True)
		start_test_daemons(*self.network_ids)
		return 'ok'

	def stop_daemons(self):
		self.spawn('', msg_only=True)
		stop_test_daemons(*self.network_ids)
		return 'ok'

	def run_setup(
			self,
			mn_type        = None,
			mn_file        = None,
			use_dfl_wallet = False,
			seed_len       = None,
			usr_entry_modes = False,
			passwd         = 'abc',
			expect_args    = []):

		mn_desc = mn_type or 'default'
		mn_type = mn_type or 'mmgen'

		if sys.platform == 'darwin' and not cfg.no_daemon_stop:
			self._macOS_eject_disk(self.asi.ramdisk.label)

		self.insert_device()

		t = self.spawn(
			'mmgen-autosign',
			self.opts
			+ ([] if mn_desc == 'default' else [f'--mnemonic-fmt={mn_type}'])
			+ ([f'--seed-len={seed_len}'] if seed_len else [])
			+ ['setup'],
			no_passthru_opts = True)

		if use_dfl_wallet:
			t.expect('Use default wallet for autosigning? (Y/n): ', 'y')
			t.passphrase('MMGen wallet', passwd)
		else:
			if use_dfl_wallet is not None: # None => no dfl wallet present
				t.expect('Use default wallet for autosigning? (Y/n): ', 'n')
			mn_file = mn_file or {'mmgen': dfl_words_file, 'bip39': dfl_bip39_file}[mn_type]
			mn = read_from_file(mn_file).strip().split()
			if not seed_len:
				t.expect('words: ', {12:'1', 18:'2', 24:'3'}[len(mn)])
				t.expect('OK? (Y/n): ', '\n')
			from mmgen.mn_entry import mn_entry
			entry_mode = 'full'
			mne = mn_entry(cfg, mn_type, entry_mode)
			if usr_entry_modes:
				t.expect('user-configured')
			else:
				t.expect(
					'Type a number.*: ',
					str(mne.entry_modes.index(entry_mode) + 1),
					regex = True)
			stealth_mnemonic_entry(t, mne, mn, entry_mode)

		t.written_to_file('Autosign wallet')

		if expect_args:
			t.expect(*expect_args)

		t.read()
		self.remove_device()

		if sys.platform == 'darwin' and not cfg.no_daemon_stop:
			atexit.register(self._macOS_eject_disk, self.asi.ramdisk.label)

		return t

	def insert_device(self, asi='asi'):
		if self.live:
			return
		loc = getattr(self, asi)
		if sys.platform == 'linux':
			self._set_e2label(loc.dev_label)
			self.txdev.attach()
			for _ in range(20):
				if loc.device_inserted:
					break
				time.sleep(0.1)
			else:
				die(2, f'device insert timeout exceeded {loc.dev_label}')
		elif sys.platform == 'darwin':
			self._macOS_mount_fs_image(loc)

	def remove_device(self, asi='asi'):
		if self.live:
			return
		loc = getattr(self, asi)
		if sys.platform == 'linux':
			self.txdev.detach()
			for _ in range(20):
				if not loc.device_inserted:
					break
				time.sleep(0.1)
			else:
				die(2, f'device remove timeout exceeded {loc.dev_label}')
		elif sys.platform == 'darwin':
			self._macOS_eject_disk(loc.dev_label)

	def _mount_ops(self, loc, cmd, *args, **kwargs):
		return getattr(getattr(self, loc), cmd)(*args, silent=self.silent_mount, **kwargs)

	def do_mount(self, *args, **kwargs):
		return self._mount_ops('asi', 'do_mount', *args, **kwargs)

	def do_umount(self, *args, **kwargs):
		return self._mount_ops('asi', 'do_umount', *args, **kwargs)

	def _gen_listing(self):
		for k in self.asi.dirs:
			d = getattr(self.asi, k)
			if d.is_dir():
				yield '{:12} {}'.format(
					str(Path(*d.parts[6:])) + ':',
					' '.join(sorted(i.name for i in d.iterdir()))).strip()

class CmdTestAutosignClean(CmdTestAutosignBase):
	have_online     = False
	live            = False
	simulate_led    = True
	no_insert_check = False
	coins           = ['btc']

	tmpdir_nums = [38]

	cmd_group = (
		('clean_no_xmr',   'cleaning signable file directories (no XMR)'),
		('clean_xmr_only', 'cleaning signable file directories (XMR-only)'),
		('clean_all',      'cleaning signable file directories (with XMR)'),
	)

	def create_fake_tx_files(self):
		imsg('Creating fake transaction files')

		if not self.asi.xmr_only:
			for fn in (
				'a.rawtx', 'a.sigtx',
				'b.rawtx', 'b.sigtx',
				'c.rawtx',
				'd.sigtx',
			):
				(self.asi.tx_dir / fn).touch()

			for fn in (
				'a.arawtx', 'a.asigtx', 'a.asubtx',
				'b.arawtx', 'b.asigtx',
				'c.asubtx',
				'd.arawtx', 'd.asubtx',
				'e.arawtx',
				'f.asigtx', 'f.asubtx',
			):
				(self.asi.txauto_dir / fn).touch()

			for fn in (
				'a.rawmsg.json', 'a.sigmsg.json',
				'b.rawmsg.json',
				'c.sigmsg.json',
				'd.rawmsg.json', 'd.sigmsg.json',
			):
				(self.asi.msg_dir / fn).touch()

		if self.asi.have_xmr:
			for fn in (
				'a.rawtx', 'a.sigtx', 'a.subtx',
				'b.rawtx', 'b.sigtx',
				'c.subtx',
				'd.rawtx', 'd.subtx',
				'e.rawtx',
				'f.sigtx', 'f.subtx',
			):
				(self.asi.xmr_tx_dir / fn).touch()

			for fn in (
				'a.raw', 'a.sig',
				'b.raw',
				'c.sig',
			):
				(self.asi.xmr_outputs_dir / fn).touch()

		return 'ok'

	def clean_no_xmr(self):
		return self._clean('btc,ltc,eth')

	def clean_xmr_only(self):
		self.asi = Autosign(Config({'_clone': self.asi.cfg, 'coins': 'xmr'}))
		return self._clean('xmr')

	def clean_all(self):
		self.asi = Autosign(Config({'_clone': self.asi.cfg, 'coins': 'xmr,btc,bch,eth'}))
		return self._clean('xmr,btc,bch,eth')

	def _clean(self, coins):

		self.spawn('', msg_only=True)

		self.insert_device()

		silence()
		self.do_mount()
		end_silence()

		self.create_fake_tx_files()
		before = '\n'.join(self._gen_listing())

		t = self.spawn('mmgen-autosign', [f'--coins={coins}', 'clean'], no_msg=True)
		out = t.read()

		if sys.platform == 'darwin':
			self.insert_device()

		silence()
		self.do_mount()
		end_silence()

		after = '\n'.join(self._gen_listing())

		chk_non_xmr = """
			tx:          a.sigtx b.sigtx c.rawtx d.sigtx
			txauto:      a.asubtx b.asigtx c.asubtx d.asubtx e.arawtx f.asubtx
			msg:         a.sigmsg.json b.rawmsg.json c.sigmsg.json d.sigmsg.json
		"""
		chk_xmr = """
			xmr:         outputs tx
			xmr/tx:      a.subtx b.sigtx c.subtx d.subtx e.rawtx f.subtx
			xmr/outputs:
		"""
		chk = ''
		shred_count = 0

		if not self.asi.xmr_only:
			for k in ('tx_dir', 'txauto_dir', 'msg_dir'):
				shutil.rmtree(getattr(self.asi, k))
			chk += chk_non_xmr.rstrip()
			shred_count += 9

		if self.asi.have_xmr:
			shutil.rmtree(self.asi.xmr_dir)
			chk += chk_xmr.rstrip()
			shred_count += 9

		self.do_umount()
		self.remove_device()

		imsg(f'\nBefore cleaning:\n{before}')
		imsg(f'\nAfter cleaning:\n{after}')

		assert f'{shred_count} files shredded' in out
		assert after + '\n' == fmt(chk), f'\n{after}\n!=\n{fmt(chk)}'

		return t

class CmdTestAutosignThreaded(CmdTestAutosignBase):
	have_online     = True
	live            = False
	no_insert_check = False
	threaded        = True

	def _wait_loop_start(self):
		t = self.spawn(
			'mmgen-autosign',
			self.opts + ['--full-summary', 'wait'],
			direct_exec      = True,
			no_passthru_opts = True,
			spawn_env_override = self.spawn_env | {'EXEC_WRAPPER_DO_RUNTIME_MSG': ''})
		self.write_to_tmpfile('autosign_thread_pid', str(t.ep.pid))
		return t

	def wait_loop_start(self):
		import threading
		threading.Thread(target=self._wait_loop_start, name='Autosign wait loop').start()
		time.sleep(0.1) # try to ensure test output is displayed before next test starts
		return 'silent'

	def wait_loop_kill(self):
		self.spawn('', msg_only=True)
		pid = int(self.read_from_tmpfile('autosign_thread_pid'))
		self.delete_tmpfile('autosign_thread_pid')
		from signal import SIGTERM
		imsg(purple(f'Killing autosign wait loop [PID {pid}]'))
		try:
			os.kill(pid, SIGTERM)
		except:
			imsg(yellow(f'{pid}: no such process'))
		return 'ok'

	def _wait_signed(self, desc):
		oqmsg_r(gray(f'→ offline wallet{"s" if desc.endswith("s") else ""} waiting for {desc}'))
		assert not self.asi.device_inserted, f'‘{self.asi.dev_label}’ is inserted!'
		assert not self.asi.mountpoint.is_mount(), f'‘{self.asi.mountpoint}’ is mounted!'
		self.insert_device()
		while True:
			oqmsg_r(gray('.'))
			if self.asi.mountpoint.is_mount():
				oqmsg_r(gray(' signing '))
				break
			time.sleep(0.1)
		while True:
			oqmsg_r(gray('>'))
			if not self.asi.mountpoint.is_mount():
				oqmsg(gray(' done'))
				break
			time.sleep(0.1)
		imsg('')
		self.remove_device()
		return 'ok'

	def insert_device_online(self):
		return self.insert_device(asi='asi_online')

	def remove_device_online(self):
		return self.remove_device(asi='asi_online')

	def do_mount_online(self, *args, **kwargs):
		return self._mount_ops('asi_online', 'do_mount', *args, **kwargs)

	def do_umount_online(self, *args, **kwargs):
		return self._mount_ops('asi_online', 'do_umount', *args, **kwargs)

	async def txview(self):
		self.spawn('', msg_only=True)
		self.insert_device()
		self.do_mount()
		src = Path(self.asi.txauto_dir)
		from mmgen.tx import CompletedTX
		txs = sorted(
			[await CompletedTX(cfg=cfg, filename=path, quiet_open=True) for path in sorted(src.iterdir())],
			key = lambda x: x.timestamp)
		for tx in txs:
			imsg(blue(f'\nViewing ‘{tx.infile.name}’:'))
			out = tx.info.format(terse=True)
			imsg(indent(out, indent='  '))
		self.do_umount()
		self.remove_device()
		return 'ok'

class CmdTestAutosign(CmdTestAutosignBase):
	'autosigning transactions for all supported coins'
	coins           = ['btc', 'bch', 'ltc', 'eth']
	daemon_coins    = ['btc', 'bch', 'ltc']
	txfile_coins    = ['btc', 'bch', 'ltc', 'eth', 'mm1', 'etc']
	have_online     = False
	live            = False
	simulate_led    = True
	no_insert_check = True

	filedir_map = (
		('btc', ''),
		('bch', ''),
		('ltc', 'litecoin'),
		('eth', 'ethereum'),
		('mm1', 'ethereum'),
		('etc', 'ethereum_classic'),
	)

	cmd_group = (
		('start_daemons',             'starting daemons'),
		('copy_tx_files',             'copying transaction files'),
		('gen_key',                   'generating key'),
		('create_dfl_wallet',         'creating default MMGen wallet'),
		('bad_opt1',                  'running ‘mmgen-autosign’ with --seed-len in invalid context'),
		('bad_opt2',                  'running ‘mmgen-autosign’ with --mnemonic-fmt in invalid context'),
		('bad_opt3',                  'running ‘mmgen-autosign’ with --led in invalid context'),
		('run_setup_dfl_wallet',      'running ‘autosign setup’ (with default wallet)'),
		('sign_quiet',                'signing transactions (--quiet)'),
		('remove_signed_txfiles',     'removing signed transaction files'),
		('run_setup_bip39',           'running ‘autosign setup’ (BIP39 mnemonic)'),
		('create_bad_txfiles',        'creating bad transaction files'),
		('sign_full_summary',         'signing transactions (--full-summary)'),
		('remove_signed_txfiles_btc', 'removing transaction files (BTC only)'),
		('remove_bad_txfiles',        'removing bad transaction files'),
		('sign_led',                  'signing transactions (--led - BTC files only)'),
		('remove_signed_txfiles',     'removing signed transaction files'),
		('sign_stealth_led',          'signing transactions (--stealth-led)'),
		('remove_signed_txfiles',     'removing signed transaction files'),
		('copy_msgfiles',             'copying message files'),
		('sign_quiet_msg',            'signing transactions and messages (--quiet)'),
		('remove_signed_txfiles',     'removing signed transaction files'),
		('create_bad_txfiles2',       'creating bad transaction files'),
		('remove_signed_msgfiles',    'removing signed message files'),
		('create_invalid_msgfile',    'creating invalid message file'),
		('sign_full_summary_msg',     'signing transactions and messages (--full-summary)'),
		('remove_invalid_msgfile',    'removing invalid message file'),
		('remove_bad_txfiles2',       'removing bad transaction files'),
		('sign_no_unsigned',          'signing transactions and messages (nothing to sign)'),
		('sign_no_unsigned_xmr',      'signing transactions and messages (nothing to sign, with XMR)'),
		('sign_no_unsigned_xmronly',  'signing transactions and messages (nothing to sign, XMR-only)'),
		('wipe_key',                  'wiping the wallet encryption key'),
		('stop_daemons',              'stopping daemons'),
		('sign_bad_no_daemon',        'signing transactions (error, no daemons running)'),
	)

	def __init__(self, trunner, cfgs, spawn):

		super().__init__(trunner, cfgs, spawn)

		if trunner is None:
			return

		if self.live and not cfg.exact_output:
			die(1, red('autosign_live tests must be run with --exact-output enabled!'))

		if self.no_insert_check:
			self.opts.append('--no-insert-check')

		self.tx_file_ops('set_count') # initialize self.tx_count here so we can resume anywhere
		self.bad_tx_count = 0

		def gen_msg_fns():
			fmap = dict(self.filedir_map)
			for coin in self.coins:
				if coin == 'xmr':
					continue
				sdir = os.path.join('test', 'ref', fmap[coin])
				for fn in os.listdir(sdir):
					if fn.endswith(f'[{coin.upper()}].rawmsg.json'):
						yield os.path.join(sdir, fn)

		self.ref_msgfiles = tuple(gen_msg_fns())
		self.good_msg_count = 0
		self.bad_msg_count = 0

		if self.simulate_led:
			LEDControl.create_dummy_control_files()
			db = LEDControl.boards['dummy']
			usrgrp = {'linux': 'root:root', 'darwin': 'root:wheel'}[sys.platform]
			for fn in (db.status, db.trigger): # trigger the auto-chmod feature
				run(f'sudo chmod 644 {fn}'.split(), check=True)
				run(f'sudo chown {usrgrp} {fn}'.split(), check=True)
			self.have_dummy_control_files = True
			self.spawn_env['MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE'] = '1'

	def gen_key(self):
		self.insert_device()
		t = self.spawn('mmgen-autosign', self.opts + ['gen_key'])
		t.expect_getend('Wrote key file ')
		t.read()
		self.remove_device()
		return t

	def create_dfl_wallet(self):
		t = self.spawn('mmgen-walletconv', [
				f'--outdir={cfg.data_dir}',
				'--usr-randchars=0', '--quiet', '--hash-preset=1', '--label=foo',
				'test/ref/98831F3A.hex'
			]
		)
		t.passphrase_new('new MMGen wallet', 'abc')
		t.written_to_file('MMGen wallet')
		return t

	def _bad_opt(self, cmdline, expect):
		t = self.spawn('mmgen-autosign', ['--coins=btc'] + cmdline, exit_val=1)
		t.expect(expect)
		return t

	def bad_opt1(self):
		return self._bad_opt(['--seed-len=128'], 'makes sense')

	def bad_opt2(self):
		return self._bad_opt(['--mnemonic-fmt=bip39', 'wait'], 'makes sense')

	def bad_opt3(self):
		return self._bad_opt(['--led', 'gen_key'], 'makes no sense')

	def run_setup_dfl_wallet(self):
		return self.run_setup(mn_type='default', use_dfl_wallet=True)

	def run_setup_bip39(self):
		from mmgen.cfgfile import mmgen_cfg_file
		fn = mmgen_cfg_file(cfg, 'usr').fn
		old_data = mmgen_cfg_file(cfg, 'usr').get_data(fn)
		new_data = [d.replace('bip39:fixed', 'bip39:full')[2:]
			if d.startswith('# mnemonic_entry_modes') else d for d in old_data]
		with open(fn, 'w') as fh:
			fh.write('\n'.join(new_data) + '\n')
		t = self.run_setup(
			mn_type  = 'bip39',
			seed_len = 256,
			usr_entry_modes = True)
		with open(fn, 'w') as fh:
			fh.write('\n'.join(old_data) + '\n')
		return t

	def copy_tx_files(self):
		self.spawn('', msg_only=True)
		return self.tx_file_ops('copy')

	def remove_signed_txfiles(self):
		self.tx_file_ops('remove_signed')
		return 'skip'

	def remove_signed_txfiles_btc(self):
		self.tx_file_ops('remove_signed', txfile_coins=['btc'])
		return 'skip'

	def tx_file_ops(self, op, txfile_coins=[]):

		assert op in ('copy', 'set_count', 'remove_signed')

		from .ct_ref import CmdTestRef
		def gen():
			d = CmdTestRef.sources['ref_tx_file']
			dirmap = [e for e in self.filedir_map if e[0] in (txfile_coins or self.txfile_coins)]
			for coin, coindir in dirmap:
				for network in (0, 1):
					fn = d[coin][network]
					if fn:
						yield (coindir, fn)

		data = list(gen()) + [('', '25EFA3[2.34].testnet.rawtx')] # TX with 2 non-MMGen outputs

		self.tx_count = len(data)
		if op == 'set_count':
			return

		self.insert_device()

		silence()
		self.do_mount(verbose=cfg.verbose or cfg.exact_output)
		end_silence()

		for coindir, fn in data:
			src = joinpath(ref_dir, coindir, fn)
			if cfg.debug_utf8:
				ext = '.testnet.rawtx' if fn.endswith('.testnet.rawtx') else '.rawtx'
				fn = fn[:-len(ext)] + '-α' + ext
			target = joinpath(self.asi.tx_dir, fn)
			if not op == 'remove_signed':
				shutil.copyfile(src, target)
			try:
				os.unlink(target.replace('.rawtx', '.sigtx'))
			except:
				pass

		self.do_umount()
		self.remove_device()

		return 'ok'

	def create_bad_txfiles(self):
		return self.bad_txfiles('create')

	def remove_bad_txfiles(self):
		return self.bad_txfiles('remove')

	create_bad_txfiles2 = create_bad_txfiles
	remove_bad_txfiles2 = remove_bad_txfiles

	def bad_txfiles(self, op):
		self.insert_device()
		self.do_mount()
		# create or delete 2 bad tx files
		self.spawn('', msg_only=True)
		fns = [joinpath(self.asi.tx_dir, f'bad{n}.rawtx') for n in (1, 2)]
		if op == 'create':
			for fn in fns:
				with open(fn, 'w') as fp:
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
		self.remove_device()
		return 'ok'

	def copy_msgfiles(self):
		return self.msgfile_ops('copy')

	def remove_signed_msgfiles(self):
		return self.msgfile_ops('remove_signed')

	def create_invalid_msgfile(self):
		return self.msgfile_ops('create_invalid')

	def remove_invalid_msgfile(self):
		return self.msgfile_ops('remove_invalid')

	def msgfile_ops(self, op):
		self.spawn('', msg_only=True)
		destdir = joinpath(self.asi.mountpoint, 'msg')
		self.insert_device()
		self.do_mount()
		os.makedirs(destdir, exist_ok=True)
		if op.endswith('_invalid'):
			fn = os.path.join(destdir, 'DEADBE[BTC].rawmsg.json')
			if op == 'create_invalid':
				with open(fn, 'w') as fp:
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
					shutil.copy2(fn, destdir)
				elif op == 'remove_signed':
					os.unlink(os.path.join(destdir, os.path.basename(fn).replace('rawmsg', 'sigmsg')))
		self.do_umount()
		self.remove_device()
		return 'ok'

	def do_sign(self, args=[], have_msg=False, exc_exit_val=None, expect_str=None):

		tx_desc = Signable.transaction.desc
		self.insert_device()

		def do_return():
			if expect_str:
				t.expect(expect_str)
			t.read()
			self.remove_device()
			imsg('')
			return t

		t = self.spawn(
				'mmgen-autosign',
				self.opts + args,
				exit_val = exc_exit_val or (1 if self.bad_tx_count or (have_msg and self.bad_msg_count) else None))

		if exc_exit_val:
			return do_return()

		t.expect(
			f'{self.tx_count} {tx_desc}{suf(self.tx_count)} signed' if self.tx_count else
			f'No unsigned {tx_desc}s')

		if self.bad_tx_count:
			t.expect(f'{self.bad_tx_count} {tx_desc}{suf(self.bad_tx_count)} failed to sign')

		if have_msg:
			t.expect(
				f'{self.good_msg_count} message file{suf(self.good_msg_count)}{{0,1}} signed'
					if self.good_msg_count else
				'No unsigned message files', regex=True)

			if self.bad_msg_count:
				t.expect(
					f'{self.bad_msg_count} message file{suf(self.bad_msg_count)}{{0,1}} failed to sign',
					regex = True)

		return do_return()

	def sign_quiet(self):
		return self.do_sign(['--quiet'])

	def sign_full_summary(self):
		return self.do_sign(['--full-summary'])

	def sign_led(self):
		return self.do_sign(['--quiet', '--led'])

	def sign_stealth_led(self):
		return self.do_sign(['--quiet', '--stealth-led'])

	def sign_quiet_msg(self):
		return self.do_sign(['--quiet'], have_msg=True)

	def sign_full_summary_msg(self):
		return self.do_sign(['--full-summary'], have_msg=True)

	def sign_bad_no_daemon(self):
		return self.do_sign(exc_exit_val=2, expect_str='listening on the correct port')

	def sign_no_unsigned(self):
		return self._sign_no_unsigned(
			coins   = 'BTC',
			present = ['non_xmr_signables'],
			absent  = ['xmr_signables'])

	def sign_no_unsigned_xmr(self):
		if self.coins == ['btc']:
			return 'skip'
		return self._sign_no_unsigned(
			coins = 'XMR,BTC',
			present = ['xmr_signables', 'non_xmr_signables'])

	def sign_no_unsigned_xmronly(self):
		if self.coins == ['btc']:
			return 'skip'
		return self._sign_no_unsigned(
			coins   = 'XMR',
			present = ['xmr_signables'],
			absent  = ['non_xmr_signables'])

	def _sign_no_unsigned(self, coins, present=[], absent=[]):
		self.insert_device()
		t = self.spawn('mmgen-autosign', ['--quiet', '--no-insert-check', f'--coins={coins}'])
		res = t.read()
		self.remove_device()
		for signable_list in present:
			for signable_clsname in getattr(Signable, signable_list):
				desc = getattr(Signable, signable_clsname).desc
				assert f'No unsigned {desc}s' in res, f'‘No unsigned {desc}s’ missing in output'
		for signable_list in absent:
			for signable_clsname in getattr(Signable, signable_list):
				desc = getattr(Signable, signable_clsname).desc
				assert not f'No unsigned {desc}s' in res, f'‘No unsigned {desc}s’ should be absent in output'
		return t

	def wipe_key(self):
		self.insert_device()
		t = self.spawn('mmgen-autosign', ['--quiet', '--no-insert-check', 'wipe_key'])
		t.expect('Shredding')
		t.read()
		self.remove_device()
		return t

class CmdTestAutosignBTC(CmdTestAutosign):
	'autosigning BTC transactions'
	coins        = ['btc']
	daemon_coins = ['btc']
	txfile_coins = ['btc']

class CmdTestAutosignLive(CmdTestAutosignBTC):
	'live autosigning BTC transactions'
	live            = True
	simulate_led    = False
	no_insert_check = False

	cmd_group = (
		('start_daemons',         'starting daemons'),
		('copy_tx_files',         'copying transaction files'),
		('gen_key',               'generating key'),
		('run_setup_mmgen',       'running ‘autosign setup’ (MMGen native mnemonic)'),
		('sign_live',             'signing transactions'),
		('create_bad_txfiles',    'creating bad transaction files'),
		('sign_live_led',         'signing transactions (--led)'),
		('remove_bad_txfiles',    'removing bad transaction files'),
		('sign_live_stealth_led', 'signing transactions (--stealth-led)'),
		('stop_daemons',          'stopping daemons'),
	)

	def __init__(self, trunner, cfgs, spawn):

		super().__init__(trunner, cfgs, spawn)

		if trunner is None:
			return

		try:
			LEDControl(enabled=True, simulate=self.simulate_led)
		except Exception as e:
			msg(str(e))
			die(2, 'LEDControl initialization failed')

	def run_setup_mmgen(self):
		return self.run_setup(mn_type='mmgen', use_dfl_wallet=None)

	def sign_live(self):
		return self.do_sign_live()

	def sign_live_led(self):
		return self.do_sign_live(['--led'], 'The LED should start blinking slowly now')

	def sign_live_stealth_led(self):
		return self.do_sign_live(['--stealth-led'], 'You should see no LED activity now')

	def do_sign_live(self, led_opts=None, led_msg=None):

		def prompt_remove():
			omsg_r(orange('\nExtract removable device and then hit ENTER '))
			input()

		def prompt_insert_sign(t):
			omsg(orange(insert_msg))
			t.expect(f'{self.tx_count} non-automount transactions signed')
			if self.bad_tx_count:
				t.expect(f'{self.bad_tx_count} non-automount transactions failed to sign')
			t.expect('Waiting')

		if led_opts:
			opts_msg = '‘' + ' '.join(led_opts) + '’'
			info_msg = 'Running ‘mmgen-autosign wait’ with {}. {}'.format(opts_msg, led_msg)
			insert_msg = 'Insert removable device and watch for fast LED activity during signing'
		else:
			opts_msg = 'no LED'
			info_msg = 'Running ‘mmgen-autosign wait’'
			insert_msg = 'Insert removable device '

		self.spawn('', msg_only=True)

		self.do_umount()
		prompt_remove()
		omsg('\n' + cyan(indent(info_msg)))

		t = self.spawn(
			'mmgen-autosign',
			self.opts + (led_opts or []) + ['--quiet', '--no-summary', 'wait'],
			no_msg   = True,
			exit_val = 1)

		if not cfg.exact_output:
			omsg('')

		prompt_insert_sign(t)

		self.do_mount() # race condition due to device insertion detection
		self.remove_signed_txfiles()
		self.do_umount()

		imsg(purple('\nKilling wait loop!'))
		t.kill(2) # 2 = SIGINT

		if self.simulate_led and led_opts:
			t.expect('Stopping LED')
		return t

class CmdTestAutosignLiveSimulate(CmdTestAutosignLive):
	'live autosigning BTC transactions with simulated LED support'
	simulate_led = True
