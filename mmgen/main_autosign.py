#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
mmgen-autosign: Auto-sign MMGen transactions
"""

import sys,os,subprocess,time,signal,shutil
from stat import *

mountpoint   = u'/mnt/tx'
tx_dir       = u'/mnt/tx/tx'
part_label   = u'MMGEN_TX'
wallet_dir   = u'/dev/shm/autosign'
key_fn       = u'autosign.key'

no_daemon_coins = ('ETH',)

from mmgen.common import *
prog_name = os.path.basename(sys.argv[0])
opts_data = lambda: {
	'desc': 'Auto-sign MMGen transactions',
	'usage':'[opts] [command]',
	'options': """
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-c, --coins=c       Coins to sign for (comma-separated list)
-l, --led           Use status LED to signal standby, busy and error
-m, --mountpoint=m  Specify an alternate mountpoint (default: '{mp}')
-s, --stealth-led   Stealth LED mode - signal busy and error only, and only
                    after successful authorization.
-q, --quiet         Produce quieter output
-v, --verbose       Produce more verbose output
""".format(mp=mountpoint),
	'notes': """

                              COMMANDS

gen_key - generate the wallet encryption key and copy it to '{td}'
setup   - generate the wallet encryption key and wallet
wait    - start in loop mode: wait-mount-sign-unmount-wait


                             USAGE NOTES

If invoked with no command, the program mounts a removable device containing
MMGen transactions, signs any unsigned transactions, unmounts the removable
device and exits.

If invoked with 'wait', the program waits in a loop, mounting, signing and
unmounting every time the removable device is inserted.

On supported platforms (currently Orange Pi and Raspberry Pi boards), the
status LED indicates whether the program is busy or in standby mode, i.e.
ready for device insertion or removal.

The removable device must have a partition labeled MMGEN_TX and a user-
writable directory '/tx', where unsigned MMGen transactions are placed.

On the signing machine the mount point '{mp}' must exist and /etc/fstab
must contain the following entry:

    LABEL='MMGEN_TX' /mnt/tx auto noauto,user 0 0

Transactions are signed with a wallet on the signing machine (in the directory
'{wd}') encrypted with a 64-character hexadecimal password on the
removable device.

The password and wallet can be created in one operation by invoking the
command with 'setup' with the removable device inserted.  The user will be
prompted for a seed mnemonic.

Alternatively, the password and wallet can be created separately by first
invoking the command with 'gen_key' and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -r0 -q -iwords -d{wd} -p1 -P{td}/{kf} -Llabel

Note that the hash preset must be '1'.  Multiple wallets are permissible.

For good security, it's advisable to re-generate a new wallet and key for
each signing session.

This command is currently available only on Linux-based platforms.
""".format(pnm=prog_name,wd=wallet_dir,td=tx_dir,kf=key_fn,mp=mountpoint)
}

cmd_args = opts.init(opts_data,add_opts=['mmgen_keys_from_file','in_fmt'])

import mmgen.tx
from mmgen.txsign import txsign
from mmgen.protocol import CoinProtocol,init_coin

if opt.stealth_led: opt.led = True

if opt.mountpoint: mountpoint = opt.mountpoint # TODO: make global
opt.outdir = tx_dir = os.path.join(mountpoint,'tx')

def check_daemons_running():
	if opt.coin:
		die(1,'--coin option not supported with this command.  Use --coins instead')
	if opt.coins:
		coins = opt.coins.upper().split(',')
	else:
		ymsg('Warning: no coins specified, so defaulting to BTC only')
		coins = ['BTC']

	for coin in coins:
		if coin in no_daemon_coins: continue
		g.proto = CoinProtocol(coin,g.testnet)
		vmsg('Checking {} daemon'.format(coin))
		try:
			rpc_init(reinit=True)
			g.rpch.getbalance()
		except SystemExit as e:
			if e[0] != 0:
				ydie(1,'{} daemon not running or not listening on port {}'.format(coin,g.proto.rpc_port))

def get_wallet_files():
	wfs = filter(lambda x: x[-6:] == '.mmdat',os.listdir(wallet_dir))
	if not wfs:
		die(1,'No wallet files present!')
	return [os.path.join(wallet_dir,w) for w in wfs]

def do_mount():
	if not os.path.ismount(mountpoint):
		if subprocess.Popen(['mount',mountpoint],stderr=subprocess.PIPE,stdout=subprocess.PIPE).wait() == 0:
			msg('Mounting '+mountpoint)
	try:
		ds = os.stat(tx_dir)
		assert S_ISDIR(ds.st_mode)
		assert ds.st_mode & S_IWUSR|S_IRUSR == S_IWUSR|S_IRUSR
	except:
		die(1,'{} missing, or not read/writable by user!'.format(tx_dir))

def do_umount():
	if os.path.ismount(mountpoint):
		subprocess.call(['sync'])
		msg('Unmounting '+mountpoint)
		subprocess.call(['umount',mountpoint])

def sign_tx_file(txfile):
	try:
		init_coin(mmgen.tx.MMGenTX(txfile,coin_sym_only=True).coin)
		reload(sys.modules['mmgen.tx'])
		tx = mmgen.tx.MMGenTX(txfile)
		if tx.coin not in no_daemon_coins:
			rpc_init(reinit=True)
		txsign(tx,wfs,None,None)
		tx.write_to_file(ask_write=False)
		return True
	except:
		return False

def sign():
	dirlist  = os.listdir(tx_dir)
	raw      = [f      for f in dirlist if f[-6:] == '.rawtx']
	signed   = [f[:-6] for f in dirlist if f[-6:] == '.sigtx']
	unsigned = [os.path.join(tx_dir,f) for f in raw if f[:-6] not in signed]

	if unsigned:
		fails = 0
		for txfile in unsigned:
			ret = sign_tx_file(txfile)
			if not ret:
				fails += 1
			qmsg('')
		time.sleep(0.3)
		n_ok = len(unsigned) - fails
		msg('{} transaction{} signed'.format(n_ok,suf(n_ok)))
		if fails:
			ymsg('{} transaction{} failed to sign'.format(fails,suf(fails)))
		return False if fails else True
	else:
		msg('No unsigned transactions')
		time.sleep(1)
		return True

def decrypt_wallets():
	opt.hash_preset = '1'
	opt.set_by_user = ['hash_preset']
	opt.passwd_file = os.path.join(tx_dir,key_fn)
#	opt.passwd_file = '/tmp/key'
	from mmgen.seed import SeedSource
	msg(u"Unlocking wallet{} with key from '{}'".format(suf(wfs),opt.passwd_file))
	fails = 0
	for wf in wfs:
		try:
			SeedSource(wf)
		except SystemExit as e:
			if e[0] != 0:
				fails += 1

	return False if fails else True

def do_sign():
	if not opt.stealth_led: set_led('busy')
	do_mount()
	key_ok = decrypt_wallets()
	if key_ok:
		if opt.stealth_led: set_led('busy')
		ret = sign()
		do_umount()
		set_led(('standby','off','error')[(not ret)*2 or bool(opt.stealth_led)])
		return ret
	else:
		msg('Password is incorrect!')
		do_umount()
		if not opt.stealth_led: set_led('error')
		return False

def wipe_existing_key():
	fn = os.path.join(tx_dir,key_fn)
	try: os.stat(fn)
	except: pass
	else:
		msg(u'\nWiping existing key {}'.format(fn))
		subprocess.call(['wipe','-cf',fn])

def create_key():
	from binascii import hexlify
	kdata = hexlify(os.urandom(32))
	fn = os.path.join(tx_dir,key_fn)
	desc = u'key file {}'.format(fn)
	msg('Creating ' + desc)
	try:
		with open(fn,'w') as f: f.write(kdata+'\n')
		os.chmod(fn,0400)
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
	msg("Deleting '{}'".format(wallet_dir))
	try: shutil.rmtree(wallet_dir)
	except: pass

def create_wallet_dir():
	try: os.mkdir(wallet_dir)
	except: pass
	try: os.stat(wallet_dir)
	except: die(2,"Unable to create wallet directory '{}'".format(wallet_dir))

def setup():
	remove_wallet_dir()
	gen_key(no_unmount=True)
	from mmgen.seed import SeedSource
	opt.hidden_incog_input_params = None
	opt.quiet = True
	opt.in_fmt = 'words'
	ss_in = SeedSource()
	opt.out_fmt = 'mmdat'
	opt.usr_randchars = 0
	opt.hash_preset = '1'
	opt.set_by_user = ['hash_preset']
	opt.passwd_file = os.path.join(tx_dir,key_fn)
	from mmgen.obj import MMGenWalletLabel
	opt.label = MMGenWalletLabel('Autosign Wallet')
	ss_out = SeedSource(ss=ss_in)
	ss_out.write_to_file(desc='autosign wallet',outdir=wallet_dir)

def ev_sleep(secs):
	ev.wait(secs)
	return (False,True)[ev.isSet()]

def do_led(on,off):
	if not on:
		with open(status_ctl,'w') as f: f.write('0\n')
		while True:
			if ev_sleep(3600): return

	while True:
		for s_time,val in ((on,255),(off,0)):
			with open(status_ctl,'w') as f: f.write('{}\n'.format(val))
			if ev_sleep(s_time): return

def set_led(cmd):
	if not opt.led: return
	vmsg("Setting LED state to '{}'".format(cmd))
	timings = {
		'off':     ( 0, 0 ),
		'standby': ( 2.2, 0.2 ),
		'busy':    ( 0.06, 0.06 ),
		'error':   ( 0.5, 0.5 )}[cmd]
	global led_thread
	if led_thread:
		ev.set(); led_thread.join(); ev.clear()
	led_thread = threading.Thread(target=do_led,name='LED loop',args=timings)
	led_thread.start()

def get_insert_status():
	if os.getenv('MMGEN_TEST_SUITE'): return True
	try: os.stat(os.path.join(u'/dev/disk/by-label',part_label))
	except: return False
	else: return True

def do_loop():
	n,prev_status = 0,False
	if not opt.stealth_led:
		set_led('standby')
	while True:
		status = get_insert_status()
		if status and not prev_status:
			msg('Device insert detected')
			do_sign()
		prev_status = status
		if not n % 10:
			msg_r('\r{}\rWaiting'.format(' '*17))
		time.sleep(1)
		msg_r('.')
		n += 1

def check_access(fn,desc='status LED control',init_val=None):
	try:
		with open(fn) as f: b = f.read().strip()
		with open(fn,'w') as f:
			f.write('{}\n'.format(init_val or b))
		return True
	except:
		m1 = "You do not have access to the {} file\n".format(desc)
		m2 = "To allow access, run 'sudo chmod 0666 {}'".format(fn)
		msg(m1+m2)
		return False

def check_wipe_present():
	try:
		subprocess.Popen(['wipe','-v'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	except:
		die(2,"The 'wipe' utility must be installed before running this program")

def init_led():
	sc = {
		'opi': '/sys/class/leds/orangepi:red:status/brightness',
		'rpi': '/sys/class/leds/led0/brightness'
	}
	tc = {
		'rpi': '/sys/class/leds/led0/trigger', # mmc,none
	}
	for k in ('opi','rpi'):
		try: os.stat(sc[k])
		except: pass
		else:
			board = k
			break
	else:
		die(2,'Control files not found!  LED option not supported')

	status_ctl  = sc[board]
	trigger_ctl = tc[board] if board in tc else None

	if not check_access(status_ctl) or (
			trigger_ctl and not check_access(trigger_ctl,desc='LED trigger',init_val='none')
		):
		sys.exit(1)

	if trigger_ctl:
		with open(trigger_ctl,'w') as f: f.write('none\n')

	return status_ctl,trigger_ctl

# main()
if len(cmd_args) not in (0,1):
	opts.usage()

if len(cmd_args) == 1:
	if cmd_args[0] in ('gen_key','setup'):
		globals()[cmd_args[0]]()
		sys.exit(0)
	elif cmd_args[0] != 'wait':
		die(1,"'{}': unrecognized command".format(cmd_args[0]))

check_wipe_present()
wfs = get_wallet_files()

check_daemons_running()

def at_exit(exit_val,nl=False):
	if nl: msg('')
	msg('Cleaning up...')
	if opt.led:
		set_led('off')
		ev.set()
		led_thread.join()
		if trigger_ctl:
			with open(trigger_ctl,'w') as f: f.write('mmc0\n')
	sys.exit(exit_val)

def handler(a,b): at_exit(1,nl=True)

signal.signal(signal.SIGTERM,handler)
signal.signal(signal.SIGINT,handler)

if opt.led:
	import threading
	status_ctl,trigger_ctl = init_led()
	ev = threading.Event()
	led_thread = None

if len(cmd_args) == 0:
	ret = do_sign()
	at_exit(int(not ret))
elif cmd_args[0] == 'wait':
	do_loop()
