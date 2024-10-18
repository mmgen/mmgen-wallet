#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
test.cmdtest_d.ct_misc: Miscellaneous test groups for the cmdtest.py test suite
"""

import sys, re

from mmgen.util import die

from ..include.common import cfg, start_test_daemons, stop_test_daemons, imsg
from .common import get_file_with_ext, dfl_words_file
from .ct_base import CmdTestBase
from .ct_main import CmdTestMain

class CmdTestDev(CmdTestBase):
	'developer scripts'
	networks = ('btc',)
	cmd_group = (
		('compute_file_chksum', 'scripts/compute-file-chksum.py'),
		('create_bip_hd_chain_params', 'scripts/create-bip-hd-chain-params.py'),
	)
	tmpdir_nums = [99]
	color = True

	def _spawn(self, script, args):
		return self.spawn(script, args, cmd_dir='.', no_exec_wrapper=True)

	def compute_file_chksum(self):
		t = self._spawn('scripts/compute-file-chksum.py', ['test/ref/25EFA3[2.34].testnet.rawtx'])
		t.expect('3df942')
		return t

	def create_bip_hd_chain_params(self):
		t = self._spawn('scripts/create-bip-hd-chain-params.py', ['test/ref/altcoin/slip44-mini.json'])
		t.expect('[defaults]')
		t.expect(r"secp.*0488ade4.*0488b21e.*0'\/0\/0", regex=True)
		t.expect('[bip-44]')
		t.expect('[bip-49]')
		t.match_expect_list(
			['0', 'BTC', 'x', 'm', 'P2SH', '049d7878', '049d7cb2', '80', '05', 'x', 'Bitcoin', '1'])
		return t

class CmdTestMisc(CmdTestBase):
	'miscellaneous tests (RPC backends, xmrwallet_txview, term)'
	networks = ('btc',)
	tmpdir_nums = [99]
	passthru_opts = ('daemon_data_dir', 'rpc_port')
	cmd_group = (
		('rpc_backends',         'RPC backends'),
		('bch_txview_legacy1',   '‘mmgen-tool --coin=bch --cashaddr=0 txview terse=0’'),
		('bch_txview_legacy2',   '‘mmgen-tool --coin=bch --cashaddr=0 txview terse=1’'),
		('bch_txview_cashaddr1', '‘mmgen-tool --coin=bch --cashaddr=1 txview terse=0’'),
		('bch_txview_cashaddr2', '‘mmgen-tool --coin=bch --cashaddr=1 txview terse=1’'),
		('xmrwallet_txview',     '‘mmgen-xmrwallet txview’'),
		('xmrwallet_txlist',     '‘mmgen-xmrwallet txlist’'),
		('coin_daemon_info',     '‘examples/coin-daemon-info.py’'),
		('examples_bip_hd',      '‘examples/bip_hd.py’'),
		('term_echo',            'term.set("echo")'),
		('term_cleanup',         'term.register_cleanup()'),
	)
	need_daemon = True
	color = True

	def rpc_backends(self):
		backends = cfg._autoset_opts['rpc_backend'][1]
		for b in backends:
			t = self.spawn_chk('mmgen-tool', [f'--rpc-backend={b}', 'daemon_version'], extra_desc=f'({b})')
		return t

	def _bch_txview(self, view_pref, terse, expect):
		if cfg.no_altcoin:
			return 'skip'
		tx = 'test/ref/bitcoin_cash/895108-BCH[2.65913].rawtx'
		t = self.spawn('mmgen-tool', ['--coin=bch', f'--cashaddr={view_pref}', 'txview', tx, f'terse={terse}'])
		#t = self.spawn('mmgen-tool', ['--coin=bch', '--longhelp'])
		t.expect(expect)
		return t

	def bch_txview_legacy1(self):
		return self._bch_txview(0, 0, '[qzuffa536e0eqfwz3smapckhlw9wge4p5spvx5j7h7]')

	def bch_txview_legacy2(self):
		return self._bch_txview(0, 1, '[qzuffa536e0eqfwz3smapckhlw9wge4p5spvx5j7h7]')

	def bch_txview_cashaddr1(self):
		return self._bch_txview(1, 0, '[1HpynST7vkLn8yNtdrqPfeghexZk4sdB3W]')

	def bch_txview_cashaddr2(self):
		return self._bch_txview(1, 1, '[1HpynST7vkLn8yNtdrqPfeghexZk4sdB3W]')

	def xmrwallet_txview(self, op='txview'):
		if cfg.no_altcoin:
			return 'skip'
		files = get_file_with_ext('test/ref/monero', 'tx', no_dot=True, delete=False, return_list=True)
		t = self.spawn('mmgen-xmrwallet', [op] + files)
		res = t.read(strip_color=True)
		if op == 'txview':
			for s in (
				'Amount:    0.74 XMR',
				'Dest:      56VQ9M6k',
			):
				assert s in res, f'{s} not in {res}'
		elif op == 'txlist':
			assert re.search('3EBD06-.*D94583-.*8BFA29-', res, re.DOTALL)
		return t

	def xmrwallet_txlist(self):
		return self.xmrwallet_txview(op='txlist')

	def examples_bip_hd(self):
		if cfg.no_altcoin:
			return 'skip'
		return self.spawn('examples/bip_hd.py', cmd_dir='.')

	def coin_daemon_info(self):
		if cfg.no_altcoin:
			coins = ['btc']
		else:
			coins = ['btc', 'ltc', 'eth']
			start_test_daemons('ltc', 'eth')
		t = self.spawn('examples/coin-daemon-info.py', coins, cmd_dir='.')
		for coin in coins:
			t.expect(coin.upper() + r'\s+mainnet\s+Up', regex=True)
		if cfg.pexpect_spawn:
			t.send('q')
		if not cfg.no_altcoin:
			stop_test_daemons('ltc', 'eth')
		return t

	def term_echo(self):

		def test_echo():
			t.expect('echo> ', 'foo\n')
			t.expect('foo')

		def test_noecho():
			t.expect('noecho> ', 'foo\n')
			import pexpect
			try:
				t.expect('foo')
			except pexpect.TIMEOUT:
				imsg('[input not echoed - OK]')
			else:
				die('TestSuiteException', 'Terminal echoed in noecho mode!')
			t.send('x')

		if self.skip_for_win('no termios support') or self.skip_for_mac('termios.ECHO issues'):
			return 'skip'

		t = self.spawn('test/misc/term_ni.py', ['echo'], cmd_dir='.', pexpect_spawn=True, timeout=1)
		t.p.logfile = None
		t.p.logfile_read = sys.stdout if cfg.verbose or cfg.exact_output else None
		t.p.logfile_send = None

		test_noecho()
		test_echo()
		test_noecho()

		return t

	def term_cleanup(self):
		if self.skip_for_win('no termios support'):
			return 'skip'
		return self.spawn('test/misc/term_ni.py', ['cleanup'], cmd_dir='.', pexpect_spawn=True)

class CmdTestOutput(CmdTestBase):
	'screen output'
	networks = ('btc',)
	cmd_group = (
		('output_gr',            (1, 'Greek text', [])),
		('output_ru',            (1, 'Russian text', [])),
		('output_zh',            (1, 'Chinese text', [])),
		('output_jp',            (1, 'Japanese text', [])),
		('oneshot_warning',      (1, 'Oneshot warnings', [])),
		('oneshot_warning_term', (1, 'Oneshot warnings (pexpect_spawn)', []))
	)
	color = True

	def screen_output(self, lang):
		return self.spawn('test/misc/utf8_output.py', [lang], cmd_dir='.')

	def output_gr(self):
		return self.screen_output('gr')
	def output_ru(self):
		return self.screen_output('ru')
	def output_zh(self):
		return self.screen_output('zh')
	def output_jp(self):
		return self.screen_output('jp')

	def oneshot_warning(self, pexpect_spawn=None):
		t = self.spawn('test/misc/oneshot_warning.py', cmd_dir='.', pexpect_spawn=pexpect_spawn)
		nl = '\r\n' if sys.platform == 'win32' or t.pexpect_spawn else '\n'
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

	def oneshot_warning_term(self):
		if self.skip_for_win('no pexpect_spawn'):
			return 'skip'
		return self.oneshot_warning(pexpect_spawn=True)

class CmdTestRefTX(CmdTestMain, CmdTestBase):
	'create a reference transaction file (administrative command)'
	segwit_opts_ok = False
	passthru_opts = ('daemon_data_dir', 'rpc_port', 'coin', 'testnet')
	tmpdir_nums = [31, 32, 33, 34]
	need_daemon = True
	cmd_group = (
		('ref_tx_addrgen1', (31, 'address generation (legacy)',     [[[], 1]])),
		('ref_tx_addrgen2', (32, 'address generation (compressed)', [[[], 1]])),
		('ref_tx_addrgen3', (33, 'address generation (segwit)',     [[[], 1]])),
		('ref_tx_addrgen4', (34, 'address generation (bech32)',     [[[], 1]])),
		('ref_tx_txcreate',
			(31, 'transaction creation',
			([['addrs'], 31], [['addrs'], 32], [['addrs'], 33], [['addrs'], 34]))
		),
	)

	def __init__(self, trunner, cfgs, spawn):
		if cfgs:
			for n in self.tmpdir_nums:
				cfgs[str(n)].update({
					'addr_idx_list': '1-2',
					'segwit': n in (33, 34),
					'dep_generators': {'addrs':'ref_tx_addrgen'+str(n)[-1]}
				})
		CmdTestMain.__init__(self, trunner, cfgs, spawn)

	def ref_tx_addrgen(self, atype):
		if atype not in self.proto.mmtypes:
			return
		return self.spawn('mmgen-addrgen', ['--outdir='+self.tmpdir, '--type='+atype, dfl_words_file, '1-2'])

	def ref_tx_addrgen1(self):
		return self.ref_tx_addrgen(atype='L')
	def ref_tx_addrgen2(self):
		return self.ref_tx_addrgen(atype='C')
	def ref_tx_addrgen3(self):
		return self.ref_tx_addrgen(atype='S')
	def ref_tx_addrgen4(self):
		return self.ref_tx_addrgen(atype='B')

	def ref_tx_txcreate(self, f1, f2, f3, f4):
		sources = ['31', '32']
		if 'S' in self.proto.mmtypes:
			sources += ['33']
		if 'B' in self.proto.mmtypes:
			sources += ['34']
		return self.txcreate_common(
				addrs_per_wallet = 2,
				sources          = sources,
				add_args         = ['--locktime=1320969600'],
				do_label         = True)
