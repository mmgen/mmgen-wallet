#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
test.test_py_d.ts_cfgfile: CfgFile tests for the MMGen test.py test suite
"""

import os,time,shutil

from ..include.common import cfg,read_from_file,write_to_file,imsg
from .ts_base import TestSuiteBase

from mmgen.cfg import gc
from mmgen.color import yellow
from mmgen.cfgfile import CfgFileSampleSys,CfgFileSampleUsr,cfg_file_sample

class TestSuiteCfgFile(TestSuiteBase):
	'CfgFile API'
	networks = ('btc',)
	tmpdir_nums = [40]
	base_passthru_opts = ()
	color = True

	cmd_group = (
		('sysfile',                  (40,'init with system cfg sample file in place', [])),
		('no_metadata_sample',       (40,'init with unversioned cfg sample file', [])),
		('altered_sample',           (40,'init with user-modified cfg sample file', [])),
		('old_sample',               (40,'init with old v2 cfg sample file', [])),
		('old_sample_bad_var',       (40,'init with old v2 cfg sample file and bad variable in mmgen.cfg', [])),
		('autoset_opts',             (40,'setting autoset opts', [])),
		('autoset_opts_cmdline',     (40,'setting autoset opts (override on cmdline)', [])),
		('autoset_opts_bad',         (40,'setting autoset opts (bad value in cfg file)', [])),
		('autoset_opts_bad_cmdline', (40,'setting autoset opts (bad param on cmdline)', [])),
		('coin_specific_vars',       (40,'setting coin-specific vars', [])),
		('chain_names',              (40,'setting chain names', [])),
		('mnemonic_entry_modes',     (40,'setting mnemonic entry modes', [])),
	)

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		self.spawn_env['MMGEN_TEST_SUITE_CFGTEST'] = '1'

	def spawn_test(self,args=[],extra_desc='',pexpect_spawn=None):
		return self.spawn(
			'test/misc/cfg.py',
			[f'--data-dir={self.path("data_dir")}'] + args,
			cmd_dir = '.',
			extra_desc = extra_desc,
			pexpect_spawn = pexpect_spawn )

	def path(self,id_str):
		return {
			'ref':         'test/ref/mmgen.cfg',
			'data_dir':    '{}/data_dir'.format(self.tmpdir),
			'shared_data': '{}/data_dir/{}'.format(self.tmpdir,CfgFileSampleSys.test_fn_subdir),
			'usr':         '{}/data_dir/mmgen.cfg'.format(self.tmpdir),
			'sys':         '{}/data_dir/{}/mmgen.cfg'.format(self.tmpdir,CfgFileSampleSys.test_fn_subdir),
			'sample':      '{}/data_dir/mmgen.cfg.sample'.format(os.path.abspath(self.tmpdir)),
		}[id_str]

	def copy_sys_sample(self):
		os.makedirs(self.path('shared_data'),exist_ok=True)
		shutil.copy2(self.path('ref'),self.path('sys'))

	def sysfile(self):
		self.copy_sys_sample()
		t = self.spawn_test()
		t.read()
		u = read_from_file(self.path('usr'))
		S = read_from_file(self.path('sys'))
		assert u[-1] == '\n', u
		assert u.replace('\r\n','\n') == S, 'u != S'
		self.check_replaced_sample()
		return t

	def check_replaced_sample(self):
		S = read_from_file(self.path('sys'))
		s = read_from_file(self.path('sample'))
		assert s[-1] == '\n', s
		assert S.splitlines() == s.splitlines()[:-1], 'sys != sample[:-1]'

	def bad_sample(self,s,e):
		write_to_file(self.path('sample'),s)
		t = self.spawn_test()
		t.expect(e)
		t.read()
		self.check_replaced_sample()
		return t

	def no_metadata_sample(self):
		self.copy_sys_sample()
		s = read_from_file(self.path('sys'))
		e = CfgFileSampleUsr.out_of_date_fs.format(self.path('sample'))
		return self.bad_sample(s,e)

	def altered_sample(self):
		s = '\n'.join(read_from_file(self.path('sample')).splitlines()[1:]) + '\n'
		e = CfgFileSampleUsr.altered_by_user_fs.format(self.path('sample'))
		return self.bad_sample(s,e)

	def old_sample_common(self,old_set=False,args=[],pexpect_spawn=False):
		s = read_from_file(self.path('sys'))
		d = s.replace('monero_','zcash_').splitlines()
		a1 = ['','# Uncomment to make foo true:','# foo true']
		a2 = ['','# Uncomment to make bar false:','# bar false']
		d = d + a1 + a2
		chk = cfg_file_sample.cls_make_metadata(d)
		write_to_file(self.path('sample'),'\n'.join(d+chk) + '\n')

		t = self.spawn_test(args=args,pexpect_spawn=pexpect_spawn)

		t.expect('options have changed')
		for s in ('have been added','monero_','have been removed','zcash_','foo','bar'):
			t.expect(s)

		if old_set:
			for s in ('must be deleted','bar','foo'):
				t.expect(s)

		cp = CfgFileSampleUsr.details_confirm_prompt + ' (y/N): '

		t.expect(cp,'y')

		for s in ('CHANGES','Removed','# zcash_','# foo','# bar','Added','# monero_'):
			t.expect(s)

		if t.pexpect_spawn: # view and exit pager
			time.sleep(1 if cfg.exact_output else t.send_delay)
			t.send('q')

		t.expect(cp,'n')

		if old_set:
			t.expect('unrecognized option')
			t.req_exit_val = 1

		if args == ['parse_test']:
			t.expect('parsed chunks: 29')
			t.expect('usr cfg: testnet=true rpc_password=passwOrd')

		if not old_set:
			self.check_replaced_sample()

		return t

	def old_sample(self):
		d = ['testnet true','rpc_password passwOrd']
		write_to_file(self.path('usr'),'\n'.join(d) + '\n')
		return self.old_sample_common(args=['parse_test'])

	def old_sample_bad_var(self):
		d = ['foo true','bar false']
		write_to_file(self.path('usr'),'\n'.join(d) + '\n')
		return self.old_sample_common(
			old_set       = True,
			pexpect_spawn = False if gc.platform == 'win' else True )

	def _autoset_opts(self,args=[],text='rpc_backend aiohttp\n'):
		write_to_file( self.path('usr'), text )
		imsg(yellow(f'Wrote cfg file:\n  {text}'))
		return self.spawn_test(args=args)

	def autoset_opts(self):
		return self._autoset_opts(args=['autoset_opts'])

	def autoset_opts_cmdline(self):
		return self._autoset_opts(args=['--rpc-backend=curl','autoset_opts_cmdline'])

	def _autoset_opts_bad(self,kwargs):
		t = self._autoset_opts(**kwargs)
		t.req_exit_val = 1
		return t

	def autoset_opts_bad(self):
		return self._autoset_opts_bad({'text':'rpc_backend foo\n'})

	def autoset_opts_bad_cmdline(self):
		return self._autoset_opts_bad({'args':['--rpc-backend=foo']})

	def coin_specific_vars(self):
		"""
		ensure that derived classes explicitly set these variables
		"""
		d = [
			'btc_max_tx_fee 1.2345',
			'eth_max_tx_fee 5.4321',
			'btc_ignore_daemon_version true',
			'eth_ignore_daemon_version true'
		]
		write_to_file(self.path('usr'),'\n'.join(d) + '\n')
		imsg(yellow('Wrote cfg file:\n  {}'.format('\n  '.join(d))))

		for coin,res1_chk,res2_chk,res2_chk_eq in (
			('BTC','True', '1.2345',True),
			('LTC','False','1.2345',False),
			('BCH','False','1.2345',False),
			('ETH','True', '5.4321',True),
			('ETC','False','5.4321',False)
		):
			if cfg.no_altcoin and coin != 'BTC':
				continue
			t = self.spawn_test(
				args = [
					f'--coin={coin}',
					'coin_specific_vars',
					'ignore_daemon_version',
					'max_tx_fee'
				],
				extra_desc=f'({coin})' )
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

		txt = 'mnemonic_entry_modes mmgen:full bip39:short'
		write_to_file(self.path('usr'),txt+'\n')
		imsg(yellow(f'Wrote cfg file: {txt!r}'))
		t = run("{'mmgen': 'full', 'bip39': 'short'}")
		# check that set_dfl_entry_mode() set the mode correctly:
		t.expect('mmgen: full')
		t.expect('bip39: short')
		return t

	def chain_names(self):

		if cfg.no_altcoin:
			return 'skip'

		def run(chk,testnet):
			for coin,chain_chk in (('ETH',chk),('ETC',None)):
				t = self.spawn_test(
					args = [f'--coin={coin}',f'--testnet={(0,1)[testnet]}','coin_specific_vars','chain_names'],
					extra_desc = f'({coin} testnet={testnet!r:5} chain_names={chain_chk})' )
				chain = t.expect_getend('chain_names: ')
				if chain_chk:
					assert chain == chain_chk, f'{chain} != {chain_chk}'
				else:
					assert chain != chain_chk, f'{chain} == {chain_chk}'
				t.read()
				t.ok()
			return t

		txt = 'eth_mainnet_chain_names istanbul constantinople'
		write_to_file(self.path('usr'),txt+'\n')
		imsg(yellow(f'Wrote cfg file: {txt!r}'))
		t = run("['istanbul', 'constantinople']",False)
		t = run(None,True)

		txt = 'eth_testnet_chain_names rinkeby'
		write_to_file(self.path('usr'),txt+'\n')
		imsg(yellow(f'Wrote cfg file: {txt!r}'))
		t = run(None,False)
		t = run("['rinkeby']",True)

		t.skip_ok = True
		return t
