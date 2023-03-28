#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
mmgen-autosign: Auto-sign MMGen transactions and message files
"""

import sys,os,asyncio,signal,shutil
from subprocess import run,PIPE,DEVNULL
from collections import namedtuple
from stat import *

import mmgen.opts as opts
from .util import msg,msg_r,ymsg,rmsg,gmsg,bmsg,die,suf,fmt_list,async_run,exit_if_mswin
from .color import yellow,red,orange

mountpoint   = '/mnt/tx'
tx_dir       = '/mnt/tx/tx'
msg_dir      = '/mnt/tx/msg'
part_label   = 'MMGEN_TX'
wallet_dir   = '/dev/shm/autosign'
mn_fmts      = {
	'mmgen': 'words',
	'bip39': 'bip39',
}
mn_fmt_dfl   = 'mmgen'

opts_data = {
	'sets': [('stealth_led', True, 'led', True)],
	'text': {
		'desc': 'Auto-sign MMGen transactions and message files',
		'usage':'[opts] [command]',
		'options': f"""
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-c, --coins=c         Coins to sign for (comma-separated list)
-I, --no-insert-check Don’t check for device insertion
-l, --led             Use status LED to signal standby, busy and error
-m, --mountpoint=M    Specify an alternate mountpoint 'M' (default: {mountpoint!r})
-M, --mnemonic-fmt=F  During setup, prompt for mnemonic seed phrase of format
                      'F' (choices: {fmt_list(mn_fmts,fmt='no_spc')}; default: {mn_fmt_dfl!r})
-n, --no-summary      Don’t print a transaction summary
-s, --stealth-led     Stealth LED mode - signal busy and error only, and only
                      after successful authorization.
-S, --full-summary    Print a full summary of each signed transaction after
                      each autosign run. The default list of non-MMGen outputs
                      will not be printed.
-q, --quiet           Produce quieter output
-v, --verbose         Produce more verbose output
""",
	'notes': f"""

                              COMMANDS

gen_key - generate the wallet encryption key and copy it to {mountpoint!r}
setup   - generate the wallet encryption key and wallet
wait    - start in loop mode: wait-mount-sign-unmount-wait


                             USAGE NOTES

If invoked with no command, the program mounts a removable device containing
unsigned MMGen transactions and/or message files, signs them, unmounts the
removable device and exits.

If invoked with 'wait', the program waits in a loop, mounting the removable
device, performing signing operations and unmounting the device every time it
is inserted.

On supported platforms (currently Orange Pi, Rock Pi and Raspberry Pi boards),
the status LED indicates whether the program is busy or in standby mode, i.e.
ready for device insertion or removal.

The removable device must have a partition labeled MMGEN_TX with a user-
writable root directory and a directory named '/tx', where unsigned MMGen
transactions are placed. Optionally, the directory '/msg' may also be created
and unsigned message files created by `mmgen-msg` placed in this directory.

On the signing machine the mount point {mountpoint!r} must exist and /etc/fstab
must contain the following entry:

    LABEL='MMGEN_TX' /mnt/tx auto noauto,user 0 0

Transactions are signed with a wallet on the signing machine (in the directory
{wallet_dir!r}) encrypted with a 64-character hexadecimal password saved
in the file `autosign.key` in the root of the removable device partition.

The password and wallet can be created in one operation by invoking the
command with 'setup' with the removable device inserted.  In this case, the
user will be prompted for a seed mnemonic.

Alternatively, the password and wallet can be created separately by first
invoking the command with 'gen_key' and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -r0 -q -iwords -d{wallet_dir} -p1 -P/mnt/tx/autosign.key -Llabel

Note that the hash preset must be '1'.  Multiple wallets are permissible.

For good security, it's advisable to re-generate a new wallet and key for
each signing session.

This command is currently available only on Linux-based platforms.
"""
	}
}

cfg = opts.init(
	opts_data,
	add_opts = ['outdir','passwd_file'], # in _set_ok, so must be set
	init_opts = {
		'quiet': True,
		'out_fmt': 'wallet',
		'usr_randchars': 0,
		'hash_preset': '1',
		'label': 'Autosign Wallet',
	})

cmd_args = cfg._args

type(cfg)._set_ok += ('outdir','passwd_file')

exit_if_mswin('autosigning')

if cfg.mnemonic_fmt:
	if cfg.mnemonic_fmt not in mn_fmts:
		die(1,'{!r}: invalid mnemonic format (must be one of: {})'.format(
			cfg.mnemonic_fmt,
			fmt_list(mn_fmts,fmt='no_spc') ))

from .wallet import Wallet
from .tx import UnsignedTX
from .tx.sign import txsign
from .protocol import init_proto
from .rpc import rpc_init

if cfg.mountpoint:
	mountpoint = cfg.mountpoint

keyfile = os.path.join(mountpoint,'autosign.key')
msg_dir = os.path.join(mountpoint,'msg')
tx_dir  = os.path.join(mountpoint,'tx')

cfg.outdir = tx_dir
cfg.passwd_file = keyfile

async def check_daemons_running():
	if cfg.coin != type(cfg).coin:
		die(1,'--coin option not supported with this command.  Use --coins instead')
	if cfg.coins:
		coins = cfg.coins.upper().split(',')
	else:
		ymsg('Warning: no coins specified, defaulting to BTC')
		coins = ['BTC']

	for coin in coins:
		proto = init_proto( cfg,  coin, testnet=cfg.network=='testnet', need_amt=True )
		if proto.sign_mode == 'daemon':
			cfg._util.vmsg(f'Checking {coin} daemon')
			from .exception import SocketError
			try:
				await rpc_init(cfg,proto)
			except SocketError as e:
				die(2,f'{coin} daemon not running or not listening on port {proto.rpc_port}')

def get_wallet_files():
	try:
		dlist = os.listdir(wallet_dir)
	except:
		die(1,f"Cannot open wallet directory {wallet_dir!r}. Did you run 'mmgen-autosign setup'?")

	fns = [x for x in dlist if x.endswith('.mmdat')]
	if fns:
		return [os.path.join(wallet_dir,w) for w in fns]
	else:
		die(1,'No wallet files present!')

def do_mount():
	if not os.path.ismount(mountpoint):
		if run(['mount',mountpoint],stderr=DEVNULL,stdout=DEVNULL).returncode == 0:
			msg(f'Mounting {mountpoint}')
	global have_msg_dir
	have_msg_dir = os.path.isdir(msg_dir)
	for cdir in [tx_dir] + ([msg_dir] if have_msg_dir else []):
		try:
			ds = os.stat(cdir)
			assert S_ISDIR(ds.st_mode), f'{cdir!r} is not a directory!'
			assert ds.st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR, f'{cdir!r} is not read/write for this user!'
		except:
			die(1,f'{cdir!r} missing or not read/writable by user!')

def do_umount():
	if os.path.ismount(mountpoint):
		run(['sync'],check=True)
		msg(f'Unmounting {mountpoint}')
		run(['umount',mountpoint],check=True)

async def sign_object(d,fn):
	try:
		if d.desc == 'transaction':
			tx1 = UnsignedTX(cfg=cfg,filename=fn)
			if tx1.proto.sign_mode == 'daemon':
				tx1.rpc = await rpc_init(cfg,tx1.proto)
			tx2 = await txsign(cfg,tx1,wfs[:],None,None)
			if tx2:
				tx2.file.write(ask_write=False)
				return tx2
			else:
				return False
		elif d.desc == 'message file':
			from .msg import UnsignedMsg,SignedMsg
			m = UnsignedMsg(cfg,infile=fn)
			await m.sign(wallet_files=wfs[:])
			m = SignedMsg(cfg,data=m.__dict__)
			m.write_to_file(
				outdir = os.path.abspath(msg_dir),
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

async def sign(target):
	td = namedtuple('tdata',['desc','rawext','sigext','dir','fail_desc'])
	d = {
		'msg': td('message file', 'rawmsg.json', 'sigmsg.json', msg_dir, 'sign or signed incompletely'),
		'tx':  td('transaction',  'rawtx',       'sigtx',       tx_dir,  'sign'),
	}[target]

	raw      = [fn[:-len(d.rawext)] for fn in os.listdir(d.dir) if fn.endswith('.'+d.rawext)]
	signed   = [fn[:-len(d.sigext)] for fn in os.listdir(d.dir) if fn.endswith('.'+d.sigext)]
	unsigned = [os.path.join(d.dir,fn+d.rawext) for fn in raw if fn not in signed]

	if unsigned:
		ok,bad = ([],[])
		for fn in unsigned:
			ret = await sign_object(d,fn)
			if ret:
				ok.append(ret)
			else:
				bad.append(fn)
			cfg._util.qmsg('')
		await asyncio.sleep(0.3)
		msg(f'{len(ok)} {d.desc}{suf(ok)} signed')
		if bad:
			rmsg(f'{len(bad)} {d.desc}{suf(bad)} failed to {d.fail_desc}')
		if ok and not cfg.no_summary:
			print_summary(d,ok)
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

def decrypt_wallets():
	msg(f'Unlocking wallet{suf(wfs)} with key from {cfg.passwd_file!r}')
	fails = 0
	for wf in wfs:
		try:
			Wallet(cfg,wf,ignore_in_fmt=True)
		except SystemExit as e:
			if e.code != 0:
				fails += 1

	return False if fails else True

def print_summary(d,signed_objects):

	if d.desc == 'message file':
		gmsg('\nSigned message files:')
		for m in signed_objects:
			gmsg('  ' + os.path.join(msg_dir,m.signed_filename) )
		return

	if cfg.full_summary:
		bmsg('\nAutosign summary:\n')
		def gen():
			for tx in signed_objects:
				yield tx.info.format(terse=True)
		msg_r(''.join(gen()))
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
						tx.txid.fmt(width=t_wid,color=True) if nm is non_mmgen[0] else ' '*t_wid,
						nm.addr.fmt(width=a_wid,color=True),
						nm.amt.hl() + ' ' + yellow(tx.coin))

		msg('\n'.join(gen()))
	else:
		msg('No non-MMGen outputs')

async def do_sign():
	if not cfg.stealth_led:
		led.set('busy')
	do_mount()
	key_ok = decrypt_wallets()
	if key_ok:
		if cfg.stealth_led:
			led.set('busy')
		ret1 = await sign('tx')
		ret2 = await sign('msg') if have_msg_dir else True
		ret = ret1 and ret2
		do_umount()
		led.set(('standby','off','error')[(not ret)*2 or bool(cfg.stealth_led)])
		return ret
	else:
		msg('Password is incorrect!')
		do_umount()
		if not cfg.stealth_led:
			led.set('error')
		return False

def wipe_existing_key():
	try: os.stat(keyfile)
	except: pass
	else:
		from .fileutil import shred_file
		msg(f'\nShredding existing key {keyfile!r}')
		shred_file( keyfile, verbose=cfg.verbose )

def create_key():
	kdata = os.urandom(32).hex()
	desc = f'key file {keyfile!r}'
	msg('Creating ' + desc)
	try:
		with open(keyfile,'w') as fp:
			fp.write(kdata+'\n')
		os.chmod(keyfile,0o400)
		msg('Wrote ' + desc)
	except:
		die(2,'Unable to write ' + desc)

def gen_key(no_unmount=False):
	create_wallet_dir()
	if not get_insert_status():
		die(1,'Removable device not present!')
	do_mount()
	wipe_existing_key()
	create_key()
	if not no_unmount:
		do_umount()

def remove_wallet_dir():
	msg(f'Deleting {wallet_dir!r}')
	try: shutil.rmtree(wallet_dir)
	except: pass

def create_wallet_dir():
	try: os.mkdir(wallet_dir)
	except: pass
	try: os.stat(wallet_dir)
	except: die(2,f'Unable to create wallet directory {wallet_dir!r}')

def setup():
	remove_wallet_dir()
	gen_key(no_unmount=True)
	ss_in = Wallet(cfg,in_fmt=mn_fmts[cfg.mnemonic_fmt or mn_fmt_dfl])
	ss_out = Wallet(cfg,ss=ss_in)
	ss_out.write_to_file(desc='autosign wallet',outdir=wallet_dir)

def get_insert_status():
	if cfg.no_insert_check:
		return True
	try: os.stat(os.path.join('/dev/disk/by-label',part_label))
	except: return False
	else: return True

async def do_loop():
	n,prev_status = 0,False
	if not cfg.stealth_led:
		led.set('standby')
	while True:
		status = get_insert_status()
		if status and not prev_status:
			msg('Device insertion detected')
			await do_sign()
		prev_status = status
		if not n % 10:
			msg_r(f"\r{' '*17}\rWaiting")
			sys.stderr.flush()
		await asyncio.sleep(1)
		msg_r('.')
		n += 1

if len(cmd_args) not in (0,1):
	opts.usage()

if len(cmd_args) == 1:
	cmd = cmd_args[0]
	if cmd in ('gen_key','setup'):
		(gen_key if cmd == 'gen_key' else setup)()
		sys.exit(0)
	elif cmd != 'wait':
		die(1,f'{cmd!r}: unrecognized command')

wfs = get_wallet_files()

def at_exit(exit_val,message='\nCleaning up...'):
	if message:
		msg(message)
	led.stop()
	sys.exit(exit_val)

def handler(a,b):
	at_exit(1)

signal.signal(signal.SIGTERM,handler)
signal.signal(signal.SIGINT,handler)

from .led import LEDControl
led = LEDControl(
	enabled = cfg.led,
	simulate = os.getenv('MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE') )
led.set('off')

async def main():
	await check_daemons_running()

	if len(cmd_args) == 0:
		ret = await do_sign()
		at_exit(int(not ret),message='')
	elif cmd_args[0] == 'wait':
		await do_loop()

async_run(main())
