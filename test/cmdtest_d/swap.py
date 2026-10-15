# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.swap: asset swap tests for the cmdtest.py test suite
"""

import os, json

from mmgen.cfg import Config
from mmgen.util import make_chksum_6, cached_property
from mmgen.protocol import init_proto
from mmgen.wallet.mmgen import wallet as MMGenWallet
from mmgen.tx.file import txfile_json_dumps # pylint: disable=no-name-in-module

from ..include.common import make_burn_addr, gr_uc, imsg

from .include.runner import CmdTestRunner
from .include.common import cleanup_env, dfl_words_file

from .autosign import CmdTestAutosign, CmdTestAutosignThreaded
from .regtest import CmdTestRegtest, dfl_wcls, rt_pw, strip_ansi_escapes
from .ethdev import CmdTestEthdevMethods
from .rune import CmdTestRuneMethods

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
			memoless        = False,
			menu_prompt     = None,
			expect          = None):
		t.expect(menu_prompt or self.menu_prompt, 'q')
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
		if memoless:
			return t
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

	def _swaptxcreate_bad(self, args, *, add_opts=[], exit_val=1, expect1=None, expect2=None):
		t = self._swaptxcreate(args, add_opts=add_opts, exit_val=exit_val)
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
				'--ltc-rpc-port=19571'],
			spawn_only = spawn_only)

	def _swaptxsend(
			self,
			*,
			add_opts   = [],
			spawn_only = False,
			status     = False,
			dump_hex   = False,
			expect_pats = None):
		fn = self.get_file_with_ext('sigtx')
		t = self.spawn(
			'mmgen-txsend',
			add_opts + ['-q', '-d', self.tmpdir, '--bob', fn],
			no_passthru_opts = ['coin'])
		if spawn_only:
			return t
		t.view_tx('v')
		if expect_pats:
			t.expect(expect_pats, regex=True)
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

	def _swaptxbump(self, fee, *, add_opts=[], output_args=[], single_output=False, exit_val=None):
		self.get_file_with_ext('rawtx', delete_all=True)
		fn = self.get_file_with_ext('sigtx')
		t = self.spawn(
			'mmgen-txbump',
			['-q', '-d', self.tmpdir] + self.bob_opt + add_opts + output_args + [fn],
			exit_val = exit_val)
		t = self._swaptxbump_ui_common(
				t,
				interactive_fee = fee,
				single_output   = single_output,
				new_outputs     = bool(output_args))
		t.read()
		os.unlink(fn) # bumped sigtx replaces the original
		return t

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
			single_output   = False,
			new_outputs     = False):
		if new_outputs:
			if not self.proto.is_vm:
				t.expect(f'{self.fee_desc}: ', interactive_fee + '\n')
			t.expect('(Y/n): ', 'y')        # fee ok?
			t.expect('(Y/n): ', 'y')        # change ok?
		else:
			if not (self.proto.is_vm or single_output):
				t.expect('ENTER for the change output): ', '\n')
				t.expect('(Y/n): ', 'y')    # confirm deduct from chg output
			t.expect('to continue: ', '\n') # exit swap quote
			t.expect(f'{self.fee_desc}: ', interactive_fee + '\n')
			t.expect('(Y/n): ', 'y')        # fee ok?
		t.expect('(y/N): ', 'n')            # comment?
		t.expect('(y/N): ', 'y')            # save?
		return t

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
		ret = CmdTestRunner(cfg, t.repo_root, t.data_dir, t.autosign_data_dir, t.trash_dir, t.trash_dir2)
		ret.init_group(self.cross_group)
		ret.parent_group = self
		return ret

	def start_thornode_servers(self):
		import importlib
		pkg = 'test.cmdtest_d.httpd.thornode'
		d = {
			'rpc': 'ThornodeRPCServer',
			'swap': 'ThornodeSwapServer',
			'midgard': 'ThornodeMidgardServer'}
		for name in self.thornode_servers:
			cls = getattr(importlib.import_module(f'{pkg}.{name}'), d[name])
			attr = f'{name}_server'
			setattr(self, attr, cls(self.cfg))
			getattr(self, attr).start()

	def stop_thornode_servers(self):
		self.spawn(msg_only=True)
		for name in self.thornode_servers:
			if self.cfg.no_daemon_stop:
				imsg(f'(leaving Thornode {name} server running by user request)')
			else:
				getattr(self, f'{name}_server').stop()
		return 'ok'

class CmdTestSwap(
		CmdTestSwapMethods,
		CmdTestRuneMethods,
		CmdTestRegtest,
		CmdTestAutosignThreaded,
		CmdTestEthdevMethods):
	'swap operations (LTC <=> BCH)'

	bdb_wallet = True
	networks = ('btc',)
	tmpdir_nums = [37]
	thornode_servers = ('rpc', 'swap')
	passthru_opts = ('rpc_backend',)
	coins         = ['bch', 'ltc']
	daemon_coins  = ['bch', 'ltc']
	subseed_idx = '29L'
	rune_menu_prompt = 'efresh balance:\b'
	refreq_txid = '0c7454c06d3fc0e520d34283e6f491ce7afe5abb3f569bbdfea1732e04b716ec'

	cmd_group_in = (
		('list_assets',              'listing swap assets'),
		('subgroup.init_swap',       []),
		('subgroup.create',          ['init_swap']),
		('subgroup.create_bad',      ['init_swap']),
		('subgroup.create_neterror', ['init_swap']),
		('subgroup.signsend',        ['init_swap']),
		('subgroup.signsend_bad',    ['init_swap']),
		('subgroup.autosign',        ['signsend']),
		('subgroup.memoless',        ['init_swap']),
		('stop_thornode_servers',    'stopping the Thornode RPC and swap servers'),
		('stop',                     'stopping regtest daemons'))

	cmd_subgroups = {
		'init_swap': (
			'Initialize regtest setup for swap operations',
			('setup_send_coin',               'setting up the sending coin regtest blockchain (BCH)'),
			('walletcreate_bob',              'wallet creation (Bob)'),
			('addrgen_bob_send',              'address generation (Bob, sending coin)'),
			('addrimport_bob_send',           'importing Bob’s addresses (sending coin)'),
			('fund_bob_send',                 'funding Bob’s wallet (compressed)'),
			('bob_bal_send',                  'displaying Bob’s send balance (BCH)'),

			('setup_recv_coin',               'setting up the receiving coin regtest blockchain (LTC)'),
			('addrgen_bob_recv',              'address generation (Bob, receiving coin)'),
			('addrimport_bob_recv',           'importing Bob’s addresses (receiving coin)'),
			('fund_bob_recv1',                'funding Bob’s wallet (bech32)'),
			('fund_bob_recv2',                'funding Bob’s wallet (native Segwit)'),
			('addrgen_bob_recv_subwallet',    'address generation (Bob, receiving coin)'),
			('addrimport_bob_recv_subwallet', 'importing Bob’s addresses (receiving coin)'),
			('fund_bob_recv_subwallet',       'funding Bob’s subwwallet (native Segwit)'),
			('bob_bal_recv',                  'displaying Bob’s receive balance (LTC)'),
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
			('swaptxcreate8',  'creating a swap transaction (quote only)'),
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
			('swaptxcreate_bad10', 'creating a swap transaction (bad, --quote with no amount)'),
		),
		'create_neterror': (
			'Swap TX create operations: network error handling',
			('swaptxcreate_neterror1', 'creating a swap transaction (network error, trading paused)'),
			('swaptxcreate_neterror2', 'creating a swap transaction (network error, trading for coin paused)'),
			('swaptxcreate_neterror3', 'creating a swap transaction (network error, trading for coin halted)'),
			('swaptxcreate_neterror4', 'creating a swap transaction (network error, memoless swaps halted)'),
		),
		'signsend': (
			'Swap TX create, sign and send operations (LTC => BCH)',
			('swaptxsign1_create', 'creating a swap transaction (full args)'),
			('swaptxsign1',        'signing the transaction'),
			('swaptxsend1',        'sending the transaction'),
			('swaptxsend1_status', 'getting status of sent transaction'),
			('generate_ltc',       'generating a block'),
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
			('generate_ltc',       'generating a block'),
			('swap_bal1',          'checking the balance'),
			('swaptxsign1_do',     'creating, signing and sending a swap transaction'),
			('generate_ltc',       'generating a block'),
			('swap_bal2',          'checking the balance'),
		),
		'signsend_bad': (
			'Swap TX create, sign and send operations: error handling',
			('swaptxsign_bad1_create', 'creating a swap transaction (non-wallet swap address)'),
			('swaptxsign_bad1',        'signing the transaction (non-wallet swap address)'),
			('swaptxsign_bad2_create', 'creating a swap transaction'),
			('swaptxsign_bad2',        'signing the transaction'),
			('swaptxsend_neterror1',   'sending the transaction (LTC swaps halted)'),
			('swaptxsend_neterror2',   'sending the transaction (BCH swaps halted)'),
			('swaptxsend_bad2',        'sending the transaction (swap quote expired)'),
		),
		'autosign': (
			'Swap TX operations with autosigning (LTC => BCH)',
			('run_setup_bip39',        'setting up offline autosigning'),
			('swap_wait_loop_start',   'starting autosign wait loop'),
			('autosign_swaptxcreate1', 'creating a swap transaction'),
			('autosign_swaptxsend1',   'sending the transaction'),
			('autosign_swaptxbump1',   'bumping the transaction'),
			('autosign_swaptxsend2',   'sending the transaction'),
			('generate_ltc',           'generating a block'),
			('swap_bal3',              'checking the balance'),
			('wait_loop_kill',         'stopping autosign wait loop'),
		),
		'memoless': (
			'Memoless swap TX operations (LTC => BCH)',
			('rune_addrgen',              'generating RUNE addresses'),
			('rune_addrimport',           'importing RUNE addresses'),
			('rune_bal_refresh',          'refreshing balances in RUNE tracking wallet'),
			('memoless_swaptxcreate',     'creating a memoless swap transaction (--no-refreq-tx)'),
			('rune_txcreate_refreq',      'creating a rune reference request transaction'),
			('rune_txsign_refreq',        'signing the transaction'),
			('rune_txsend_refreq',        'sending the transaction'),
			('refreq_swaptxcreate',       'creating a memoless swap transaction (first pass)'),
			('refreq_swaptxsign',         'signing the transaction'),
			('refreq_swaptxsend',         'sending the transaction'),
			('remote_get_refnum',         'getting the reference number'),
			('refnum_swaptxcreate1',      'creating a memoless swap transaction (second pass)'),
			('refnum_swaptxsign1',        'signing the transaction'),
			('refnum_swaptxsend1',        'sending the transaction'),
			('refnum_swaptxbump1',        'bumping the transaction'),
			('refnum_swaptxsign2',        'signing the bumped transaction'),
			('refnum_swaptxsend2',        'sending the bumped transaction'),
			('refnum_swaptxcreate2',      'creating a memoless swap transaction (second pass, no chg)'),
			('refnum_swaptxsign3',        'signing the transaction'),
			('refnum_swaptxbump2',        'bumping the transaction'),
			('refnum_swaptxsign4',        'signing the bumped transaction'),
			('refnum_swaptxsend3',        'sending the bumped transaction'),
			('remote_get_refnum_color',   'getting the reference number (color output)'),
			('remote_validate_refnum',    'validating the reference number'),
			('remote_validate_refnum_short', 'validating the reference number (short form for asset)'),
			('remote_get_inbound_ltc',    'getting inbound address (LTC)'),
			('tool_get_memoless_amt',     'getting the memoless amount (LTC)'),
			('remote_validate_amt',       'validating the memoless amount'),
			('remote_validate_amt_short', 'validating the memoless amount (short form for asset)'),
			('txcreate_memoless_amt',     'creating a transaction sending the memoless amount'),
			('txsign_memoless_amt',       'signing the transaction'),
			('txsend_memoless_amt',       'sending the transaction'),
			('generate_ltc',              'generating a block'),
			('bob_bal_memoless',          'displaying Bob’s balance (LTC)'),
		),
	}

	def __init__(self, cfg, trunner, cfgs, spawn):

		CmdTestAutosignThreaded.__init__(self, cfg, trunner, cfgs, spawn)
		CmdTestRegtest.__init__(self, cfg, trunner, cfgs, spawn)

		if trunner is None:
			return

		self.protos = [init_proto(cfg, k, network='regtest', need_amt=True) for k in ('ltc', 'bch')]

		self.opts.append('--bob')
		self.rune_opts = [f'--outdir={self.tmpdir}', '--regtest=1', '--bob', '--quiet']
		self.eth_opts = self.rune_opts

		self.start_thornode_servers()

	@property
	def sid(self):
		return self._user_sid('bob')

	@cached_property
	def subsid(self):
		return self._get_user_subsid('bob', self.subseed_idx)

	def list_assets(self):
		t = self.spawn('mmgen-swaptxcreate', ['--list-assets'])
		t.expect('AVAILABLE')
		t.expect('ETH.MM1')
		t.expect('Blacklisted')
		t.expect('ETH.JUNK')
		return t

	def setup_send_coin(self):
		self.user_sids = {}
		return self._setup(proto=self.protos[1], remove_datadir=True)

	def addrgen_bob_send(self):
		return self._addrgen_bob(1, ['C'])

	def addrimport_bob_send(self):
		return self.addrimport('bob', mmtypes=['C'], proto=self.protos[1])

	def fund_bob_send(self):
		return self._fund_bob(1, 'C', '5')

	def bob_bal_send(self):
		return self._bob_bal(1, '5')

	def setup_recv_coin(self):
		return self._setup(proto=self.protos[0], remove_datadir=False)

	def addrgen_bob_recv(self):
		return self._addrgen_bob(0, ['S', 'B'])

	def addrimport_bob_recv(self):
		return self._addrimport_bob(0)

	def fund_bob_recv1(self):
		return self._fund_bob(0, 'S', '5')

	def fund_bob_recv2(self):
		return self._fund_bob(0, 'B', '5')

	def addrgen_bob_recv_subwallet(self):
		return self._addrgen_bob(0, ['C', 'B'], subseed_idx=self.subseed_idx)

	def addrimport_bob_recv_subwallet(self):
		return self._subwallet_addrimport('bob', self.subseed_idx, ['C', 'B'], proto=self.protos[0])

	def fund_bob_recv_subwallet(self, proto_idx=0, amt='5'):
		coin_arg = f'--coin={self.protos[proto_idx].coin}'
		t = self.spawn('mmgen-tool', ['--bob', coin_arg, 'listaddresses'])
		addr = next(s for s in strip_ansi_escapes(t.read()).splitlines() if 'C:1 No' in s).split()[3]
		t = self.spawn(
			'mmgen-regtest',
			self.regtest_opts + [coin_arg, 'send', addr, str(amt)],
			no_passthru_opts = ['coin'],
			no_msg = True)
		return t

	def bob_bal_recv(self):
		return self._bob_bal(0, '15')

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
		addr = make_burn_addr(self.protos[0], mmtype='bech32')
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

	def swaptxcreate8(self):
		t = self._swaptxcreate(['BCH', '0.56789', 'LTC'], add_opts=['--quote', '--no-quiet'])
		t.expect('SWAP QUOTE')
		return t

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
		addr = make_burn_addr(self.protos[1], mmtype='compressed')
		t = self._swaptxcreate_bad(['BCH', '1.234', addr, 'LTC', 'S'])
		t.expect('to confirm: ', 'NO\n')
		return t

	def swaptxcreate_bad9(self):
		return self._swaptxcreate_bad(['BCH', '1.234', 'S', 'LTC', 'B'], exit_val=2, expect1='invalid command-')

	def swaptxcreate_bad10(self):
		return self._swaptxcreate_bad(['BCH', 'LTC'], add_opts=['--quote'], exit_val=1, expect1='send amount')

	def swaptxcreate_neterror1(self):
		return self._swaptxcreate_neterror('ltc_global_paused', 'Trading is paused on the')

	def swaptxcreate_neterror2(self):
		return self._swaptxcreate_neterror('ltc_paused', 'Trading is paused for asset')

	def swaptxcreate_neterror3(self):
		return self._swaptxcreate_neterror('ltc_halted', 'Trading is halted for asset')

	def swaptxcreate_neterror4(self):
		return self._swaptxcreate_neterror('halt_memoless', 'Memoless swaps are halted', add_opts=['--memoless'])

	def _swaptxcreate_neterror(self, key, expect_str, *, add_opts=[]):
		if key:
			self.rpc_server.setvar(key, True)
		ret = self._swaptxcreate_bad(['BCH', 'LTC'], add_opts=add_opts, exit_val=2, expect1=expect_str)
		if key:
			self.rpc_server.setvar(key, False)
		return ret

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
		addr = make_burn_addr(self.protos[1], mmtype='compressed')
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

	def generate_ltc(self):
		return self.generate(num_blocks=1, add_opts=['--coin=LTC'])

	def swap_bal1(self):
		return self._bob_bal(0, '10.67894238')

	def swap_bal2(self):
		return self._bob_bal(0, '8.90148152')

	def swap_bal3(self):
		return self._bob_bal(0, '8.90143896')

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

	def swaptxsend_neterror1(self):
		return self._swaptxsend_bad_neterror('ltc_halted')

	def swaptxsend_neterror2(self):
		return self._swaptxsend_bad_neterror('bch_halted')

	def _swaptxsend_bad_neterror(self, key):
		fn = self.get_file_with_ext('sigtx')
		self.rpc_server.setvar(key, True)
		t = self.spawn('mmgen-txsend', ['-d', self.tmpdir, '--bob', fn], exit_val=2)
		t.expect('halted')
		self.rpc_server.setvar(key, False)
		return t

	def swaptxsend_bad2(self):
		fn = self.get_file_with_ext('sigtx')
		with open(fn) as fh:
			data = json.load(fh)
		data['MMGenTransaction']['swap_quote_expiry'] -= 2400
		data['chksum'] = make_chksum_6(txfile_json_dumps(data['MMGenTransaction']))
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
			inputs = '2',
			output_args = ['LTC', '3.88', f'{self.sid}:S:5', 'BCH', f'{self.sid}:C:3'])

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

	# memoless:

	def rune_addrgen(self):
		return self._addrgen(coin='RUNE')

	def rune_addrimport(self):
		return self._addrimport(add_args=['--coin=RUNE', '--bob'])

	def rune_bal_refresh(self):
		return self._rune_bal_refresh(
			add_opts = ['--coin=rune'],
			menu_prompt = self.rune_menu_prompt)

	def _memoless_swaptxcreate(
			self,
			args,
			*,
			add_opts = ['--memoless'],
			refreq   = False,
			refnum   = False):
		t = self._swaptxcreate(args, add_opts=add_opts)
		if refnum:
			return self._swaptxcreate_ui_common(t, inputs='2')
		if args[-1] == 'BCH': # no dest addr
			t.expect('(Y/n): ', 'y')
		t.expect('to continue: ', '\n')
		if refreq:
			t.expect(self.rune_menu_prompt, 'q')
			t.expect('spend from: ', '3\n')
			t.expect('(y/N): ', 'y') # add comment?
			t.expect('Comment: ', 'Memoless!\n')
			t.expect('view: ', 'y')
			t.expect('to continue: ', 'z')
			t.expect('(y/N): ', 'y') # save?
			t.written_to_file('Unsigned transaction')
		else:
			self.write_to_tmpfile('memo', t.expect_getend('MEMO: '))
		return t

	def memoless_swaptxcreate(self):
		return self._memoless_swaptxcreate(
			['LTC', '2.345', f'{self.subsid}:B:1', 'BCH'], # no dest addr
			add_opts  = ['--no-refreq'])

	def rune_txcreate_refreq(self):
		self.get_file_with_ext('rawtx', delete_all=True)
		memo = self.read_from_tmpfile('memo')
		return self._rune_txcreate(
			args = ['deposit,0', f'data:{memo}'],
			add_opts = ['--coin=rune', '--fee=0.2'],
			expect_pat = r'to spend:.*\b0\b.*RUNE',
			menu_prompt = self.rune_menu_prompt)

	def rune_txsign_refreq(self):
		self.get_file_with_ext('sigtx', delete_all=True)
		return self._rune_txsign()

	def rune_txsend_refreq(self):
		return self._rune_txsend()

	def refreq_swaptxcreate(self):
		self.get_file_with_ext('rawtx', delete_all=True)
		return self._memoless_swaptxcreate(
			['LTC', '2.345', f'{self.subsid}:B:1', 'BCH', f'{self.sid}:C:2'],
			refreq = True)

	refreq_swaptxsign = rune_txsign_refreq
	refreq_swaptxsend = rune_txsend_refreq

	def remote_get_refnum(self):
		t = self._rune_remote('get_refnum', (self.refreq_txid,), color=False)
		self.write_to_tmpfile('memo_info.json', t.read().strip())
		return t

	def _refnum_swaptxcreate(self, args, *, chg_addr=None, dest_addr=None):
		data = json.loads(self.read_from_tmpfile('memo_info.json'))
		return self._memoless_swaptxcreate(args, add_opts=[f'--refnum={data["reference"]}'], refnum=True)

	def refnum_swaptxcreate1(self):
		return self._refnum_swaptxcreate(['LTC', '2.345', f'{self.subsid}:B:1', 'BCH', f'{self.sid}:C:2'])

	def refnum_swaptxsign1(self):
		return self._swaptxsign()

	def refnum_swaptxsend1(self):
		return self._swaptxsend(expect_pats=[r'Fee:.*0\.0000084'])

	def refnum_swaptxbump1(self):
		return self._swaptxbump('100s')

	def refnum_swaptxsign2(self):
		return self._swaptxsign()

	def refnum_swaptxsend2(self):
		return self._swaptxsend(expect_pats=[r'Fee:.*0\.00014'])

	def refnum_swaptxcreate2(self):
		return self._refnum_swaptxcreate(['LTC', 'BCH'])

	def refnum_swaptxsign3(self):
		return self._swaptxsign()

	def refnum_swaptxbump2(self):
		return self._swaptxbump('700s', single_output=True)

	def refnum_swaptxsign4(self):
		return self._swaptxsign()

	def refnum_swaptxsend3(self):
		# depending on whether invoked as ‘swap’ or ‘swap.memoless’, TX spends different
		# addrtype and thus has different size:
		return self._swaptxsend(expect_pats=[r'Fee:.*0\.00186421', r'Fee:.*0\.00177765'])

	def remote_get_refnum_color(self):
		t = self._rune_remote('get_refnum', (self.refreq_txid,))
		return t

	def remote_validate_refnum(self):
		return self._remote_validate_refnum()

	def remote_validate_refnum_short(self):
		return self._remote_validate_refnum(asset='ltc')

	def _remote_validate_refnum(self, *, asset=None):
		data = json.loads(self.read_from_tmpfile('memo_info.json'))
		return self._rune_remote('validate_refnum', [(asset or data['asset']), data['reference']])

	def remote_get_inbound_ltc(self):
		t = self._rune_remote('inbound_addrs', ['coin=ltc'], color=False)
		self.write_to_tmpfile('inbound_addr_info.json', t.read().strip())
		return t

	def tool_get_memoless_amt(self):
		return self._tool_get_memoless_amt()

	def tool_get_memoless_amt_short(self):
		return self._tool_get_memoless_amt(asset='ltc')

	def _tool_get_memoless_amt(self, *, asset=None):
		data = json.loads(self.read_from_tmpfile('memo_info.json'))
		t = self.spawn(
			'mmgen-tool',
			['memoless_amt', (asset or data['asset']), '0.12345', data['reference']],
			env = cleanup_env(self.cfg))
		self.write_to_tmpfile('memoless_amt', t.read().strip())
		return t

	def remote_validate_amt(self):
		return self._remote_validate_amt()

	def remote_validate_amt_short(self):
		return self._remote_validate_amt(asset='ltc')

	def _remote_validate_amt(self, *, asset=None):
		data = json.loads(self.read_from_tmpfile('memo_info.json'))
		amt = self.read_from_tmpfile('memoless_amt').strip()
		return self._rune_remote('validate_amt', [(asset or data['asset']), amt])

	def txcreate_memoless_amt(self):
		self.get_file_with_ext('rawtx', delete_all=True)
		data = json.loads(self.read_from_tmpfile('inbound_addr_info.json'))
		amt = self.read_from_tmpfile('memoless_amt').strip()
		return self.txcreate_ui_common(
			self.spawn(
				'mmgen-txcreate',
				['--coin=ltc']
				+ self.rune_opts
				+ ['{},{}'.format(data['address'], amt), 'B']),
			inputs = '1',
			auto_chg_addr = 'B',
			interactive_fee = '10s')

	def txsign_memoless_amt(self):
		self.get_file_with_ext('sigtx', delete_all=True)
		txfile = self.get_file_with_ext('rawtx')
		return self.txsign_ui_common(
			self.spawn('mmgen-txsign', self.rune_opts + [txfile]),
			do_passwd = True,
			passwd = rt_pw)

	def txsend_memoless_amt(self):
		txfile = self.get_file_with_ext('sigtx')
		t = self.spawn('mmgen-txsend', self.rune_opts + [txfile])
		self.txsend_ui_common(t, bogus_send=False)
		return t

	def bob_bal_memoless(self):
		return self._bob_bal(0, None, skip_check=True)

	# admin methods:

	def sleep(self):
		import time
		time.sleep(1000)
		return 'ok'

	def listaddresses0(self):
		return self._listaddresses(0)

	def listaddresses1(self):
		return self._listaddresses(1)

	def mempool0(self):
		return self._mempool(0)

	def mempool1(self):
		return self._mempool(1)
