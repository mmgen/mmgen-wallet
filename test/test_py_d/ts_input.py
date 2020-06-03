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

from ..include.common import *
from .ts_base import *
from .input import *
from mmgen.wallet import Wallet

class TestSuiteInput(TestSuiteBase):
	'user input'
	networks = ('btc',)
	tmpdir_nums = []
	color = True
	cmd_group = (
		('get_passphrase_ui',             (1,"hash preset, password and label (wallet.py)", [])),
		('get_passphrase_cmdline',        (1,"hash preset, password and label (wallet.py - from cmdline)", [])),
		('get_passphrase_crypto',         (1,"hash preset, password and label (crypto.py)", [])),
		('password_entry_noecho',         (1,"utf8 password entry", [])),
		('password_entry_echo',           (1,"utf8 password entry (echoed)", [])),
		('mnemonic_entry_mmgen',          (1,"stealth mnemonic entry (mmgen)", [])),
		('mnemonic_entry_mmgen_minimal',  (1,"stealth mnemonic entry (mmgen - minimal entry mode)", [])),
		('mnemonic_entry_bip39',          (1,"stealth mnemonic entry (bip39)", [])),
		('mnemonic_entry_bip39_short',    (1,"stealth mnemonic entry (bip39 - short entry mode)", [])),
		('mn2hex_interactive_mmgen',      (1,"mn2hex_interactive (mmgen)", [])),
		('mn2hex_interactive_mmgen_fixed',(1,"mn2hex_interactive (mmgen - fixed (10-letter) entry mode)", [])),
		('mn2hex_interactive_bip39',      (1,"mn2hex_interactive (bip39)", [])),
		('mn2hex_interactive_bip39_short',(1,"mn2hex_interactive (bip39 - short entry mode (+pad entry))", [])),
		('mn2hex_interactive_bip39_fixed',(1,"mn2hex_interactive (bip39 - fixed (4-letter) entry mode)", [])),
		('mn2hex_interactive_xmr',        (1,"mn2hex_interactive (xmrseed)", [])),
		('mn2hex_interactive_xmr_short',  (1,"mn2hex_interactive (xmrseed - short entry mode)", [])),
		('dieroll_entry',                 (1,"dieroll entry (base6d)", [])),
		('dieroll_entry_usrrand',         (1,"dieroll entry (base6d) with added user entropy", [])),
	)

	def get_passphrase_ui(self):
		t = self.spawn('test/misc/get_passphrase.py',['--usr-randchars=0','seed'],cmd_dir='.')

		# 1 - new wallet, default hp,label;empty pw
		t.expect('accept the default.*: ','\n',regex=True)

		# bad repeat
		t.expect('new MMGen wallet: ','pass1\n')
		t.expect('peat passphrase: ','pass2\n')

		# good repeat
		t.expect('new MMGen wallet: ','\n')
		t.expect('peat passphrase: ','\n')
		t.expect('mpty pass')

		t.expect('no label: ','\n')

		t.expect('[][3][No Label]')

		# 2 - new wallet, user-selected hp,pw,label
		t.expect('accept the default.*: ', '1\n', regex=True)

		t.expect('new MMGen wallet: ','pass1\n')
		t.expect('peat passphrase: ','pass1\n')

		t.expect('no label: ','lbl1\n')

		t.expect('[pass1][1][lbl1]')

		# 3 - passchg, nothing changes
		t.expect('new hash preset')
		t.expect('reuse the old value.*: ','\n',regex=True)
		t.expect('unchanged')

		t.expect('new passphrase.*: ','pass1\n',regex=True)
		t.expect('peat passphrase: ','pass1\n')
		t.expect('unchanged')

		t.expect('reuse the label .*: ','\n',regex=True)
		t.expect('unchanged')

		t.expect('[pass1][1][lbl1]')

		# 4 - passchg, everything changes
		t.expect('new hash preset')
		t.expect('reuse the old value.*: ','2\n',regex=True)
		t.expect(' changed to')

		t.expect('new passphrase.*: ','pass2\n',regex=True)
		t.expect('peat passphrase: ','pass2\n')
		t.expect(' changed')

		t.expect('reuse the label .*: ','lbl2\n',regex=True)
		t.expect(' changed to')
		t.expect('[pass2][2][lbl2]')

		# 5 - wallet from file
		t.expect('from file')

		# bad passphrase
		t.expect('passphrase for MMGen wallet: ','bad\n')
		t.expect('Trying again')

		# good passphrase
		t.expect('passphrase for MMGen wallet: ','reference password\n')
		t.expect('[reference password][1][No Label]')

		t.read()

		return t

	def get_passphrase_cmdline(self):
		open('test/trash/pwfile','w').write('reference password\n')
		t = self.spawn('test/misc/get_passphrase.py', [
			'--usr-randchars=0',
			'--label=MyLabel',
			'--passwd-file=test/trash/pwfile',
			'--hash-preset=1',
			'seed' ],
			cmd_dir = '.' )
		for foo in range(4):
			t.expect('[reference password][1][MyLabel]')
		t.read()
		return t

	def get_passphrase_crypto(self):
		t = self.spawn('test/misc/get_passphrase.py',['--usr-randchars=0','crypto'],cmd_dir='.')

		# new passwd
		t.expect('passphrase for .*: ', 'x\n', regex=True)
		t.expect('peat passphrase: ', '\n')
		t.expect('passphrase for .*: ', 'pass1\n', regex=True)
		t.expect('peat passphrase: ', 'pass1\n')
		t.expect('[pass1]')

		# existing passwd
		t.expect('passphrase for .*: ', 'pass2\n', regex=True)
		t.expect('[pass2]')

		# hash preset
		t.expect('accept the default .*: ', '0\n', regex=True)
		t.expect('nvalid')
		t.expect('accept the default .*: ', '8\n', regex=True)
		t.expect('nvalid')
		t.expect('accept the default .*: ', '7\n', regex=True)
		t.expect('[7]')

		# hash preset (default)
		t.expect('accept the default .*: ', '\n', regex=True)
		t.expect(f'[{g.dfl_hash_preset}]')

		t.read()
		return t

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

	def _mn2hex(self,fmt,entry_mode='full',mn=None,pad_entry=False,enter_for_dfl=False):
		mn = mn or sample_mn[fmt]['mn'].split()
		t = self.spawn('mmgen-tool',['mn2hex_interactive','fmt='+fmt,'mn_len=12','print_mn=1'])
		from mmgen.mn_entry import mn_entry
		mne = mn_entry(fmt,entry_mode)
		t.expect(
			'Type a number.*: ',
			('\n' if enter_for_dfl else str(mne.entry_modes.index(entry_mode)+1)),
			regex = True )
		t.expect('Using (.+) entry mode',regex=True)
		mode = strip_ansi_escapes(t.p.match.group(1)).lower()
		assert mode == mne.em.name.lower(), '{} != {}'.format(mode,mne.em.name.lower())
		stealth_mnemonic_entry(t,mne,mn,entry_mode=entry_mode,pad_entry=pad_entry)
		t.expect(sample_mn[fmt]['hex'])
		t.read()
		return t

	def _user_seed_entry(self,fmt,usr_rand=False,out_fmt=None,entry_mode='full',mn=None):
		wcls = Wallet.fmt_code_to_type(fmt)
		wf = os.path.join(ref_dir,'FE3C6545.{}'.format(wcls.ext))
		if wcls.wclass == 'mnemonic':
			mn = mn or read_from_file(wf).strip().split()
		elif wcls.wclass == 'dieroll':
			mn = mn or list(read_from_file(wf).strip().translate(dict((ord(ws),None) for ws in '\t\n ')))
			for idx,val in ((5,'x'),(18,'0'),(30,'7'),(44,'9')):
				mn.insert(idx,val)
		t = self.spawn('mmgen-walletconv',['-r10','-S','-i',fmt,'-o',out_fmt or fmt])
		t.expect('{} type:.*{}'.format(capfirst(wcls.wclass),wcls.mn_type),regex=True)
		t.expect(wcls.choose_seedlen_prompt,'1')
		t.expect('(Y/n): ','y')
		if wcls.wclass == 'mnemonic':
			t.expect('Type a number.*: ','6',regex=True)
			t.expect('invalid')
			from mmgen.mn_entry import mn_entry
			mne = mn_entry(fmt,entry_mode)
			t.expect('Type a number.*: ',str(mne.entry_modes.index(entry_mode)+1),regex=True)
			t.expect('Using (.+) entry mode',regex=True)
			mode = strip_ansi_escapes(t.p.match.group(1)).lower()
			assert mode == mne.em.name.lower(), '{} != {}'.format(mode,mne.em.name.lower())
			stealth_mnemonic_entry(t,mne,mn,entry_mode=entry_mode)
		elif wcls.wclass == 'dieroll':
			user_dieroll_entry(t,mn)
			if usr_rand:
				t.expect(wcls.user_entropy_prompt,'y')
				t.usr_rand(10)
			else:
				t.expect(wcls.user_entropy_prompt,'n')
		if not usr_rand:
			sid_chk = 'FE3C6545'
			sid = t.expect_getend('Valid {} for Seed ID '.format(wcls.desc))
			sid = strip_ansi_escapes(sid.split(',')[0])
			assert sid == sid_chk,'Seed ID mismatch! {} != {}'.format(sid,sid_chk)
		t.expect('to confirm: ','YES\n')
		t.read()
		return t

	def mnemonic_entry_mmgen_minimal(self):
		from mmgen.mn_entry import mn_entry
		# erase_chars: '\b\x7f'
		m = mn_entry('mmgen','minimal')
		np = 2
		mn = (
			'z',
			'aa',
			'1d2ud',
			'fo{}ot{}#'.format('1' * np, '2' * (m.em.pad_max - np)), # substring of 'football'
			'des1p)%erate\n', # substring of 'desperately'
			'#t!(ie',
			'!)sto8o',
			'the123m8!%s',
			'349t(5)rip',
			'di\b\bdesce',
			'cea',
			'bu\x7f\x7fsuic',
			'app\bpl',
			'wd',
			'busy')
		return self._user_seed_entry('words',entry_mode='minimal',mn=mn)
	def mnemonic_entry_mmgen(self):           return self._user_seed_entry('words',entry_mode='full')
	def mnemonic_entry_bip39(self):           return self._user_seed_entry('bip39',entry_mode='full')
	def mnemonic_entry_bip39_short(self):     return self._user_seed_entry('bip39',entry_mode='short')

	def mn2hex_interactive_mmgen(self):       return self._mn2hex('mmgen',entry_mode='full')
	def mn2hex_interactive_mmgen_fixed(self): return self._mn2hex('mmgen',entry_mode='fixed')
	def mn2hex_interactive_bip39(self):       return self._mn2hex('bip39',entry_mode='full')
	def mn2hex_interactive_bip39_short(self): return self._mn2hex('bip39',entry_mode='short',pad_entry=True)
	def mn2hex_interactive_bip39_fixed(self): return self._mn2hex('bip39',entry_mode='fixed',enter_for_dfl=True)
	def mn2hex_interactive_xmr(self):         return self._mn2hex('xmrseed',entry_mode='full')
	def mn2hex_interactive_xmr_short(self):   return self._mn2hex('xmrseed',entry_mode='short')

	def dieroll_entry(self):         return self._user_seed_entry('dieroll')
	def dieroll_entry_usrrand(self): return self._user_seed_entry('dieroll',usr_rand=True,out_fmt='bip39')
