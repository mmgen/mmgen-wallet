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
test.cmdtest_d.ct_swap: asset swap tests for the cmdtest.py test suite
"""

from .ct_regtest import CmdTestRegtest, rt_data, dfl_wcls, rt_pw

sample1 = '=:ETH.ETH:0x86d526d6624AbC0178cF7296cD538Ecc080A95F1:0/1/0'
sample2 = '00010203040506'

class CmdTestSwap(CmdTestRegtest):
	bdb_wallet = True
	networks = ('btc',)
	tmpdir_nums = [37]

	cmd_group_in = (
		('setup',             'regtest (Bob and Alice) mode setup'),
		('subgroup.init_bob', []),
		('subgroup.fund_bob', ['init_bob']),
		('subgroup.data',     ['init_bob']),
		('stop',              'stopping regtest daemon'),
	)
	cmd_subgroups = {
		'init_bob': (
			'creating Bob’s MMGen wallet and tracking wallet',
			('walletgen_bob',       'wallet generation (Bob)'),
			('addrgen_bob',         'address generation (Bob)'),
			('addrimport_bob',      'importing Bob’s addresses'),
		),
		'fund_bob': (
			'funding Bob’s wallet',
			('fund_bob', 'funding Bob’s wallet'),
			('bob_bal1', 'Bob’s balance'),
		),
		'data': (
			'OP_RETURN data operations',
			('data_tx1_create',  'Creating a transaction with OP_RETURN data (hex-encoded ascii)'),
			('data_tx1_sign',    'Signing the transaction'),
			('data_tx1_send',    'Sending the transaction'),
			('data_tx1_chk',     'Checking the sent transaction'),
			('generate3',        'Generate 3 blocks'),
			('data_tx2_do',      'Creating and sending a transaction with OP_RETURN data (binary)'),
			('data_tx2_chk',     'Checking the sent transaction'),
			('generate3',        'Generate 3 blocks'),
		),
	}

	def __init__(self, trunner, cfgs, spawn):
		super().__init__(trunner, cfgs, spawn)
		gldict = globals()
		for k in rt_data:
			gldict[k] = rt_data[k]['btc']

	@property
	def sid(self):
		return self._user_sid('bob')

	def addrgen_bob(self):
		return self.addrgen('bob', mmtypes=['S', 'B'])

	def addrimport_bob(self):
		return self.addrimport('bob', mmtypes=['S', 'B'])

	def fund_bob(self):
		return self.fund_wallet('bob', 'B', '500')

	def data_tx1_create(self):
		return self._data_tx_create('1', 'B:2', 'B:3', 'data', sample1)

	def _data_tx_create(self, src, dest, chg, pfx, sample):
		t = self.spawn(
			'mmgen-txcreate',
			['-d', self.tmpdir, '-B', '--bob', f'{self.sid}:{dest},1', f'{self.sid}:{chg}', f'{pfx}:{sample}'])
		return self.txcreate_ui_common(t, menu=[], inputs='1', interactive_fee='3s')

	def data_tx1_sign(self):
		return self._data_tx_sign()

	def _data_tx_sign(self):
		fn = self.get_file_with_ext('rawtx')
		t = self.spawn('mmgen-txsign', ['-d', self.tmpdir, '--bob', fn])
		t.view_tx('v')
		t.passphrase(dfl_wcls.desc, rt_pw)
		t.do_comment(None)
		t.expect('(Y/n): ', 'y')
		t.written_to_file('Signed transaction')
		return t

	def data_tx1_send(self):
		return self._data_tx_send()

	def _data_tx_send(self):
		fn = self.get_file_with_ext('sigtx')
		t = self.spawn('mmgen-txsend', ['-q', '-d', self.tmpdir, '--bob', fn])
		t.expect('view: ', 'n')
		t.expect('(y/N): ', '\n')
		t.expect('to confirm: ', 'YES\n')
		t.written_to_file('Sent transaction')
		return t

	def data_tx1_chk(self):
		return self._data_tx_chk(sample1.encode().hex())

	def data_tx2_do(self):
		return self._data_tx_do('2', 'B:4', 'B:5', 'hexdata', sample2, 'v')

	def data_tx2_chk(self):
		return self._data_tx_chk(sample2)

	def _data_tx_do(self, src, dest, chg, pfx, sample, view):
		t = self.user_txdo(
			user         = 'bob',
			fee          = '30s',
			outputs_cl   = [f'{self.sid}:{dest},1', f'{self.sid}:{chg}', f'{pfx}:{sample}'],
			outputs_list = src,
			add_comment  = 'Transaction with OP_RETURN data',
			return_early = True)

		t.view_tx(view)
		if view == 'v':
			t.expect(sample)
			t.expect('amount:')
		t.passphrase(dfl_wcls.desc, rt_pw)
		t.written_to_file('Signed transaction')
		self._do_confirm_send(t)
		t.expect('Transaction sent')
		return t

	def _data_tx_chk(self, sample):
		mp = self._get_mempool(do_msg=True)
		assert len(mp) == 1
		self.write_to_tmpfile('data_tx1_id', mp[0]+'\n')
		tx_hex = self._do_cli(['getrawtransaction', mp[0]])
		tx = self._do_cli(['decoderawtransaction', tx_hex], decode_json=True)
		v0 = tx['vout'][0]
		assert v0['scriptPubKey']['hex'] == f'6a{(len(sample) // 2):02x}{sample}'
		assert v0['scriptPubKey']['type'] == 'nulldata'
		assert v0['value'] == "0.00000000"
		return 'ok'

	def generate3(self):
		return self.generate(3)
