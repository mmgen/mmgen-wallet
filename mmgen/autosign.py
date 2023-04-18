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

from .util import msg,msg_r,ymsg,rmsg,gmsg,bmsg,die,suf,fmt_list
from .color import yellow,red,orange
from .wallet import Wallet

class Autosign:

	dfl_mountpoint = os.path.join(os.sep,'mnt','tx')
	wallet_dir     = os.path.join(os.sep,'dev','shm','autosign')
	disk_label_dir = os.path.join(os.sep,'dev','disk','by-label')
	part_label = 'MMGEN_TX'

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

		self.tx_dir  = os.path.join( self.mountpoint, 'tx' )
		self.msg_dir = os.path.join( self.mountpoint, 'msg' )
		self.keyfile = os.path.join( self.mountpoint, 'autosign.key' )

		cfg.outdir = self.tx_dir
		cfg.passwd_file = self.keyfile

	async def check_daemons_running(self):

		if 'coin' in self.cfg._uopts:
			die(1,'--coin option not supported with this command.  Use --coins instead')

		if self.cfg.coins:
			coins = self.cfg.coins.upper().split(',')
		else:
			ymsg('Warning: no coins specified, defaulting to BTC')
			coins = ['BTC']

		from .protocol import init_proto
		for coin in coins:
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

		if not os.path.ismount(self.mountpoint):
			if run( ['mount',self.mountpoint], stderr=DEVNULL, stdout=DEVNULL ).returncode == 0:
				msg(f'Mounting {self.mountpoint}')

		self.have_msg_dir = os.path.isdir(self.msg_dir)

		from stat import S_ISDIR,S_IWUSR,S_IRUSR 
		for cdir in [self.tx_dir] + ([self.msg_dir] if self.have_msg_dir else []):
			try:
				ds = os.stat(cdir)
				assert S_ISDIR(ds.st_mode), f'{cdir!r} is not a directory!'
				assert ds.st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR, f'{cdir!r} is not read/write for this user!'
			except:
				die(1,f'{cdir!r} missing or not read/writable by user!')

	def do_umount(self):
		if os.path.ismount(self.mountpoint):
			run( ['sync'], check=True )
			msg(f'Unmounting {self.mountpoint}')
			run( ['umount',self.mountpoint], check=True )

	async def sign_object(self,d,fn):
		from .tx import UnsignedTX
		from .tx.sign import txsign
		from .rpc import rpc_init
		try:
			if d.desc == 'transaction':
				tx1 = UnsignedTX( cfg=self.cfg, filename=fn )
				if tx1.proto.sign_mode == 'daemon':
					tx1.rpc = await rpc_init( self.cfg, tx1.proto )
				tx2 = await txsign( self.cfg, tx1, self.wallet_files[:], None, None )
				if tx2:
					tx2.file.write(ask_write=False)
					return tx2
				else:
					return False
			elif d.desc == 'message file':
				from .msg import UnsignedMsg,SignedMsg
				m = UnsignedMsg( self.cfg, infile=fn )
				await m.sign( wallet_files=self.wallet_files[:] )
				m = SignedMsg( self.cfg, data=m.__dict__ )
				m.write_to_file(
					outdir = os.path.abspath(self.msg_dir),
					ask_overwrite = False )
				if m.data.get('failed_sids'):
					die('MsgFileFailedSID',f'Failed Seed IDs: {fmt_list(m.data["failed_sids"],fmt="bare")}')
				return m
		except Exception as e:
			ymsg(f'An error occurred with {d.desc} {fn!r}:\n    {e!s}')
			return False
		except:
			ymsg(f'An error occurred with {d.desc} {fn!r}')
			return False

	async def sign(self,target):

		_td = namedtuple('tdata',['desc','rawext','sigext','dir','fail_desc'])

		d = {
			'msg': _td('message file', 'rawmsg.json', 'sigmsg.json', self.msg_dir, 'sign or signed incompletely'),
			'tx':  _td('transaction',  'rawtx',       'sigtx',       self.tx_dir,  'sign'),
		}[target]

		raw      = [fn[:-len(d.rawext)] for fn in os.listdir(d.dir) if fn.endswith('.'+d.rawext)]
		signed   = [fn[:-len(d.sigext)] for fn in os.listdir(d.dir) if fn.endswith('.'+d.sigext)]
		unsigned = [os.path.join( d.dir, fn+d.rawext ) for fn in raw if fn not in signed]

		if unsigned:
			ok = []
			bad = []
			for fn in unsigned:
				ret = await self.sign_object(d,fn)
				if ret:
					ok.append(ret)
				else:
					bad.append(fn)
				self.cfg._util.qmsg('')
			await asyncio.sleep(0.3)
			msg(f'{len(ok)} {d.desc}{suf(ok)} signed')
			if bad:
				rmsg(f'{len(bad)} {d.desc}{suf(bad)} failed to {d.fail_desc}')
			if ok and not self.cfg.no_summary:
				self.print_summary(d,ok)
			if bad:
				msg('')
				rmsg(f'Failed {d.desc}s:')
				def gen_bad_disp():
					if d.desc == 'transaction':
						for fn in sorted(bad):
							yield red(fn)
					elif d.desc == 'message file':
						for rawfn in sorted(bad):
							sigfn = rawfn[:-len(d.rawext)] + d.sigext
							yield orange(sigfn) if os.path.exists(sigfn) else red(rawfn)
				msg('  {}\n'.format( '\n  '.join(gen_bad_disp()) ))
			return False if bad else True
		else:
			msg(f'No unsigned {d.desc}s')
			await asyncio.sleep(0.5)
			return True

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

	def print_summary(self,d,signed_objects):

		if d.desc == 'message file':
			gmsg('\nSigned message files:')
			for m in signed_objects:
				gmsg('  ' + os.path.join( self.msg_dir, m.signed_filename ))
			return

		if self.cfg.full_summary:
			bmsg('\nAutosign summary:\n')
			def gen():
				for tx in signed_objects:
					yield tx.info.format(terse=True)
			msg_r('\n'.join(gen()))
			return

		def gen():
			for tx in signed_objects:
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

	async def do_sign(self):
		if not self.cfg.stealth_led:
			self.led.set('busy')
		self.do_mount()
		key_ok = self.decrypt_wallets()
		if key_ok:
			if self.cfg.stealth_led:
				self.led.set('busy')
			ret1 = await self.sign('tx')
			ret2 = await self.sign('msg') if self.have_msg_dir else True
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
