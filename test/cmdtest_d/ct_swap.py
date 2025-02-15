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

from mmgen.protocol import init_proto

from .ct_regtest import (
	CmdTestRegtest,
	rt_data,
	dfl_wcls,
	rt_pw,
	cfg)

sample1 = '=:ETH.ETH:0x86d526d6624AbC0178cF7296cD538Ecc080A95F1:0/1/0'
sample2 = '00010203040506'

class CmdTestSwap(CmdTestRegtest):
	bdb_wallet = True
	networks = ('btc',)
	tmpdir_nums = [37]
	passthru_opts = ('rpc_backend',)

	cmd_group_in = (
		('setup',             'regtest (Bob and Alice) mode setup'),
		('subgroup.init_bob', []),
		('subgroup.fund_bob', ['init_bob']),
		('subgroup.data',     ['fund_bob']),
		('subgroup.swap',     ['fund_bob']),
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
			('fund_bob1', 'funding Bob’s wallet (bech32)'),
			('fund_bob2', 'funding Bob’s wallet (native Segwit)'),
			('bob_bal',   'displaying Bob’s balance'),
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
			('bob_listaddrs',    'Display Bob’s addresses'),
		),
		'swap': (
			'Swap operations',
			('bob_swaptxcreate1', 'Create a swap transaction'),
		),
	}

	def __init__(self, trunner, cfgs, spawn):

		super().__init__(trunner, cfgs, spawn)

		globals_dict = globals()
		for k in rt_data:
			globals_dict[k] = rt_data[k]['btc']

		self.protos = [init_proto(cfg, k, network='regtest', need_amt=True) for k in ('btc', 'ltc', 'bch')]

	@property
	def sid(self):
		return self._user_sid('bob')

	def _addrgen_bob(self, proto_idx, mmtypes, subseed_idx=None):
		return self.addrgen('bob', subseed_idx=subseed_idx, mmtypes=mmtypes, proto=self.protos[proto_idx])

	def _addrimport_bob(self, proto_idx):
		return self.addrimport('bob', mmtypes=['S', 'B'], proto=self.protos[proto_idx])

	def _fund_bob(self, proto_idx, addrtype_code, amt):
		return self.fund_wallet('bob', addrtype_code, amt, proto=self.protos[proto_idx])

	def _bob_bal(self, proto_idx, bal, skip_check=False):
		return self.user_bal('bob', bal, proto=self.protos[proto_idx], skip_check=skip_check)

	def addrgen_bob(self):
		return self._addrgen_bob(0, ['S', 'B'])

	def addrimport_bob(self):
		return self._addrimport_bob(0)

	def fund_bob1(self):
		return self._fund_bob(0, 'B', '500')

	def fund_bob2(self):
		return self._fund_bob(0, 'S', '500')

	def bob_bal(self):
		return self._bob_bal(0, '1000')

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

	def bob_listaddrs(self):
		t = self.spawn('mmgen-tool', ['--bob', 'listaddresses'])
		return t

	def bob_swaptxcreate1(self):
		t = self.spawn(
			'mmgen-swaptxcreate',
			['-d', self.tmpdir, '-B', '--bob', 'BTC', '1.234', f'{self.sid}:S:3', 'LTC'])
		return t
