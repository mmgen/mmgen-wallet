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
test.cmdtest_d.ct_chainsplit: Forking scenario tests for the cmdtest.py test suite
This module is unmaintained and currently non-functional
"""

from mmgen.util import die

from .common import get_file_with_ext, rt_pw
from .ct_regtest import CmdTestRegtest

class CmdTestChainsplit(CmdTestRegtest):
	'forking scenario tests for the cmdtest.py test suite'
	cmd_group = (
		('split_setup',                  'regtest forking scenario setup'),
		('walletgen_bob',                'generating Bob’s wallet'),
		('addrgen_bob',                  'generating Bob’s addresses'),
		('addrimport_bob',               'importing Bob’s addresses'),
		('fund_bob',                     'funding Bob’s wallet'),
		('split_fork',                   'regtest split fork'),
		('split_start_btc',              'start regtest daemon (BTC)'),
		('split_start_b2x',              'start regtest daemon (B2X)'),
		('split_gen_btc',                'mining a block (BTC)'),
		('split_gen_b2x',                'mining 100 blocks (B2X)'),
		('split_do_split',               'creating coin splitting transactions'),
		('split_sign_b2x',               'signing B2X split transaction'),
		('split_sign_btc',               'signing BTC split transaction'),
		('split_send_b2x',               'sending B2X split transaction'),
		('split_send_btc',               'sending BTC split transaction'),
		('split_gen_btc',                'mining a block (BTC)'),
		('split_gen_b2x2',               'mining a block (B2X)'),
		('split_txdo_timelock_bad_btc',  'sending transaction with bad locktime (BTC)'),
		('split_txdo_timelock_good_btc', 'sending transaction with good locktime (BTC)'),
		('split_txdo_timelock_bad_b2x',  'sending transaction with bad locktime (B2X)'),
		('split_txdo_timelock_good_b2x', 'sending transaction with good locktime (B2X)'),
	)

	def split_setup(self):
		if self.proto.coin != 'BTC':
			die(1, 'Test valid only for coin BTC')
		self.coin = 'BTC'
		return self.setup()

	def split_fork(self):
		self.coin = 'B2X'
		t = self.spawn('mmgen-regtest', ['fork', 'btc'])
		t.expect('Creating fork from coin')
		t.expect('successfully created')
		t.ok()

	def split_start(self, coin):
		self.coin = coin
		t = self.spawn('mmgen-regtest', ['bob'])
		t.expect('Starting')
		t.expect('done')
		t.ok()

	def split_start_btc(self):
		self.regtest_start(coin='BTC')

	def split_start_b2x(self):
		self.regtest_start(coin='B2X')

	def split_gen_btc(self):
		self.regtest_generate(coin='BTC')

	def split_gen_b2x(self):
		self.regtest_generate(coin='B2X', num_blocks=100)

	def split_gen_b2x2(self):
		self.regtest_generate(coin='B2X')

	def split_do_split(self):
		self.coin = 'B2X'
		sid = self.regtest_user_sid('bob')
		t = self.spawn('mmgen-split', [
			'--bob',
			'--outdir='+self.tmpdir,
			'--tx-fees=0.0001,0.0003',
			sid+':S:1', sid+':S:2'])
		t.expect(r'\[q\]uit menu, .*?:.', 'q', regex=True)
		t.expect('outputs to spend: ', '1\n')

		for _ in ('timelocked', 'split'):
			for _ in ('fee', 'change'):
				t.expect('OK? (Y/n): ', 'y')
			t.do_comment(False)
			t.view_tx('t')

		t.written_to_file('Long chain (timelocked) transaction')
		t.written_to_file('Short chain transaction')
		t.ok()

	def split_sign(self, coin, ext):
		wf = get_file_with_ext(self.regtest_user_dir('bob', coin=coin.lower()), 'mmdat')
		txfile = self.get_file_with_ext(ext, no_dot=True)
		self.coin = coin
		self.txsign(txfile, wf, extra_opts=['--bob'])

	def split_sign_b2x(self):
		return self.regtest_sign(coin='B2X', ext='533].rawtx')

	def split_sign_btc(self):
		return self.regtest_sign(coin='BTC', ext='9997].rawtx')

	def split_send(self, coin, ext):
		self.coin = coin
		txfile = self.get_file_with_ext(ext, no_dot=True)
		self.txsend(txfile, bogus_send=False, extra_opts=['--bob'])

	def split_send_b2x(self):
		return self.regtest_send(coin='B2X', ext='533].sigtx')

	def split_send_btc(self):
		return self.regtest_send(coin='BTC', ext='9997].sigtx')

	def split_txdo_timelock(self, coin, locktime, bad_locktime):
		self.coin = coin
		sid = self.regtest_user_sid('bob')
		self.regtest_user_txdo(
			'bob',
			'0.0001',
			[sid+':S:5'],
			'1',
			pw           = rt_pw,
			extra_args   = ['--locktime='+str(locktime)],
			bad_locktime = bad_locktime)

	def split_txdo_timelock_bad_btc(self):
		self.regtest_txdo_timelock('BTC', locktime=8888, bad_locktime=True)
	def split_txdo_timelock_good_btc(self):
		self.regtest_txdo_timelock('BTC', locktime=1321009871, bad_locktime=False)
	def split_txdo_timelock_bad_b2x(self):
		self.regtest_txdo_timelock('B2X', locktime=8888, bad_locktime=True)
	def split_txdo_timelock_good_b2x(self):
		self.regtest_txdo_timelock('B2X', locktime=1321009871, bad_locktime=False)
