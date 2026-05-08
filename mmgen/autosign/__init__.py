#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
autosign: Autosign MMGen transactions, message files and XMR wallet output files
"""

import sys, os, asyncio
from stat import S_IWUSR, S_IRUSR
from pathlib import Path
from subprocess import run, PIPE, DEVNULL

from ..cfg import Config
from ..util import msg, msg_r, ymsg, rmsg, gmsg, bmsg, die, suf, fmt, fmt_list, is_int, cached_property
from ..color import yellow, brown, gray
from ..wallet import Wallet, get_wallet_cls

class Autosign:

	dev_label = 'MMGEN_TX'
	linux_mount_subdir = 'mmgen_autosign'
	macOS_ramdisk_name = 'AutosignRamDisk'
	wallet_subdir = 'autosign'
	linux_blkid_cmd = 'sudo blkid -s LABEL -o value'
	keylist_fn = 'keylist.mmenc'

	cmds = ('setup', 'xmr_setup', 'sign', 'wait')

	util_cmds = (
		'gen_key',
		'macos_ramdisk_setup',
		'macos_ramdisk_delete',
		'enable_swap',
		'disable_swap',
		'clean',
		'wipe_key',
		'list_led',
		'test_led')

	mn_fmts = {
		'mmgen': 'words',
		'bip39': 'bip39'}

	dfl_mn_fmt = 'mmgen'

	non_xmr_dirs = {
		'tx_dir':     'tx',
		'txauto_dir': 'txauto',
		'msg_dir':    'msg'}

	xmr_dirs = {
		'xmr_dir':         'xmr',
		'xmr_tx_dir':      'xmr/tx',
		'xmr_outputs_dir': 'xmr/outputs'}

	non_xmr_signables = (
		'transaction',
		'automount_transaction',
		'message')

	xmr_signables = (              # order is important!
		'xmr_wallet_outputs_file', # import XMR wallet outputs BEFORE signing transactions
		'xmr_transaction')

	have_xmr = False
	xmr_only = False

	def init_fixup(self): # see test/overlay/fakemods/mmgen/autosign.py
		pass

	def __init__(self, cfg, *, cmd=None):

		if cfg.mnemonic_fmt:
			if cfg.mnemonic_fmt not in self.mn_fmts:
				die(1, '{!r}: invalid mnemonic format (must be one of: {})'.format(
					cfg.mnemonic_fmt,
					fmt_list(self.mn_fmts, fmt='no_spc')))

		match sys.platform:
			case 'linux':
				self.dfl_mountpoint = f'/mnt/{self.linux_mount_subdir}'
				self.dfl_shm_dir    = '/dev/shm'

				# linux-only attrs:
				self.old_dfl_mountpoint = '/mnt/tx'
				self.old_dfl_mountpoint_errmsg = f"""
					Mountpoint ‘{self.old_dfl_mountpoint}’ is no longer supported!
					Please rename ‘{self.old_dfl_mountpoint}’ to ‘{self.dfl_mountpoint}’
					and update your fstab accordingly.
				"""
				self.mountpoint_errmsg_fs = """
					Mountpoint ‘{}’ does not exist or does not point
					to a directory!  Please create the mountpoint and add an entry
					to your fstab as described in this script’s help text.
				"""
			case 'darwin':
				self.dfl_mountpoint = f'/Volumes/{self.dev_label}'
				self.dfl_shm_dir    = f'/Volumes/{self.macOS_ramdisk_name}'

		self.cfg = cfg

		self.dfl_wallet_dir = f'{self.dfl_shm_dir}/{self.wallet_subdir}'
		self.mountpoint = Path(cfg.mountpoint or self.dfl_mountpoint)
		self.shm_dir    = Path(self.dfl_shm_dir)
		self.wallet_dir = Path(cfg.wallet_dir or self.dfl_wallet_dir)

		match sys.platform:
			case 'linux':
				self.mount_cmd  = f'mount {self.mountpoint}'
				self.umount_cmd = f'umount {self.mountpoint}'
			case 'darwin':
				self.mount_cmd  = f'diskutil mount {self.dev_label}'
				self.umount_cmd = f'diskutil eject {self.dev_label}'

		self.init_fixup()

		if sys.platform == 'darwin': # test suite uses ‘fixed-up’ shm_dir
			from ..platform.darwin.util import MacOSRamDisk
			self.ramdisk = MacOSRamDisk(
				cfg,
				self.macOS_ramdisk_name,
				self._get_macOS_ramdisk_size(),
				path = self.shm_dir)

		self.keyfile = self.mountpoint / 'autosign.key'

		if any(k in cfg._uopts for k in ('help', 'longhelp')):
			return

		self.coins = cfg.coins.upper().split(',') if cfg.coins else []

		if cfg.xmrwallets and not 'XMR' in self.coins:
			self.coins.append('XMR')

		if not self.coins and cmd in self.cmds:
			ymsg('Warning: no coins specified, defaulting to BTC')
			self.coins = ['BTC']

		if 'XMR' in self.coins:
			self.have_xmr = True
			if len(self.coins) == 1:
				self.xmr_only = True
			self.xmr_cur_wallet_idx = None

		self.dirs = {}
		self.signables = ()

		if not self.xmr_only:
			self.dirs |= self.non_xmr_dirs
			self.signables += self.non_xmr_signables

		if self.have_xmr:
			self.dirs |= self.xmr_dirs | (
				{'txauto_dir': 'txauto'} if cfg.xmrwallet_compat and self.xmr_only else {})
			self.signables = (
				self.xmr_signables # xmr_wallet_outputs_file must be signed before XMR TXs
				+ (('automount_transaction',) if cfg.xmrwallet_compat and self.xmr_only else ())
				+ self.signables)      # self.signables could contain compat XMR TXs

		for name, path in self.dirs.items():
			setattr(self, name, self.mountpoint / path)

	@cached_property
	def swap(self):
		from .swap_mgr import SwapMgr
		return SwapMgr(self.cfg, ignore_zram=True)

	async def check_daemons_running(self):
		from ..protocol import init_proto
		for coin in self.coins:
			proto = init_proto(self.cfg,  coin, network=self.cfg.network, need_amt=True)
			if proto.sign_mode == 'daemon':
				self.cfg._util.vmsg(f'Checking {coin} daemon')
				from ..rpc import rpc_init
				from ..exception import SocketError
				try:
					await rpc_init(self.cfg, proto, ignore_wallet=True)
				except SocketError as e:
					from ..daemon import CoinDaemon
					d = CoinDaemon(self.cfg, proto=proto, test_suite=self.cfg.test_suite)
					die(2,
						f'\n{e}\nIs the {d.coind_name} daemon ({d.exec_fn}) running '
						+ 'and listening on the correct port?')

	@property
	def wallet_files(self):

		if not hasattr(self, '_wallet_files'):

			try:
				dirlist = self.wallet_dir.iterdir()
			except:
				die(1,
					f'Cannot open wallet directory ‘{self.wallet_dir}’. '
					'Did you run ‘mmgen-autosign setup’?')

			self._wallet_files = [f for f in dirlist if f.suffix == '.mmdat']

			if not self._wallet_files:
				die(1, 'No wallet files present!')

		return self._wallet_files

	def do_mount(self, *, silent=False, verbose=False):

		def check_or_create(dirname):
			path = getattr(self, dirname)
			if path.is_dir():
				if not path.stat().st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR:
					die(1, f'‘{path}’ is not read/write for this user!')
			elif path.exists():
				die(1, f'‘{path}’ is not a directory!')
			elif path.is_symlink():
				die(1, f'‘{path}’ is a symlink not pointing to a directory!')
			else:
				msg(f'Creating ‘{path}’')
				path.mkdir(parents=True)

		if sys.platform == 'linux' and not self.mountpoint.is_dir():
			def do_die(m):
				die(1, '\n' + yellow(fmt(m.strip(), indent='  ')))
			if Path(self.old_dfl_mountpoint).is_dir():
				do_die(self.old_dfl_mountpoint_errmsg)
			else:
				do_die(self.mountpoint_errmsg_fs.format(self.mountpoint))

		if not self.mountpoint.is_mount():
			redir = None if verbose else DEVNULL
			if run(self.mount_cmd.split(), stderr=redir, stdout=redir).returncode == 0:
				if not silent:
					msg(gray(f'Mounting ‘{self.mountpoint}’'))
			else:
				die(1, f'Unable to mount device ‘{self.dev_label}’ at ‘{self.mountpoint}’')

		for dirname in self.dirs:
			check_or_create(dirname)

	def do_umount(self, *, silent=False, verbose=False):
		if self.mountpoint.is_mount():
			run(['sync'], check=True)
			if not silent:
				msg(gray(f'Unmounting ‘{self.mountpoint}’'))
			redir = None if verbose else DEVNULL
			run(self.umount_cmd.split(), stdout=redir, check=True)
		if not silent:
			bmsg('It is now safe to extract the removable device')

	def decrypt_wallets(self):
		msg(f'Unlocking wallet{suf(self.wallet_files)} with key from ‘{self.keyfile}’')
		fails = 0
		for wf in self.wallet_files:
			try:
				Wallet(self.cfg, fn=wf, ignore_in_fmt=True, passwd_file=str(self.keyfile))
			except SystemExit as e:
				if e.code != 0:
					fails += 1

		return not fails

	async def sign_all(self, target_name):
		from .signable import Signable
		target = getattr(Signable, target_name)(self)
		if target.unsigned:
			good = []
			bad = []
			if len(target.unsigned) > 1 and not target.multiple_ok:
				ymsg(f'Autosign error: only one unsigned {target.desc} transaction allowed at a time!')
				target.print_bad_list(target.unsigned)
				return False
			for f in target.unsigned:
				ret = None
				try:
					ret = await target.sign(f)
				except Exception as e:
					ymsg('An error occurred with {} ‘{}’:\n    {}: ‘{}’'.format(
						target.desc, f.name, type(e).__name__, e))
				except:
					ymsg('An error occurred with {} ‘{}’'.format(target.desc, f.name))
				good.append(ret) if ret else bad.append(f)
				self.cfg._util.qmsg('')
			await asyncio.sleep(0.3)
			msg(brown(f'{len(good)} {target.desc}{suf(good)} {target.action_desc}'))
			if bad:
				rmsg(f'{len(bad)} {target.desc}{suf(bad)} {target.fail_msg}')
			if good and not self.cfg.no_summary:
				target.print_summary(good)
			if bad:
				target.print_bad_list(bad)
			return not bad
		else:
			return f'No unsigned {target.desc}s'

	async def do_sign(self):
		if not self.cfg.stealth_led:
			self.led.set('busy')
		self.do_mount()
		key_ok = self.decrypt_wallets()
		self.init_non_mmgen_keys()
		if key_ok:
			if self.cfg.stealth_led:
				self.led.set('busy')
			ret = [await self.sign_all(signable) for signable in self.signables]
			for val in ret:
				if isinstance(val, str):
					msg(val)
			if self.cfg.test_suite_autosign_threaded:
				await asyncio.sleep(0.3)
			self.do_umount()
			self.led.set('error' if not all(ret) else 'off' if self.cfg.stealth_led else 'standby')
			return all(ret)
		else:
			msg('Password is incorrect!')
			self.do_umount()
			if not self.cfg.stealth_led:
				self.led.set('error')
			return False

	def wipe_encryption_key(self):
		if self.keyfile.exists():
			ymsg(f'Shredding wallet encryption key ‘{self.keyfile}’')
			from ..fileutil import shred_file
			shred_file(self.cfg, self.keyfile)
		else:
			gmsg('No wallet encryption key on removable device')

	def create_key(self):
		desc = f'key file ‘{self.keyfile}’'
		msg('Creating ' + desc)
		try:
			self.keyfile.write_text(os.urandom(32).hex())
			self.keyfile.chmod(0o400)
		except:
			die(2, 'Unable to write ' + desc)
		msg('Wrote ' + desc)

	def gen_key(self, *, no_unmount=False):
		if not self.device_inserted:
			die(1, 'Removable device not present!')
		self.do_mount()
		self.wipe_encryption_key()
		self.create_key()
		if not no_unmount:
			self.do_umount()

	def macos_ramdisk_setup(self):
		self.ramdisk.create()

	def macos_ramdisk_delete(self):
		self.ramdisk.destroy()

	def _get_macOS_ramdisk_size(self):
		from ..addrlist import AddrIdxList
		from ..platform.darwin.util import MacOSRamDisk, warn_ramdisk_too_small
		# allow 1MB for each Monero wallet
		xmr_size = len(AddrIdxList(fmt_str=self.cfg.xmrwallets)) if self.cfg.xmrwallets else 0
		calc_size = xmr_size + 1
		usr_size = self.cfg.macos_ramdisk_size or self.cfg.macos_autosign_ramdisk_size
		if is_int(usr_size):
			usr_size = int(usr_size)
		else:
			die(1, f'{usr_size}: invalid user-specified macOS ramdisk size (not an integer)')
		min_size = MacOSRamDisk.min_size
		size = max(usr_size, calc_size, min_size)
		if usr_size and usr_size < min_size:
			warn_ramdisk_too_small(usr_size, min_size)
		return size

	def setup(self):

		def remove_wallet_dir():
			msg(f'Deleting ‘{self.wallet_dir}’')
			import shutil
			try:
				shutil.rmtree(self.wallet_dir)
			except:
				pass

		def create_wallet_dir():
			try:
				self.wallet_dir.mkdir(parents=True)
			except:
				pass
			try:
				self.wallet_dir.stat()
			except:
				die(2, f'Unable to create wallet directory ‘{self.wallet_dir}’')

		self.gen_key(no_unmount=True)

		self.swap.disable()

		if sys.platform == 'darwin':
			self.macos_ramdisk_setup()

		remove_wallet_dir()
		create_wallet_dir()

		def get_mn_wallet():
			return Wallet(self.cfg, in_fmt=self.mn_fmts[self.cfg.mnemonic_fmt or self.dfl_mn_fmt])

		if self.cfg.mnemonic_fmt or self.cfg.seed_len:
			ss_in = get_mn_wallet()
		else:
			from ..filename import find_file_in_dir
			from ..ui import keypress_confirm
			if (wf := find_file_in_dir(get_wallet_cls('mmgen'), self.cfg.data_dir)) and keypress_confirm(
					cfg         = self.cfg,
					prompt      = f'Default wallet ‘{wf}’ found.\nUse default wallet for autosigning?',
					default_yes = True):
				ss_in = Wallet(Config(), fn=wf)
			else:
				ss_in = get_mn_wallet()

		ss_out = Wallet(self.cfg, ss=ss_in, passwd_file=str(self.keyfile))
		ss_out.write_to_file(desc='autosign wallet', outdir=self.wallet_dir)

		if self.cfg.keys_from_file:
			self.setup_non_mmgen_keys()

	@property
	def xmrwallet_cfg(self):
		if not hasattr(self, '_xmrwallet_cfg'):
			self._xmrwallet_cfg = Config({
				'_clone': self.cfg,
				'coin': 'xmr',
				'wallet_rpc_user': 'autosign',
				'wallet_rpc_password': 'autosign password',
				'wallet_rpc_port': 23232 if self.cfg.test_suite_xmr_autosign else None,
				'wallet_dir': str(self.wallet_dir),
				'autosign': True,
				'autosign_mountpoint': str(self.mountpoint),
				'offline': True,
				'compat': False,
				'passwd_file': str(self.keyfile)})
		return self._xmrwallet_cfg

	def xmr_setup(self):

		def create_signing_wallets():
			from .. import xmrwallet
			if len(self.wallet_files) > 1:
				ymsg(
					'Warning: more than one wallet file, using the first '
					f'({self.wallet_files[0]}) for xmrwallet generation')
			m = xmrwallet.op(
				'create_offline',
				self.xmrwallet_cfg,
				infile  = str(self.wallet_files[0]), # MMGen wallet file
				wallets = self.cfg.xmrwallets)       # XMR wallet idxs
			asyncio.run(m.main())
			asyncio.run(m.stop_wallet_daemon())

		self.clean_old_files()

		create_signing_wallets()

	def clean_old_files(self):

		def do_shred(fn):
			nonlocal count
			msg_r('.')
			shred_file(self.cfg, fn, iterations=15)
			count += 1

		def clean_dir(s_name):

			def clean_files(rawext, sigext):
				for f in s.dir.iterdir():
					if s.clean_all and (f.name.endswith(f'.{rawext}') or f.name.endswith(f'.{sigext}')):
						do_shred(f)
					elif f.name.endswith(f'.{sigext}'):
						raw = f.parent / (f.name[:-len(sigext)] + rawext)
						if raw.is_file():
							do_shred(raw)

			from .signable import Signable
			s = getattr(Signable, s_name)(self)

			msg_r(f'Cleaning directory ‘{s.dir}’..')

			if s.dir.is_dir():
				clean_files(s.rawext, s.sigext)
				if hasattr(s, 'subext'):
					clean_files(s.rawext, s.subext)
					clean_files(s.sigext, s.subext)

			msg('done' if s.dir.is_dir() else 'skipped (no dir)')

		from ..fileutil import shred_file
		count = 0

		for s_name in self.signables:
			clean_dir(s_name)

		bmsg(f'{count} file{suf(count)} shredded')

	@property
	def device_inserted(self):
		if self.cfg.no_insert_check:
			return True
		match sys.platform:
			case 'linux':
				cp = run(self.linux_blkid_cmd.split(), stdout=PIPE, text=True)
				if cp.returncode not in (0, 2):
					die(2, f'blkid exited with error code {cp.returncode}')
				return self.dev_label in cp.stdout.splitlines()
			case 'darwin':
				if self.cfg.test_suite_root_pfx:
					return self.mountpoint.exists()
				else:
					return run(
						['diskutil', 'info', self.dev_label],
						stdout=DEVNULL, stderr=DEVNULL).returncode == 0

	async def main_loop(self):
		if not self.cfg.stealth_led:
			self.led.set('standby')
		threaded = self.cfg.test_suite_autosign_threaded
		n = 1 if threaded else 0
		prev_status = False
		while True:
			status = self.device_inserted
			if status and not prev_status:
				msg('Device insertion detected')
				await self.do_sign()
			prev_status = status
			if not n % 10:
				msg_r(f'\r{" " * 38}\rWaiting for device insertion')
			await asyncio.sleep(0.2 if threaded else 1)
			if not threaded:
				msg_r('.')
				n += 1

	def at_exit(self, exit_val, message=None):
		if message:
			msg(message)
		self.led.stop()
		sys.exit(0 if self.cfg.test_suite_autosign_threaded else int(exit_val))

	def init_exit_handler(self):

		def handler(arg1, arg2):
			self.at_exit(1, '\nCleaning up...')

		import signal
		signal.signal(signal.SIGTERM, handler)
		signal.signal(signal.SIGINT, handler)

	def init_led(self):
		from ..led import LEDControl
		self.led = LEDControl(
			enabled = self.cfg.led,
			simulate = self.cfg.test_suite_autosign_led_simulate)
		self.led.set('off')

	def setup_non_mmgen_keys(self):
		from ..fileutil import get_lines_from_file, write_data_to_file
		from ..crypto import Crypto
		from ..ui import keypress_confirm
		lines = get_lines_from_file(self.cfg, self.cfg.keys_from_file, desc='keylist data')
		write_data_to_file(
			self.cfg,
			str(self.wallet_dir / self.keylist_fn),
			Crypto(self.cfg).mmgen_encrypt(
				data = '\n'.join(lines).encode(),
				passwd = self.keyfile.read_text()),
			desc = 'encrypted keylist data',
			binary = True)
		if keypress_confirm(self.cfg, 'Securely delete original keylist file?'):
			from ..fileutil import shred_file
			shred_file(self.cfg, self.cfg.keys_from_file)

	def init_non_mmgen_keys(self):
		if not hasattr(self, 'keylist'):
			path = self.wallet_dir / self.keylist_fn
			if path.exists():
				from ..crypto import Crypto
				from ..fileutil import get_data_from_file
				self.keylist = Crypto(self.cfg).mmgen_decrypt(
					get_data_from_file(
						self.cfg,
						path,
						desc = 'encrypted keylist data',
						binary = True),
					passwd = self.keyfile.read_text()).decode().split()
			else:
				self.keylist = None
