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
autosign: Autosign MMGen transactions, message files and XMR wallet output files
"""

import sys, os, asyncio
from stat import S_IWUSR, S_IRUSR
from pathlib import Path
from subprocess import run, PIPE, DEVNULL

from .cfg import Config
from .util import msg, msg_r, ymsg, rmsg, gmsg, bmsg, die, suf, fmt, fmt_list, is_int, have_sudo, capfirst
from .color import yellow, red, orange, brown, blue
from .wallet import Wallet, get_wallet_cls
from .addrlist import AddrIdxList
from .filename import find_file_in_dir
from .fileutil import shred_file
from .ui import keypress_confirm

def SwapMgr(*args, **kwargs):
	match sys.platform:
		case 'linux':
			return SwapMgrLinux(*args, **kwargs)
		case 'darwin':
			return SwapMgrMacOS(*args, **kwargs)

class SwapMgrBase:

	def __init__(self, cfg, *, ignore_zram=False):
		self.cfg = cfg
		self.ignore_zram = ignore_zram
		self.desc = 'disk swap' if ignore_zram else 'swap'

	def enable(self, *, quiet=False):
		ret = self.do_enable()
		if not quiet:
			self.cfg._util.qmsg(
				f'{capfirst(self.desc)} successfully enabled' if ret else
				f'{capfirst(self.desc)} is already enabled' if ret is None else
				f'Could not enable {self.desc}')
		return ret

	def disable(self, *, quiet=False):
		self.cfg._util.qmsg_r(f'Attempting to disable {self.desc}...')
		ret = self.do_disable()
		self.cfg._util.qmsg('success')
		if not quiet:
			self.cfg._util.qmsg(
				f'{capfirst(self.desc)} successfully disabled ({fmt_list(ret, fmt="no_quotes")})'
					if ret and isinstance(ret, list) else
				f'{capfirst(self.desc)} successfully disabled' if ret else
				f'No active {self.desc}')
		return ret

	def process_cmds(self, op, cmds):
		if not cmds:
			return
		if have_sudo(silent=True) and not self.cfg.test_suite:
			for cmd in cmds:
				run(cmd.split(), check=True)
		else:
			pre = 'failure\n' if op == 'disable' else ''
			fs = blue('{a} {b} manually by executing the following command{c}:\n{d}')
			post = orange('[To prevent this message in the future, enable sudo without a password]')
			m = pre + fs.format(
				a = 'Please disable' if op == 'disable' else 'Enable',
				b = self.desc,
				c = suf(cmds),
				d = fmt_list(cmds, indent='  ', fmt='col')) + '\n' + post
			msg(m)
			if not self.cfg.test_suite:
				sys.exit(1)

class SwapMgrLinux(SwapMgrBase):

	def get_active(self):
		for cmd in ('/sbin/swapon', 'swapon'):
			try:
				cp = run([cmd, '--show=NAME', '--noheadings'], stdout=PIPE, text=True, check=True)
				break
			except Exception:
				if cmd == 'swapon':
					raise
		res = cp.stdout.splitlines()
		return [e for e in res if not e.startswith('/dev/zram')] if self.ignore_zram else res

	def do_enable(self):
		if ret := self.get_active():
			ymsg(f'Warning: {self.desc} is already enabled: ({fmt_list(ret, fmt="no_quotes")})')
		self.process_cmds('enable', ['sudo swapon --all'])
		return True

	def do_disable(self):
		swapdevs = self.get_active()
		if not swapdevs:
			return None
		self.process_cmds('disable', [f'sudo swapoff {swapdev}' for swapdev in swapdevs])
		return swapdevs

class SwapMgrMacOS(SwapMgrBase):

	def get_active(self):
		cmd = 'launchctl print system/com.apple.dynamic_pager'
		return run(cmd.split(), stdout=DEVNULL, stderr=DEVNULL).returncode == 0

	def _do_action(self, active, op, cmd):
		if self.get_active() is active:
			return None
		else:
			cmd = f'sudo launchctl {cmd} -w /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist'
			self.process_cmds(op, [cmd])
			return True

	def do_enable(self):
		return self._do_action(active=True, op='enable', cmd='load')

	def do_disable(self):
		return self._do_action(active=False, op='disable', cmd='unload')

class Signable:

	non_xmr_signables = (
		'transaction',
		'automount_transaction',
		'message')

	xmr_signables = (              # order is important!
		'xmr_wallet_outputs_file', # import XMR wallet outputs BEFORE signing transactions
		'xmr_transaction')

	class base:

		clean_all = False
		multiple_ok = True
		action_desc = 'signed'
		fail_msg = 'failed to sign'

		def __init__(self, parent):
			self.parent = parent
			self.cfg = parent.cfg
			self.dir = getattr(parent, self.dir_name)
			self.name = type(self).__name__

		@property
		def unsigned(self):
			return self._unprocessed('_unsigned', self.rawext, self.sigext)

		def _unprocessed(self, attrname, rawext, sigext):
			if not hasattr(self, attrname):
				dirlist = sorted(self.dir.iterdir())
				names = {f.name for f in dirlist}
				setattr(
					self,
					attrname,
					tuple(f for f in dirlist
						if f.name.endswith('.' + rawext)
							and f.name[:-len(rawext)] + sigext not in names))
			return getattr(self, attrname)

		def print_bad_list(self, bad_files):
			msg('\n{a}\n{b}'.format(
				a = red(f'Failed {self.desc}s:'),
				b = '  {}\n'.format('\n  '.join(
					self.gen_bad_list(sorted(bad_files, key=lambda f: f.name))))))

		def gen_bad_list(self, bad_files):
			for f in bad_files:
				yield red(f.name)

	class transaction(base):
		desc = 'non-automount transaction'
		dir_name = 'tx_dir'
		rawext = 'rawtx'
		sigext = 'sigtx'
		automount = False

		async def sign(self, f):
			from .tx import UnsignedTX
			tx1 = UnsignedTX(
				cfg       = self.cfg,
				filename  = f,
				automount = self.automount)
			if tx1.proto.coin == 'XMR':
				ctx = Signable.xmr_compat_transaction(self.parent)
				for k in ('desc', 'print_summary', 'print_bad_list'):
					setattr(self, k, getattr(ctx, k))
				return await ctx.sign(f, compat_call=True)
			if tx1.proto.sign_mode == 'daemon':
				from .rpc import rpc_init
				tx1.rpc = await rpc_init(self.cfg, tx1.proto, ignore_wallet=True)
			from .tx.keys import TxKeys
			tx2 = await tx1.sign(
				TxKeys(
					self.cfg,
					tx1,
					seedfiles = self.parent.wallet_files[:],
					keylist = self.parent.keylist,
					passwdfile = str(self.parent.keyfile),
					autosign = True).keys)
			if tx2:
				tx2.file.write(ask_write=False, outdir=self.dir)
				return tx2
			else:
				return False

		def print_summary(self, signables):

			if self.cfg.full_summary:
				bmsg('\nAutosign summary:\n')
				msg_r('\n'.join(tx.info.format(terse=True) for tx in signables))
				return

			def gen():
				for tx in signables:
					non_mmgen = [o for o in tx.outputs if not o.mmid]
					if non_mmgen:
						yield (tx, non_mmgen)

			body = list(gen())

			if body:
				bmsg('\nAutosign summary:')
				fs = '{}  {} {}'
				t_wid, a_wid = 6, 44

				def gen():
					yield fs.format('TX ID ', 'Non-MMGen outputs'+' '*(a_wid-17), 'Amount')
					yield fs.format('-'*t_wid, '-'*a_wid, '-'*7)
					for tx, non_mmgen in body:
						for nm in non_mmgen:
							yield fs.format(
								tx.txid.fmt(t_wid, color=True) if nm is non_mmgen[0] else ' '*t_wid,
								nm.addr.fmt(nm.addr.view_pref, a_wid, color=True),
								nm.amt.hl() + ' ' + yellow(tx.coin))

				msg('\n' + '\n'.join(gen()))
			else:
				msg('\nNo non-MMGen outputs')

	class automount_transaction(transaction):
		desc = 'automount transaction'
		dir_name = 'txauto_dir'
		rawext = 'arawtx'
		sigext = 'asigtx'
		subext = 'asubtx'
		multiple_ok = False
		automount = True

		@property
		def unsubmitted(self):
			return self._unprocessed('_unsubmitted', self.sigext, self.subext)

		@property
		def unsubmitted_raw(self):
			return self._unprocessed('_unsubmitted_raw', self.rawext, self.subext)

		unsent = unsubmitted
		unsent_raw = unsubmitted_raw

		@property
		def submitted(self):
			return self._processed('_submitted', self.subext)

		def _processed(self, attrname, ext):
			if not hasattr(self, attrname):
				setattr(self, attrname, tuple(f for f in sorted(self.dir.iterdir())
					if f.name.endswith('.' + ext)))
			return getattr(self, attrname)

		def die_wrong_num_txs(self, tx_type, *, msg=None, desc=None, show_dir=False):
			match len(getattr(self, tx_type)): # num_txs
				case 0: subj, suf, pred = ('No', 's', 'present')
				case 1: subj, suf, pred = ('One', '', 'already present')
				case _: subj, suf, pred = ('More than one', '', 'already present')
			die('AutosignTXError', '{m}{a} {b} transaction{c} {d} {e}!'.format(
				m = msg + '\n' if msg else '',
				a = subj,
				b = desc or tx_type,
				c = suf,
				d = pred,
				e = f'in ‘{getattr(self.parent, self.dir_name)}’'
					if show_dir else 'on removable device'))

		def check_create_ok(self):
			if len(self.unsigned):
				self.die_wrong_num_txs('unsigned', msg='Cannot create transaction')
			if len(self.unsent):
				die('AutosignTXError', 'Cannot create transaction: you have an unsent transaction')

		def get_unsubmitted(self, tx_type='unsubmitted'):
			if len(self.unsubmitted) == 1:
				return self.unsubmitted[0]
			else:
				self.die_wrong_num_txs(tx_type)

		def get_unsent(self):
			return self.get_unsubmitted('unsent')

		def get_submitted(self):
			if len(self.submitted) == 0:
				self.die_wrong_num_txs('submitted')
			else:
				return self.submitted

		def get_abortable(self):
			if len(self.unsent_raw) != 1:
				self.die_wrong_num_txs('unsent_raw', desc='unsent')
			if len(self.unsent) > 1:
				self.die_wrong_num_txs('unsent')
			if self.unsent:
				if self.unsent[0].stem != self.unsent_raw[0].stem:
					die(1, f'{self.unsent[0]}, {self.unsent_raw[0]}: file mismatch')
			return self.unsent_raw + self.unsent

		def shred_abortable(self):
			files = self.get_abortable() # raises AutosignTXError if no unsent TXs available
			keypress_confirm(
				self.cfg,
				'The following file{} will be securely deleted:\n{}\nOK?'.format(
					suf(files),
					fmt_list(map(str, files), fmt='col', indent='  ')),
					do_exit = True)
			for fn in files:
				msg(f'Shredding file ‘{fn}’')
				shred_file(self.cfg, fn, iterations=15)
			sys.exit(0)

		async def get_last_created(self):
			from .tx import CompletedTX
			files = [f for f in self.dir.iterdir() if f.name.endswith(self.subext)]
			return sorted(
				[await CompletedTX(cfg=self.cfg, filename=str(txfile), quiet_open=True)
					for txfile in files],
				key = lambda x: x.timestamp)[-1]

	class xmr_signable: # mixin class
		automount = True
		summary_footer = ''

		def need_daemon_restart(self, m, new_idx):
			old_idx = self.parent.xmr_cur_wallet_idx
			self.parent.xmr_cur_wallet_idx = new_idx
			return old_idx != new_idx or m.wd.state != 'ready'

		def print_summary(self, signables):
			bmsg('\nAutosign summary:')
			msg('\n'.join(s.get_info(indent='  ') for s in signables) + self.summary_footer)

	class xmr_transaction(xmr_signable, automount_transaction):
		desc = 'Monero non-compat transaction'
		dir_name = 'xmr_tx_dir'
		rawext = 'rawtx'
		sigext = 'sigtx'
		subext = 'subtx'

		async def sign(self, f, compat_call=False):
			from . import xmrwallet
			from .xmrwallet.file.tx import MoneroMMGenTX
			tx1 = MoneroMMGenTX.Completed(self.parent.xmrwallet_cfg, f)
			m = xmrwallet.op(
				'sign',
				self.parent.xmrwallet_cfg,
				infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
				wallets = str(tx1.src_wallet_idx),
				compat_call = compat_call)
			tx2 = await m.main(f, restart_daemon=self.need_daemon_restart(m, tx1.src_wallet_idx))
			tx2.write(ask_write=False)
			return tx2

	class xmr_compat_transaction(xmr_transaction):
		desc = 'Monero compat transaction'
		dir_name = 'txauto_dir'
		rawext = 'arawtx'
		sigext = 'asigtx'
		subext = 'asubtx'

	class xmr_wallet_outputs_file(xmr_signable, base):
		desc = 'Monero wallet outputs file'
		dir_name = 'xmr_outputs_dir'
		rawext = 'raw'
		sigext = 'sig'
		clean_all = True
		summary_footer = '\n'

		@property
		def unsigned(self):
			import json
			return tuple(
				f for f in super().unsigned
					if not json.loads(f.read_text())['MoneroMMGenWalletOutputsFile']['data']['imported'])

		async def sign(self, f):
			from . import xmrwallet
			wallet_idx = xmrwallet.op_cls('wallet').get_idx_from_fn(f)
			m = xmrwallet.op(
				'import_outputs',
				self.parent.xmrwallet_cfg,
				infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
				wallets = str(wallet_idx))
			obj = await m.main(f, wallet_idx, restart_daemon=self.need_daemon_restart(m, wallet_idx))
			obj.write(quiet=not obj.data.sign)
			self.action_desc = 'imported and signed' if obj.data.sign else 'imported'
			return obj

	class message(base):
		desc = 'message file'
		dir_name = 'msg_dir'
		rawext = 'rawmsg.json'
		sigext = 'sigmsg.json'
		fail_msg = 'failed to sign or signed incompletely'

		async def sign(self, f):
			from .msg import UnsignedMsg, SignedMsg
			m = UnsignedMsg(self.cfg, infile=f)
			await m.sign(wallet_files=self.parent.wallet_files[:], passwd_file=str(self.parent.keyfile))
			m = SignedMsg(self.cfg, data=m.__dict__)
			m.write_to_file(
				outdir = self.dir.resolve(),
				ask_overwrite = False)
			if m.data.get('failed_sids'):
				die(
					'MsgFileFailedSID',
					f'Failed Seed IDs: {fmt_list(m.data["failed_sids"], fmt="bare")}')
			return m

		def print_summary(self, signables):
			gmsg('\nSigned message files:')
			for message in signables:
				gmsg('  ' + message.signed_filename)

		def gen_bad_list(self, bad_files):
			for f in bad_files:
				sigfile = f.parent / (f.name[:-len(self.rawext)] + self.sigext)
				yield orange(sigfile.name) if sigfile.exists() else red(f.name)

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
		'wipe_key')

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
			from .platform.darwin.util import MacOSRamDisk
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
			self.signables += Signable.non_xmr_signables

		if self.have_xmr:
			self.dirs |= self.xmr_dirs | (
				{'txauto_dir': 'txauto'} if cfg.xmrwallet_compat and self.xmr_only else {})
			self.signables += Signable.xmr_signables + (
				('automount_transaction',) if cfg.xmrwallet_compat and self.xmr_only else ())

		for name, path in self.dirs.items():
			setattr(self, name, self.mountpoint / path)

		self.swap = SwapMgr(self.cfg, ignore_zram=True)

	async def check_daemons_running(self):
		from .protocol import init_proto
		for coin in self.coins:
			proto = init_proto(self.cfg,  coin, network=self.cfg.network, need_amt=True)
			if proto.sign_mode == 'daemon':
				self.cfg._util.vmsg(f'Checking {coin} daemon')
				from .rpc import rpc_init
				from .exception import SocketError
				try:
					await rpc_init(self.cfg, proto, ignore_wallet=True)
				except SocketError as e:
					from .daemon import CoinDaemon
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
					msg(f'Mounting ‘{self.mountpoint}’')
			else:
				die(1, f'Unable to mount device ‘{self.dev_label}’ at ‘{self.mountpoint}’')

		for dirname in self.dirs:
			check_or_create(dirname)

	def do_umount(self, *, silent=False, verbose=False):
		if self.mountpoint.is_mount():
			run(['sync'], check=True)
			if not silent:
				msg(f'Unmounting ‘{self.mountpoint}’')
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
		from .platform.darwin.util import MacOSRamDisk, warn_ramdisk_too_small
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

		wf = find_file_in_dir(get_wallet_cls('mmgen'), self.cfg.data_dir)
		if wf and keypress_confirm(
				cfg         = self.cfg,
				prompt      = f'Default wallet ‘{wf}’ found.\nUse default wallet for autosigning?',
				default_yes = True):
			ss_in = Wallet(Config(), fn=wf)
		else:
			ss_in = Wallet(self.cfg, in_fmt=self.mn_fmts[self.cfg.mnemonic_fmt or self.dfl_mn_fmt])
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
			from . import xmrwallet
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

			s = getattr(Signable, s_name)(self)

			msg_r(f'Cleaning directory ‘{s.dir}’..')

			if s.dir.is_dir():
				clean_files(s.rawext, s.sigext)
				if hasattr(s, 'subext'):
					clean_files(s.rawext, s.subext)
					clean_files(s.sigext, s.subext)

			msg('done' if s.dir.is_dir() else 'skipped (no dir)')

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
				msg_r(f'\r{" "*17}\rWaiting')
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
		from .led import LEDControl
		self.led = LEDControl(
			enabled = self.cfg.led,
			simulate = self.cfg.test_suite_autosign_led_simulate)
		self.led.set('off')

	def setup_non_mmgen_keys(self):
		from .fileutil import get_lines_from_file, write_data_to_file
		from .crypto import Crypto
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
			shred_file(self.cfg, self.cfg.keys_from_file)

	def init_non_mmgen_keys(self):
		if not hasattr(self, 'keylist'):
			path = self.wallet_dir / self.keylist_fn
			if path.exists():
				from .crypto import Crypto
				from .fileutil import get_data_from_file
				self.keylist = Crypto(self.cfg).mmgen_decrypt(
					get_data_from_file(
						self.cfg,
						path,
						desc = 'encrypted keylist data',
						binary = True),
					passwd = self.keyfile.read_text()).decode().split()
			else:
				self.keylist = None
