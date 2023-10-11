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
autosign: Auto-sign MMGen transactions, message files and XMR wallet output files
"""

import sys,os,asyncio
from pathlib import Path
from subprocess import run,DEVNULL

from .cfg import Config
from .util import msg,msg_r,ymsg,rmsg,gmsg,bmsg,die,suf,fmt,fmt_list,async_run
from .color import yellow,red,orange
from .wallet import Wallet,get_wallet_cls
from .filename import find_file_in_dir
from .ui import keypress_confirm

class AutosignConfig(Config):
	_set_ok = ('usr_randchars','_proto','outdir','passwd_file')

class Signable:

	signables = ('transaction','message','xmr_transaction','xmr_wallet_outputs_file')

	class base:

		clean_all = False
		multiple_ok = True

		def __init__(self,parent):
			self.parent = parent
			self.cfg = parent.cfg
			self.dir = getattr(parent,self.dir_name)

		@property
		def unsigned(self):
			return self._unprocessed( '_unsigned', self.rawext, self.sigext )

		@property
		def unsubmitted(self):
			return self._unprocessed( '_unsubmitted', self.sigext, self.subext )

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

	class transaction(base):
		desc = 'transaction'
		rawext = 'rawtx'
		sigext = 'sigtx'
		dir_name = 'tx_dir'
		fail_msg = 'failed to sign'

		async def sign(self,f):
			from .tx import UnsignedTX
			tx1 = UnsignedTX( cfg=self.cfg, filename=f )
			if tx1.proto.sign_mode == 'daemon':
				from .rpc import rpc_init
				tx1.rpc = await rpc_init( self.cfg, tx1.proto, ignore_wallet=True )
			from .tx.sign import txsign
			tx2 = await txsign( self.cfg, tx1, self.parent.wallet_files[:], None, None )
			if tx2:
				tx2.file.write(ask_write=False)
				return tx2
			else:
				return False

		def print_summary(self,txs):

			if self.cfg.full_summary:
				bmsg('\nAutosign summary:\n')
				msg_r('\n'.join(tx.info.format(terse=True) for tx in txs))
				return

			def gen():
				for tx in txs:
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

	class xmr_signable(transaction): # virtual class

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

		async def sign(self,f):
			from .xmrwallet import MoneroWalletOps,xmrwallet_uargs
			wallet_idx = MoneroWalletOps.wallet.get_idx_from_fn(f)
			m = MoneroWalletOps.export_key_images(
				self.parent.xmrwallet_cfg,
				xmrwallet_uargs(
					infile  = str(self.parent.wallet_files[0]), # MMGen wallet file
					wallets = str(wallet_idx),
					spec    = None ),
			)
			obj = await m.main( f, wallet_idx, restart_daemon=self.need_daemon_restart(m,wallet_idx) )
			obj.write()
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
			await m.sign( wallet_files=self.parent.wallet_files[:] )
			m = SignedMsg( self.cfg, data=m.__dict__ )
			m.write_to_file(
				outdir = self.dir.resolve(),
				ask_overwrite = False )
			if m.data.get('failed_sids'):
				die('MsgFileFailedSID',f'Failed Seed IDs: {fmt_list(m.data["failed_sids"],fmt="bare")}')
			return m

		def print_summary(self,messages):
			gmsg('\nSigned message files:')
			for m in messages:
				gmsg('  ' + m.signed_filename)

		def gen_bad_list(self,bad_files):
			for f in bad_files:
				sigfile = f.parent / ( f.name[:-len(self.rawext)] + self.sigext )
				yield orange(sigfile.name) if sigfile.exists() else red(f.name)

class Autosign:

	dfl_mountpoint     = '/mnt/mmgen_autosign'
	dfl_wallet_dir     = '/dev/shm/autosign'
	old_dfl_mountpoint = '/mnt/tx'

	dfl_dev_disk_path = '/dev/disk/by-label/MMGEN_TX'
	fake_dev_disk_path = '/tmp/mmgen-test-suite-dev.disk.by-label.MMGEN_TX'

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

	have_msg_dir = False

	def __init__(self,cfg):

		self.cfg = cfg

		if cfg.mnemonic_fmt:
			if cfg.mnemonic_fmt not in self.mn_fmts:
				die(1,'{!r}: invalid mnemonic format (must be one of: {})'.format(
					cfg.mnemonic_fmt,
					fmt_list( self.mn_fmts, fmt='no_spc' ) ))

		self.dev_disk_path = Path(
			self.fake_dev_disk_path if cfg.test_suite_xmr_autosign else
			self.dfl_dev_disk_path )
		self.mountpoint = Path(cfg.mountpoint or self.dfl_mountpoint)
		self.wallet_dir = Path(cfg.wallet_dir or self.dfl_wallet_dir)

		self.tx_dir  = self.mountpoint / 'tx'
		self.msg_dir = self.mountpoint / 'msg'
		self.keyfile = self.mountpoint / 'autosign.key'

		cfg.outdir = str(self.tx_dir)
		cfg.passwd_file = str(self.keyfile)

		if any(k in cfg._uopts for k in ('help','longhelp')):
			return

		if 'coin' in cfg._uopts:
			die(1,'--coin option not supported with this command.  Use --coins instead')

		self.coins = cfg.coins.upper().split(',') if cfg.coins else []

		if cfg._args and cfg._args[0] == 'clean':
			return

		if cfg.xmrwallets and not 'XMR' in self.coins:
			self.coins.append('XMR')

		if not self.coins:
			ymsg('Warning: no coins specified, defaulting to BTC')
			self.coins = ['BTC']

		if 'XMR' in self.coins:
			self.xmr_dir = self.mountpoint / 'xmr'
			self.xmr_tx_dir = self.mountpoint / 'xmr' / 'tx'
			self.xmr_outputs_dir = self.mountpoint / 'xmr' / 'outputs'
			self.xmr_cur_wallet_idx = None

	async def check_daemons_running(self):
		from .protocol import init_proto
		for coin in self.coins:
			proto = init_proto( self.cfg,  coin, testnet=self.cfg.network=='testnet', need_amt=True )
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

	def do_mount(self,no_xmr_chk=False):

		from stat import S_ISDIR,S_IWUSR,S_IRUSR

		def check_dir(cdir):
			try:
				ds = cdir.stat()
				assert S_ISDIR(ds.st_mode), f"'{cdir}' is not a directory!"
				assert ds.st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR, f"'{cdir}' is not read/write for this user!"
			except:
				die(1,f"'{cdir}' missing or not read/writable by user!")

		if not self.mountpoint.is_dir():
			def do_die(m):
				die(1,'\n' + yellow(fmt(m.strip(),indent='  ')))
			if Path(self.old_dfl_mountpoint).is_dir():
				do_die(self.old_dfl_mountpoint_errmsg)
			else:
				do_die(self.mountpoint_errmsg_fs.format(self.mountpoint))

		if not self.mountpoint.is_mount():
			if run( ['mount',self.mountpoint], stderr=DEVNULL, stdout=DEVNULL ).returncode == 0:
				msg(f"Mounting '{self.mountpoint}'")
			elif not self.cfg.test_suite:
				die(1,f"Unable to mount device at '{self.mountpoint}'")

		self.have_msg_dir = self.msg_dir.is_dir()

		check_dir(self.tx_dir)

		if self.have_msg_dir:
			check_dir(self.msg_dir)

		if 'XMR' in self.coins and not no_xmr_chk:
			check_dir(self.xmr_tx_dir)

	def do_umount(self):
		if self.mountpoint.is_mount():
			run( ['sync'], check=True )
			msg(f"Unmounting '{self.mountpoint}'")
			run( ['umount',self.mountpoint], check=True )
		bmsg('It is now safe to extract the removable device')

	def decrypt_wallets(self):
		msg(f"Unlocking wallet{suf(self.wallet_files)} with key from '{self.cfg.passwd_file}'")
		fails = 0
		for wf in self.wallet_files:
			try:
				Wallet( self.cfg, wf, ignore_in_fmt=True )
			except SystemExit as e:
				if e.code != 0:
					fails += 1

		return False if fails else True

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
			msg(f'{len(good)} {target.desc}{suf(good)} signed')
			if bad:
				rmsg(f'{len(bad)} {target.desc}{suf(bad)} {target.fail_msg}')
			if good and not self.cfg.no_summary:
				target.print_summary(good)
			if bad:
				target.print_bad_list(bad)
			return not bad
		else:
			msg(f'No unsigned {target.desc}s')
			await asyncio.sleep(0.5)
			return True

	async def do_sign(self):
		if not self.cfg.stealth_led:
			self.led.set('busy')
		self.do_mount()
		key_ok = self.decrypt_wallets()
		if key_ok:
			if self.cfg.stealth_led:
				self.led.set('busy')
			ret1 = await self.sign_all('transaction')
			ret2 = await self.sign_all('message') if self.have_msg_dir else True
			# import XMR wallet outputs BEFORE signing transactions:
			ret3 = await self.sign_all('xmr_wallet_outputs_file') if 'XMR' in self.coins else True
			ret4 = await self.sign_all('xmr_transaction') if 'XMR' in self.coins else True
			ret = ret1 and ret2 and ret3 and ret4
			self.do_umount()
			self.led.set(('standby','off','error')[(not ret)*2 or bool(self.cfg.stealth_led)])
			return ret
		else:
			msg('Password is incorrect!')
			self.do_umount()
			if not self.cfg.stealth_led:
				self.led.set('error')
			return False

	def wipe_existing_key(self):
		try:
			self.keyfile.stat()
		except:
			pass
		else:
			from .fileutil import shred_file
			msg(f"\nShredding existing key '{self.keyfile}'")
			shred_file( self.keyfile, verbose=self.cfg.verbose )

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
		self.do_mount(no_xmr_chk=True)
		self.wipe_existing_key()
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
		ss_out = Wallet( self.cfg, ss=ss_in )
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
				'outdir': str(self.xmr_dir), # required by vkal.write()
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

		import shutil
		try:
			shutil.rmtree(self.xmr_outputs_dir)
		except:
			pass

		self.xmr_outputs_dir.mkdir(parents=True)

		self.xmr_tx_dir.mkdir(exist_ok=True)

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

			s = getattr(Signable,s_name)(asi)

			msg_r(f"Cleaning directory '{s.dir}'..")

			if s.dir.is_dir():
				clean_files( s.rawext, s.sigext )
				if hasattr(s,'subext'):
					clean_files( s.rawext, s.subext )
					clean_files( s.sigext, s.subext )

			msg('done' if s.dir.is_dir() else 'skipped (no dir)')

		asi = get_autosign_obj( self.cfg, 'btc,xmr' )
		count = 0

		for s_name in Signable.signables:
			clean_dir(s_name)

		bmsg(f'{count} file{suf(count)} shredded')

	def get_insert_status(self):
		if self.cfg.no_insert_check:
			return True
		try:
			self.dev_disk_path.stat()
		except:
			return False
		else:
			return True

	async def do_loop(self):
		if not self.cfg.stealth_led:
			self.led.set('standby')
		testing_xmr = self.cfg.test_suite_xmr_autosign
		if testing_xmr:
			msg('Waiting for fake device insertion')
		n = 1 if testing_xmr else 0
		prev_status = False
		while True:
			status = self.get_insert_status()
			if status and not prev_status:
				msg('Device insertion detected')
				await self.do_sign()
				if testing_xmr:
					if self.dev_disk_path.exists():
						self.dev_disk_path.unlink()
			prev_status = status
			if not n % 10:
				msg_r(f"\r{' '*17}\rWaiting")
			await asyncio.sleep(1)
			if not testing_xmr:
				msg_r('.')
				n += 1

	def at_exit(self,exit_val,message=None):
		if message:
			msg(message)
		self.led.stop()
		sys.exit(0 if self.cfg.test_suite_xmr_autosign else int(exit_val))

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

def get_autosign_obj(cfg,coins=None):
	return Autosign(
		AutosignConfig({
			'mountpoint': cfg.autosign_mountpoint or cfg.mountpoint,
			'test_suite': cfg.test_suite,
			'coins': coins if isinstance(coins,str) else ','.join(coins) if coins else 'btc',
		})
	)
