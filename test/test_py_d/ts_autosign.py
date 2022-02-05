#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
ts_autosign.py: Autosign tests for the test.py test suite
"""

import os,shutil
from subprocess import run

from mmgen.globalvars import g
from mmgen.opts import opt
from ..include.common import *
from .common import *

from .ts_base import *
from .ts_shared import *
from .input import *

from mmgen.led import LEDControl

class TestSuiteAutosign(TestSuiteBase):
	'autosigning with BTC, BCH, LTC, ETH and ETC'
	networks = ('btc',)
	tmpdir_nums = [18]
	color = True
	cmd_group = (
		('autosign', 'transaction autosigning (BTC,BCH,LTC,ETH,ETC)'),
	)

	def autosign_live(self):
		return self.autosign_btc(live=True)

	def autosign_live_simulate(self):
		return self.autosign_btc(live=True,simulate=True)

	def autosign_btc(self,live=False,simulate=False):
		return self.autosign(
					coins=['btc'],
					daemon_coins=['btc'],
					txfiles=['btc'],
					txcount=3,
					live=live,
					simulate=simulate )

	# tests everything except mount/unmount
	def autosign(   self,
					coins=['btc','bch','ltc','eth'],
					daemon_coins=['btc','bch','ltc'],
					txfiles=['btc','bch','ltc','eth','mm1','etc'],
					txcount=12,
					live=False,
					simulate=False):

		if self.skip_for_win():
			return 'skip'

		def gen_key(opts):
			if not getattr(self,'key_generated',False):
				t = self.spawn('mmgen-autosign',opts+['gen_key'],extra_desc='(gen_key)')
				t.expect_getend('Wrote key file ')
				t.ok()
				self.key_generated = True

		def make_wallet(opts,mn_type=None):
			mn_desc = mn_type or 'default'
			mn_type = mn_type or 'mmgen'

			t = self.spawn(
				'mmgen-autosign',
				opts +
				([] if mn_desc == 'default' else [f'--mnemonic-fmt={mn_type}']) +
				['setup'],
				extra_desc = f'(setup - {mn_desc} mnemonic)' )

			t.expect('words: ','3')
			t.expect('OK? (Y/n): ','\n')
			mn_file = { 'mmgen': dfl_words_file, 'bip39': dfl_bip39_file }[mn_type]
			mn = read_from_file(mn_file).strip().split()
			from mmgen.mn_entry import mn_entry
			entry_mode = 'full'
			mne = mn_entry(mn_type,entry_mode)
			t.expect('Type a number.*: ',str(mne.entry_modes.index(entry_mode)+1),regex=True)
			stealth_mnemonic_entry(t,mne,mn,entry_mode)
			wf = t.written_to_file('Autosign wallet')
			t.ok()

		def copy_files(
				mountpoint,
				remove_signed_only=False,
				include_bad_tx=True,
				fdata_in = (('btc',''),
							('bch',''),
							('ltc','litecoin'),
							('eth','ethereum'),
							('mm1','ethereum'),
							('etc','ethereum_classic')) ):
			fdata = [e for e in fdata_in if e[0] in txfiles]
			from .ts_ref import TestSuiteRef
			tfns  = [TestSuiteRef.sources['ref_tx_file'][c][1] for c,d in fdata] + \
					[TestSuiteRef.sources['ref_tx_file'][c][0] for c,d in fdata] + \
					['25EFA3[2.34].testnet.rawtx'] # TX with 2 non-MMGen outputs
			tfs = [joinpath(ref_dir,d[1],fn) for d,fn in zip(fdata+fdata+[('btc','')],tfns)]

			for f,fn in zip(tfs,tfns):
				if fn: # use empty fn to skip file
					if g.debug_utf8:
						ext = '.testnet.rawtx' if fn.endswith('.testnet.rawtx') else '.rawtx'
						fn = fn[:-len(ext)] + '-α' + ext
					target = joinpath(mountpoint,'tx',fn)
					remove_signed_only or shutil.copyfile(f,target)
					try: os.unlink(target.replace('.rawtx','.sigtx'))
					except: pass

			# make 2 bad tx files
			for n in (1,2):
				bad_tx = joinpath(mountpoint,'tx',f'bad{n}.rawtx')
				if include_bad_tx and not remove_signed_only:
					with open(bad_tx,'w') as fp:
						fp.write('bad tx data')
				if not include_bad_tx:
					try: os.unlink(bad_tx)
					except: pass

		def do_autosign_live(opts,mountpoint,led_opts=[],gen_wallet=True):

			omsg(purple(
				'Running autosign test with ' +
				(f"'{' '.join(led_opts)}'" if led_opts else 'no LED')
			))

			def do_mount():
				try: run(['mount',mountpoint],check=True)
				except: pass

			def do_unmount():
				try: run(['umount',mountpoint],check=True)
				except: pass
				omsg_r(blue('\nRemove removable device and then hit ENTER '))
				input()

			if gen_wallet:
				if not opt.skip_deps:
					gen_key(opts)
					make_wallet(opts)
			else:
				do_mount()

			copy_files(mountpoint,include_bad_tx=not led_opts)

			desc = '(sign)'
			m1 = "Running 'mmgen-autosign wait'"
			m2 = 'Insert removable device '

			if led_opts:
				if led_opts == ['--led']:
					m1 = "Running 'mmgen-autosign wait' with --led. The LED should start blinking slowly now"
				elif led_opts == ['--stealth-led']:
					m1 = "Running 'mmgen-autosign wait' with --stealth-led. You should see no LED activity now"
				m2 = 'Insert removable device and watch for fast LED activity during signing'
				desc = '(sign - {})'.format(led_opts[0])

			def do_loop():
				omsg(blue(m2))
				t.expect(f'{txcount} transactions signed')
				if not led_opts:
					t.expect('2 transactions failed to sign')
				t.expect('Waiting')

			do_unmount()
			omsg(green(m1))
			t = self.spawn('mmgen-autosign',opts+led_opts+['--quiet','--no-summary','wait'],extra_desc=desc)
			if not opt.exact_output: omsg('')
			do_loop()
			do_mount() # race condition due to device insertion detection
			copy_files(mountpoint,remove_signed_only=True,include_bad_tx=not led_opts)
			do_unmount()
			do_loop()
			imsg(purple('\nKilling wait loop!'))
			t.kill(2) # 2 = SIGINT
			t.req_exit_val = 1
			if simulate and led_opts:
				t.expect("Stopping LED")
			return t

		def do_autosign(opts,mountpoint,mn_type=None,short=False):

			def autosign_expect(t,txcount):
				t.expect(f'{txcount} transactions signed')
				t.expect('2 transactions failed to sign')
				t.expect('Waiting')
				t.kill(2)
				t.req_exit_val = 1
				imsg('')
				t.ok()

			if not opt.skip_deps:
				gen_key(opts)
				make_wallet(opts,mn_type)

			copy_files(mountpoint,include_bad_tx=True)
			t = self.spawn('mmgen-autosign',opts+['--quiet','wait'],extra_desc='(sign)')
			autosign_expect(t,txcount)

			if short:
				return t

			copy_files(mountpoint,remove_signed_only=True)
			t = self.spawn('mmgen-autosign',opts+['--full-summary','wait'],extra_desc='(sign - full summary)')
			autosign_expect(t,txcount)

			copy_files(mountpoint,include_bad_tx=True,fdata_in=(('btc',''),))
			t = self.spawn(
				'mmgen-autosign',
				opts + ['--quiet','--stealth-led','wait'],
				extra_desc='(sign - --quiet --stealth-led)' )
			autosign_expect(t,3)

			copy_files(mountpoint,include_bad_tx=False,fdata_in=(('btc',''),))
			t = self.spawn('mmgen-autosign',opts+['--quiet','--led'],extra_desc='(sign - --quiet --led)')
			t.read()
			imsg('')

			return t

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

		def init_led():
			try:
				cf = LEDControl(enabled=True,simulate=simulate)
			except Exception as e:
				msg(str(e))
				die(2,'LEDControl initialization failed')
			for fn in (cf.board.status,cf.board.trigger):
				if fn:
					run(['sudo','chmod','0666',fn],check=True)

		# begin execution

		if simulate and not opt.exact_output:
			rmsg('This command must be run with --exact-output enabled!')
			return False

		if simulate or not live:
			os.environ['MMGEN_TEST_SUITE_AUTOSIGN_LED_SIMULATE'] = '1'
			LEDControl.create_dummy_control_files()

		network_ids = [c+'_tn' for c in daemon_coins] + daemon_coins
		start_test_daemons(*network_ids)

		try:
			if live:
				mountpoint = '/mnt/tx'
				opts = ['--coins='+','.join(coins)]
				check_mountpoint(mountpoint)
				init_led()
				foo = do_autosign_live(opts,mountpoint)
				foo = do_autosign_live(opts,mountpoint,led_opts=['--led'],gen_wallet=False)
				ret = do_autosign_live(opts,mountpoint,led_opts=['--stealth-led'],gen_wallet=False)
			else:
				mountpoint = self.tmpdir
				opts = ['--no-insert-check','--mountpoint='+mountpoint,'--coins='+','.join(coins)]
				try: os.mkdir(joinpath(mountpoint,'tx'))
				except: pass
				foo = do_autosign(opts,mountpoint,mn_type='mmgen',short=True)
				foo = do_autosign(opts,mountpoint,mn_type='bip39',short=True)
				ret = do_autosign(opts,mountpoint)
		finally:
			if simulate or not live:
				LEDControl.delete_dummy_control_files()
			stop_test_daemons(*[i for i in network_ids if i != 'btc'])

		return ret

class TestSuiteAutosignBTC(TestSuiteAutosign):
	'autosigning with BTC'
	cmd_group = (
		('autosign_btc', 'transaction autosigning (BTC only)'),
	)

class TestSuiteAutosignLive(TestSuiteAutosignBTC):
	'live autosigning operations with device insertion/removal and LED check'
	cmd_group = (
		('autosign_live', 'transaction autosigning (BTC,ETH,ETC - test device insertion/removal + LED)'),
	)

class TestSuiteAutosignLiveSimulate(TestSuiteAutosignBTC):
	'live autosigning operations with device insertion/removal and LED check in simulated environment'
	cmd_group = (
		('autosign_live_simulate', 'transaction autosigning (BTC,ETH,ETC - test device insertion/removal + simulated LED)'),
	)
