#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
ts_input.py: user input tests for the MMGen test.py test suite
"""

from test.common import *
from test.test_py_d.ts_base import *
from mmgen.seed import SeedSource

class TestSuiteInput(TestSuiteBase):
	'user input'
	networks = ('btc',)
	tmpdir_nums = []
	cmd_group = (
		('password_entry_noecho',         (1,"utf8 password entry", [])),
		('password_entry_echo',           (1,"utf8 password entry (echoed)", [])),
		('mnemonic_entry_mmgen',          (1,"stealth mnemonic entry (mmgen)", [])),
		('mnemonic_entry_bip39',          (1,"stealth mnemonic entry (bip39)", [])),
		('dieroll_entry',                 (1,"dieroll entry (base6d)", [])),
		('dieroll_entry_usrrand',         (1,"dieroll entry (base6d) with added user entropy", [])),
	)

	def password_entry(self,prompt,cmd_args):
		t = self.spawn('test/misc/password_entry.py',cmd_args,cmd_dir='.')
		pw = 'abc-α'
		t.expect(prompt,pw)
		ret = t.expect_getend('Entered: ')
		assert ret == pw,'Password mismatch! {} != {}'.format(ret,pw)
		return t

	def password_entry_noecho(self):
		if self.skip_for_win():
			m = "getpass() doesn't work with pexpect.popen_spawn!\n"
			m += 'Perform the following test by hand with non-ASCII password abc-α:\n'
			m += '  test/misc/password_entry.py'
			return ('skip_warn',m)
		return self.password_entry('Enter passphrase: ',[])

	def password_entry_echo(self):
		if self.skip_for_win():
			m = "getpass() doesn't work with pexpect.popen_spawn!\n"
			m += 'Perform the following test by hand with non-ASCII password abc-α:\n'
			m += '  test/misc/password_entry.py --echo-passphrase'
			return ('skip_warn',m)
		return self.password_entry('Enter passphrase (echoed): ',['--echo-passphrase'])

	def _user_seed_entry(self,fmt,usr_rand=False,out_fmt=None,mn=None):
		wcls = SeedSource.fmt_code_to_type(fmt)
		wf = os.path.join(ref_dir,'FE3C6545.{}'.format(wcls.ext))
		if wcls.wclass == 'mnemonic':
			mn = mn or read_from_file(wf).strip().split()
		elif wcls.wclass == 'dieroll':
			mn = mn or list(read_from_file(wf).strip().translate(dict((ord(ws),None) for ws in '\t\n ')))
			for idx,val in ((5,'x'),(18,'0'),(30,'7'),(44,'9')):
				mn.insert(idx,val)
		t = self.spawn('mmgen-walletconv',['-r10','-S','-i',fmt,'-o',out_fmt or fmt])
		t.expect('{} type: {}'.format(capfirst(wcls.wclass),wcls.mn_type))
		t.expect(wcls.choose_seedlen_prompt,'1')
		t.expect('(Y/n): ','y')
		if wcls.wclass == 'mnemonic':
			stealth_mnemonic_entry(t,mn,fmt=fmt)
		elif wcls.wclass == 'dieroll':
			user_dieroll_entry(t,mn)
			if usr_rand:
				t.expect(wcls.user_entropy_prompt,'y')
				t.usr_rand(10)
			else:
				t.expect(wcls.user_entropy_prompt,'n')
		if not usr_rand:
			sid_chk = 'FE3C6545'
			sid = t.expect_getend('Valid {} for Seed ID '.format(wcls.desc))[:8]
			assert sid == sid_chk,'Seed ID mismatch! {} != {}'.format(sid,sid_chk)
		t.expect('to confirm: ','YES\n')
		t.read()
		return t

	def mnemonic_entry_mmgen(self):           return self._user_seed_entry('words',entry_mode='full')
	def mnemonic_entry_bip39(self):           return self._user_seed_entry('bip39',entry_mode='full')

	def dieroll_entry(self):         return self._user_seed_entry('dieroll')
	def dieroll_entry_usrrand(self): return self._user_seed_entry('dieroll',usr_rand=True,out_fmt='bip39')
