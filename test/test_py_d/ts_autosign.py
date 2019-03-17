#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
from mmgen.globalvars import g
from mmgen.opts import opt
from test.common import read_from_file
from test.test_py_d.common import *

from test.test_py_d.ts_base import *
from test.test_py_d.ts_shared import *

class TestSuiteAutosign(TestSuiteBase):
	'autosigning with BTC, BCH, LTC, ETH and ETC'
	networks = ('btc',)
	tmpdir_nums = [18]
	cmd_group = (
		('autosign', 'transaction autosigning (BTC,BCH,LTC,ETH,ETC)'),
	)

	def autosign_live(self):
		return self.autosign_minimal(live=True)

	def autosign_minimal(self,live=False):
		return self.autosign(
					coins=['btc','eth'],
					txfiles=['btc','eth','mm1','etc'],
					txcount=7,
					live=live)

	# tests everything except device detection, mount/unmount
	def autosign(   self,
					coins=['btc','bch','ltc','eth'],
					txfiles=['btc','bch','ltc','eth','mm1','etc'],
					txcount=11,
					live=False):

		if self.skip_for_win(): return

		def make_wallet(opts):
			t = self.spawn('mmgen-autosign',opts+['gen_key'],extra_desc='(gen_key)')
			t.expect_getend('Wrote key file ')
			t.ok()

			t = self.spawn('mmgen-autosign',opts+['setup'],extra_desc='(setup)')
			t.expect('words: ','3')
			t.expect('OK? (Y/n): ','\n')
			mn_file = dfl_words_file
			mn = read_from_file(mn_file).strip().split()
			mn = ['foo'] + mn[:5] + ['realiz','realized'] + mn[5:]
			wnum = 1
			max_wordlen = 12

			def get_pad_chars(n):
				ret = ''
				for i in range(n):
					m = int(os.urandom(1).hex(),16) % 32
					ret += r'123579!@#$%^&*()_+-=[]{}"?/,.<>|'[m]
				return ret

			for i in range(len(mn)):
				w = mn[i]
				if len(w) > 5:
					w = w + '\n'
				else:
					w = get_pad_chars(3 if randbool() else 0) + w[0] + get_pad_chars(3) + w[1:] + get_pad_chars(7)
					w = w[:max_wordlen+1]
				em,rm = 'Enter word #{}: ','Repeat word #{}: '
				ret = t.expect((em.format(wnum),rm.format(wnum-1)))
				if ret == 0: wnum += 1
				for j in range(len(w)):
					t.send(w[j])
					time.sleep(0.005)
			wf = t.written_to_file('Autosign wallet')
			t.ok()

		def copy_files(mountpoint,remove_signed_only=False,include_bad_tx=True):
			fdata_in = (('btc',''),
						('bch',''),
						('ltc','litecoin'),
						('eth','ethereum'),
						('mm1','ethereum'),
						('etc','ethereum_classic'))
			fdata = [e for e in fdata_in if e[0] in txfiles]
			from test.test_py_d.ts_ref import TestSuiteRef
			tfns  = [TestSuiteRef.sources['ref_tx_file'][c][1] for c,d in fdata] + \
					[TestSuiteRef.sources['ref_tx_file'][c][0] for c,d in fdata]
			tfs = [joinpath(ref_dir,d[1],fn) for d,fn in zip(fdata+fdata,tfns)]

			for f,fn in zip(tfs,tfns):
				if fn: # use empty fn to skip file
					target = joinpath(mountpoint,'tx',fn)
					remove_signed_only or shutil.copyfile(f,target)
					try: os.unlink(target.replace('.rawtx','.sigtx'))
					except: pass

			# make a bad tx file
			bad_tx = joinpath(mountpoint,'tx','bad.rawtx')
			if include_bad_tx and not remove_signed_only:
				open(bad_tx,'w').write('bad tx data')
			if not include_bad_tx:
				try: os.unlink(bad_tx)
				except: pass

		def do_autosign_live(opts,mountpoint,led_opts=[],gen_wallet=True):

			def do_mount():
				try: subprocess.check_call(['mount',mountpoint])
				except: pass

			def do_unmount():
				try: subprocess.check_call(['umount',mountpoint])
				except: pass
				omsg_r(blue('\nRemove removable device and then hit ENTER '))
				input()

			if gen_wallet: make_wallet(opts)
			else: do_mount()

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
					t.expect('1 transaction failed to sign')
				t.expect('Waiting')

			do_unmount()
			omsg(green(m1))
			t = self.spawn('mmgen-autosign',opts+led_opts+['wait'],extra_desc=desc)
			if not opt.exact_output: omsg('')
			do_loop()
			do_mount() # race condition due to device insertion detection
			copy_files(mountpoint,remove_signed_only=True,include_bad_tx=not led_opts)
			do_unmount()
			do_loop()
			t.kill(2) # 2 = SIGINT
			t.req_exit_val = 1
			return t

		def do_autosign(opts,mountpoint):
			make_wallet(opts)
			copy_files(mountpoint,include_bad_tx=True)
			t = self.spawn('mmgen-autosign',opts+['wait'],extra_desc='(sign)')
			t.expect('{} transactions signed'.format(txcount))
			t.expect('1 transaction failed to sign')
			t.expect('Waiting')
			t.kill(2)
			t.req_exit_val = 1
			return t

		if live:
			mountpoint = '/mnt/tx'
			if not os.path.ismount(mountpoint):
				try:
					subprocess.check_call(['mount',mountpoint])
					imsg("Mounted '{}'".format(mountpoint))
				except:
					ydie(1,"Could not mount '{}'!  Exiting".format(mountpoint))

			txdir = joinpath(mountpoint,'tx')
			if not os.path.isdir(txdir):
				ydie(1,"Directory '{}' does not exist!  Exiting".format(mountpoint))

			opts = ['--coins='+','.join(coins)]
			led_files = {   'opi': ('/sys/class/leds/orangepi:red:status/brightness',),
							'rpi': ('/sys/class/leds/led0/brightness','/sys/class/leds/led0/trigger') }
			for k in ('opi','rpi'):
				if os.path.exists(led_files[k][0]):
					led_support = k
					break
			else:
				led_support = None

			if led_support:
				for fn in (led_files[led_support]):
					subprocess.check_call(['sudo','chmod','0666',fn])
				omsg(purple('Running autosign test with no LED'))
				do_autosign_live(opts,mountpoint)
				omsg(purple("Running autosign test with '--led'"))
				do_autosign_live(opts,mountpoint,led_opts=['--led'],gen_wallet=False)
				omsg(purple("Running autosign test with '--stealth-led'"))
				return do_autosign_live(opts,mountpoint,led_opts=['--stealth-led'],gen_wallet=False)
			else:
				return do_autosign_live(opts,mountpoint)
		else:
			mountpoint = self.tmpdir
			opts = ['--no-insert-check','--mountpoint='+mountpoint,'--coins='+','.join(coins)]
			try: os.mkdir(joinpath(mountpoint,'tx'))
			except: pass
			return do_autosign(opts,mountpoint)

class TestSuiteAutosignMinimal(TestSuiteAutosign):
	'autosigning with BTC, ETH and ETC'
	cmd_group = (
		('autosign_minimal', 'transaction autosigning (BTC,ETH,ETC)'),
	)

class TestSuiteAutosignLive(TestSuiteAutosignMinimal):
	'live autosigning operations'
	cmd_group = (
		('autosign_live', 'transaction autosigning (BTC,ETH,ETC - test device insertion/removal + LED)'),
	)
