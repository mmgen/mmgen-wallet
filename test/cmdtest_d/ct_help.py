#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.ct_help: helpscreen test group for the cmdtest.py test suite
"""

import sys, os, time

from mmgen.util import ymsg
from mmgen.cfg import gc

from ..include.common import cfg
from .ct_base import CmdTestBase

class CmdTestHelp(CmdTestBase):
	'help, info and usage screens'
	networks = ('btc', 'ltc', 'bch', 'eth', 'xmr', 'doge')
	passthru_opts = ('daemon_data_dir', 'rpc_port', 'coin', 'testnet')
	cmd_group = (
		('usage1',            (1, 'usage message (via --usage)', [])),
		('usage2',            (1, 'usage message (via bad invocation)', [])),
		('version',           (1, 'version message', [])),
		('license',           (1, 'license message', [])),
		('helpscreens',       (1, 'help screens',             [])),
		('longhelpscreens',   (1, 'help screens (--longhelp)', [])),
		('show_hash_presets', (1, 'info screen (--show-hash-presets)', [])),
		('tool_help',         (1, '‘mmgen-tool’ usage screen', [])),
		('tool_cmd_usage',    (1, '‘mmgen-tool’ usage screen', [])),
		('test_help',         (1, '‘cmdtest.py’ help screens', [])),
		('tooltest_help',     (1, '‘tooltest.py’ help screens', [])),
	)

	def usage1(self):
		t = self.spawn('mmgen-txsend', ['--usage'], no_passthru_opts=True)
		t.expect('USAGE: mmgen-txsend')
		return t

	def usage2(self):
		t = self.spawn('mmgen-walletgen', ['foo'], exit_val=1, no_passthru_opts=True)
		t.expect('USAGE: mmgen-walletgen')
		return t

	def version(self):
		t = self.spawn('mmgen-tool', ['--version'], exit_val=0)
		t.expect('MMGEN-TOOL version')
		return t

	def license(self):
		t = self.spawn(
			'mmgen-walletconv',
			['--stdout', '--in-fmt=hex', '--out-fmt=hex'],
			env = {'MMGEN_NO_LICENSE':''},
			no_passthru_opts = True)
		t.expect('to continue: ', 'w')
		t.expect('TERMS AND CONDITIONS') # start of GPL text
		if cfg.pexpect_spawn:
			t.send('G')
		t.expect('return for a fee.')    # end of GPL text
		if cfg.pexpect_spawn:
			t.send('q')
		t.expect('to continue: ', 'c')
		t.expect('data: ', 'beadcafe'*4 + '\n')
		t.expect('to confirm: ', 'YES\n')
		return t

	def spawn_chk_expect(self, *args, **kwargs):
		expect = kwargs.pop('expect')
		t = self.spawn(*args, **kwargs)
		t.expect(expect)
		if t.pexpect_spawn:
			time.sleep(0.4)
			t.send('q')
		t.read()
		t.ok()
		t.skip_ok = True
		return t

	def helpscreens(self, arg='--help', scripts=(), expect='USAGE:.*OPTIONS:', pager=True):

		scripts = list(scripts or gc.cmd_caps_data)

		def gen_skiplist():
			for script in scripts:
				d = gc.cmd_caps_data[script]
				for cap in d.caps:
					if cap not in self.proto.mmcaps:
						yield script
						break
				else:
					if sys.platform == 'win32' and 'w' not in d.platforms:
						yield script
					elif d.coin and len(d.coin) > 1 and self.proto.coin.lower() not in (d.coin, 'btc'):
						yield script

		for cmdname in sorted(set(scripts) - set(list(gen_skiplist()))):
			t = self.spawn(
				f'mmgen-{cmdname}',
				[arg],
				extra_desc       = f'(mmgen-{cmdname})',
				no_passthru_opts = not gc.cmd_caps_data[cmdname].proto)
			t.expect(expect, regex=True)
			if pager and t.pexpect_spawn:
				time.sleep(0.2)
				t.send('q')
			t.read()
			t.ok()
			t.skip_ok = True

		return t

	def longhelpscreens(self):
		return self.helpscreens(arg='--longhelp', expect='USAGE:.*GLOBAL OPTIONS:')

	def show_hash_presets(self):
		return self.helpscreens(
			arg = '--show-hash-presets',
			scripts = (
				'walletgen', 'walletconv', 'walletchk', 'passchg', 'subwalletgen',
				'addrgen', 'keygen', 'passgen',
				'txsign', 'txdo', 'txbump'),
			expect = 'Available parameters.*Preset',
			pager  = False)

	def tool_help(self):

		if os.getenv('PYTHONOPTIMIZE') == '2':
			ymsg('Skipping tool help with PYTHONOPTIMIZE=2 (no docstrings)')
			return 'skip'

		for arg in (
			'help',
			'usage',
		):
			t = self.spawn_chk_expect(
				'mmgen-tool',
				[arg],
				extra_desc = f'(mmgen-tool {arg})',
				expect = 'GENERAL USAGE')
		return t

	def tool_cmd_usage(self):

		if os.getenv('PYTHONOPTIMIZE') == '2':
			ymsg('Skipping tool cmd usage with PYTHONOPTIMIZE=2 (no docstrings)')
			return 'skip'

		from mmgen.main_tool import mods

		for cmdlist in mods.values():
			for cmd in cmdlist:
				t = self.spawn_chk('mmgen-tool', ['help', cmd], extra_desc=f'({cmd})')
		return t

	def test_help(self):
		for arg, expect in (
			('--help', 'USAGE'),
			('--list-cmds', 'AVAILABLE COMMANDS'),
			('--list-cmd-groups', 'AVAILABLE COMMAND GROUPS')
		):
			t = self.spawn_chk_expect(
				'cmdtest.py',
				[arg],
				cmd_dir = 'test',
				extra_desc = f'(cmdtest.py {arg})',
				expect = expect)
		return t

	def tooltest_help(self):
		for arg, expect in (
			('--list-cmds', 'Available commands'),
			('--testing-status', 'Testing status')
		):
			t = self.spawn_chk_expect(
				'tooltest.py',
				[arg],
				cmd_dir = 'test',
				extra_desc = f'(tooltest.py {arg})',
				expect = expect)
		return t
