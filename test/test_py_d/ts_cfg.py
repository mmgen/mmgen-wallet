#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
#
# Project source code repository: https://github.com/mmgen/mmgen
# Licensed according to the terms of GPL Version 3.  See LICENSE for details.

"""
ts_misc.py: CfgFile tests for the MMGen test.py test suite
"""

import shutil

from test.common import *
from test.test_py_d.ts_base import *
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
	)

	def __init__(self,trunner,cfgs,spawn):
		os.environ['MMGEN_TEST_SUITE_CFGTEST'] = '1'
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)

	def spawn_test(self,args=[]):
		return self.spawn('test/misc/cfg.py',['--data-dir={}'.format(self.path('data_dir'))]+args,cmd_dir='.')

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
			t.expect('{} cfg: {}'.format(k,self.path(k)))
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
			t.req_exit_val = 2

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
