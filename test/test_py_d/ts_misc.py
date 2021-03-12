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
ts_misc.py: Miscellaneous test groups for the test.py test suite
"""

from mmgen.globalvars import g
from ..include.common import *
from .common import *
from .ts_base import *
from .ts_main import TestSuiteMain

class TestSuiteMisc(TestSuiteBase):
	'miscellaneous tests (RPC backends)'
	networks = ('btc',)
	tmpdir_nums = [99]
	passthru_opts = ('daemon_data_dir','rpc_port')
	cmd_group = (
		('rpc_backends', 'RPC backends'),
	)

	def rpc_backends(self):
		backends = g.autoset_opts['rpc_backend'][1]
		for b in backends:
			t = self.spawn_chk('mmgen-tool',[f'--rpc-backend={b}','daemon_version'],extra_desc=f' ({b})')
		return t

class TestSuiteHelp(TestSuiteBase):
	'help, info and usage screens'
	networks = ('btc','ltc','bch','eth')
	tmpdir_nums = []
	passthru_opts = ('daemon_data_dir','rpc_port','coin','testnet')
	cmd_group = (
		('helpscreens',           (1,'help screens',             [])),
		('longhelpscreens',       (1,'help screens (--longhelp)',[])),
		('opt_show_hash_presets', (1,'info screen (--show-hash-presets)',[])),
		('tool_help',             (1,"'mmgen-tool' usage screen",[])),
		('test_help',             (1,"'test.py' help screens",[])),
	)
	def helpscreens(self,
		arg = '--help',
		scripts = ( 'walletgen','walletconv','walletchk','passchg','subwalletgen',
					'addrgen','keygen','passgen',
					'seedsplit','seedjoin',
					'txcreate','txsign','txsend','txdo','txbump',
					'addrimport','autosign')
		):
		if self.test_name == 'helpscreens' and self.proto.base_coin != 'ETH':
			scripts += ('regtest',)
		for s in scripts:
			t = self.spawn_chk(f'mmgen-{s}',[arg],extra_desc=f'(mmgen-{s})',no_output=True)
		return t

	def longhelpscreens(self):
		return self.helpscreens(arg='--longhelp')

	def opt_show_hash_presets(self):
		return self.helpscreens(
			arg = '--show-hash-presets',
			scripts = (
					'walletgen','walletconv','walletchk','passchg','subwalletgen',
					'addrgen','keygen','passgen',
					'txsign','txdo','txbump'))

	def tool_help(self):
		for args in (
			['--help'],
			['--longhelp'],
			['help'],
			['usage'],
			['help','randpair']
		):
			t = self.spawn_chk('mmgen-tool',args,extra_desc=f"('mmgen-tool {fmt_list(args,fmt='bare')}')")
		return t

	def test_help(self):
		for args in (
			['--help'],
			['--list-cmds'],
			['--list-cmd-groups']
		):
			t = self.spawn_chk('test.py',args,cmd_dir='test',extra_desc=f"('test.py {fmt_list(args,fmt='bare')}')")
		return t

class TestSuiteOutput(TestSuiteBase):
	'screen output'
	networks = ('btc',)
	tmpdir_nums = []
	cmd_group = (
		('output_gr', (1,"Greek text", [])),
		('output_ru', (1,"Russian text", [])),
		('output_zh', (1,"Chinese text", [])),
		('output_jp', (1,"Japanese text", []))
	)

	def screen_output(self,lang):
		t = self.spawn('test/misc/utf8_output.py',[lang],cmd_dir='.')
		t.read()
		return t

	def output_gr(self): return self.screen_output('gr')
	def output_ru(self): return self.screen_output('ru')
	def output_zh(self): return self.screen_output('zh')
	def output_jp(self): return self.screen_output('jp')

class TestSuiteRefTX(TestSuiteMain,TestSuiteBase):
	'create a reference transaction file (administrative command)'
	segwit_opts_ok = False
	passthru_opts = ('daemon_data_dir','rpc_port','coin','testnet')
	tmpdir_nums = [31,32,33,34]
	cmd_group = (
		('ref_tx_addrgen1', (31,'address generation (legacy)', [[[],1]])),
		('ref_tx_addrgen2', (32,'address generation (compressed)', [[[],1]])),
		('ref_tx_addrgen3', (33,'address generation (segwit)', [[[],1]])),
		('ref_tx_addrgen4', (34,'address generation (bech32)', [[[],1]])),
		('ref_tx_txcreate', (31,'transaction creation',
								([['addrs'],31],[['addrs'],32],[['addrs'],33],[['addrs'],34]))),
	)

	def __init__(self,trunner,cfgs,spawn):
		if cfgs:
			for n in self.tmpdir_nums:
				cfgs[str(n)].update({   'addr_idx_list': '1-2',
										'segwit': n in (33,34),
										'dep_generators': { 'addrs':'ref_tx_addrgen'+str(n)[-1] }})
		return TestSuiteMain.__init__(self,trunner,cfgs,spawn)

	def ref_tx_addrgen(self,atype):
		if atype not in self.proto.mmtypes:
			return
		t = self.spawn('mmgen-addrgen',['--outdir='+self.tmpdir,'--type='+atype,dfl_words_file,'1-2'])
		t.read()
		return t

	def ref_tx_addrgen1(self): return self.ref_tx_addrgen(atype='L')
	def ref_tx_addrgen2(self): return self.ref_tx_addrgen(atype='C')
	def ref_tx_addrgen3(self): return self.ref_tx_addrgen(atype='S')
	def ref_tx_addrgen4(self): return self.ref_tx_addrgen(atype='B')

	def ref_tx_txcreate(self,f1,f2,f3,f4):
		sources = ['31','32']
		if 'S' in self.proto.mmtypes: sources += ['33']
		if 'B' in self.proto.mmtypes: sources += ['34']
		return self.txcreate_common(
									addrs_per_wallet = 2,
									sources          = sources,
									add_args         = ['--locktime=1320969600'],
									do_label         = True )
