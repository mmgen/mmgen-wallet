#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen-wallet
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
test.cmdtest_d.input: user input tests for the MMGen cmdtest.py test suite
"""

import sys, os

from mmgen.cfg import gc
from mmgen.util import fmt, capfirst, remove_whitespace
from mmgen.wallet import get_wallet_cls

from ..include.common import (
	imsg,
	imsg_r,
	sample_mn,
	get_data_from_file,
	read_from_file,
	strip_ansi_escapes
)
from .include.common import Ctrl_U, ref_dir
from .base import CmdTestBase
from .include.input import stealth_mnemonic_entry, user_dieroll_entry

hold_protect_delay = 2 if sys.platform == 'darwin' else None

class CmdTestInput(CmdTestBase):
	'user input'
	networks = ('btc',)
	tmpdir_nums = [1]
	color = True
	cmd_group_in = (
		('subgroup.char', []),
		('subgroup.line', []),
		('subgroup.password', []),
		('subgroup.misc', []),
		('subgroup.wallet', []),
		('subgroup.mnemonic', []),
		('subgroup.dieroll', []),
	)
	cmd_subgroups = {
	'char': (
		'get_char() function',
		('get_char1',                    'get_char()'),
		('get_char2',                    'get_char() [multiple characters]'),
		('get_char3',                    'get_char() [no prompt]'),
		('get_char4',                    'get_char() [utf8]'),
		('get_char_term1',               'get_char() [term, utf8]'),
		('get_char_term2',               'get_char() [term, multiple characters]'),
		('get_char_term3',               'get_char() [term, prehold_protect=False]'),
		('get_char_term4',               'get_char() [term, immed_chars="xyz"]'),
	),
	'line': (
		'line_input() function',
		('line_input',                    'line_input()'),
		('line_input_term1',              'line_input() [term]'),
		('line_input_term2',              'line_input() [term, no hold protect]'),
		('line_input_insert',             'line_input() [inserted text]'),
		('line_input_insert_term1',       'line_input() [inserted text, term]'),
		('line_input_insert_term2',       'line_input() [inserted text, term, no hold protect]'),
		('line_input_edit_term',          'line_input() [edited text, term, utf8]'),
		('line_input_edit_term_insert',   'line_input() [inserted + edited text, term, utf8]'),
		('line_input_erase_term',         'line_input() [inserted + erased text, term]'),
	),
	'password': (
		'password entry via line_input()',
		('password_entry_noecho',         'utf8 password entry'),
		('password_entry_noecho_term',    'utf8 password entry [term]'),
		('password_entry_echo',           'utf8 password entry (echoed)'),
		('password_entry_echo_term',      'utf8 password entry (echoed) [term]'),
	),
	'misc': (
		'miscellaneous user-level UI functions',
		('get_seed_from_stdin',           'reading seed phrase from STDIN'),
	),
	'wallet': (
		'hash preset, password and label entry',
		('get_passphrase_ui',             'hash preset, password and label (wallet.py)'),
		('get_passphrase_cmdline',        'hash preset, password and label (wallet.py - from cmdline)'),
		('get_passphrase_crypto',         'hash preset, password and label (crypto.py)'),
	),
	'mnemonic': (
		'mnemonic entry',
		('mnemonic_entry_mmgen',           'stealth mnemonic entry (mmgen)'),
		('mnemonic_entry_mmgen_minimal',   'stealth mnemonic entry (mmgen - minimal entry mode)'),
		('mnemonic_entry_bip39',           'stealth mnemonic entry (bip39)'),
		('mnemonic_entry_bip39_short',     'stealth mnemonic entry (bip39 - short entry mode)'),
		('mn2hex_interactive_mmgen',       'mn2hex_interactive (mmgen)'),
		('mn2hex_interactive_mmgen_fixed', 'mn2hex_interactive (mmgen - fixed (10-letter) entry mode)'),
		('mn2hex_interactive_bip39',       'mn2hex_interactive (bip39)'),
		('mn2hex_interactive_bip39_short', 'mn2hex_interactive (bip39 - short entry mode (+pad entry))'),
		('mn2hex_interactive_bip39_fixed', 'mn2hex_interactive (bip39 - fixed (4-letter) entry mode)'),
		('mn2hex_interactive_xmr',         'mn2hex_interactive (xmrseed)'),
		('mn2hex_interactive_xmr_short',   'mn2hex_interactive (xmrseed - short entry mode)'),
	),
	'dieroll': (
		'dieroll entry',
		('dieroll_entry',                 'dieroll entry (base6d)'),
		('dieroll_entry_usrrand',         'dieroll entry (base6d) with added user entropy'),
	)
	}

	def get_seed_from_stdin(self):
		self.spawn(msg_only=True)
		from subprocess import run, PIPE
		cmd = ['python3', 'cmds/mmgen-walletconv', '--skip-cfg-file', '--in-fmt=words', '--out-fmt=words', '--outdir=test/trash']
		mn = sample_mn['mmgen']['mn']
		run_env = dict(os.environ)
		run_env['MMGEN_TEST_SUITE'] = ''

		cp = run(cmd, input=mn.encode(), stdout=PIPE, stderr=PIPE, env=run_env)

		from mmgen.color import set_vt100
		set_vt100()
		imsg(cp.stderr.decode().strip())
		res = get_data_from_file(self.cfg, 'test/trash/A773B05C[128].mmwords', silent=True).strip()
		assert res == mn, f'{res} != {mn}'
		return 'ok' if b'written to file' in cp.stderr else 'error'

	def get_passphrase_ui(self):
		t = self.spawn('test/misc/get_passphrase.py', ['--usr-randchars=0', 'seed'], cmd_dir='.')

		# 1 - new wallet, default hp, label;empty pw
		t.expect('accept the default.*: ', '\n', regex=True)

		# bad repeat
		t.expect('new MMGen wallet: ', 'pass1\n')
		t.expect('peat passphrase: ', 'pass2\n')

		# good repeat
		t.expect('new MMGen wallet: ', '\n')
		t.expect('peat passphrase: ', '\n')
		t.expect('mpty pass')

		t.expect('no label: ', '\n')

		t.expect('[][3][No Label]')

		# 2 - new wallet, user-selected hp, pw, label
		t.expect('accept the default.*: ', '1\n', regex=True)

		t.expect('new MMGen wallet: ', 'pass1\n')
		t.expect('peat passphrase: ', 'pass1\n')

		t.expect('no label: ', 'lbl1\n')

		t.expect('[pass1][1][lbl1]')

		# 3 - passchg, nothing changes
		t.expect('new hash preset')
		t.expect('reuse the old value.*: ', '\n', regex=True)
		t.expect('unchanged')

		t.expect('new passphrase.*: ', 'pass1\n', regex=True)
		t.expect('peat new passphrase: ', 'pass1\n')
		t.expect('unchanged')

		t.expect('reuse the label .*: ', '\n', regex=True)
		t.expect('unchanged')

		t.expect('[pass1][1][lbl1]')

		# 4 - passchg, everything changes
		t.expect('new hash preset')
		t.expect('reuse the old value.*: ', '2\n', regex=True)
		t.expect(' changed to')

		t.expect('new passphrase.*: ', 'pass2\n', regex=True)
		t.expect('peat new passphrase: ', 'pass2\n')
		t.expect(' changed')

		t.expect('reuse the label .*: ', 'lbl2\n', regex=True)
		t.expect(' changed to')
		t.expect('[pass2][2][lbl2]')

		# 5 - wallet from file
		t.expect('from file')

		# bad passphrase
		t.expect('passphrase for MMGen wallet: ', 'bad\n')
		t.expect('Trying again')

		# good passphrase
		t.expect('passphrase for MMGen wallet: ', 'reference password\n')
		t.expect('[reference password][1][No Label]')

		return t

	def get_passphrase_cmdline(self):
		with open('test/trash/pwfile', 'w') as fp:
			fp.write('reference password\n')
		t = self.spawn('test/misc/get_passphrase.py', [
			'--usr-randchars=0',
			'--label=MyLabel',
			'--passwd-file=test/trash/pwfile',
			'--hash-preset=1',
			'seed'],
			cmd_dir = '.')
		for _ in range(4):
			t.expect('[reference password][1][MyLabel]')

		return t

	def get_passphrase_crypto(self):
		t = self.spawn('test/misc/get_passphrase.py', ['--usr-randchars=0', 'crypto'], cmd_dir='.')

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
		t.expect(f'[{gc.dfl_hash_preset}]')

		return t

	def _input_func(self, func_name, arg_dfls, func_args, text, expect, term, delay=None):
		if term and sys.platform == 'win32':
			return ('skip_warn', 'pexpect_spawn not supported on Windows platform')
		func_args = dict(zip(arg_dfls.keys(), func_args))
		t = self.spawn(
			'test/misc/input_func.py',
			[func_name, repr(func_args)],
			cmd_dir='.',
			pexpect_spawn=term)
		imsg('Parameters:')
		imsg(f'  pexpect_spawn: {term}')
		imsg(f'  sending:       {text!r}')
		imsg(f'  expecting:     {expect!r}')
		imsg('\nFunction args:')
		for k, v in func_args.items():
			imsg('  {:14} {!r}'.format(k+':', v))
		imsg_r('\nScript output: ')
		prompt_add = (func_args['insert_txt'] if term else '') if func_name == 'line_input' else ''
		prompt = func_args['prompt'] + prompt_add
		t.expect('Calling ')
		if prompt:
			t.expect(prompt, text, delay=delay)
		else:
			t.send(text, delay=delay)
		ret = t.expect_getend('  ==> ')
		assert ret == repr(expect), f'Text mismatch! {ret} != {repr(expect)}'
		return t

	def _get_char(self, func_args, text, expect, term):
		arg_dfls = {
			'prompt': '',
			'immed_chars': '',
			'prehold_protect': True,
			'num_bytes': 5,
		}
		return self._input_func('get_char', arg_dfls, func_args, text, expect, term)

	def _line_input(self, func_args, text, expect, term, delay=None):
		arg_dfls = {
			'prompt': '', # positional
			'echo': True,
			'insert_txt': '',
			'hold_protect': True,
		}
		return self._input_func('line_input', arg_dfls, func_args, text+'\n', expect, term, delay=delay)

	def get_char1(self):
		return self._get_char(['prompt> ', '', True, 5], 'x', 'x', False)

	def get_char2(self):
		expect = 'x' if sys.platform == 'win32' else 'xxxxx'
		return self._get_char(['prompt> ', '', True, 5], 'xxxxx', expect, False)

	def get_char3(self):
		return self._get_char(['', '', True, 5], 'x', 'x', False)

	def get_char4(self):
		return self._get_char(['prompt> ', '', True, 2], 'α', 'α', False) # UTF-8, must get 2 bytes

	def get_char_term1(self):
		return self._get_char(['prompt> ', '', True, 2], 'β', 'β', True)  # UTF-8, must get 2 bytes

	def get_char_term2(self):
		return self._get_char(['prompt> ', '', True, 5], 'xxxxx', 'xxxxx', True)

	def get_char_term3(self):
		return self._get_char(['', '', False, 5], 'x', 'x', True)

	def get_char_term4(self):
		return self._get_char(['prompt> ', 'xyz', False, 5], 'x', 'x', True)

	def line_input(self):
		return self._line_input(
			['prompt> ', True, '', True],
			'foo',
			'foo',
			False)

	def line_input_term1(self):
		return self._line_input(
			['prompt> ', True, '', True],
			'foo',
			'foo',
			True,
			hold_protect_delay)

	def line_input_term2(self):
		return self._line_input(
			['prompt> ', True, '', False],
			'foo',
			'foo',
			True)

	def line_input_insert(self):
		return self._line_input(
			['prompt> ', True, 'inserted text', True],
			'foo',
			'foo',
			False)

	def line_input_insert_term1(self):
		if self.skip_for_mac('readline text buffer issues'):
			return 'skip'
		return self._line_input(
			['prompt> ', True, 'foo', True],
			'bar',
			'foobar',
			True,
			hold_protect_delay)

	def line_input_insert_term2(self):
		if self.skip_for_mac('readline text buffer issues'):
			return 'skip'
		return self._line_input(
			['prompt> ', True, 'foo', False],
			'bar',
			'foobar',
			True)

	def line_input_edit_term(self):
		return self._line_input(
			['prompt> ', True, '', True],
			'\b\bφυφυ\b\bβαρ',
			'φυβαρ',
			True,
			hold_protect_delay)

	def line_input_edit_term_insert(self):
		if self.skip_for_mac('readline text buffer issues'):
			return 'skip'
		return self._line_input(
			['prompt> ', True, 'φυφυ', True],
			'\b\bβαρ',
			'φυβαρ',
			True,
			hold_protect_delay)

	def line_input_erase_term(self):
		if self.skip_for_mac('readline text buffer issues'):
			return 'skip'
		return self._line_input(
			['prompt> ', True, 'foobarbaz', True],
			Ctrl_U + 'foobar',
			'foobar',
			True,
			hold_protect_delay)

	def _password_entry(self, prompt, opts=[], term=False):
		if term and sys.platform == 'win32':
			return ('skip_warn', 'pexpect_spawn not supported on Windows platform')
		t = self.spawn('test/misc/input_func.py', opts + ['passphrase'], cmd_dir='.', pexpect_spawn=term)
		imsg(f'Terminal: {term}')
		pw = 'abc-α'
		t.expect(prompt, pw+'\n')
		ret = t.expect_getend('Entered: ')
		assert ret == pw, f'Password mismatch! {ret} != {pw}'
		return t

	winskip_msg = """
		pexpect_spawn not supported on Windows platform
		Perform the following test by hand with non-ASCII password abc-α
		or another password in your native alphabet:

		  test/misc/input_func.py{} passphrase
	"""

	def password_entry_noecho(self, term=False):
		return self._password_entry('Enter passphrase: ', term=term)

	def password_entry_noecho_term(self):
		if self.skip_for_win('no pexpect_spawn'):
			return ('skip_warn', '\n' + fmt(self.winskip_msg.format(''), strip_char='\t'))
		return self.password_entry_noecho(term=True)

	def password_entry_echo(self, term=False):
		return self._password_entry('Enter passphrase (echoed): ', ['--echo-passphrase'], term=term)

	def password_entry_echo_term(self):
		if self.skip_for_win('no pexpect_spawn'):
			return ('skip_warn', '\n' + fmt(self.winskip_msg.format(' --echo-passphrase'), strip_char='\t'))
		return self.password_entry_echo(term=True)

	def _mn2hex(self, fmt, entry_mode='full', mn=None, pad_entry=False, enter_for_dfl=False):
		mn = mn or sample_mn[fmt]['mn'].split()
		t = self.spawn('mmgen-tool', ['mn2hex_interactive', 'fmt='+fmt, 'mn_len=12', 'print_mn=1'])
		from mmgen.mn_entry import mn_entry
		mne = mn_entry(self.cfg, fmt, entry_mode=entry_mode)
		t.expect(
			'Type a number.*: ',
			('\n' if enter_for_dfl else str(mne.entry_modes.index(entry_mode)+1)),
			regex = True)
		t.expect(r'Using entry mode (\S+)', regex=True)
		mode = strip_ansi_escapes(t.p.match.group(1)).lower()
		assert mode == mne.em.name.lower(), f'{mode} != {mne.em.name.lower()}'
		stealth_mnemonic_entry(t, mne, mn, entry_mode=entry_mode, pad_entry=pad_entry)
		t.expect(sample_mn[fmt]['hex'])
		return t

	def _user_seed_entry(
			self,
			fmt,
			usr_rand    = False,
			out_fmt     = None,
			entry_mode  = 'full',
			mn          = None,
			seedlen_opt = False):

		wcls = get_wallet_cls(fmt_code=fmt)
		wf = os.path.join(ref_dir, f'FE3C6545.{wcls.ext}')
		if wcls.base_type == 'mnemonic':
			mn = mn or read_from_file(wf).strip().split()
		elif wcls.type == 'dieroll':
			mn = mn or list(remove_whitespace(read_from_file(wf)))
			for idx, val in ((5, 'x'), (18, '0'), (30, '7'), (44, '9')):
				mn.insert(idx, val)
		t = self.spawn(
			'mmgen-walletconv',
			['--usr-randchars=10', '--stdout']
			+ (['--seed-len=128'] if seedlen_opt else [])
			+ [f'--in-fmt={fmt}', f'--out-fmt={out_fmt or fmt}']
		)
		t.expect(f'{capfirst(wcls.base_type or wcls.type)} type:.*{wcls.mn_type}', regex=True)
		if not seedlen_opt:
			t.expect(wcls.choose_seedlen_prompt, '1')
			t.expect('(Y/n): ', 'y')
		if wcls.base_type == 'mnemonic':
			t.expect('Type a number.*: ', '6', regex=True)
			t.expect('invalid')
			from mmgen.mn_entry import mn_entry
			mne = mn_entry(self.cfg, fmt, entry_mode=entry_mode)
			t.expect('Type a number.*: ', str(mne.entry_modes.index(entry_mode)+1), regex=True)
			t.expect(r'Using entry mode (\S+)', regex=True)
			mode = strip_ansi_escapes(t.p.match.group(1)).lower()
			assert mode == mne.em.name.lower(), f'{mode} != {mne.em.name.lower()}'
			stealth_mnemonic_entry(t, mne, mn, entry_mode=entry_mode)
		elif wcls.type == 'dieroll':
			user_dieroll_entry(t, mn)
			if usr_rand:
				t.expect(wcls.user_entropy_prompt, 'y')
				t.usr_rand(10)
			else:
				t.expect(wcls.user_entropy_prompt, 'n')
		if not usr_rand:
			sid_chk = 'FE3C6545'
			sid = strip_ansi_escapes(
				t.expect_getend(f'Valid {wcls.desc} for Seed ID').split(',')[0])
			assert sid_chk in sid, f'Seed ID mismatch! {sid_chk} not found in {sid}'
		t.expect('to confirm: ', 'YES\n')
		return t

	def mnemonic_entry_mmgen_minimal(self):
		from mmgen.mn_entry import mn_entry
		# erase_chars: '\b\x7f'
		m = mn_entry(self.cfg, 'mmgen', entry_mode='minimal')
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
		return self._user_seed_entry('words', entry_mode='minimal', mn=mn)
	def mnemonic_entry_mmgen(self):
		return self._user_seed_entry('words', entry_mode='full')
	def mnemonic_entry_bip39(self):
		return self._user_seed_entry('bip39', entry_mode='full')
	def mnemonic_entry_bip39_short(self):
		return self._user_seed_entry('bip39', entry_mode='short')

	def mn2hex_interactive_mmgen(self):
		return self._mn2hex('mmgen', entry_mode='full')
	def mn2hex_interactive_mmgen_fixed(self):
		return self._mn2hex('mmgen', entry_mode='fixed')
	def mn2hex_interactive_bip39(self):
		return self._mn2hex('bip39', entry_mode='full')
	def mn2hex_interactive_bip39_short(self):
		return self._mn2hex('bip39', entry_mode='short', pad_entry=True)
	def mn2hex_interactive_bip39_fixed(self):
		return self._mn2hex('bip39', entry_mode='fixed', enter_for_dfl=True)
	def mn2hex_interactive_xmr(self):
		return self._mn2hex('xmrseed', entry_mode='full')
	def mn2hex_interactive_xmr_short(self):
		return self._mn2hex('xmrseed', entry_mode='short')

	def dieroll_entry(self):
		return self._user_seed_entry('dieroll', seedlen_opt=True)
	def dieroll_entry_usrrand(self):
		return self._user_seed_entry('dieroll', usr_rand=True, out_fmt='bip39')
