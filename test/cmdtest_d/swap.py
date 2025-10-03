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
test.cmdtest_d.swap: asset swap tests for the cmdtest.py test suite
"""

from pathlib import Path

from mmgen.cfg import Config
from mmgen.protocol import init_proto
from mmgen.wallet.mmgen import wallet as MMGenWallet

from ..include.common import imsg, make_burn_addr, gr_uc

from .include.runner import CmdTestRunner
from .include.common import dfl_bip39_file, dfl_words_file
from .httpd.thornode.swap import ThornodeSwapServer

from .autosign import CmdTestAutosign, CmdTestAutosignThreaded
from .regtest import CmdTestRegtest, rt_data, dfl_wcls, rt_pw, strip_ansi_escapes

sample1 = gr_uc[:24]
sample2 = '00010203040506'

def create_cross_methods(cross_coin, cross_group, cmd_group_in, cmd_subgroups):

	method_template = """
def {name}(self):
	self.spawn(log_only=True)
	return {group}.run_test("{method_name}", sub=True)
"""

	tests = [c[0] for v in tuple(cmd_subgroups.values()) + (cmd_group_in,)
		for c in v if isinstance(c, tuple) and c[0].startswith(f'{cross_coin}_')]

	return ''.join(method_template.format(
		name = k,
		method_name = k.removeprefix(f'{cross_coin}_'),
		group = cross_group)
			for k in tests)

class CmdTestSwapMethods:

	@property
	def bob_opt(self):
		return ['--bob'] if self.proto.base_proto == 'Bitcoin' else ['--regtest=1']

	@property
	def fee_desc(self):
		return 'fee or gas price' if self.proto.is_evm else 'fee'

	def walletconv_bob(self):
		t = self.spawn(
			'mmgen-walletconv',
			['--bob', '--quiet', '-r0', f'-d{self.cfg.data_dir}/regtest/bob', dfl_words_file],
			no_passthru_opts = ['coin', 'eth_daemon_id'])
		t.hash_preset(MMGenWallet.desc, '1')
		t.passphrase_new('new '+MMGenWallet.desc, rt_pw)
		t.label()
		return t

	def _addrgen_bob(self, proto_idx, mmtypes, subseed_idx=None):
		return self.addrgen('bob', subseed_idx=subseed_idx, mmtypes=mmtypes, proto=self.protos[proto_idx])

	def _addrimport_bob(self, proto_idx):
		return self.addrimport('bob', mmtypes=['S', 'B'], proto=self.protos[proto_idx])

	def _fund_bob(self, proto_idx, addrtype_code, amt):
		return self.fund_wallet('bob', amt, mmtype=addrtype_code, proto=self.protos[proto_idx])

	def _bob_bal(self, proto_idx, bal, skip_check=False):
		return self.user_bal('bob', bal, proto=self.protos[proto_idx], skip_check=skip_check)

	def _data_tx_create(self, src, dest, chg, pfx, sample):
		t = self.spawn(
			'mmgen-txcreate',
			['-d', self.tmpdir, '-B', '--bob', f'{self.sid}:{dest},1', f'{self.sid}:{chg}', f'{pfx}:{sample}'])
		return self.txcreate_ui_common(t, menu=[], inputs='1', interactive_fee='3s')

	def _data_tx_sign(self):
		fn = self.get_file_with_ext('rawtx')
		t = self.spawn('mmgen-txsign', ['-d', self.tmpdir, '--bob', fn])
		t.view_tx('v')
		t.passphrase(dfl_wcls.desc, rt_pw)
		t.do_comment(None)
		t.expect('(Y/n): ', 'y')
		t.written_to_file('Signed transaction')
		return t

	def _data_tx_send(self):
		fn = self.get_file_with_ext('sigtx')
		t = self.spawn('mmgen-txsend', ['-q', '-d', self.tmpdir, '--bob', fn])
		t.expect('view: ', 'n')
		t.expect('(y/N): ', '\n')
		t.expect('to confirm: ', 'YES\n')
		t.written_to_file('Sent transaction')
		return t

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

	def _swaptxcreate_ui_common(
			self,
			t,
			*,
			inputs          = '1',
			interactive_fee = None,
			file_desc       = 'Unsigned transaction',
			tweaks          = [],
			reload_quote    = False,
			sign_and_send   = False,
			need_passphrase = True,
			expect         = None):
		t.expect(self.menu_prompt, 'q')
		t.expect(self.input_sels_prompt, f'{inputs}\n')
		if reload_quote:
			t.expect('to continue: ', 'r')  # reload swap quote
		t.expect('to continue: ', '\n')     # exit swap quote view
		if self.proto.has_usr_fee:
			t.expect('(Y/n): ', 'y')            # fee OK?
			t.expect('(Y/n): ', 'y')            # change OK?
		t.expect('(y/N): ', 'n')            # add comment?
		t.expect('view: ', 'y')             # view TX
		if expect:
			t.expect(expect)
		t.expect('to continue: ', '\n')
		if sign_and_send:
			if need_passphrase:
				t.passphrase(dfl_wcls.desc, rt_pw)
			t.expect('to confirm: ', 'YES\n')
		else:
			t.expect('(y/N): ', 'y')            # save?
		t.written_to_file(file_desc)
		return t

	def _swaptxcreate(self, args, *, action='txcreate', add_opts=[], exit_val=None):
		self.get_file_with_ext('rawtx', delete_all=True)
		return self.spawn(
			f'mmgen-swap{action}',
			['-q', '-d', self.tmpdir, '-B', '--bob']
			+ add_opts
			+ args,
			exit_val = exit_val,
			no_passthru_opts = ['coin'])

	def _swaptxcreate_bad(self, args, *, exit_val=1, expect1=None, expect2=None):
		t = self._swaptxcreate(args, exit_val=exit_val)
		if expect1:
			t.expect(expect1)
		if expect2:
			t.expect(expect2)
		return t

	def _swaptxsend1(self, *, add_opts=[], spawn_only=False):
		return self._swaptxsend(
			add_opts = add_opts + [
			# test overriding host:port with coin-specific options:
			'--rpc-host=unreachable', # unreachable host
			'--ltc-rpc-host=localhost',
			'--rpc-port=46381',       # bad port
			'--ltc-rpc-port=20680',
			],
			spawn_only = spawn_only)

	def _swaptxsend(self, *, add_opts=[], spawn_only=False, status=False, dump_hex=False):
		fn = self.get_file_with_ext('sigtx')
		t = self.spawn(
			'mmgen-txsend',
			add_opts + ['-q', '-d', self.tmpdir, '--bob', fn],
			no_passthru_opts = ['coin'])
		if spawn_only:
			return t
		t.view_tx('v')
		if status:
			return t
		t.expect('(y/N): ', 'n')
		if not dump_hex:
			t.expect('to confirm: ', 'YES\n')
		return t

	def _swaptxsign(self, *, add_opts=[], expect=None):
		self.get_file_with_ext('sigtx', delete_all=True)
		fn = self.get_file_with_ext('rawtx')
		t = self.spawn(
			'mmgen-txsign',
			add_opts + ['-d', self.tmpdir, '--bob', fn],
			no_passthru_opts = ['coin'])
		t.view_tx('t')
		if expect:
			t.expect(expect)
		t.passphrase(dfl_wcls.desc, rt_pw)
		t.do_comment(None)
		t.expect('(Y/n): ', 'y')
		t.written_to_file('Signed transaction')
		return t

	def _swaptxbump(self, fee, *, add_opts=[], output_args=[], exit_val=None):
		self.get_file_with_ext('rawtx', delete_all=True)
		fn = self.get_file_with_ext('sigtx')
		t = self.spawn(
			'mmgen-txbump',
			['-q', '-d', self.tmpdir] + self.bob_opt + add_opts + output_args + [fn],
			exit_val = exit_val)
		return self._swaptxbump_ui_common(t, interactive_fee=fee, new_outputs=bool(output_args))

	def _swaptxbump_ui_common_new_outputs(
			self,
			t,
			*,
			tweaks          = [],
			inputs          = None,
			interactive_fee = None,
			file_desc       = None):
		return self._swaptxbump_ui_common(
				t,
				inputs          = inputs,
				interactive_fee = interactive_fee,
				file_desc       = file_desc,
				new_outputs     = True)

	def _swaptxbump_ui_common(
			self,
			t,
			*,
			inputs          = None,
			interactive_fee = None,
			file_desc       = None,
			new_outputs     = False):
		if new_outputs:
			if not self.proto.is_vm:
				t.expect(f'{self.fee_desc}: ', interactive_fee + '\n')
			t.expect('(Y/n): ', 'y')        # fee ok?
			t.expect('(Y/n): ', 'y')        # change ok?
		else:
			if not self.proto.is_vm:
				t.expect('ENTER for the change output): ', '\n')
				t.expect('(Y/n): ', 'y')    # confirm deduct from chg output
			t.expect('to continue: ', '\n') # exit swap quote
			t.expect(f'{self.fee_desc}: ', interactive_fee + '\n')
			t.expect('(Y/n): ', 'y')        # fee ok?
		t.expect('(y/N): ', 'n')            # comment?
		t.expect('(y/N): ', 'y')            # save?
		return t

	def _generate_for_proto(self, proto_idx):
		return self.generate(num_blocks=1, add_opts=[f'--coin={self.protos[proto_idx].coin}'])

	def _swaptxsign_bad(self, expect, *, add_opts=[], exit_val=1):
		self.get_file_with_ext('sigtx', delete_all=True)
		fn = self.get_file_with_ext('rawtx')
		t = self.spawn('mmgen-txsign', add_opts + ['-d', self.tmpdir, '--bob', fn], exit_val=exit_val)
		t.expect('view: ', '\n')
		t.expect(expect)
		return t

	def _listaddresses(self, proto_idx):
		return self.user_bal('bob', None, proto=self.protos[proto_idx], skip_check=True)

	def _mempool(self, proto_idx):
		self.spawn(msg_only=True)
		data = self._do_cli(['getrawmempool'], add_opts=[f'--coin={self.protos[proto_idx].coin}'])
		assert data
		return 'ok'

	def _thornode_server_stop(self, attrname='swap_server', name='thornode swap server'):
		self.spawn(msg_only=True)
		if self.cfg.no_daemon_stop:
			imsg(f'(leaving {name} running by user request)')
		else:
			getattr(self, attrname).stop()
		return 'ok'

	def create_cross_runner(self, trunner, *, add_cfg={}):
		cfg = Config({
			'_clone': trunner.cfg,
			'coin': self.cross_coin,
			'resume': None,
			'resuming': None,
			'resume_after': None,
			'exit_after': None,
			'log': None} | add_cfg)
		t = trunner
		ret = CmdTestRunner(cfg, t.repo_root, t.data_dir, t.trash_dir, t.trash_dir2)
		ret.init_group(self.cross_group)
		ret.parent_group = self
		return ret

class CmdTestSwap(CmdTestSwapMethods, CmdTestRegtest, CmdTestAutosignThreaded):
	'swap operations for BTC, BCH and LTC'

	bdb_wallet = True
	networks = ('btc',)
	tmpdir_nums = [37]
	passthru_opts = ('rpc_backend',)
	coins = ('btc',)
	need_daemon = True

	cmd_group_in = (
		('list_assets',           'listing swap assets'),
		('subgroup.init_data',    []),
		('subgroup.data',         ['init_data']),
		('subgroup.init_swap',    []),
		('subgroup.create',       ['init_swap']),
		('subgroup.create_bad',   ['init_swap']),
		('subgroup.signsend',     ['init_swap']),
		('subgroup.signsend_bad', ['init_swap']),
		('subgroup.autosign',     ['init_data', 'signsend']),
		('swap_server_stop',      'stopping the Thornode server'),
		('stop',                  'stopping regtest daemons'),
	)
	cmd_subgroups = {
		'init_data': (
			'Initialize regtest setup for OP_RETURN data operations',
			('setup',            'regtest (Bob and Alice) mode setup'),
			('walletcreate_bob', 'wallet creation (Bob)'),
			('addrgen_bob',      'address generation (Bob)'),
			('addrimport_bob',   'importing Bob’s addresses'),
			('fund_bob1',        'funding Bob’s wallet (bech32)'),
			('fund_bob2',        'funding Bob’s wallet (native Segwit)'),
			('bob_bal',          'displaying Bob’s balance'),
		),
		'data': (
			'OP_RETURN data operations',
			('data_tx1_create',  'Creating a transaction with OP_RETURN data (hex-encoded UTF-8)'),
			('data_tx1_sign',    'Signing the transaction'),
			('data_tx1_send',    'Sending the transaction'),
			('data_tx1_chk',     'Checking the sent transaction'),
			('generate3',        'Generate 3 blocks'),
			('data_tx2_do',      'Creating and sending a transaction with OP_RETURN data (binary)'),
			('data_tx2_chk',     'Checking the sent transaction'),
			('generate3',        'Generate 3 blocks'),
			('bob_listaddrs',    'Display Bob’s addresses'),
		),
		'init_swap': (
			'Initialize regtest setup for swap operations',
			('setup_send_coin',               'setting up the sending coin regtest blockchain'),
			('walletcreate_bob',              'wallet creation (Bob)'),
			('addrgen_bob_send',              'address generation (Bob, sending coin)'),
			('addrimport_bob_send',           'importing Bob’s addresses (sending coin)'),
			('fund_bob_send',                 'funding Bob’s wallet (bech32)'),
			('bob_bal_send',                  'displaying Bob’s send balance'),

			('setup_recv_coin',               'setting up the receiving coin regtest blockchain'),
			('addrgen_bob_recv',              'address generation (Bob, receiving coin)'),
			('addrimport_bob_recv',           'importing Bob’s addresses (receiving coin)'),
			('fund_bob_recv1',                'funding Bob’s wallet (bech32)'),
			('fund_bob_recv2',                'funding Bob’s wallet (native Segwit)'),
			('addrgen_bob_recv_subwallet',    'address generation (Bob, receiving coin)'),
			('addrimport_bob_recv_subwallet', 'importing Bob’s addresses (receiving coin)'),
			('fund_bob_recv_subwallet',       'funding Bob’s subwwallet (native Segwit)'),
			('bob_bal_recv',                  'displaying Bob’s receive balance'),
		),
		'create': (
			'Swap TX create operations (BCH => LTC)',
			('swaptxcreate1',  'creating a swap transaction (full args)'),
			('swaptxcreate2',  'creating a swap transaction (coin args only)'),
			('swaptxcreate3',  'creating a swap transaction (no chg arg)'),
			('swaptxcreate4',  'creating a swap transaction (chg and dest by addrtype)'),
			('swaptxcreate5',  'creating a swap transaction (chg and dest by addrlist ID)'),
			('swaptxcreate6',  'creating a swap transaction (dest is non-wallet addr)'),
			('swaptxcreate7',  'creating a swap transaction (coin-amt-coin)'),
		),
		'create_bad': (
			'Swap TX create operations: error handling',
			('swaptxcreate_bad1',  'creating a swap transaction (bad, used destination address)'),
			('swaptxcreate_bad2',  'creating a swap transaction (bad, used change address)'),
			('swaptxcreate_bad3',  'creating a swap transaction (bad, unsupported send coin)'),
			('swaptxcreate_bad4',  'creating a swap transaction (bad, unsupported recv coin)'),
			('swaptxcreate_bad5',  'creating a swap transaction (bad, malformed cmdline)'),
			('swaptxcreate_bad6',  'creating a swap transaction (bad, malformed cmdline)'),
			('swaptxcreate_bad7',  'creating a swap transaction (bad, bad user input, user exit)'),
			('swaptxcreate_bad8',  'creating a swap transaction (bad, non-MMGen change address)'),
			('swaptxcreate_bad9',  'creating a swap transaction (bad, invalid addrtype)'),
		),
		'signsend': (
			'Swap TX create, sign and send operations (LTC => BCH)',
			('swaptxsign1_create', 'creating a swap transaction (full args)'),
			('swaptxsign1',        'signing the transaction'),
			('swaptxsend1',        'sending the transaction'),
			('swaptxsend1_status', 'getting status of sent transaction'),
			('generate1',          'generating a block'),
			('swaptxsign2_create', 'creating a swap transaction (non-wallet swap address)'),
			('swaptxsign2',        'signing the transaction'),
			('swaptxsend2',        'sending the transaction'),
			('mempool1',           'viewing the mempool'),
			('swaptxbump1',        'bumping the transaction'),
			('swaptxsign3',        'signing the transaction'),
			('swaptxsend3',        'sending the transaction'),
			('mempool1',           'viewing the mempool'),
			('swaptxbump2',        'bumping the transaction again'),
			('swaptxsign4',        'signing the transaction'),
			('swaptxsend4',        'sending the transaction'),
			('mempool1',           'viewing the mempool'),
			('generate1',          'generating a block'),
			('swap_bal1',          'checking the balance'),
			('swaptxsign1_do',     'creating, signing and sending a swap transaction'),
			('generate1',          'generating a block'),
			('swap_bal2',          'checking the balance'),
		),
		'signsend_bad': (
			'Swap TX create, sign and send operations: error handling',
			('swaptxsign_bad1_create', 'creating a swap transaction (non-wallet swap address)'),
			('swaptxsign_bad1',        'signing the transaction (non-wallet swap address)'),
			('swaptxsign_bad2_create', 'creating a swap transaction'),
			('swaptxsign_bad2',        'signing the transaction'),
			('swaptxsend_bad2',        'sending the transaction (swap quote expired)'),
		),
		'autosign': (
			'Swap TX operations with autosigning (BTC => LTC)',
			('run_setup_bip39',        'setting up offline autosigning'),
			('swap_wait_loop_start',   'starting autosign wait loop'),
			('autosign_swaptxcreate1', 'creating a swap transaction'),
			('autosign_swaptxsend1',   'sending the transaction'),
			('autosign_swaptxbump1',   'bumping the transaction'),
			('autosign_swaptxsend2',   'sending the transaction'),
			('generate0',              'generating a block'),
			('swap_bal3',              'checking the balance'),
			('wait_loop_kill',         'stopping autosign wait loop'),
		),
	}

	def __init__(self, cfg, trunner, cfgs, spawn):

		CmdTestAutosignThreaded.__init__(self, cfg, trunner, cfgs, spawn)
		CmdTestRegtest.__init__(self, cfg, trunner, cfgs, spawn)

		if trunner is None:
			return

		globals_dict = globals()
		for k in rt_data:
			globals_dict[k] = rt_data[k]['btc']

		self.protos = [init_proto(cfg, k, network='regtest', need_amt=True) for k in ('btc', 'ltc', 'bch')]

		self.swap_server = ThornodeSwapServer(cfg)
		self.swap_server.start()

		self.opts.append('--bob')

	@property
	def sid(self):
		return self._user_sid('bob')

	def list_assets(self):
		t = self.spawn('mmgen-swaptxcreate', ['--list-assets'])
		t.expect('AVAILABLE')
		t.expect('ETH.MM1')
		t.expect('Blacklisted')
		t.expect('ETH.JUNK')
		return t

	def walletcreate_bob(self):
		dest = Path(self.tr.data_dir, 'regtest', 'bob')
		dest.mkdir(exist_ok=True)
		t = self.spawn('mmgen-walletconv', [
			'--quiet',
			'--usr-randchars=0',
			'--hash-preset=1',
			'--label=SwapWalletLabel',
			f'--outdir={str(dest)}',
			dfl_bip39_file])
		t.expect('wallet: ', rt_pw + '\n')
		t.expect('phrase: ', rt_pw + '\n')
		t.written_to_file('wallet')
		return t

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

	def data_tx1_sign(self):
		return self._data_tx_sign()

	def data_tx1_send(self):
		return self._data_tx_send()

	def data_tx1_chk(self):
		return self._data_tx_chk(sample1.encode().hex())

	def data_tx2_do(self):
		return self._data_tx_do('2', 'B:4', 'B:5', 'hexdata', sample2, 'v')

	def data_tx2_chk(self):
		return self._data_tx_chk(sample2)

	def generate3(self):
		return self.generate(3)

	def bob_listaddrs(self):
		t = self.spawn('mmgen-tool', ['--bob', 'listaddresses'])
		return t

	def setup_send_coin(self):
		self.user_sids = {}
		return self._setup(proto=self.protos[2], remove_datadir=True)

	def addrgen_bob_send(self):
		return self._addrgen_bob(2, ['C'])

	def addrimport_bob_send(self):
		return self.addrimport('bob', mmtypes=['C'], proto=self.protos[2])

	def fund_bob_send(self):
		return self._fund_bob(2, 'C', '5')

	def bob_bal_send(self):
		return self._bob_bal(2, '5')

	def setup_recv_coin(self):
		return self._setup(proto=self.protos[1], remove_datadir=False)

	def addrgen_bob_recv(self):
		return self._addrgen_bob(1, ['S', 'B'])

	def addrimport_bob_recv(self):
		return self._addrimport_bob(1)

	def fund_bob_recv1(self):
		return self._fund_bob(1, 'S', '5')

	def fund_bob_recv2(self):
		return self._fund_bob(1, 'B', '5')

	def addrgen_bob_recv_subwallet(self):
		return self._addrgen_bob(1, ['C', 'B'], subseed_idx='29L')

	def addrimport_bob_recv_subwallet(self):
		return self._subwallet_addrimport('bob', '29L', ['C', 'B'], proto=self.protos[1])

	def fund_bob_recv_subwallet(self, proto_idx=1, amt='5'):
		coin_arg = f'--coin={self.protos[proto_idx].coin}'
		t = self.spawn('mmgen-tool', ['--bob', coin_arg, 'listaddresses'])
		addr = [s for s in strip_ansi_escapes(t.read()).splitlines() if 'C:1 No' in s][0].split()[3]
		t = self.spawn(
			'mmgen-regtest',
			[coin_arg, 'send', addr, str(amt)],
			no_passthru_opts = ['coin'],
			no_msg = True)
		return t

	def bob_bal_recv(self):
		return self._bob_bal(1, '15')

	def swaptxcreate1(self, idx=3):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['BCH', '1.234', f'{self.sid}:C:{idx}', 'LTC', f'{self.sid}:B:3'],
				add_opts = ['--trade-limit=0%', '--stream-interval=1']),
			expect = ':3541e5/1/0')

	def swaptxcreate2(self):
		t = self._swaptxcreate(
			['BCH', 'LTC'],
			add_opts = ['--no-quiet', '--stream-interval=10', '--trade-limit=3.337%'])
		t.expect('Enter a number> ', '1')
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t, reload_quote=True, expect=':1386e6/10/0')

	def swaptxcreate3(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['BCH', 'LTC', f'{self.sid}:B:3'],
				add_opts = ['--trade-limit=10.1%']),
			expect = ':1289e6/3/0')

	def swaptxcreate4(self):
		t = self._swaptxcreate(
			['BCH', '1.234', 'C', 'LTC', 'B'],
			add_opts = ['--trade-limit=-1.123%'])
		t.expect('OK? (Y/n): ', 'y')
		t.expect('Enter a number> ', '1')
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t, expect=':358e6/3/0')

	def swaptxcreate5(self):
		t = self._swaptxcreate(
			['BCH', '1.234', f'{self.sid}:C', 'LTC', f'{self.sid}:B'],
			add_opts = ['--trade-limit=3.6'])
		t.expect('OK? (Y/n): ', 'y')
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t, expect=':36e7/3/0')

	def swaptxcreate6(self):
		addr = make_burn_addr(self.protos[1], mmtype='bech32')
		t = self._swaptxcreate(
			['BCH', '1.234', f'{self.sid}:C', 'LTC', addr],
			add_opts = ['--trade-limit=2.7%'])
		t.expect('OK? (Y/n): ', 'y')
		t.expect('to confirm: ', 'YES\n')
		return self._swaptxcreate_ui_common(t, expect=':3445e5/3/0')

	def swaptxcreate7(self):
		t = self._swaptxcreate(['BCH', '0.56789', 'LTC'])
		t.expect('OK? (Y/n): ', 'y')
		t.expect('Enter a number> ', '1')
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t, expect=':0/3/0')

	def swaptxcreate_bad1(self):
		t = self._swaptxcreate_bad(
			['BCH', '1.234', f'{self.sid}:C:3', 'LTC', f'{self.sid}:S:1'],
			expect1 = 'Requested destination address',
			expect2 = 'Address reuse harms your privacy')
		t.expect('(y/N): ', 'n')
		return t

	def swaptxcreate_bad2(self):
		t = self._swaptxcreate_bad(
			['BCH', '1.234', f'{self.sid}:C:1', 'LTC', f'{self.sid}:S:2'],
			expect1 = 'Requested change address',
			expect2 = 'Address reuse harms your privacy')
		t.expect('(y/N): ', 'n')
		return t

	def swaptxcreate_bad3(self):
		return self._swaptxcreate_bad(['RTC', 'LTC'], exit_val=2, expect1='unrecognized asset')

	def swaptxcreate_bad4(self):
		return self._swaptxcreate_bad(['LTC', 'XTC'], exit_val=2, expect1='unrecognized asset')

	def swaptxcreate_bad5(self):
		return self._swaptxcreate_bad(['LTC'], expect1='USAGE:')

	def swaptxcreate_bad6(self):
		return self._swaptxcreate_bad(['LTC', '1.2345'], expect1='USAGE:')

	def swaptxcreate_bad7(self):
		t = self._swaptxcreate(['BCH', 'LTC'], exit_val=1)
		t.expect('Enter a number> ', '3')
		t.expect('Enter a number> ', '1')
		t.expect('OK? (Y/n): ', 'n')
		return t

	def swaptxcreate_bad8(self):
		addr = make_burn_addr(self.protos[2], mmtype='compressed')
		t = self._swaptxcreate_bad(['BCH', '1.234', addr, 'LTC', 'S'])
		t.expect('to confirm: ', 'NO\n')
		return t

	def swaptxcreate_bad9(self):
		return self._swaptxcreate_bad(['BCH', '1.234', 'S', 'LTC', 'B'], exit_val=2, expect1='invalid command-')

	def swaptxsign1_create(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(['LTC', '4.321', f'{self.sid}:S:2', 'BCH', f'{self.sid}:C:2']))

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend1()

	def swaptxsend1_status(self):
		t = self._swaptxsend1(add_opts=['--status'], spawn_only=True)
		t.expect('in mempool')
		return t

	def swaptxsign2_create(self):
		addr = make_burn_addr(self.protos[2], mmtype='compressed')
		t = self._swaptxcreate(['LTC', '4.56789', f'{self.sid}:S:3', 'BCH', addr])
		t.expect('to confirm: ', 'YES\n') # confirm non-MMGen destination
		return self._swaptxcreate_ui_common(t)

	def swaptxsign2(self):
		return self._swaptxsign(add_opts=['--allow-non-wallet-swap'], expect='swap to non-wallet address')

	def swaptxsend2(self):
		return self._swaptxsend()

	def swaptxbump1(self):
		return self._swaptxbump('20s', add_opts=['--allow-non-wallet-swap'])

	def swaptxbump2(self): # create one-output TX back to self to rescue funds
		return self._swaptxbump('40s', output_args=[f'{self.sid}:S:4'])

	def swaptxsign3(self):
		return self.swaptxsign2()

	def swaptxsend3(self):
		return self._swaptxsend()

	def swaptxsign4(self):
		return self._swaptxsign()

	def swaptxsend4(self):
		return self._swaptxsend()

	def generate0(self):
		return self._generate_for_proto(0)

	def generate1(self):
		return self._generate_for_proto(1)

	def generate2(self):
		return self._generate_for_proto(2)

	def swap_bal1(self):
		return self._bob_bal(1, '10.67894238')

	def swap_bal2(self):
		return self._bob_bal(1, '8.90148152')

	def swap_bal3(self):
		return self._bob_bal(0, '999.99990407')

	def swaptxsign1_do(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(['LTC', '1.777444', f'{self.sid}:B:2', 'BCH', f'{self.sid}:C:2'], action='txdo'),
			sign_and_send = True,
			file_desc = 'Sent transaction')

	def swaptxsign_bad1_create(self):
		return self.swaptxcreate6()

	def swaptxsign_bad1(self):
		return self._swaptxsign_bad('non-wallet address forbidden')

	def swaptxsign_bad2_create(self):
		return self.swaptxcreate1(idx=4)

	def swaptxsign_bad2(self):
		return self._swaptxsign()

	def swaptxsend_bad2(self):
		import json
		from mmgen.tx.file import json_dumps
		from mmgen.util import make_chksum_6
		fn = self.get_file_with_ext('sigtx')
		with open(fn) as fh:
			data = json.load(fh)
		data['MMGenTransaction']['swap_quote_expiry'] -= 2400
		data['chksum'] = make_chksum_6(json_dumps(data['MMGenTransaction']))
		with open(fn, 'w') as fh:
			json.dump(data, fh)
		t = self.spawn('mmgen-txsend', ['-d', self.tmpdir, '--bob', fn], exit_val=1)
		t.expect('expired')
		return t

	run_setup_bip39 = CmdTestAutosign.run_setup_bip39
	run_setup = CmdTestAutosign.run_setup

	def swap_wait_loop_start(self):
		return self.wait_loop_start(add_opts=['--allow-non-wallet-swap'])

	def autosign_swaptxcreate1(self):
		return self._user_txcreate(
			'bob',
			progname = 'swaptxcreate',
			ui_handler = self._swaptxcreate_ui_common,
			output_args = ['BTC', '8.88', f'{self.sid}:S:3', 'LTC', f'{self.sid}:S:3'])

	def autosign_swaptxsend1(self):
		return self._user_txsend('bob', need_rbf=True)

	def autosign_swaptxbump1(self):
		return self._user_txcreate(
			'bob',
			progname = 'txbump',
			ui_handler = self._swaptxbump_ui_common_new_outputs,
			output_args = [f'{self.sid}:S:3'])

	def autosign_swaptxsend2(self):
		return self._user_txsend('bob', need_rbf=True)

	# admin methods:

	def sleep(self):
		import time
		time.sleep(1000)
		return 'ok'

	def listaddresses0(self):
		return self._listaddresses(0)

	def listaddresses1(self):
		return self._listaddresses(1)

	def listaddresses2(self):
		return self._listaddresses(2)

	def mempool0(self):
		return self._mempool(0)

	def mempool1(self):
		return self._mempool(1)

	def mempool2(self):
		return self._mempool(2)

	def swap_server_stop(self):
		return self._thornode_server_stop()
