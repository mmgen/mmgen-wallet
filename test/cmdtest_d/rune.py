#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.rune: THORChain RUNE tests for the cmdtest.py test suite
"""

from hashlib import md5

from mmgen.fileutil import get_data_from_file

from .include.common import dfl_sid, dfl_words_file
from .include.proxy import TestProxy
from .httpd.thornode.rpc import ThornodeRPCServer
from .ethdev import CmdTestEthdevMethods
from .base import CmdTestBase
from .shared import CmdTestShared
from .swap import CmdTestSwapMethods

class CmdTestRune(CmdTestEthdevMethods, CmdTestBase, CmdTestShared):
	'THORChain RUNE tracking wallet and transacting operations'
	networks = ('rune',)
	passthru_opts = ('coin', 'http_timeout')
	tmpdir_nums = [50]
	color = True
	menu_prompt = 'efresh balance:\b'
	txhex_chksum = '83f85785'

	cmd_group_in = (
		('subgroup.init',   []),
		('subgroup.main',   ['init']),
		('rpc_server_stop', 'stopping the Thornode RPC server'),
	)
	cmd_subgroups = {
		'init': (
			'initializing wallets',
			('addrgen',    'generating addresses'),
			('addrimport', 'importing addresses'),
		),
		'main': (
			'tracking wallet and transaction operations',
			('twview',               'viewing unspent outputs in tracking wallet'),
			('bal_refresh',          'refreshing address balance in tracking wallet'),
			('txcreate1',            'creating a transaction'),
			('txsign1',              'signing the transaction'),
			('txsend1_test',         'testing whether the transaction can be sent'),
			('txsend1',              'sending the transaction'),
			('txhex1',               'dumping the transaction hex'),
		),
	}

	def __init__(self, cfg, trunner, cfgs, spawn):
		CmdTestBase.__init__(self, cfg, trunner, cfgs, spawn)
		if trunner is None:
			return

		self.eth_opts = [f'--outdir={self.tmpdir}', '--regtest=1', '--quiet']
		self.eth_opts_noquiet = [f'--outdir={self.tmpdir}', '--regtest=1']

		self.rune_opts = self.eth_opts

		from mmgen.protocol import init_proto
		self.proto = init_proto(cfg, network_id=self.proto.coin + '_rt', need_amt=True)
		self.spawn_env['MMGEN_BOGUS_SEND'] = ''

		self.rpc_server = ThornodeRPCServer(cfg)
		self.rpc_server.start()

		TestProxy(self, cfg)

		self.txhex_file = f'{self.tmpdir}/tx_dump.hex'

	def addrgen(self):
		return self._addrgen()

	def addrimport(self):
		return self._addrimport()

	def twview(self):
		return self.spawn('mmgen-tool', self.rune_opts + self.add_eth_opts + ['twview'])

	def bal_refresh(self):
		t = self.spawn(
			'mmgen-tool',
			self.rune_opts + self.add_eth_opts + ['listaddresses', 'interactive=1'])
		t.expect(self.menu_prompt, 'R')
		t.expect('menu): ', '3\n')
		t.expect('(y/N): ', 'y')
		t.expect(r'Total RUNE: \S*\D9876.54321321\D', regex=True)
		t.expect('address #3 refreshed')
		t.expect(self.menu_prompt, 'q')
		return t

	def txcreate1(self):
		t = self.spawn('mmgen-txcreate', self.rune_opts + ['98831F3A:X:2,54.321'])
		t.expect(self.menu_prompt, 'q')
		t.expect('spend from: ', '3\n')
		t.expect('(y/N): ', 'y') # add comment?
		t.expect('Comment: ', 'RUNE Boy\n')
		t.expect('view: ', 'y')
		t.expect('to continue: ', 'z')
		t.expect('(y/N): ', 'y') # save?
		t.written_to_file('Unsigned transaction')
		return t

	def txsign1(self):
		return self.txsign_ui_common(
			self.spawn(
				'mmgen-txsign',
				self.rune_opts + [self.get_file_with_ext('rawtx'), dfl_words_file],
				no_passthru_opts = ['coin']),
			has_label = True)

	def txsend1_test(self):
		return self._txsend(add_opts=['--test', f'--proxy=localhost:{TestProxy.port}'], test=True)

	def txsend1(self):
		return self._txsend()

	def _txsend(self, add_opts=[], *, test=False, dump_hex=False):
		t = self.spawn(
			'mmgen-txsend',
			self.rune_opts + add_opts + [self.get_file_with_ext('sigtx')],
			no_passthru_opts = ['coin'])
		t.expect('view: ', 'y')
		t.expect('to continue: ', 'z')
		t.expect('(y/N): ', 'n') # edit comment?
		if dump_hex:
			t.written_to_file('hex data')
		elif test:
			t.expect('can be sent')
		else:
			t.expect('to confirm: ', 'YES\n')
			t.expect('Transaction sent: ')
			if t.expect(['written to file', 'txid mismatch']):
				self.tr.warn('txid mismatch')
				return 'ok'
		return t

	def txhex1(self):
		t = self._txsend(add_opts=[f'--dump-hex={self.txhex_file}'], dump_hex=True)
		t.read()
		txhex = get_data_from_file(self.cfg, self.txhex_file, silent=True)
		if md5(txhex.encode()).hexdigest()[:8] != self.txhex_chksum:
			self.tr.warn('txid mismatch')
		return t

	def rpc_server_stop(self):
		return CmdTestSwapMethods._thornode_server_stop(
			self, attrname='rpc_server', name='Thornode RPC server')
