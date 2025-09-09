#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen-wallet
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
test.cmdtest_d.cfgfile: CfgFile tests for the MMGen cmdtest.py test suite
"""

import sys, os, time, shutil

from mmgen.color import yellow
from mmgen.cfgfile import CfgFileSampleSys, CfgFileSampleUsr, cfg_file_sample

from ..include.common import read_from_file, write_to_file, imsg
from .base import CmdTestBase

class CmdTestCfgFile(CmdTestBase):
	'CfgFile API'
	networks = ('btc',)
	tmpdir_nums = [40]
	base_passthru_opts = ()
	color = True

	cmd_group = (
		('sysfile',                  (40, 'init with system cfg sample file in place', [])),
		('opts_data_sets1',          (40, 'opts_data["sets"] opt set in environment', [])),
		('opts_data_sets2',          (40, 'opts_data["sets"] opt set in cfg_file', [])),
		('no_metadata_sample',       (40, 'init with unversioned cfg sample file', [])),
		('altered_sample',           (40, 'init with user-modified cfg sample file', [])),
		('old_sample',               (40, 'init with old v2 cfg sample file', [])),
		('old_sample_bad_var',       (40, 'init with old v2 cfg sample file and bad variable in mmgen.cfg', [])),
		('autoset_opts',             (40, 'setting autoset opts', [])),
		('autoset_opts_cmdline',     (40, 'setting autoset opts (override on cmdline)', [])),
		('autoset_opts_bad',         (40, 'setting autoset opts (bad value in cfg file)', [])),
		('autoset_opts_bad_cmdline', (40, 'setting autoset opts (bad param on cmdline)', [])),
		('coin_specific_vars',       (40, 'setting coin-specific vars', [])),
		('chain_names',              (40, 'setting chain names', [])),
		('mnemonic_entry_modes',     (40, 'setting mnemonic entry modes', [])),
		('opt_override1',            (40, 'cfg file opts not overridden', [])),
		('opt_override2',            (40, 'negative cmdline opts overriding cfg file opts', [])),
	)

	def __init__(self, cfg, trunner, cfgs, spawn):
		CmdTestBase.__init__(self, cfg, trunner, cfgs, spawn)
		self.spawn_env['MMGEN_TEST_SUITE_CFGTEST'] = '1'

	def read_from_cfgfile(self, loc):
		return read_from_file(self.path(loc))

	def write_to_cfgfile(self, loc, data, verbose=False):
		write_to_file(self.path(loc), '\n'.join(data) + '\n')
		if verbose:
			imsg(yellow(f'Wrote cfg file: {data!r}'))

	def spawn_test(self, opts=[], args=[], extra_desc='', pexpect_spawn=None, exit_val=None):
		return self.spawn(
			'test/misc/cfg.py',
			[f'--data-dir={self.path("data_dir")}'] + opts + args,
			cmd_dir       = '.',
			extra_desc    = extra_desc,
			pexpect_spawn = pexpect_spawn,
			exit_val      = exit_val)

	def path(self, id_str):
		return {
			'ref':         'test/ref/mmgen.cfg',
			'data_dir':    '{}/data_dir'.format(self.tmpdir),
			'shared_data': '{}/data_dir/{}'.format(self.tmpdir, CfgFileSampleSys.test_fn_subdir),
			'usr':         '{}/data_dir/mmgen.cfg'.format(self.tmpdir),
			'sys':         '{}/data_dir/{}/mmgen.cfg'.format(self.tmpdir, CfgFileSampleSys.test_fn_subdir),
			'sample':      '{}/data_dir/mmgen.cfg.sample'.format(os.path.abspath(self.tmpdir)),
		}[id_str]

	def copy_sys_sample(self):
		os.makedirs(self.path('shared_data'), exist_ok=True)
		shutil.copy2(self.path('ref'), self.path('sys'))

	def sysfile(self):
		self.copy_sys_sample()
		t = self.spawn_test()
		t.read()
		u = self.read_from_cfgfile('usr')
		S = self.read_from_cfgfile('sys')
		assert u[-1] == '\n', u
		assert u.replace('\r\n', '\n') == S, 'u != S'
		self.check_replaced_sample()
		return t

	def check_replaced_sample(self):
		s = self.read_from_cfgfile('sample')
		S = self.read_from_cfgfile('sys')
		assert s[-1] == '\n', s
		assert S.splitlines() == s.splitlines()[:-1], 'sys != sample[:-1]'

	def bad_sample(self, s, e):
		write_to_file(self.path('sample'), s)
		t = self.spawn_test()
		t.expect(e)
		t.read()
		self.check_replaced_sample()
		return t

	def opts_data_sets1(self): # no_license (in env) sets grokify
		self.write_to_cfgfile('usr', ['scroll true'])
		t = self.spawn_test(args=['print_cfg', 'no_license', 'foobleize', 'grokify', 'scroll'])
		t.expect('foobleize: None')
		t.expect('grokify: True')
		return t

	def opts_data_sets2(self): # autosign (in cfg file) sets foobleize
		self.write_to_cfgfile('usr', ['autosign true'])
		t = self.spawn_test(args=['print_cfg', 'no_license', 'autosign', 'foobleize', 'grokify'])
		t.expect('foobleize: True')
		t.expect('grokify: True')
		return t

	def no_metadata_sample(self):
		self.copy_sys_sample()
		S = self.read_from_cfgfile('sys')
		e = CfgFileSampleUsr.out_of_date_fs.format(self.path('sample'))
		return self.bad_sample(S, e)

	def altered_sample(self):
		s = '\n'.join(self.read_from_cfgfile('sample').splitlines()[1:]) + '\n'
		e = CfgFileSampleUsr.altered_by_user_fs.format(self.path('sample'))
		return self.bad_sample(s, e)

	def old_sample_common(self, old_set=False, args=[], pexpect_spawn=False):
		d = (
			self.read_from_cfgfile('sys').replace('monero_', 'zcash_').splitlines()
			+ ['', '# Uncomment to make foo true:', '# foo true']
			+ ['', '# Uncomment to make bar false:', '# bar false']
		)
		self.write_to_cfgfile('sample', d + cfg_file_sample.cls_make_metadata(d))

		t = self.spawn_test(args=args, pexpect_spawn=pexpect_spawn, exit_val=1 if old_set else None)

		t.expect('options have changed')
		for s in ('have been added', 'monero_', 'have been removed', 'zcash_', 'foo', 'bar'):
			t.expect(s)

		if old_set:
			for s in ('must be deleted', 'bar', 'foo'):
				t.expect(s)

		cp = CfgFileSampleUsr.details_confirm_prompt + ' (y/N): '

		t.expect(cp, 'y')

		for s in ('CHANGES', 'Removed', '# zcash_', '# foo', '# bar', 'Added', '# monero_'):
			t.expect(s)

		if t.pexpect_spawn: # view and exit pager
			time.sleep(1 if self.cfg.exact_output else t.send_delay)
			t.send('q')

		t.expect(cp, 'n')

		if old_set:
			t.expect('unrecognized option')

		if args == ['parse_test']:
			t.expect('parsed chunks: 29')
			t.expect('usr cfg: testnet=true rpc_password=passwOrd')

		if not old_set:
			self.check_replaced_sample()

		return t

	def old_sample(self):
		self.write_to_cfgfile('usr', ['testnet true', 'rpc_password passwOrd'])
		return self.old_sample_common(args=['parse_test'])

	def old_sample_bad_var(self):
		self.write_to_cfgfile('usr', ['foo true', 'bar false'])
		t = self.old_sample_common(
			old_set       = True,
			pexpect_spawn = not sys.platform == 'win32')
		t.expect('unrecognized option')
		return t

	def _autoset_opts(self, args=[], text='rpc_backend aiohttp', exit_val=None):
		self.write_to_cfgfile('usr', [text], verbose=True)
		return self.spawn_test(args=args, exit_val=exit_val)

	def autoset_opts(self):
		return self._autoset_opts(args=['autoset_opts'])

	def autoset_opts_cmdline(self):
		return self._autoset_opts(args=['--rpc-backend=curl', 'autoset_opts_cmdline'])

	def _autoset_opts_bad(self, expect, kwargs):
		t = self._autoset_opts(exit_val=1, **kwargs)
		t.expect(expect)
		return t

	def autoset_opts_bad(self):
		return self._autoset_opts_bad('not unique substring', {'text':'rpc_backend foo'})

	def autoset_opts_bad_cmdline(self):
		return self._autoset_opts_bad('not unique substring', {'args':['--rpc-backend=foo']})

	def coin_specific_vars(self):
		"""
		ensure that derived classes explicitly set these variables
		"""

		if self.cfg.no_altcoin:
			return 'skip'

		d = [
			'btc_max_tx_fee 1.2345',
			'eth_max_tx_fee 5.4321',
			'btc_ignore_daemon_version true',
			'eth_ignore_daemon_version true'
		]
		self.write_to_cfgfile('usr', d, verbose=True)

		for coin, res1_chk, res2_chk, res2_chk_eq in (
			('BTC', 'True',  '1.2345', True),
			('LTC', 'None',  '1.2345', False),
			('BCH', 'None',  '1.2345', False),
			('ETH', 'True',  '5.4321', True),
			('ETC', 'None',  '5.4321', False)
		):
			t = self.spawn_test(
				args = [
					f'--coin={coin}',
					'coin_specific_vars',
					'ignore_daemon_version',
					'max_tx_fee'
				],
				extra_desc=f'({coin})')
			res1 = t.expect_getend('ignore_daemon_version: ')
			res2 = t.expect_getend('max_tx_fee: ')
			assert res1 == res1_chk, f'{res1} != {res1_chk}'
			if res2_chk_eq:
				assert res2 == res2_chk, f'{res2} != {res2_chk}'
			else:
				assert res2 != res2_chk, f'{res2} == {res2_chk}'
			t.read()
			t.ok()

		t.skip_ok = True
		return t

	def mnemonic_entry_modes(self):

		def run(modes_chk):
			t = self.spawn_test(args=['mnemonic_entry_modes'])
			modes = t.expect_getend('mnemonic_entry_modes: ')
			assert modes_chk == modes, f'{modes_chk} != {modes}'
			return t

		self.write_to_cfgfile('usr', ['mnemonic_entry_modes mmgen:full bip39:short'], verbose=True)

		t = run("{'mmgen': 'full', 'bip39': 'short'}")
		# check that set_dfl_entry_mode() set the mode correctly:
		t.expect('mmgen: full')
		t.expect('bip39: short')
		return t

	def chain_names(self):

		if self.cfg.no_altcoin:
			return 'skip'

		def run(chk, testnet):
			for coin, chain_chk in (('ETH', chk), ('ETC', None)):
				t = self.spawn_test(
					args = [f'--coin={coin}', f'--testnet={(0, 1)[testnet]}', 'coin_specific_vars', 'chain_names'],
					extra_desc = f'({coin} testnet={testnet!r:5} chain_names={chain_chk})')
				chain = t.expect_getend('chain_names: ')
				if chain_chk:
					assert chain == chain_chk, f'{chain} != {chain_chk}'
				else:
					assert chain != chain_chk, f'{chain} == {chain_chk}'
				t.read()
				t.ok()
			return t

		self.write_to_cfgfile('usr', ['eth_mainnet_chain_names istanbul constantinople'], verbose=True)

		t = run("['istanbul', 'constantinople']", False)
		t = run(None, True)

		self.write_to_cfgfile('usr', ['eth_testnet_chain_names rinkeby'], verbose=True)

		t = run(None, False)
		t = run("['rinkeby']", True)

		t.skip_ok = True
		return t

	def opt_override1(self):
		self.write_to_cfgfile('usr', ['no_license true', 'scroll true'])
		t = self.spawn_test(
			args = ['print_cfg', 'scroll', 'no_license'])
		t.expect('scroll: True')
		t.expect('no_license: True')
		return t

	def opt_override2(self):
		self.write_to_cfgfile('usr', ['no_license true', 'scroll true'])
		t = self.spawn_test(
			args = ['print_cfg', 'scroll', 'no_license'],
			opts = ['--no-scrol', '--lic'])
		t.expect('scroll: False')
		t.expect('no_license: False')
		return t
