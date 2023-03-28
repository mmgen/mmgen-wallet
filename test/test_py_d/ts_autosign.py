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
test.test_py_d.ts_autosign: Autosign tests for the test.py test suite
"""

import os,shutil
from subprocess import run

from mmgen.globalvars import gc

from ..include.common import *
from .common import *
from .ts_base import *
from .ts_shared import *
from .input import *

from mmgen.led import LEDControl

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

def check_mountpoint(mountpoint):
	if not os.path.ismount(mountpoint):
		try:
			run(['mount',mountpoint],check=True)
			imsg(f'Mounted {mountpoint}')
		except:
			die(2,f'Could not mount {mountpoint}!  Exiting')

	txdir = joinpath(mountpoint,'tx')
	if not os.path.isdir(txdir):
		die(2,f'Directory {txdir} does not exist!  Exiting')

def do_mount(mountpoint):
	if not os.path.ismount(mountpoint):
		try: run(['mount',mountpoint],check=True)
		except: pass

def do_umount(mountpoint):
	if os.path.ismount(mountpoint):
		try: run(['umount',mountpoint],check=True)
		except: pass

class TestSuiteAutosignBase(TestSuiteBase):
	networks     = ('btc',)
	tmpdir_nums  = [18]
	color        = True

	def __init__(self,trunner,cfgs,spawn):
		super().__init__(trunner,cfgs,spawn)
		if trunner == None:
			return
		if gc.platform == 'win':
			die(1,f'Test {type(self).__name__} not supported for Windows platform')
		self.network_ids = [c+'_tn' for c in self.daemon_coins] + self.daemon_coins

		if self.simulate and not cfg.exact_output:
			die(1,red('This command must be run with --exact-output enabled!'))

		if self.simulate or not self.live:
			os.environ['MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE'] = '1'
			LEDControl.create_dummy_control_files()

		if self.live:
			self.mountpoint = '/mnt/tx'
			self.opts = ['--coins='+','.join(self.coins)]
			check_mountpoint(self.mountpoint)
			init_led(self.simulate)
		else:
			self.mountpoint = self.tmpdir
			try:
				os.mkdir(joinpath(self.mountpoint,'tx'))
			except:
				pass
			self.opts = [
				'--coins='+','.join(self.coins),
				'--mountpoint='+self.mountpoint,
				'--no-insert-check' ]

		self.tx_file_ops('set_count') # initialize tx_count here so we can resume anywhere

		def gen_msg_fns():
			fmap = dict(filedir_map)
			for coin in self.coins:
				sdir = os.path.join('test','ref',fmap[coin])
				for fn in os.listdir(sdir):
					if fn.endswith(f'[{coin.upper()}].rawmsg.json'):
						yield os.path.join(sdir,fn)

		self.ref_msgfiles = tuple(gen_msg_fns())
		self.good_msg_count = 0
		self.bad_msg_count = 0

	def __del__(self):
		if gc.platform == 'win' or self.tr == None:
			return
		if self.simulate or not self.live:
			LEDControl.delete_dummy_control_files()

	def start_daemons(self):
		self.spawn('',msg_only=True)
		start_test_daemons(*self.network_ids)
		return 'ok'

	def stop_daemons(self):
		self.spawn('',msg_only=True)
		stop_test_daemons(*[i for i in self.network_ids if i != 'btc'])
		return 'ok'

	def gen_key(self):
		t = self.spawn( 'mmgen-autosign', self.opts + ['gen_key'] )
		t.expect_getend('Wrote key file ')
		return t

	def make_wallet_mmgen(self):
		return self.make_wallet(mn_type='mmgen')

	def make_wallet_bip39(self):
		return self.make_wallet(mn_type='bip39')

	def make_wallet(self,mn_type=None):
		mn_desc = mn_type or 'default'
		mn_type = mn_type or 'mmgen'

		t = self.spawn(
			'mmgen-autosign',
			self.opts +
			([] if mn_desc == 'default' else [f'--mnemonic-fmt={mn_type}']) +
			['setup'] )

		t.expect('words: ','3')
		t.expect('OK? (Y/n): ','\n')
		mn_file = { 'mmgen': dfl_words_file, 'bip39': dfl_bip39_file }[mn_type]
		mn = read_from_file(mn_file).strip().split()
		from mmgen.mn_entry import mn_entry
		entry_mode = 'full'
		mne = mn_entry( cfg, mn_type, entry_mode )
		t.expect('Type a number.*: ',str(mne.entry_modes.index(entry_mode)+1),regex=True)
		stealth_mnemonic_entry(t,mne,mn,entry_mode)
		wf = t.written_to_file('Autosign wallet')
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

		fdata = [e for e in filedir_map if e[0] in (txfile_coins or self.txfile_coins)]

		from .ts_ref import TestSuiteRef
		tfns  = [TestSuiteRef.sources['ref_tx_file'][c][1] for c,d in fdata] + \
				[TestSuiteRef.sources['ref_tx_file'][c][0] for c,d in fdata] + \
				['25EFA3[2.34].testnet.rawtx'] # TX with 2 non-MMGen outputs
		self.tx_count = len([fn for fn in tfns if fn])
		if op == 'set_count':
			return
		tfs = [joinpath(ref_dir,d[1],fn) for d,fn in zip(fdata+fdata+[('btc','')],tfns)]

		for f,fn in zip(tfs,tfns):
			if fn: # use empty fn to skip file
				if cfg.debug_utf8:
					ext = '.testnet.rawtx' if fn.endswith('.testnet.rawtx') else '.rawtx'
					fn = fn[:-len(ext)] + '-α' + ext
				target = joinpath(self.mountpoint,'tx',fn)
				if not op == 'remove_signed':
					shutil.copyfile(f,target)
				try:
					os.unlink(target.replace('.rawtx','.sigtx'))
				except:
					pass

		return 'ok'

	def create_bad_txfiles(self):
		return self.bad_txfiles('create')

	def remove_bad_txfiles(self):
		return self.bad_txfiles('remove')

	def bad_txfiles(self,op):
		if self.live:
			do_mount(self.mountpoint)
		# create or delete 2 bad tx files
		self.spawn('',msg_only=True)
		fns = [joinpath(self.mountpoint,'tx',f'bad{n}.rawtx') for n in (1,2)]
		if op == 'create':
			for fn in fns:
				with open(fn,'w') as fp:
					fp.write('bad tx data\n')
			self.bad_tx_count = 2
		elif op == 'remove':
			for fn in fns:
				try: os.unlink(fn)
				except: pass
			self.bad_tx_count = 0
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
		destdir = joinpath(self.mountpoint,'msg')
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
		return 'ok'

class TestSuiteAutosign(TestSuiteAutosignBase):
	'autosigning transactions for all supported coins'
	coins        = ['btc','bch','ltc','eth']
	daemon_coins = ['btc','bch','ltc']
	txfile_coins = ['btc','bch','ltc','eth','mm1','etc']
	live         = False
	simulate     = False
	bad_tx_count = 0
	cmd_group = (
		('start_daemons',            'starting daemons'),
		('copy_tx_files',            'copying transaction files'),
		('gen_key',                  'generating key'),
		('make_wallet_mmgen',        'making wallet (MMGen native)'),
		('sign_quiet',               'signing transactions (--quiet)'),
		('remove_signed_txfiles',    'removing signed transaction files'),
		('make_wallet_bip39',        'making wallet (BIP39)'),
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
		('create_bad_txfiles',       'creating bad transaction files'),
		('remove_signed_msgfiles',   'removing signed message files'),
		('create_invalid_msgfile',   'creating invalid message file'),
		('sign_full_summary_msg',    'signing transactions and messages (--full-summary)'),
		('remove_invalid_msgfile',   'removing invalid message file'),
		('remove_bad_txfiles',       'removing bad transaction files'),
		('sign_no_unsigned_msg',     'signing transactions and messages (nothing to sign)'),
		('stop_daemons',             'stopping daemons'),
	)

	def do_sign(self,args,have_msg=False):
		t = self.spawn('mmgen-autosign', self.opts + args )
		t.expect(
			f'{self.tx_count} transactions signed' if self.tx_count else
			'No unsigned transactions' )

		if self.bad_tx_count:
			t.expect(f'{self.bad_tx_count} transactions failed to sign')
			t.req_exit_val = 1

		if have_msg:
			t.expect(
				f'{self.good_msg_count} message files{{0,1}} signed' if self.good_msg_count else
				'No unsigned message files', regex=True )

			if self.bad_msg_count:
				t.expect(f'{self.bad_msg_count} message files{{0,1}} failed to sign', regex=True)
				t.req_exit_val = 1

		if 'wait' in args:
			t.expect('Waiting')
			t.kill(2)
			t.req_exit_val = 1
		else:
			t.read()

		imsg('')
		return t

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

class TestSuiteAutosignBTC(TestSuiteAutosign):
	'autosigning BTC transactions'
	coins        = ['btc']
	daemon_coins = ['btc']
	txfile_coins = ['btc']

class TestSuiteAutosignLive(TestSuiteAutosignBTC):
	'live autosigning BTC transactions'
	live = True
	cmd_group = (
		('start_daemons',        'starting daemons'),
		('copy_tx_files',        'copying transaction files'),
		('gen_key',              'generating key'),
		('make_wallet_bip39',    'making wallet (BIP39)'),
		('sign_live',            'signing transactions'),
		('create_bad_txfiles',   'creating bad transaction files'),
		('sign_live_led',        'signing transactions (--led)'),
		('remove_bad_txfiles',   'removing bad transaction files'),
		('sign_live_stealth_led','signing transactions (--stealth-led)'),
		('stop_daemons',         'stopping daemons'),
	)

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

		do_umount(self.mountpoint)
		prompt_remove()
		omsg(green(info_msg))
		t = self.spawn(
			'mmgen-autosign',
			self.opts + led_opts + ['--quiet','--no-summary','wait'])
		if not cfg.exact_output:
			omsg('')
		prompt_insert_sign(t)

		do_mount(self.mountpoint) # race condition due to device insertion detection
		self.remove_signed_txfiles()
		do_umount(self.mountpoint)

		imsg(purple('\nKilling wait loop!'))
		t.kill(2) # 2 = SIGINT
		t.req_exit_val = 1
		if self.simulate and led_opts:
			t.expect("Stopping LED")
		return t

class TestSuiteAutosignLiveSimulate(TestSuiteAutosignLive):
	'live autosigning BTC transactions with simulated LED support'
	simulate = True
