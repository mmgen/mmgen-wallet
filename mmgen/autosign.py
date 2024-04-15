#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
autosign: Auto-sign MMGen transactions, message files and XMR wallet output files
"""

import sys,os,asyncio
from stat import S_ISDIR,S_IWUSR,S_IRUSR
from pathlib import Path
from subprocess import run,DEVNULL

from .cfg import Config
from .util import msg,msg_r,ymsg,rmsg,gmsg,bmsg,die,suf,fmt,fmt_list,async_run
from .color import yellow,red,orange,brown
from .wallet import Wallet,get_wallet_cls
from .filename import find_file_in_dir
from .ui import keypress_confirm

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

		def __init__(self,parent):
			self.parent = parent
			self.cfg = parent.cfg
			self.dir = getattr(parent,self.dir_name)
			self.name = type(self).__name__

		@property
		def submitted(self):
			return self._processed('_submitted', self.subext)

		def _processed(self, attrname, ext):
			if not hasattr(self, attrname):
				setattr(self, attrname, tuple(f for f in sorted(self.dir.iterdir()) if f.name.endswith('.'+ext)))
			return getattr(self, attrname)

		@property
		def unsigned(self):
			return self._unprocessed( '_unsigned', self.rawext, self.sigext )

		@property
		def unsubmitted(self):
			return self._unprocessed( '_unsubmitted', self.sigext, self.subext )

		@property
		def unsubmitted_raw(self):
			return self._unprocessed( '_unsubmitted_raw', self.rawext, self.subext )

		unsent = unsubmitted
		unsent_raw = unsubmitted_raw

		def _unprocessed(self,attrname,rawext,sigext):
			if not hasattr(self,attrname):
				dirlist = sorted(self.dir.iterdir())
				names = {f.name for f in dirlist}
				setattr(
					self,
					attrname,
					tuple(f for f in dirlist
						if f.name.endswith('.' + rawext)
							and f.name[:-len(rawext)] + sigext not in names) )
			return getattr(self,attrname)

		def print_bad_list(self,bad_files):
			msg('\n{a}\n{b}'.format(
				a = red(f'Failed {self.desc}s:'),
				b = '  {}\n'.format('\n  '.join(self.gen_bad_list(sorted(bad_files,key=lambda f: f.name))))
			))

		def die_wrong_num_txs(self, tx_type, msg=None, desc=None, show_dir=False):
			num_txs = len(getattr(self, tx_type))
			die('AutosignTXError', "{m}{a} {b} transaction{c} {d} {e}!".format(
				m = msg + '\n' if msg else '',
				a = 'One' if num_txs == 1 else 'More than one' if num_txs else 'No',
				b = desc or tx_type,
				c = suf(num_txs),
				d = 'already present' if num_txs else 'present',
				e = f'in ‘{getattr(self.parent, self.dir_name)}’' if show_dir else 'on removable device',
			))

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
			if keypress_confirm(
					self.cfg,
					'The following file{} will be securely deleted:\n{}\nOK?'.format(
						suf(files),
						fmt_list(map(str, files), fmt='col', indent='  '))):
				for f in files:
					msg(f'Shredding file ‘{f}’')
					from .fileutil import shred_file
					shred_file(f)
				sys.exit(0)
			else:
				die(1, 'Exiting at user request')

		async def get_last_created(self):
			from .tx import CompletedTX
			ext = '.' + Signable.automount_transaction.subext
			files = [f for f in self.dir.iterdir() if f.name.endswith(ext)]
			return sorted(
				[await CompletedTX(cfg=self.cfg, filename=str(txfile), quiet_open=True) for txfile in files],
				key = lambda x: x.timestamp)[-1]

	class transaction(base):
		desc = 'non-automount transaction'
		rawext = 'rawtx'
		sigext = 'sigtx'
		dir_name = 'tx_dir'
		fail_msg = 'failed to sign'

		async def sign(self,f):
			from .tx import UnsignedTX
			tx1 = UnsignedTX(
					cfg       = self.cfg,
					filename  = f,
					automount = self.name=='automount_transaction')
			if tx1.proto.sign_mode == 'daemon':
				from .rpc import rpc_init
				tx1.rpc = await rpc_init( self.cfg, tx1.proto, ignore_wallet=True )
			from .tx.sign import txsign
			tx2 = await txsign(
					cfg_parm    = self.cfg,
					tx          = tx1,
					seed_files  = self.parent.wallet_files[:],
					kl          = None,
					kal         = None,
					passwd_file = str(self.parent.keyfile))
			if tx2:
				tx2.file.write(ask_write=False, outdir=self.dir)
				return tx2
			else:
				return False

		def print_summary(self,signables):

			if self.cfg.full_summary:
				bmsg('\nAutosign summary:\n')
				msg_r('\n'.join(tx.info.format(terse=True) for tx in signables))
				return

			def gen():
				for tx in signables:
					non_mmgen = [o for o in tx.outputs if not o.mmid]
					if non_mmgen:
						yield (tx,non_mmgen)

			body = list(gen())

			if body:
				bmsg('\nAutosign summary:')
				fs = '{}  {} {}'
				t_wid,a_wid = 6,44

				def gen():
					yield fs.format('TX ID ','Non-MMGen outputs'+' '*(a_wid-17),'Amount')
					yield fs.format('-'*t_wid, '-'*a_wid, '-'*7)
					for tx,non_mmgen in body:
						for nm in non_mmgen:
							yield fs.format(
								tx.txid.fmt( width=t_wid, color=True ) if nm is non_mmgen[0] else ' '*t_wid,
								nm.addr.fmt( width=a_wid, color=True ),
								nm.amt.hl() + ' ' + yellow(tx.coin))

				msg('\n' + '\n'.join(gen()))
			else:
				msg('\nNo non-MMGen outputs')

		def gen_bad_list(self,bad_files):
			for f in bad_files:
				yield red(f.name)

	class automount_transaction(transaction):
		desc   = 'automount transaction'
		dir_name = 'txauto_dir'
		rawext = 'arawtx'
		sigext = 'asigtx'
		subext = 'asubtx'
		multiple_ok = False

	class xmr_signable(transaction): # mixin class

		def need_daemon_restart(self,m,new_idx):
			old_idx = self.parent.xmr_cur_wallet_idx
			self.parent.xmr_cur_wallet_idx = new_idx
			return old_idx != new_idx or m.wd.state != 'ready'

		def print_summary(self,signables):
			bmsg('\nAutosign summary:')
			msg('\n'.join(s.get_info(indent='  ') for s in signables) + self.summary_footer)

	class xmr_transaction(xmr_signable):
		dir_name = 'xmr_tx_dir'
		desc = 'Monero transaction'
		subext = 'subtx'
		multiple_ok = False
		summary_footer = ''

		async def sign(self,f):
			from .xmrwallet import MoneroMMGenTX,MoneroWalletOps,xmrwallet_uargs
			tx1 = MoneroMMGenTX.Completed( self.parent.xmrwallet_cfg, f )
			m = MoneroWalletOps.sign(
				self.parent.xmrwallet_cfg,
				xmrwallet_uargs(
					infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
					wallets = str(tx1.src_wallet_idx),
					spec    = None ),
			)
			tx2 = await m.main( f, restart_daemon=self.need_daemon_restart(m,tx1.src_wallet_idx) )
			tx2.write(ask_write=False)
			return tx2

	class xmr_wallet_outputs_file(xmr_signable):
		desc = 'Monero wallet outputs file'
		rawext = 'raw'
		sigext = 'sig'
		dir_name = 'xmr_outputs_dir'
		clean_all = True
		summary_footer = '\n'

		@property
		def unsigned(self):
			import json
			return tuple(
				f for f in super().unsigned
					if not json.loads(f.read_text())['MoneroMMGenWalletOutputsFile']['data']['imported'])

		async def sign(self,f):
			from .xmrwallet import MoneroWalletOps,xmrwallet_uargs
			wallet_idx = MoneroWalletOps.wallet.get_idx_from_fn(f)
			m = MoneroWalletOps.import_outputs(
				self.parent.xmrwallet_cfg,
				xmrwallet_uargs(
					infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
					wallets = str(wallet_idx),
					spec    = None ),
			)
			obj = await m.main(f, wallet_idx, restart_daemon=self.need_daemon_restart(m,wallet_idx))
			obj.write(quiet=not obj.data.sign)
			self.action_desc = 'imported and signed' if obj.data.sign else 'imported'
			return obj

	class message(base):
		desc = 'message file'
		rawext = 'rawmsg.json'
		sigext = 'sigmsg.json'
		dir_name = 'msg_dir'
		fail_msg = 'failed to sign or signed incompletely'

		async def sign(self,f):
			from .msg import UnsignedMsg,SignedMsg
			m = UnsignedMsg( self.cfg, infile=f )
			await m.sign(wallet_files=self.parent.wallet_files[:], passwd_file=str(self.parent.keyfile))
			m = SignedMsg( self.cfg, data=m.__dict__ )
			m.write_to_file(
				outdir = self.dir.resolve(),
				ask_overwrite = False )
			if m.data.get('failed_sids'):
				die('MsgFileFailedSID',f'Failed Seed IDs: {fmt_list(m.data["failed_sids"],fmt="bare")}')
			return m

		def print_summary(self,signables):
			gmsg('\nSigned message files:')
			for message in signables:
				gmsg('  ' + message.signed_filename)

		def gen_bad_list(self,bad_files):
			for f in bad_files:
				sigfile = f.parent / ( f.name[:-len(self.rawext)] + self.sigext )
				yield orange(sigfile.name) if sigfile.exists() else red(f.name)

class Autosign:

	dfl_mountpoint     = '/mnt/mmgen_autosign'
	dfl_wallet_dir     = '/dev/shm/autosign'
	old_dfl_mountpoint = '/mnt/tx'
	dfl_dev_label_dir  = '/dev/disk/by-label'
	dev_label          = 'MMGEN_TX'

	old_dfl_mountpoint_errmsg = f"""
		Mountpoint '{old_dfl_mountpoint}' is no longer supported!
		Please rename '{old_dfl_mountpoint}' to '{dfl_mountpoint}'
		and update your fstab accordingly.
	"""
	mountpoint_errmsg_fs = """
		Mountpoint '{}' does not exist or does not point
		to a directory!  Please create the mountpoint and add an entry
		to your fstab as described in this script’s help text.
	"""

	mn_fmts    = {
		'mmgen': 'words',
		'bip39': 'bip39',
	}
	dfl_mn_fmt = 'mmgen'

	non_xmr_dirs = {
		'tx_dir':     'tx',
		'txauto_dir': 'txauto',
		'msg_dir':    'msg',
	}
	xmr_dirs = {
		'xmr_dir':         'xmr',
		'xmr_tx_dir':      'xmr/tx',
		'xmr_outputs_dir': 'xmr/outputs',
	}
	have_xmr = False
	xmr_only = False

	def init_cfg(self): # see test/overlay/fakemods/mmgen/autosign.py
		self.mountpoint     = Path(self.cfg.mountpoint or self.dfl_mountpoint)
		self.wallet_dir     = Path(self.cfg.wallet_dir or self.dfl_wallet_dir)
		self.dev_label_path = Path(self.dfl_dev_label_dir) / self.dev_label
		self.mount_cmd      = 'mount'
		self.umount_cmd     = 'umount'

	def __init__(self,cfg,cmd=None):

		if cfg.mnemonic_fmt:
			if cfg.mnemonic_fmt not in self.mn_fmts:
				die(1,'{!r}: invalid mnemonic format (must be one of: {})'.format(
					cfg.mnemonic_fmt,
					fmt_list( self.mn_fmts, fmt='no_spc' ) ))

		self.cfg = cfg
		self.init_cfg()

		self.keyfile = self.mountpoint / 'autosign.key'

		if any(k in cfg._uopts for k in ('help','longhelp')):
			return

		if 'coin' in cfg._uopts:
			die(1,'--coin option not supported with this command.  Use --coins instead')

		self.coins = cfg.coins.upper().split(',') if cfg.coins else []

		if cfg.xmrwallets and not 'XMR' in self.coins:
			self.coins.append('XMR')

		if not self.coins and cmd not in ('gen_key','wipe_key'):
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
			self.dirs |= self.xmr_dirs
			self.signables += Signable.xmr_signables

		for name,path in self.dirs.items():
			setattr(self, name, self.mountpoint / path)

	async def check_daemons_running(self):
		from .protocol import init_proto
		for coin in self.coins:
			proto = init_proto(self.cfg,  coin, network=self.cfg.network, need_amt=True)
			if proto.sign_mode == 'daemon':
				self.cfg._util.vmsg(f'Checking {coin} daemon')
				from .rpc import rpc_init
				from .exception import SocketError
				try:
					await rpc_init( self.cfg, proto, ignore_wallet=True )
				except SocketError as e:
					from .daemon import CoinDaemon
					d = CoinDaemon( self.cfg, proto=proto, test_suite=self.cfg.test_suite )
					die(2,
						f'\n{e}\nIs the {d.coind_name} daemon ({d.exec_fn}) running '
						+ 'and listening on the correct port?' )

	@property
	def wallet_files(self):

		if not hasattr(self,'_wallet_files'):

			try:
				dirlist = self.wallet_dir.iterdir()
			except:
				die(1,f"Cannot open wallet directory '{self.wallet_dir}'. Did you run ‘mmgen-autosign setup’?")

			self._wallet_files = [f for f in dirlist if f.suffix == '.mmdat']

			if not self._wallet_files:
				die(1,'No wallet files present!')

		return self._wallet_files

	def do_mount(self, silent=False):

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

		if not self.mountpoint.is_dir():
			def do_die(m):
				die(1,'\n' + yellow(fmt(m.strip(),indent='  ')))
			if Path(self.old_dfl_mountpoint).is_dir():
				do_die(self.old_dfl_mountpoint_errmsg)
			else:
				do_die(self.mountpoint_errmsg_fs.format(self.mountpoint))

		if not self.mountpoint.is_mount():
			if run(
					self.mount_cmd.split() + [str(self.mountpoint)],
					stderr = DEVNULL,
					stdout = DEVNULL).returncode == 0:
				if not silent:
					msg(f"Mounting '{self.mountpoint}'")
			else:
				die(1,f"Unable to mount device at '{self.mountpoint}'")

		for dirname in self.dirs:
			check_or_create(dirname)

	def do_umount(self,silent=False):
		if self.mountpoint.is_mount():
			run( ['sync'], check=True )
			if not silent:
				msg(f"Unmounting '{self.mountpoint}'")
			run(self.umount_cmd.split() + [str(self.mountpoint)], check=True)
		if not silent:
			bmsg('It is now safe to extract the removable device')

	def decrypt_wallets(self):
		msg(f"Unlocking wallet{suf(self.wallet_files)} with key from ‘{self.keyfile}’")
		fails = 0
		for wf in self.wallet_files:
			try:
				Wallet(self.cfg, wf, ignore_in_fmt=True, passwd_file=str(self.keyfile))
			except SystemExit as e:
				if e.code != 0:
					fails += 1

		return not fails

	async def sign_all(self,target_name):
		target = getattr(Signable,target_name)(self)
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
					ymsg(f"An error occurred with {target.desc} '{f.name}':\n    {type(e).__name__}: {e!s}")
				except:
					ymsg(f"An error occurred with {target.desc} '{f.name}'")
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
		if key_ok:
			if self.cfg.stealth_led:
				self.led.set('busy')
			ret = [await self.sign_all(signable) for signable in self.signables]
			for val in ret:
				if isinstance(val,str):
					msg(val)
			if self.cfg.test_suite_autosign_threaded:
				await asyncio.sleep(1)
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
			from .fileutil import shred_file
			ymsg(f'Shredding wallet encryption key ‘{self.keyfile}’')
			shred_file(self.keyfile, verbose=self.cfg.verbose)
		else:
			gmsg('No wallet encryption key on removable device')

	def create_key(self):
		desc = f"key file '{self.keyfile}'"
		msg('Creating ' + desc)
		try:
			self.keyfile.write_text( os.urandom(32).hex() )
			self.keyfile.chmod(0o400)
		except:
			die(2,'Unable to write ' + desc)
		msg('Wrote ' + desc)

	def gen_key(self,no_unmount=False):
		if not self.get_insert_status():
			die(1,'Removable device not present!')
		self.do_mount()
		self.wipe_encryption_key()
		self.create_key()
		if not no_unmount:
			self.do_umount()

	def setup(self):

		def remove_wallet_dir():
			msg(f"Deleting '{self.wallet_dir}'")
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
				die(2,f"Unable to create wallet directory '{self.wallet_dir}'")

		remove_wallet_dir()
		create_wallet_dir()
		self.gen_key(no_unmount=True)
		wf = find_file_in_dir( get_wallet_cls('mmgen'), self.cfg.data_dir )
		if wf and keypress_confirm(
				cfg         = self.cfg,
				prompt      = f"Default wallet '{wf}' found.\nUse default wallet for autosigning?",
				default_yes = True ):
			ss_in = Wallet( Config(), wf )
		else:
			ss_in = Wallet( self.cfg, in_fmt=self.mn_fmts[self.cfg.mnemonic_fmt or self.dfl_mn_fmt] )
		ss_out = Wallet( self.cfg, ss=ss_in, passwd_file=str(self.keyfile) )
		ss_out.write_to_file( desc='autosign wallet', outdir=self.wallet_dir )

	@property
	def xmrwallet_cfg(self):
		if not hasattr(self,'_xmrwallet_cfg'):
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
				'passwd_file': str(self.keyfile),
			})
		return self._xmrwallet_cfg

	def xmr_setup(self):

		def create_signing_wallets():
			from .xmrwallet import MoneroWalletOps,xmrwallet_uargs
			if len(self.wallet_files) > 1:
				ymsg(f'Warning: more than one wallet file, using the first ({self.wallet_files[0]}) for xmrwallet generation')
			m = MoneroWalletOps.create_offline(
				self.xmrwallet_cfg,
				xmrwallet_uargs(
					infile  = str(self.wallet_files[0]), # MMGen wallet file
					wallets = self.cfg.xmrwallets,  # XMR wallet idxs
					spec    = None ),
			)
			async_run(m.main())
			async_run(m.stop_wallet_daemon())

		self.clean_old_files()

		create_signing_wallets()

	def clean_old_files(self):

		def do_shred(f):
			nonlocal count
			msg_r('.')
			from .fileutil import shred_file
			shred_file( f, verbose=self.cfg.verbose )
			count += 1

		def clean_dir(s_name):

			def clean_files(rawext,sigext):
				for f in s.dir.iterdir():
					if s.clean_all and (f.name.endswith(f'.{rawext}') or f.name.endswith(f'.{sigext}')):
						do_shred(f)
					elif f.name.endswith(f'.{sigext}'):
						raw = f.parent / ( f.name[:-len(sigext)] + rawext )
						if raw.is_file():
							do_shred(raw)

			s = getattr(Signable,s_name)(self)

			msg_r(f"Cleaning directory '{s.dir}'..")

			if s.dir.is_dir():
				clean_files( s.rawext, s.sigext )
				if hasattr(s,'subext'):
					clean_files( s.rawext, s.subext )
					clean_files( s.sigext, s.subext )

			msg('done' if s.dir.is_dir() else 'skipped (no dir)')

		count = 0

		for s_name in self.signables:
			clean_dir(s_name)

		bmsg(f'{count} file{suf(count)} shredded')

	def get_insert_status(self):
		return self.cfg.no_insert_check or self.dev_label_path.exists()

	async def main_loop(self):
		if not self.cfg.stealth_led:
			self.led.set('standby')
		threaded = self.cfg.test_suite_autosign_threaded
		n = 1 if threaded else 0
		prev_status = False
		while True:
			status = self.get_insert_status()
			if status and not prev_status:
				msg('Device insertion detected')
				await self.do_sign()
			prev_status = status
			if not n % 10:
				msg_r(f"\r{' '*17}\rWaiting")
			await asyncio.sleep(0.2 if threaded else 1)
			if not threaded:
				msg_r('.')
				n += 1

	def at_exit(self,exit_val,message=None):
		if message:
			msg(message)
		self.led.stop()
		sys.exit(0 if self.cfg.test_suite_autosign_threaded else int(exit_val))

	def init_exit_handler(self):

		def handler(arg1,arg2):
			self.at_exit(1,'\nCleaning up...')

		import signal
		signal.signal( signal.SIGTERM, handler )
		signal.signal( signal.SIGINT, handler )

	def init_led(self):
		from .led import LEDControl
		self.led = LEDControl(
			enabled = self.cfg.led,
			simulate = self.cfg.test_suite_autosign_led_simulate )
		self.led.set('off')
