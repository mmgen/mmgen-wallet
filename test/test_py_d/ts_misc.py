#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
	networks = ('btc','ltc','bch','eth','xmr')
	tmpdir_nums = []
	passthru_opts = ('daemon_data_dir','rpc_port','coin','testnet')
	cmd_group = (
		('usage',                 (1,'usage message',[])),
		('version',               (1,'version message',[])),
		('helpscreens',           (1,'help screens',             [])),
		('longhelpscreens',       (1,'help screens (--longhelp)',[])),
		('show_hash_presets',     (1,'info screen (--show-hash-presets)',[])),
		('tool_help',             (1,"'mmgen-tool' usage screen",[])),
		('test_help',             (1,"'test.py' help screens",[])),
	)

	def usage(self):
		t = self.spawn(f'mmgen-walletgen',['foo'])
		t.expect('USAGE: mmgen-walletgen')
		t.expect('SystemExit: 1')
		t.req_exit_val = 1
		return t

	def version(self):
		t = self.spawn(f'mmgen-tool',['--version'])
		t.expect('MMGEN-TOOL version')
		return t

	def helpscreens(self,arg='--help',scripts=(),expect='USAGE:.*OPTIONS:'):

		scripts = list(scripts) or [s.replace('mmgen-','') for s in os.listdir('cmds')]

		if 'tx' not in self.proto.mmcaps:
			scripts = [s for s in scripts if not (s == 'regtest' or s.startswith('tx'))]

		if self.proto.coin not in ('BTC','XMR') and 'xmrwallet' in scripts:
			scripts.remove('xmrwallet')

		for s in sorted(scripts):
			t = self.spawn(f'mmgen-{s}',[arg],extra_desc=f'(mmgen-{s})')
			t.expect(expect,regex=True)
			t.read()
			t.ok()
			t.skip_ok = True

		return t

	def longhelpscreens(self):
		return self.helpscreens(arg='--longhelp',expect='USAGE:.*LONG OPTIONS:')

	def show_hash_presets(self):
		return self.helpscreens(
			arg = '--show-hash-presets',
			scripts = (
					'walletgen','walletconv','walletchk','passchg','subwalletgen',
					'addrgen','keygen','passgen',
					'txsign','txdo','txbump'),
			expect = 'Available parameters.*Preset' )

	def tool_help(self):

		if os.getenv('PYTHONOPTIMIZE') == '2':
			ymsg('Skipping tool help with PYTHONOPTIMIZE=2 (no docstrings)')
			return 'skip'

		for args in (
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
		('output_jp', (1,"Japanese text", [])),
		('oneshot_warning', (1,"Oneshot warnings", []))
	)
	color = True

	def screen_output(self,lang):
		return self.spawn('test/misc/utf8_output.py',[lang],cmd_dir='.')

	def output_gr(self): return self.screen_output('gr')
	def output_ru(self): return self.screen_output('ru')
	def output_zh(self): return self.screen_output('zh')
	def output_jp(self): return self.screen_output('jp')

	def oneshot_warning(self):
		nl = '\r\n' if g.platform == 'win' or opt.pexpect_spawn else '\n'
		t = self.spawn('test/misc/oneshot_warning.py',cmd_dir='.')
		for s in (
			f'pw{nl}wg1',
			'foo is experimental',
			'wg2', 'The bar command is dangerous',
			'wg3', 'baz variant alpha',
			'wg4', 'baz variant beta',
			'w1', 'foo variant alpha',
			'w2', 'foo variant beta',
			'w3', 'bar is experimental',
			'pw',
			"passphrase from file 'A'",
			"passphrase from file 'B'",
			f'wg1{nl}wg2{nl}wg3{nl}wg4{nl}w1{nl}w2{nl}w3',
			'pw',
			"passphrase from file 'A'",
			"passphrase from file 'B'",
			f'wg1{nl}wg2{nl}wg3{nl}wg4{nl}w1{nl}w2{nl}w3',
			'bottom',
		):
			t.expect(s)
		return t

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
		return self.spawn('mmgen-addrgen',['--outdir='+self.tmpdir,'--type='+atype,dfl_words_file,'1-2'])

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
