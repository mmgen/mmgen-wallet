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
test.cmdtest_d.ethswap: Ethereum swap tests for the cmdtest.py test suite
"""

from subprocess import run, PIPE, DEVNULL

from mmgen.util import msg_r, rmsg, die
from mmgen.protocol import init_proto
from mmgen.fileutil import get_data_from_file

from ..include.common import imsg, chk_equal

from .include.common import dfl_sid, eth_inbound_addr, thorchain_router_addr_file
from .include.proxy import TestProxy
from .httpd.thornode.swap import ThornodeSwapServer

from .regtest import CmdTestRegtest
from .swap import CmdTestSwapMethods, create_cross_methods
from .ethdev import CmdTestEthdev

class CmdTestEthSwapMethods:

	async def token_deploy_a(self):
		return await self._token_deploy_math(num=1)

	async def token_deploy_b(self):
		return await self._token_deploy_owned(num=1)

	async def token_deploy_c(self):
		return await self._token_deploy_token(num=1)

	def token_compile_router(self):

		if not self.using_solc:
			bin_fn = 'test/ref/ethereum/bin/THORChain_Router.bin'
			imsg(f'Using precompiled contract data ‘{bin_fn}’')
			import shutil
			shutil.copy(bin_fn, self.tmpdir)
			return 'skip'

		imsg("Compiling THORChain router contract")
		self.spawn(msg_only=True)
		cmd = [
			'solc',
			'--evm-version=constantinople',
			'--overwrite',
			f'--output-dir={self.tmpdir}',
			'--bin',
			'test/ref/ethereum/THORChain_Router.sol']
		imsg('Executing: {}'.format(' '.join(cmd)))
		cp = run(cmd, stdout=DEVNULL, stderr=PIPE)
		if cp.returncode != 0:
			rmsg('solc failed with the following output:')
			die(2, cp.stderr.decode())
		imsg('THORChain router contract compiled')
		return 'ok'

	async def token_deploy_router(self):
		return await self._token_deploy(
			key = 'thorchain_router',
			gas = 1_000_000,
			fn  = f'{self.tmpdir}/THORChain_Router.bin')

	async def token_fund_user(self):
		return await self._token_transfer_ops(
			op          = 'fund_user',
			mm_idxs     = [1, 2, 12],
			token_addr  = 'token_addr1',
			amt         = self.token_fund_amt)

	def token_addrgen(self):
		return self._token_addrgen(mm_idxs=[1], naddrs=12)

	def token_addrimport(self):
		return self._token_addrimport('token_addr1', '1-12', expect='12/12')

	def token_addrimport_inbound(self):
		token_addr = self.read_from_tmpfile('token_addr1').strip()
		return self.spawn(
			'mmgen-addrimport',
			['--quiet', '--regtest=1', f'--token-addr={token_addr}', f'--address={eth_inbound_addr}']
			+ self.add_eth_opts)

	def token_bal1(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:1\s+{self.token_fund_amt}\s')

	def token_bal2(self):
		return self._token_bal_check(pat=rf'{eth_inbound_addr}\s+\S+\s+87.654321\s')

	async def _check_token_swaptx_memo(self, chk):
		from mmgen.proto.eth.contract import Contract
		self.spawn(msg_only=True)
		addr = get_data_from_file(self.cfg, thorchain_router_addr_file, quiet=True).strip()
		c = Contract(self.cfg, self.proto, addr, rpc=await self.rpc)
		res = (await c.do_call('saved_memo()'))[2:]
		memo_len = int(res[64:128], 16)
		chk_equal(bytes.fromhex(res[128:128+(2*memo_len)]).decode(), chk)
		imsg(f'saved_memo: {chk}')
		return 'ok'

	def _swaptxsend_eth_proxy(self, *, add_opts=[], test=False):
		t = self._swaptxsend(
			add_opts = ['--tx-proxy=eth'] + (['--test'] if test else []) + add_opts,
			spawn_only = True)
		t.expect('view: ', 'y')
		t.expect('continue: ', '\n') # exit swap quote
		t.expect('(y/N): ', '\n')    # add comment
		if not test:
			t.expect('to confirm: ', 'YES\n')
		return t

class CmdTestEthSwap(CmdTestSwapMethods, CmdTestRegtest):
	'Ethereum swap operations'

	bdb_wallet = True
	tmpdir_nums = [47]
	networks = ('btc',)
	passthru_opts = ('coin', 'rpc_backend', 'eth_daemon_id')
	cross_group = 'ethswap_eth'
	cross_coin = 'eth'

	cmd_group_in = (
		('setup',                   'regtest (Bob and Alice) mode setup'),
		('eth_setup',               'Ethereum devnet setup'),
		('subgroup.init',           []),
		('subgroup.fund',           ['init']),
		('subgroup.eth_init',       []),
		('subgroup.eth_fund',       ['eth_init']),
		('subgroup.swap',           ['fund', 'eth_fund']),
		('subgroup.eth_swap',       ['fund', 'eth_fund']),
		('subgroup.token_init',     ['eth_fund']),
		('subgroup.token_swap',     ['fund', 'token_init']),
		('subgroup.eth_token_swap', ['fund', 'token_init']),
		('swap_server_stop',        'stopping the Thornode server'),
		('eth_stop',                'stopping the Ethereum daemon'),
		('stop',                    'stopping the regtest daemon'),
	)
	cmd_subgroups = {
	'init': (
		'creating Bob’s MMGen wallet and tracking wallet',
		('walletconv_bob', 'wallet creation (Bob)'),
		('addrgen_bob',    'address generation (Bob)'),
		('addrimport_bob', 'importing Bob’s addresses'),
	),
	'fund': (
		'funding Bob’s wallet',
		('bob_import_miner_addr', 'importing miner’s coinbase addr into Bob’s wallet'),
		('fund_bob',              'funding Bob’s wallet'),
		('generate',              'mining a block'),
		('bob_bal1',              'Bob’s balance'),
	),
	'eth_init': (
		'initializing the ETH tracking wallet',
		('eth_addrgen',                 ''),
		('eth_addrimport',              ''),
		('eth_addrimport_devaddr',      ''),
		('eth_addrimport_reth_devaddr', ''),
		('eth_fund_devaddr',            ''),
		('eth_del_reth_devaddr',        ''),
	),
	'eth_fund': (
		'funding the ETH tracking wallet',
		('eth_fund_mmgen_addr1',  ''),
		('eth_fund_mmgen_addr1b', ''),
		('eth_fund_mmgen_addr2',  ''),
		('eth_bal1',              ''),
	),
	'token_init': (
		'deploying tokens and initializing the ETH token tracking wallet',
		('eth_token_compile1',           ''),
		('eth_token_deploy_a',           ''),
		('eth_token_deploy_b',           ''),
		('eth_token_deploy_c',           ''),
		('eth_token_compile_router',     ''),
		('eth_token_deploy_router',      ''),
		('eth_token_fund_user',          ''),
		('eth_token_addrgen',            ''),
		('eth_token_addrimport',         ''),
		('eth_token_addrimport_inbound', ''),
		('eth_token_bal1',               ''),
	),
	'token_swap': (
		'token swap operations (BTC -> MM1)',
		('swaptxcreate3', 'creating a BTC->MM1 swap transaction'),
		('swaptxsign3',   'signing the swap transaction'),
		('swaptxsend3',   'sending the swap transaction'),
	),
	'swap': (
		'swap operations (BTC -> ETH)',
		('swaptxcreate1', 'creating a BTC->ETH swap transaction'),
		('swaptxcreate2', 'creating a BTC->ETH swap transaction (used account)'),
		('swaptxsign1',   'signing the swap transaction'),
		('swaptxsend1',   'sending the swap transaction'),
		('swaptxbump1',   'bumping the swap transaction'),
		('swaptxsign2',   'signing the bump transaction'),
		('swaptxsend2',   'sending the bump transaction'),
		('generate',      'generating a block'),
		('bob_bal2',      'Bob’s balance'),
		('swaptxdo1',     'creating, signing and sending a swap transaction'),
		('generate',      'generating a block'),
		('bob_bal3',      'Bob’s balance'),
	),
	'eth_swap': (
		'swap operations (ETH -> BTC)',
		('eth_swaptxcreate1', ''),
		('eth_swaptxcreate2', ''),
		('eth_swaptxsign1',   ''),
		('eth_swaptxsend1',   ''),
		('eth_swaptxstatus1', ''),
		('eth_bal2',          ''),
	),
	'eth_token_swap': (
		'swap operations (ETH -> ERC20, ERC20 -> BTC, ERC20 -> ETH)',
		# ETH -> MM1
		('eth_swaptxcreate3a',         ''),
		('eth_swaptxcreate3b',         ''),
		('eth_swaptxsign3',            ''),
		('eth_swaptxsend3',            ''),
		('eth_swaptxmemo3',            ''),
		# MM1 -> BTC
		('eth_swaptxcreate4',          ''),
		('eth_swaptxsign4',            ''),
		('eth_swaptxsend4',            ''),
		('eth_swaptxmemo4',            ''),
		('eth_swaptxstatus4',          ''),
		('eth_swaptxreceipt4',         ''),
		('eth_token_bal2',             ''),
		# MM1 -> ETH
		('eth_swaptxcreate5a',         ''),
		('eth_swaptxcreate5b',         ''),
		('eth_swaptxsign5',            ''),
		('eth_etherscan_server_start', ''),
		('eth_swaptxsend5_test',       ''),
		('eth_swaptxsend5a',           ''),
		('eth_swaptxsend5b',           ''),
		('eth_swaptxsend5',            ''),
		('eth_etherscan_server_stop',  ''),
	),
	}

	exec(create_cross_methods(cross_coin, cross_group, cmd_group_in, cmd_subgroups))

	def __init__(self, cfg, trunner, cfgs, spawn):

		super().__init__(cfg, trunner, cfgs, spawn)

		if not trunner:
			return

		globals()[self.cross_group] = self.create_cross_runner(
			trunner,
			add_cfg = {'eth_daemon_id': trunner.cfg.eth_daemon_id})

		self.swap_server = ThornodeSwapServer(cfg)
		self.swap_server.start()

		TestProxy(self, cfg)

	def swaptxcreate1(self):
		t = self._swaptxcreate(['BTC', '8.765', 'ETH'])
		t.expect('OK? (Y/n): ', 'y')
		t.expect(':E:2')
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate2(self):
		t = self._swaptxcreate(['BTC', '8.765', 'ETH', f'{dfl_sid}:E:1'])
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend()

	def swaptxsend2(self):
		return self._swaptxsend(add_opts=[f'--proxy=localhost:{TestProxy.port}'])

	swaptxsign3 = swaptxsign2 = swaptxsign1
	swaptxsend3 = swaptxsend1

	def swaptxbump1(self): # create one-output TX back to self to rescue funds
		return self._swaptxbump('40s', output_args=[f'{dfl_sid}:B:1'])

	def swaptxdo1(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['BTC', '0.223344', f'{dfl_sid}:B:3', 'ETH', f'{dfl_sid}:E:2'],
				action = 'txdo'),
			sign_and_send = True,
			file_desc = 'Sent transaction')

	def bob_bal2(self):
		return self._user_bal_cli('bob', chk='499.9999252')

	def bob_bal3(self):
		return self._user_bal_cli('bob', chk='499.77656902')

	def swaptxcreate3(self):
		t = self._swaptxcreate(['BTC', '0.87654321', 'ETH.MM1', f'{dfl_sid}:E:5'])
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swap_server_stop(self):
		return self._thornode_server_stop()

class CmdTestEthSwapEth(CmdTestEthSwapMethods, CmdTestSwapMethods, CmdTestEthdev):
	'Ethereum swap operations - Ethereum wallet'

	networks = ('eth',)
	tmpdir_nums = [48]
	fund_amt = '123.456'
	token_fund_amt = 1000
	is_helper = True
	add_eth_opts = ['--bob']

	bals = lambda self, k: {
		'swap1': [('98831F3A:E:1', '123.456')],
		'swap2': [('98831F3A:E:1', {'geth': '114.690978056', 'reth': '114.69097664'}[self.daemon.id])],
	}[k]

	cmd_group_in = CmdTestEthdev.cmd_group_in + (
		# eth_fund:
		('fund_mmgen_addr1',         'funding user address :1)'),
		('fund_mmgen_addr1b',        'funding user address :3)'),
		('fund_mmgen_addr2',         'funding user address :11)'),
		('bal1',                     'the ETH balance'),
		# eth_swap:
		('swaptxcreate1',            'creating an ETH->BTC swap transaction'),
		('swaptxcreate2',            'creating an ETH->BTC swap transaction (spec address, trade limit)'),
		('swaptxsign1',              'signing the transaction'),
		('swaptxsend1',              'sending the transaction'),
		('swaptxstatus1',            'getting the transaction status (with --verbose)'),
		('bal2',                     'the ETH balance'),
		# token_init:
		('token_compile1',           'compiling ERC20 token #1'),
		('token_deploy_a',           'deploying ERC20 token MM1 (SafeMath)'),
		('token_deploy_b',           'deploying ERC20 token MM1 (Owned)'),
		('token_deploy_c',           'deploying ERC20 token MM1 (Token)'),
		('token_compile_router',     'compiling THORChain router contract'),
		('token_deploy_router',      'deploying THORChain router contract'),
		('token_fund_user',          'transferring token funds from dev to user'),
		('token_addrgen',            'generating token addresses'),
		('token_addrimport',         'importing token addresses using token address (MM1)'),
		('token_addrimport_inbound', 'importing THORNode inbound token address'),
		('token_bal1',               'the token balance'),

		# eth_token_swap:
		# ETH -> MM1
		('swaptxcreate3a',         'creating an ETH->MM1 swap transaction'),
		('swaptxcreate3b',         'creating an ETH->MM1 swap transaction (specific address)'),
		('swaptxsign3',            'signing the transaction'),
		('swaptxsend3',            'sending the transaction'),
		('swaptxmemo3',            'the memo of the sent transaction'),

		# MM1 -> BTC
		('swaptxcreate4',          'creating an MM1->BTC swap transaction'),
		('swaptxsign4',            'signing the transaction'),
		('swaptxsend4',            'sending the transaction'),
		('swaptxmemo4',            'checking the memo'),
		('swaptxstatus4',          'getting the transaction status'),
		('swaptxreceipt4',         'getting the transaction receipt'),
		('token_bal2',             'the token balance'),

		# MM1 -> ETH
		('swaptxcreate5a',         'creating an MM1->ETH swap transaction'),
		('swaptxcreate5b',         'creating an MM1->ETH swap transaction (specific address)'),
		('swaptxsign5',            'signing the transaction'),
		('etherscan_server_start', 'starting the Etherscan server'),
		('swaptxsend5_test',       'testing the transaction via Etherscan'),
		('swaptxsend5a',           'sending the transaction via Etherscan (p1)'),
		('swaptxsend5b',           'sending the transaction via Etherscan (p2)'),
		('swaptxsend5',            'sending the transaction via Etherscan (complete)'),
		('etherscan_server_stop',  'stopping the Etherscan server'),
	)

	def fund_mmgen_addr1b(self):
		return self._fund_mmgen_addr(arg=f'{dfl_sid}:E:3,0.001')

	def swaptxcreate1(self):
		t = self._swaptxcreate(['ETH', '8.765', 'BTC'])
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate2(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['ETH', '8.765', 'BTC', f'{dfl_sid}:B:4'],
				add_opts = ['--trade-limit=3%' ,'--stream-interval=7']),
			expect = ':2019e4/7/0')

	def swaptxcreate3a(self):
		t = self._swaptxcreate(['ETH', '0.7654321', 'ETH.MM1'], add_opts=['--gas=fallback'])
		t.expect(f'{dfl_sid}:E:4') # check that correct unused address was found
		t.expect('(Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate3b(self):
		t = self._swaptxcreate(['ETH', '8.765', 'ETH.MM1', f'{dfl_sid}:E:5'], add_opts=['--gas=auto'])
		return self._swaptxcreate_ui_common(t)

	async def swaptxmemo3(self):
		self.spawn(msg_only=True)
		import json
		fn = self.get_file_with_ext('sigtx')
		tx = json.loads(get_data_from_file(self.cfg, fn, quiet=True).strip())
		txid = tx['MMGenTransaction']['coin_txid']
		chk = '=:ETH.MM1:0x48596c861c970eb4ca72c5082ff7fecd8ee5be9d:0/3/0' # E:5
		imsg(f'TxID: {txid}\nmemo: {chk}')
		res = await (await self.rpc).call('eth_getTransactionByHash', '0x' + txid)
		chk_equal(bytes.fromhex(res['input'].removeprefix('0x')).decode(), chk)
		return 'ok'

	def swaptxcreate4(self):
		t = self._swaptxcreate(['ETH.MM1', '87.654321', 'BTC', f'{dfl_sid}:C:2'], add_opts=['--gas=auto'])
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate5a(self):
		t = self._swaptxcreate(
			['ETH.MM1', '98.7654321', 'ETH'],
			add_opts = ['--gas=58000', '--router-gas=500000'])
		t.expect(f'{dfl_sid}:E:13') # check that correct unused address was found
		t.expect('(Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate5b(self):
		t = self._swaptxcreate(['ETH.MM1', '98.7654321', 'ETH', f'{dfl_sid}:E:12'])
		return self._swaptxcreate_ui_common(t)

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend()

	def swaptxstatus1(self):
		return self._swaptxsend(add_opts=['--verbose', '--status'], status=True)

	async def swaptxmemo4(self):
		import time
		time.sleep(1)
		return await self._check_token_swaptx_memo('=:b:mkQsXA7mqDtnUpkaXMbDtAL1KMeof4GPw3:0/3/0')

	def swaptxreceipt4(self):
		return self._swaptxsend(add_opts=['--receipt'], spawn_only=True)

	def swaptxsend5_test(self):
		return self._swaptxsend_eth_proxy(test=True)

	def swaptxsend5a(self):
		return self._swaptxsend_eth_proxy(
			add_opts = ['--txhex-idx=1', f'--proxy=localhost:{TestProxy.port}'])

	def swaptxsend5b(self):
		return self._swaptxsend_eth_proxy(add_opts=['--txhex-idx=2'])

	def swaptxsend5(self):
		return self._swaptxsend_eth_proxy()

	swaptxsign5 = swaptxsign4 = swaptxsign3 = swaptxsign1
	swaptxsend4 = swaptxsend3 = swaptxsend1
	swaptxstatus4 = swaptxstatus1

	def bal1(self):
		return self.bal('swap1')

	def bal2(self):
		return self.bal('swap2')
