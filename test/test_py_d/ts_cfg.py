#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
ts_misc.py: CfgFile tests for the MMGen test.py test suite
"""

import shutil

from ..include.common import *
from .ts_base import *
from mmgen.cfg import *

class TestSuiteCfg(TestSuiteBase):
	'CfgFile API'
	networks = ('btc',)
	tmpdir_nums = [40]
	base_passthru_opts = ()

	cmd_group = (
		('nosysfile',          (40,'init with missing system cfg sample file', [])),
		('sysfile',            (40,'init with system cfg sample file in place', [])),
		('no_metadata_sample', (40,'init with unversioned cfg sample file', [])),
		('altered_sample',     (40,'init with user-modified cfg sample file', [])),
		('old_sample',         (40,'init with old v2 cfg sample file', [])),
		('old_sample_bad_var', (40,'init with old v2 cfg sample file and bad variable in mmgen.cfg', [])),
		('coin_specific_vars', (40,'test setting of coin-specific vars', [])),
		('chain_names',        (40,'test setting of chain names', [])),
		('mnemonic_entry_modes',(40,'test setting of mnemonic entry modes', [])),
	)

	def __init__(self,trunner,cfgs,spawn):
		os.environ['MMGEN_TEST_SUITE_CFGTEST'] = '1'
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)

	def spawn_test(self,args=[],extra_desc=''):
		return self.spawn(
			'test/misc/cfg.py',
			[f'--data-dir={self.path("data_dir")}'] + args,
			cmd_dir = '.',
			extra_desc = extra_desc )

	def path(self,id_str):
		return {
			'ref':         'test/ref/mmgen.cfg',
			'data_dir':    '{}/data_dir'.format(self.tmpdir),
			'shared_data': '{}/data_dir/{}'.format(self.tmpdir,CfgFileSampleSys.test_fn_subdir),
			'usr':         '{}/data_dir/mmgen.cfg'.format(self.tmpdir),
			'sys':         '{}/data_dir/{}/mmgen.cfg'.format(self.tmpdir,CfgFileSampleSys.test_fn_subdir),
			'sample':      '{}/data_dir/mmgen.cfg.sample'.format(self.tmpdir),
		}[id_str]

	def nosysfile(self):
		t = self.spawn_test()
		errstr = CfgFile.file_not_found_fs.format(CfgFileSampleSys.desc,self.path('shared_data')+'/mmgen.cfg')
		for i in (1,2,3,4,5):
			t.expect(errstr)
		for k in ('usr','sys','sample'):
			t.expect('{} cfg file:\s+{}'.format(capfirst(k),self.path(k)),regex=True)
			assert not os.path.exists(self.path(k)), self.path(k)
		t.read()
		return t

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

	def old_sample_common(self,old_set=False,args=[]):
		s = read_from_file(self.path('sys'))
		d = s.replace('monero_','zcash_').splitlines()
		a1 = ['','# Uncomment to make foo true:','# foo true']
		a2 = ['','# Uncomment to make bar false:','# bar false']
		d = d + a1 + a2
		chk = CfgFileSample.cls_make_metadata(d)
		write_to_file(self.path('sample'),'\n'.join(d+chk) + '\n')

		t = self.spawn_test(args=args)

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
		t.expect(cp,'n')

		if old_set:
			t.expect('unrecognized option')
			t.req_exit_val = 1

		if args == ['parse_test']:
			t.expect('parsed chunks: 29')
			t.expect('usr cfg: testnet=true rpc_password=passwOrd')

		t.read()

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
		return self.old_sample_common(old_set=True)

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
			t.read()
			return t

		txt = 'mnemonic_entry_modes mmgen:full bip39:short'
		write_to_file(self.path('usr'),txt+'\n')
		imsg(yellow(f'Wrote cfg file: "{txt}"'))
		return run("{'mmgen': 'full', 'bip39': 'short'}")

	def chain_names(self):

		def run(chk,testnet):
			for coin,chain_chk in (('ETH',chk),('ETC',None)):
				t = self.spawn_test(
					args       = [f'--coin={coin}',f'--testnet={(0,1)[testnet]}','coin_specific_vars','chain_name'],
					extra_desc = f'({coin} testnet={testnet} chain={chain_chk})' )
				chain = t.expect_getend('chain_name: ')
				if chain_chk:
					assert chain == chain_chk, f'{chain} != {chain_chk}'
				else:
					assert chain != chain_chk, f'{chain} == {chain_chk}'
				t.read()
				t.ok()
			return t

		write_to_file(self.path('usr'),'eth_mainnet_chain_name foobar\n')
		imsg(yellow('Wrote cfg file: "eth_mainnet_chain_name foobar"'))
		t = run('foobar',False)
		t = run(None,True)

		write_to_file(self.path('usr'),'eth_testnet_chain_name foobar\n')
		imsg(yellow('Wrote cfg file: "eth_testnet_chain_name foobar"'))
		t = run(None,False)
		t = run('foobar',True)

		t.skip_ok = True
		return t
