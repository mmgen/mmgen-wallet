#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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

class TestSuiteAutosign(TestSuiteBase):
	'autosigning with BTC, BCH, LTC, ETH and ETC'
	networks = ('btc',)
	tmpdir_nums = [18]
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

		def make_wallet(opts):
			t = self.spawn('mmgen-autosign',opts+['gen_key'],extra_desc='(gen_key)')
			t.expect_getend('Wrote key file ')
			t.ok()

			t = self.spawn('mmgen-autosign',opts+['setup'],extra_desc='(setup)')
			t.expect('words: ','3')
			t.expect('OK? (Y/n): ','\n')
			mn_file = dfl_words_file
			mn = read_from_file(mn_file).strip().split()
			from mmgen.mn_entry import mn_entry
			entry_mode = 'full'
			mne = mn_entry('mmgen',entry_mode)
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
				bad_tx = joinpath(mountpoint,'tx','bad{}.rawtx'.format(n))
				if include_bad_tx and not remove_signed_only:
					open(bad_tx,'w').write('bad tx data')
				if not include_bad_tx:
					try: os.unlink(bad_tx)
					except: pass

		def do_autosign_live(opts,mountpoint,led_opts=[],gen_wallet=True):

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
				t.expect('{} transactions signed'.format(txcount))
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

		def do_autosign(opts,mountpoint):

			if not opt.skip_deps:
				make_wallet(opts)

			copy_files(mountpoint,include_bad_tx=True)

			t = self.spawn('mmgen-autosign',opts+['--full-summary','wait'],extra_desc='(sign - full summary)')
			t.expect('{} transactions signed'.format(txcount))
			t.expect('2 transactions failed to sign')
			t.expect('Waiting')
			t.kill(2)
			t.req_exit_val = 1
			imsg('')
			t.ok()

			copy_files(mountpoint,remove_signed_only=True)
			t = self.spawn('mmgen-autosign',opts+['--quiet','wait'],extra_desc='(sign)')
			t.expect('{} transactions signed'.format(txcount))
			t.expect('2 transactions failed to sign')
			t.expect('Waiting')
			t.kill(2)
			t.req_exit_val = 1
			imsg('')
			t.ok()

			copy_files(mountpoint,include_bad_tx=True,fdata_in=(('btc',''),))
			t = self.spawn(
				'mmgen-autosign',
				opts + ['--quiet','--stealth-led','wait'],
				extra_desc='(sign - --quiet --stealth-led)' )
			t.expect('2 transactions failed to sign')
			t.expect('Waiting')
			t.kill(2)
			t.req_exit_val = 1
			imsg('')
			t.ok()

			copy_files(mountpoint,include_bad_tx=False,fdata_in=(('btc',''),))
			t = self.spawn(
				'mmgen-autosign',
				opts + ['--quiet','--led'],
				extra_desc='(sign - --quiet --led)' )
			t.read()
			imsg('')
			t.ok()

			return t

		# begin execution

		if simulate and not opt.exact_output:
			rmsg('This command must be run with --exact-output enabled!')
			return False
		network_ids = [c+'_tn' for c in daemon_coins] + daemon_coins
		start_test_daemons(*network_ids)

		if live:
			mountpoint = '/mnt/tx'
			if not os.path.ismount(mountpoint):
				try:
					run(['mount',mountpoint],check=True)
					imsg("Mounted '{}'".format(mountpoint))
				except:
					ydie(1,"Could not mount '{}'!  Exiting".format(mountpoint))

			txdir = joinpath(mountpoint,'tx')
			if not os.path.isdir(txdir):
				ydie(1,"Directory '{}' does not exist!  Exiting".format(mountpoint))

			opts = ['--coins='+','.join(coins)]

			from mmgen.led import LEDControl

			if simulate:
				LEDControl.create_dummy_control_files()

			try:
				cf = LEDControl(enabled=True,simulate=simulate)
			except:
				ret = "'no LED support detected'"
			else:
				for fn in (cf.board.status,cf.board.trigger):
					if fn:
						run(['sudo','chmod','0666',fn],check=True)
				os.environ['MMGEN_TEST_SUITE_AUTOSIGN_LIVE'] = '1'
				omsg(purple('Running autosign test with no LED'))
				do_autosign_live(opts,mountpoint)
				omsg(purple("Running autosign test with '--led'"))
				do_autosign_live(opts,mountpoint,led_opts=['--led'],gen_wallet=False)
				omsg(purple("Running autosign test with '--stealth-led'"))
				ret = do_autosign_live(opts,mountpoint,led_opts=['--stealth-led'],gen_wallet=False)
		else:
			mountpoint = self.tmpdir
			opts = ['--no-insert-check','--mountpoint='+mountpoint,'--coins='+','.join(coins)]
			try: os.mkdir(joinpath(mountpoint,'tx'))
			except: pass
			ret = do_autosign(opts,mountpoint)

		stop_test_daemons(*network_ids)
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
