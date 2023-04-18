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
autosign: Auto-sign MMGen transactions and message files
"""

import sys,os,asyncio
from subprocess import run,PIPE,DEVNULL
from collections import namedtuple

from .cfg import Config
from .util import msg,msg_r,ymsg,rmsg,gmsg,bmsg,die,suf,fmt,fmt_list
from .color import yellow,red,orange
from .wallet import Wallet

class AutosignConfig(Config):
	_set_ok = ('usr_randchars','_proto','outdir','passwd_file')

class Signable:

	class base:

		def __init__(self,parent):
			self.parent = parent
			self.cfg = parent.cfg
			self.dir = getattr(parent,self.dir_name)

		@property
		def unsigned(self):
			if not hasattr(self,'_unsigned'):
				dirlist = tuple(os.scandir(self.dir))
				names = tuple(f.name for f in dirlist)
				self._unsigned = tuple(f for f in dirlist
					if f.name.endswith('.'+self.rawext)
						and f.name[:-len(self.rawext)]+self.sigext not in names)
			return self._unsigned

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
			tx1 = UnsignedTX( cfg=self.cfg, filename=f.path )
			if tx1.proto.sign_mode == 'daemon':
				from .rpc import rpc_init
				tx1.rpc = await rpc_init( self.cfg, tx1.proto )
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
				yield red(f.path)

	class message(base):
		desc = 'message file'
		rawext = 'rawmsg.json'
		sigext = 'sigmsg.json'
		dir_name = 'msg_dir'
		fail_msg = 'failed to sign or signed incompletely'

		async def sign(self,f):
			from .msg import UnsignedMsg,SignedMsg
			m = UnsignedMsg( self.cfg, infile=f.path )
			await m.sign( wallet_files=self.parent.wallet_files[:] )
			m = SignedMsg( self.cfg, data=m.__dict__ )
			m.write_to_file(
				outdir = os.path.abspath(self.dir),
				ask_overwrite = False )
			if m.data.get('failed_sids'):
				die('MsgFileFailedSID',f'Failed Seed IDs: {fmt_list(m.data["failed_sids"],fmt="bare")}')
			return m

		def print_summary(self,messages):
			gmsg('\nSigned message files:')
			for m in messages:
				gmsg('  ' + os.path.join( self.dir, m.signed_filename ))

		def gen_bad_list(self,bad_files):
			for f in bad_files:
				sigfile = f.path[:-len(self.rawext)] + self.sigext
				yield orange(sigfile) if os.path.exists(sigfile) else red(f.path)

class Autosign:

	dfl_mountpoint = os.path.join(os.sep,'mnt','mmgen_autosign')
	dfl_wallet_dir = os.path.join(os.sep,'dev','shm','autosign')
	disk_label_dir = os.path.join(os.sep,'dev','disk','by-label')
	part_label = 'MMGEN_TX'

	old_dfl_mountpoint = os.path.join(os.sep,'mnt','tx')
	old_dfl_mountpoint_errmsg = f"""
		Mountpoint {old_dfl_mountpoint!r} is no longer supported!
		Please rename {old_dfl_mountpoint!r} to {dfl_mountpoint!r}
		and update your fstab accordingly.
	"""
	mountpoint_errmsg_fs = """
		Mountpoint {!r} does not exist or does not point
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

		if cfg.mnemonic_fmt:
			if cfg.mnemonic_fmt not in self.mn_fmts:
				die(1,'{!r}: invalid mnemonic format (must be one of: {})'.format(
					cfg.mnemonic_fmt,
					fmt_list( self.mn_fmts, fmt='no_spc' ) ))

		self.cfg = cfg

		self.mountpoint = cfg.mountpoint or self.dfl_mountpoint
		self.wallet_dir = cfg.wallet_dir or self.dfl_wallet_dir

		self.tx_dir  = os.path.join( self.mountpoint, 'tx' )
		self.msg_dir = os.path.join( self.mountpoint, 'msg' )
		self.keyfile = os.path.join( self.mountpoint, 'autosign.key' )

		cfg.outdir = self.tx_dir
		cfg.passwd_file = self.keyfile

		if 'coin' in cfg._uopts and not any(k in cfg._uopts for k in ('help','longhelp')):
			die(1,'--coin option not supported with this command.  Use --coins instead')

		self.coins = cfg.coins.upper().split(',') if cfg.coins else []

		if not self.coins:
			ymsg('Warning: no coins specified, defaulting to BTC')
			self.coins = ['BTC']

	async def check_daemons_running(self):
		from .protocol import init_proto
		for coin in self.coins:
			proto = init_proto( self.cfg,  coin, testnet=self.cfg.network=='testnet', need_amt=True )
			if proto.sign_mode == 'daemon':
				self.cfg._util.vmsg(f'Checking {coin} daemon')
				from .rpc import rpc_init
				from .exception import SocketError
				try:
					await rpc_init( self.cfg, proto )
				except SocketError as e:
					die(2,f'{coin} daemon not running or not listening on port {proto.rpc_port}')

	@property
	def wallet_files(self):

		if not hasattr(self,'_wallet_files'):

			try:
				dirlist = os.listdir(self.wallet_dir)
			except:
				die(1,f'Cannot open wallet directory {self.wallet_dir!r}. Did you run ‘mmgen-autosign setup’?')

			fns = [fn for fn in dirlist if fn.endswith('.mmdat')]
			if fns:
				self._wallet_files = [os.path.join(self.wallet_dir,fn) for fn in fns]
			else:
				die(1,'No wallet files present!')

		return self._wallet_files

	def do_mount(self):

		from stat import S_ISDIR,S_IWUSR,S_IRUSR

		def check_dir(cdir):
			try:
				ds = os.stat(cdir)
				assert S_ISDIR(ds.st_mode), f'{cdir!r} is not a directory!'
				assert ds.st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR, f'{cdir!r} is not read/write for this user!'
			except:
				die(1,f'{cdir!r} missing or not read/writable by user!')

		if not os.path.isdir(self.mountpoint):
			def do_die(m):
				die(1,'\n' + yellow(fmt(m.strip(),indent='  ')))
			if os.path.isdir(self.old_dfl_mountpoint):
				do_die(self.old_dfl_mountpoint_errmsg)
			else:
				do_die(self.mountpoint_errmsg_fs.format(self.mountpoint))

		if not os.path.ismount(self.mountpoint):
			if run( ['mount',self.mountpoint], stderr=DEVNULL, stdout=DEVNULL ).returncode == 0:
				msg(f'Mounting {self.mountpoint!r}')

		self.have_msg_dir = os.path.isdir(self.msg_dir)

		check_dir(self.tx_dir)

		if self.have_msg_dir:
			check_dir(self.msg_dir)

	def do_umount(self):
		if os.path.ismount(self.mountpoint):
			run( ['sync'], check=True )
			msg(f'Unmounting {self.mountpoint}')
			run( ['umount',self.mountpoint], check=True )

	def decrypt_wallets(self):
		msg(f'Unlocking wallet{suf(self.wallet_files)} with key from {self.cfg.passwd_file!r}')
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
			for f in target.unsigned:
				ret = None
				try:
					ret = await target.sign(f)
				except Exception as e:
					ymsg(f'An error occurred with {target.desc} {f.name!r}:\n    {type(e).__name__}: {e!s}')
				except:
					ymsg(f'An error occurred with {target.desc} {f.name!r}')
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
			ret = ret1 and ret2
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
		try: os.stat(self.keyfile)
		except: pass
		else:
			from .fileutil import shred_file
			msg(f'\nShredding existing key {self.keyfile!r}')
			shred_file( self.keyfile, verbose=self.cfg.verbose )

	def create_key(self):
		kdata = os.urandom(32).hex()
		desc = f'key file {self.keyfile!r}'
		msg('Creating ' + desc)
		try:
			with open(self.keyfile,'w') as fp:
				fp.write(kdata+'\n')
			os.chmod(self.keyfile,0o400)
			msg('Wrote ' + desc)
		except:
			die(2,'Unable to write ' + desc)

	def gen_key(self,no_unmount=False):
		self.create_wallet_dir()
		if not self.get_insert_status():
			die(1,'Removable device not present!')
		self.do_mount()
		self.wipe_existing_key()
		self.create_key()
		if not no_unmount:
			self.do_umount()

	def remove_wallet_dir(self):
		msg(f'Deleting {self.wallet_dir!r}')
		import shutil
		try: shutil.rmtree(self.wallet_dir)
		except: pass

	def create_wallet_dir(self):
		try: os.mkdir(self.wallet_dir)
		except: pass
		try: os.stat(self.wallet_dir)
		except: die(2,f'Unable to create wallet directory {self.wallet_dir!r}')

	def setup(self):
		self.remove_wallet_dir()
		self.gen_key(no_unmount=True)
		ss_in  = Wallet( self.cfg, in_fmt=self.mn_fmts[self.cfg.mnemonic_fmt or self.dfl_mn_fmt] )
		ss_out = Wallet( self.cfg, ss=ss_in )
		ss_out.write_to_file( desc='autosign wallet', outdir=self.wallet_dir )

	def get_insert_status(self):
		if self.cfg.no_insert_check:
			return True
		try: os.stat(os.path.join( self.disk_label_dir, self.part_label ))
		except: return False
		else: return True

	async def do_loop(self):
		n,prev_status = 0,False
		if not self.cfg.stealth_led:
			self.led.set('standby')
		while True:
			status = self.get_insert_status()
			if status and not prev_status:
				msg('Device insertion detected')
				await self.do_sign()
			prev_status = status
			if not n % 10:
				msg_r(f"\r{' '*17}\rWaiting")
				sys.stderr.flush()
			await asyncio.sleep(1)
			msg_r('.')
			n += 1

	def at_exit(self,exit_val,message=None):
		if message:
			msg(message)
		self.led.stop()
		sys.exit(int(exit_val))

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
			simulate = os.getenv('MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE') )
		self.led.set('off')
