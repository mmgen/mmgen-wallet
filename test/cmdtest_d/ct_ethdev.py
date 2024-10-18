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
test.cmdtest_d.ct_ethdev: Ethdev tests for the cmdtest.py test suite
"""

import sys, os, re, shutil, asyncio, json
from decimal import Decimal
from collections import namedtuple
from subprocess import run, PIPE, DEVNULL
from pathlib import Path

from mmgen.color import yellow, blue, cyan, set_vt100
from mmgen.util import msg, rmsg, die

from ..include.common import (
	cfg,
	check_solc_ver,
	omsg,
	imsg,
	imsg_r,
	joinpath,
	read_from_file,
	write_to_file,
	cmp_or_die,
	strip_ansi_escapes,
	silence,
	end_silence,
	gr_uc,
	stop_test_daemons
)
from .common import (
	ref_dir,
	dfl_words_file,
	tx_comment_jp,
	tx_comment_lat_cyr_gr,
	tw_comment_zh,
	tw_comment_lat_cyr_gr,
	get_file_with_ext,
	ok_msg,
	Ctrl_U
)
from .ct_base import CmdTestBase
from .ct_shared import CmdTestShared

del_addrs = ('4', '1')
dfl_sid = '98831F3A'

# The OpenEthereum dev address with lots of coins.  Create with "ethkey -b info ''":
dfl_devaddr = '00a329c0648769a73afac7f9381e08fb43dbea72'
dfl_devkey = '4d5db4107d237df6a3d58ee5f70ae63d73d7658d4026f2eefd2f204c81682cb7'

burn_addr  = 'deadbeef'*5
burn_addr2 = 'beadcafe'*5

amt1 = '999999.12345689012345678'
amt2 = '888.111122223333444455'

parity_devkey_fn = 'parity.devkey'

def set_vbals(daemon_id):
	global vbal1, vbal2, vbal3, vbal4, vbal5, vbal6, vbal7, vbal9
	if daemon_id == 'geth':
		vbal1 = '1.2288334'
		vbal2 = '99.996560752'
		vbal3 = '1.2314176'
		vbal4 = '127.0287834'
		vbal5 = '1000126.14775104212345678'
		vbal6 = '1000126.14880104212345678'
		vbal7 = '1000124.91891764212345678'
		vbal9 = '1.2262504'
	else:
		vbal1 = '1.2288396'
		vbal2 = '99.997088092'
		vbal3 = '1.23142525'
		vbal3 = '1.2314246'
		vbal4 = '127.0287896'
		vbal5 = '1000126.14828458212345678'
		vbal6 = '1000126.14933458212345678'
		vbal7 = '1000124.91944498212345678'
		vbal9 = '1.226261'

bals = lambda k: {
	'1': [  ('98831F3A:E:1', '123.456')],
	'2': [  ('98831F3A:E:1', '123.456'), ('98831F3A:E:11', '1.234')],
	'3': [  ('98831F3A:E:1', '123.456'), ('98831F3A:E:11', '1.234'), ('98831F3A:E:21', '2.345')],
	'4': [  ('98831F3A:E:1', '100'),
			('98831F3A:E:2', '23.45495'),
			('98831F3A:E:11', '1.234'),
			('98831F3A:E:21', '2.345')],
	'5': [  ('98831F3A:E:1', '100'),
			('98831F3A:E:2', '23.45495'),
			('98831F3A:E:11', '1.234'),
			('98831F3A:E:21', '2.345'),
			(burn_addr + r'\s+non-MMGen', amt1)],
	'8': [  ('98831F3A:E:1', '0'),
			('98831F3A:E:2', '23.45495'),
			('98831F3A:E:11', vbal1),
			('98831F3A:E:12', '99.99895'),
			('98831F3A:E:21', '2.345'),
			(burn_addr + r'\s+non-MMGen', amt1)],
	'9': [  ('98831F3A:E:1', '0'),
			('98831F3A:E:2', '23.45495'),
			('98831F3A:E:11', vbal1),
			('98831F3A:E:12', vbal2),
			('98831F3A:E:21', '2.345'),
			(burn_addr + r'\s+non-MMGen', amt1)],
	'10': [ ('98831F3A:E:1', '0'),
			('98831F3A:E:2', '23.0218'),
			('98831F3A:E:3', '0.4321'),
			('98831F3A:E:11', vbal1),
			('98831F3A:E:12', vbal2),
			('98831F3A:E:21', '2.345'),
			(burn_addr + r'\s+non-MMGen', amt1)]
}[k]

token_bals = lambda k: {
	'1': [  ('98831F3A:E:11', '1000', '1.234')],
	'2': [  ('98831F3A:E:11', '998.76544', vbal3),
			('98831F3A:E:12', '1.23456', '0')],
	'3': [  ('98831F3A:E:11', '110.654317776666555545', vbal1),
			('98831F3A:E:12', '1.23456', '0')],
	'4': [  ('98831F3A:E:11', '110.654317776666555545', vbal1),
			('98831F3A:E:12', '1.23456', '0'),
			(burn_addr + r'\s+non-MMGen', amt2, amt1)],
	'5': [  ('98831F3A:E:11', '110.654317776666555545', vbal1),
			('98831F3A:E:12', '1.23456', '99.99895'),
			(burn_addr + r'\s+non-MMGen', amt2, amt1)],
	'6': [  ('98831F3A:E:11', '110.654317776666555545', vbal1),
			('98831F3A:E:12', '0', vbal2),
			('98831F3A:E:13', '1.23456', '0'),
			(burn_addr + r'\s+non-MMGen', amt2, amt1)],
	'7': [  ('98831F3A:E:11', '67.444317776666555545', vbal9),
			('98831F3A:E:12', '43.21', vbal2),
			('98831F3A:E:13', '1.23456', '0'),
			(burn_addr + r'\s+non-MMGen', amt2, amt1)]
}[k]

token_bals_getbalance = lambda k: {
	'1': (vbal4, '999999.12345689012345678'),
	'2': ('111.888877776666555545', '888.111122223333444455')
}[k]

coin = cfg.coin

class CmdTestEthdev(CmdTestBase, CmdTestShared):
	'Ethereum transacting, token deployment and tracking wallet operations'
	networks = ('eth', 'etc')
	passthru_opts = ('coin', 'daemon_id', 'http_timeout', 'rpc_backend')
	tmpdir_nums = [22]
	color = True
	cmd_group_in = (
		('setup',             f'dev mode tests for coin {coin} (start daemon)'),
		('subgroup.misc',     []),
		('subgroup.init',     []),
		('subgroup.msg',      ['init']),
		('subgroup.main',     ['init']),
		('subgroup.contract', ['main']),
		('subgroup.token',    ['contract']),
		('subgroup.twexport', ['token']),
		('subgroup.cached',   ['token']),
		('subgroup.view',     ['cached']),
		('subgroup.label',    ['cached']),
		('subgroup.remove',   ['cached']),
		('stop',              'stopping daemon'),
	)
	cmd_subgroups = {
	'misc': (
		'miscellaneous commands',
		('daemon_version', 'mmgen-tool daemon_version'),
	),
	'init': (
		'initializing wallets',
		('wallet_upgrade1',     'upgrading the tracking wallet (v1 -> v2)'),
		('wallet_upgrade2',     'upgrading the tracking wallet (v2 -> v3)'),
		('addrgen',             'generating addresses'),
		('addrimport',          'importing addresses'),
		('addrimport_dev_addr', "importing dev faucet address 'Ox00a329c..'"),
		('fund_dev_address',    'funding the default (Parity dev) address'),
	),
	'msg': (
		'message signing',
		('msgsign_chk',          "signing a message (low-level, check against 'eth_sign' RPC call)"),
		('msgcreate',            'creating a message file'),
		('msgsign',              'signing the message file'),
		('msgverify',            'verifying the message file'),
		('msgexport',            'exporting the message file data to JSON for third-party verifier'),
		('msgverify_export',     'verifying the exported JSON data'),

		('msgcreate_raw',        'creating a message file (--msghash-type=raw)'),
		('msgsign_raw',          'signing the message file (msghash_type=raw)'),
		('msgverify_raw',        'verifying the message file (msghash_type=raw)'),
		('msgexport_raw',        'exporting the message file data to JSON (msghash_type=raw)'),
		('msgverify_export_raw', 'verifying the exported JSON data (msghash_type=raw)'),
	),
	'main': (
		'creating, signing, sending and bumping Ethereum transactions',
		('txcreate1',            'creating a transaction (spend from dev address to address :1)'),
		('txview1_raw',          'viewing the raw transaction'),
		('txsign1',              'signing the transaction'),
		('txview1_sig',          'viewing the signed transaction'),
		('tx_status0_bad',       'getting the transaction status'),
		('txsign1_ni',           'signing the transaction (non-interactive)'),
		('txsend1',              'sending the transaction'),
		('bal1',                 f'the {coin} balance'),

		('txcreate2',            'creating a transaction (spend from dev address to address :11)'),
		('txsign2',              'signing the transaction'),
		('txsend2',              'sending the transaction'),
		('bal2',                 f'the {coin} balance'),

		('txcreate3',            'creating a transaction (spend from dev address to address :21)'),
		('txsign3',              'signing the transaction'),
		('txsend3',              'sending the transaction'),
		('bal3',                 f'the {coin} balance'),

		('tx_status1',           'getting the transaction status'),

		('txcreate4',            'creating a transaction (spend from MMGen address, low TX fee)'),
		('txbump',               'bumping the transaction fee'),

		('txsign4',              'signing the transaction'),
		('txsend4',              'sending the transaction'),
		('tx_status1a',          'getting the transaction status'),
		('bal4',                 f'the {coin} balance'),

		('txcreate5',            'creating a transaction (fund burn address)'),
		('txsign5',              'signing the transaction'),
		('txsend5',              'sending the transaction'),

		('addrimport_burn_addr', 'importing burn address'),
		('bal5',                 f'the {coin} balance'),

		('add_comment1',         'adding a UTF-8 label (zh)'),
		('chk_comment1',         'checking the label'),
		('add_comment2',         'adding a UTF-8 label (lat+cyr+gr)'),
		('chk_comment2',         'checking the label'),
		('remove_comment',       'removing the label'),
	),
	'contract': (
		'creating and deploying ERC20 tokens',
		('token_compile1',  'compiling ERC20 token #1'),
		('token_deploy1a',  'deploying ERC20 token #1 (SafeMath)'),
		('token_deploy1b',  'deploying ERC20 token #1 (Owned)'),
		('token_deploy1c',  'deploying ERC20 token #1 (Token)'),

		('tx_status2',      'getting the transaction status'),
		('bal6',            f'the {coin} balance'),

		('token_compile2',  'compiling ERC20 token #2'),
		('token_deploy2a',  'deploying ERC20 token #2 (SafeMath)'),
		('token_deploy2b',  'deploying ERC20 token #2 (Owned)'),
		('token_deploy2c',  'deploying ERC20 token #2 (Token)'),

		('contract_deploy', 'deploying contract (create, sign, send)'),
	),
	'token': (
		'creating, signing, sending and bumping ERC20 token transactions',

		('token_fund_users',           'transferring token funds from dev to user'),
		('token_user_bals',            'show balances after transfer'),
		('token_addrgen',              'generating token addresses'),
		('token_addrimport_badaddr1',  'importing token addresses (no token address)'),
		('token_addrimport_badaddr2',  'importing token addresses (bad token address)'),
		('token_addrimport_addr1',     'importing token addresses using token address (MM1)'),
		('token_addrimport_addr2',     'importing token addresses using token address (MM2)'),
		('token_addrimport_batch',     'importing token addresses (dummy batch mode) (MM1)'),
		('token_addrimport_sym',       'importing token addresses using token symbol (MM2)'),

		('bal7',                       f'the {coin} balance'),
		('token_bal1',                 f'the {coin} balance and token balance'),

		('token_txcreate1',            'creating a token transaction'),
		('token_txview1_raw',          'viewing the raw transaction'),
		('token_txsign1',              'signing the transaction'),
		('token_txsend1',              'sending the transaction'),
		('token_txview1_sig',          'viewing the signed transaction'),
		('tx_status3',                 'getting the transaction status'),
		('token_bal2',                 f'the {coin} balance and token balance'),

		('token_txcreate2',            'creating a token transaction (to burn address)'),
		('token_txbump',               'bumping the transaction fee'),

		('token_txsign2',              'signing the transaction'),
		('token_txsend2',              'sending the transaction'),
		('token_bal3',                 f'the {coin} balance and token balance'),

		('del_dev_addr',               'deleting the dev address'),

		('bal1_getbalance',            f'the {coin} balance (getbalance)'),

		('addrimport_token_burn_addr', 'importing the token burn address'),

		('token_bal4',                 f'the {coin} balance and token balance'),
		('token_bal_getbalance',       'the token balance (getbalance)'),

		('txcreate_noamt',             'creating a transaction (full amount send)'),
		('txsign_noamt',               'signing the transaction'),
		('txsend_noamt',               'sending the transaction'),

		('bal8',                       f'the {coin} balance'),
		('token_bal5',                 'the token balance'),

		('token_txcreate_noamt',       'creating a token transaction (full amount send)'),
		('token_txsign_noamt',         'signing the transaction'),
		('token_txsend_noamt',         'sending the transaction'),

		('bal9',                       f'the {coin} balance'),
		('token_bal6',                 'the token balance'),

		('listaddresses1',             'listaddresses'),
		('listaddresses2',             'listaddresses minconf=999999999 (ignored)'),
		('listaddresses3',             'listaddresses sort=age (ignored)'),
		('listaddresses4',             'listaddresses showempty=1 sort=age (ignored)'),

		('token_listaddresses1',       'listaddresses --token=mm1'),
		('token_listaddresses2',       'listaddresses --token=mm1 showempty=1'),
	),
	'twexport': (
		'exporting and importing tracking wallet to JSON',
		('twexport_noamt',       'exporting the tracking wallet (include_amts=0)'),
		('twmove',               'moving the tracking wallet'),
		('twimport',             'importing the tracking wallet'),
		('twview7',              'twview (cached_balances=1)'),
		('twview8',              'twview'),
		('twexport',             'exporting the tracking wallet'),
		('tw_chktotal',          'checking total value in tracking wallet dump'),
		('twmove',               'moving the tracking wallet'),
		('twimport',             'importing the tracking wallet'),
		('twcompare',            'comparing imported tracking wallet with original'),
		('edit_json_twdump',     'editing the tracking wallet JSON dump'),
		('twmove',               'moving the tracking wallet'),
		('twimport_nochksum',    'importing the edited tracking wallet JSON dump (ignore_checksum=1)'),

		('token_listaddresses3', 'listaddresses --token=mm1 showempty=1'),
		('token_listaddresses4', 'listaddresses --token=mm2 showempty=1'),
		('twview9',              'twview (check balance)'),
	),
	'cached': (
		'creating and sending transactions using cached balances',
		('twview_cached_balances',          'twview (cached balances)'),
		('token_twview_cached_balances',    'token twview (cached balances)'),
		('txcreate_cached_balances',        'txcreate (cached balances)'),
		('token_txcreate_cached_balances',  'token txcreate (cached balances)'),

		('txdo_cached_balances',            'txdo (cached balances)'),
		('txcreate_refresh_balances',       'refreshing balances'),
		('bal10',                           f'the {coin} balance'),

		('token_txdo_cached_balances',      'token txdo (cached balances)'),
		('token_txcreate_refresh_balances', 'refreshing token balances'),
		('token_bal7',                      'the token balance'),
	),
	'view': (
		'viewing addresses and unspent outputs',
		('twview1',       'twview'),
		('twview2',       'twview wide=1'),
		('twview3',       'twview wide=1 sort=age (ignored)'),
		('twview4',       'twview wide=1 minconf=999999999 (ignored)'),
		('twview5',       'twview wide=1 minconf=0 (ignored)'),
		('token_twview1', 'twview --token=mm1'),
		('token_twview2', 'twview --token=mm1 wide=1'),
		('token_twview3', 'twview --token=mm1 wide=1 sort=age (ignored)'),
	),
	'label': (
		'creating, editing and removing labels',
		('edit_comment1',       f'adding label to addr #{del_addrs[0]} in {coin} tracking wallet (zh)'),
		('edit_comment2',       f'editing label for addr #{del_addrs[0]} in {coin} tracking wallet (zh)'),
		('edit_comment3',       f'adding label to addr #{del_addrs[1]} in {coin} tracking wallet (lat+cyr+gr)'),
		('edit_comment4',       f'removing label from addr #{del_addrs[0]} in {coin} tracking wallet'),
		('token_edit_comment1', f'adding label to addr #{del_addrs[0]} in {coin} token tracking wallet'),
	),
	'remove': (
		'removing addresses from tracking wallet',
		('remove_addr1',       f'removing addr #{del_addrs[0]} from {coin} tracking wallet'),
		('twview6',            'twview (balance reduced after address removal)'),
		('remove_addr2',       f'removing addr #{del_addrs[1]} from {coin} tracking wallet'),
		('token_remove_addr1', f'removing addr #{del_addrs[0]} from {coin} token tracking wallet'),
		('token_remove_addr2', f'removing addr #{del_addrs[1]} from {coin} token tracking wallet'),
	),
	}

	def __init__(self, trunner, cfgs, spawn):
		CmdTestBase.__init__(self, trunner, cfgs, spawn)
		if trunner is None:
			return

		self.eth_args         = [f'--outdir={self.tmpdir}', '--regtest=1', '--quiet']
		self.eth_args_noquiet = [f'--outdir={self.tmpdir}', '--regtest=1']

		from mmgen.protocol import init_proto
		self.proto = init_proto( cfg, cfg.coin, network='regtest', need_amt=True)

		from mmgen.daemon import CoinDaemon
		self.daemon = CoinDaemon( cfg, self.proto.coin+'_rt', test_suite=True)

		set_vbals(self.daemon.id)

		self.using_solc = check_solc_ver()
		if not self.using_solc:
			omsg(yellow('Using precompiled contract data'))

		omsg(blue(f'Coin daemon {self.daemon.id!r} selected'))

		self.genesis_fn = joinpath(self.tmpdir, 'genesis.json')
		self.keystore_dir = os.path.relpath(joinpath(self.daemon.datadir, 'keystore'))

		write_to_file(
			joinpath(self.tmpdir, parity_devkey_fn),
			dfl_devkey+'\n')

		self.message = 'attack at dawn'
		self.spawn_env['MMGEN_BOGUS_SEND'] = ''

	@property
	async def rpc(self):
		from mmgen.rpc import rpc_init
		return await rpc_init(cfg, self.proto)

	async def setup(self):
		self.spawn('', msg_only=True)

		if not self.using_solc:
			srcdir = os.path.join(self.tr.repo_root, 'test', 'ref', 'ethereum', 'bin')
			from shutil import copytree
			for d in ('mm1', 'mm2'):
				copytree(os.path.join(srcdir, d), os.path.join(self.tmpdir, d))

		d = self.daemon

		if d.id in ('geth', 'erigon'):
			self.genesis_setup(d)
			set_vt100()

		if d.id == 'erigon':
			self.write_to_tmpfile('signer_key', self.keystore_data['key']+'\n')
			d.usr_coind_args = [
				'--miner.sigfile={}'.format(os.path.join(self.tmpdir, 'signer_key')),
				'--miner.etherbase={}'.format(self.keystore_data['address'])]

		if d.id in ('geth', 'erigon'):
			imsg('  {:19} {}'.format('Cmdline:', ' '.join(e for e in d.start_cmd if not 'verbosity' in e)))

		if not cfg.no_daemon_autostart:
			if not d.id in ('geth', 'erigon'):
				d.stop(silent=True)
				d.remove_datadir()
			d.start( silent = not (cfg.verbose or cfg.exact_output))
			rpc = await self.rpc
			imsg(f'Daemon: {rpc.daemon.coind_name} v{rpc.daemon_version_str}')

		return 'ok'

	@property
	def keystore_data(self):
		if not hasattr(self, '_keystore_data'):

			wallet_fn = os.path.join( self.keystore_dir, os.listdir(self.keystore_dir)[0])

			from mmgen.proto.eth.misc import decrypt_geth_keystore
			key = decrypt_geth_keystore(
				cfg       = cfg,
				wallet_fn = wallet_fn,
				passwd = b'')

			with open(wallet_fn) as fh:
				res = json.loads(fh.read())

			res.update( { 'key': key.hex()})
			self._keystore_data = res

		return self._keystore_data

	def genesis_setup(self, d):

		def make_key():
			pwfile = joinpath(self.tmpdir, 'account_passwd')
			write_to_file(pwfile, '')
			run(['rm', '-rf', self.keystore_dir])
			cmd = f'geth account new --password={pwfile} --lightkdf --keystore {self.keystore_dir}'
			cp = run(cmd.split(), stdout=PIPE, stderr=PIPE)
			if cp.returncode:
				die(1, cp.stderr.decode())

		def make_genesis(signer_addr, prealloc_addr):
			return {
				'config': {
					'chainId': 1337, # TODO: replace constant with var
					'homesteadBlock': 0,
					'eip150Block': 0,
					'eip155Block': 0,
					'eip158Block': 0,
					'byzantiumBlock': 0,
					'constantinopleBlock': 0,
					'petersburgBlock': 0,
					'istanbulBlock': 0,
					'muirGlacierBlock': 0,
					'berlinBlock': 0,
					'londonBlock': 0,
					'arrowGlacierBlock': 0,
					'grayGlacierBlock': 0,
					'shanghaiTime': 0,
					'terminalTotalDifficulty': 0,
					'terminalTotalDifficultyPassed': True,
					'isDev': True
				},
				'nonce': '0x0',
				'timestamp': '0x0',
				'extraData': '0x',
				'gasLimit': '0xaf79e0',
				'difficulty': '0x1',
				'mixHash': '0x0000000000000000000000000000000000000000000000000000000000000000',
				'coinbase': '0x0000000000000000000000000000000000000000',
				'number': '0x0',
				'gasUsed': '0x0',
				'parentHash': '0x0000000000000000000000000000000000000000000000000000000000000000',
				'baseFeePerGas': '0x3b9aca00',
				'excessBlobGas': None,
				'blobGasUsed': None,
				'alloc': {
					prealloc_addr: { 'balance': hex(prealloc_amt.toWei())}
				}
			}

		def init_genesis(fn):
			cmd = f'{d.exec_fn} init --datadir {d.datadir} {fn}'
			cp = run( cmd.split(), stdout=PIPE, stderr=PIPE)
			if cp.returncode:
				die(1, cp.stderr.decode())

		d.stop(quiet=True)
		d.remove_datadir()

		imsg(cyan('Initializing Genesis Block:'))

		prealloc_amt = self.proto.coin_amt('1_000_000_000')

		make_key()
		signer_addr = self.keystore_data['address']
		self.write_to_tmpfile( 'signer_addr', signer_addr + '\n')

		imsg(f'  Keystore:           {self.keystore_dir}')
		imsg(f'  Signer key:         {self.keystore_data["key"]}')
		imsg(f'  Signer address:     {signer_addr}')
		imsg(f'  Faucet:             {dfl_devaddr} ({prealloc_amt} ETH)')
		imsg(f'  Genesis block data: {self.genesis_fn}')

		genesis_data = make_genesis(signer_addr, dfl_devaddr)
		write_to_file( self.genesis_fn, json.dumps(genesis_data, indent='  ')+'\n')
		init_genesis(self.genesis_fn)

	def daemon_version(self):
		t = self.spawn('mmgen-tool', self.eth_args + ['daemon_version'])
		t.expect('version')
		return t

	async def _wallet_upgrade(self, src_fn, expect1, expect2=None):
		if self.proto.coin == 'ETC':
			msg(f'skipping test {self.test_name!r} for ETC')
			return 'skip'
		from mmgen.tw.ctl import TwCtl
		twctl = await TwCtl(cfg, self.proto, no_wallet_init=True)
		from_fn = Path(ref_dir) / 'ethereum' / src_fn
		bak_fn = twctl.tw_dir / f'upgraded-{src_fn}'
		twctl.tw_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
		dest = shutil.copy2(from_fn, twctl.tw_path)
		assert dest == twctl.tw_path, f'{dest} != {twctl.tw_path}'
		t = self.spawn('mmgen-tool', self.eth_args + ['twview'])
		t.expect(expect1)
		if expect2:
			t.expect(expect2)
		t.read()
		twctl.tw_path.rename(bak_fn)
		return t

	async def wallet_upgrade1(self):
		return await self._wallet_upgrade('tracking-wallet-v1.json', 'accounts field', 'network field')

	async def wallet_upgrade2(self):
		return await self._wallet_upgrade('tracking-wallet-v2.json', 'token params field', 'network field')

	def addrgen(self, addrs='1-3,11-13,21-23'):
		t = self.spawn('mmgen-addrgen', self.eth_args + [dfl_words_file, addrs])
		t.written_to_file('Addresses')
		return t

	def addrimport(
			self,
			ext       = '21-23]{}.regtest.addrs',
			expect    = '9/9',
			add_args  = [],
			bad_input = False,
			exit_val  = None):
		ext = ext.format('-α' if cfg.debug_utf8 else '')
		fn = self.get_file_with_ext(ext, no_dot=True, delete=False)
		t = self.spawn('mmgen-addrimport', ['--regtest=1'] + add_args + [fn], exit_val=exit_val)
		if bad_input:
			return t
		t.expect('Importing')
		t.expect(expect)
		return t

	def addrimport_one_addr(self, addr=None, extra_args=[]):
		t = self.spawn('mmgen-addrimport', ['--regtest=1', '--quiet', f'--address={addr}'] + extra_args)
		t.expect('OK')
		return t

	def addrimport_dev_addr(self):
		return self.addrimport_one_addr(addr=dfl_devaddr)

	def addrimport_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr)

	def txcreate(
			self,
			args            = [],
			menu            = [],
			acct            = '1',
			caller          = 'txcreate',
			interactive_fee = '50G',
			fee_info_data   = ('0.00105', '50'),
			no_read         = False,
			print_listing   = True,
			tweaks          = []):
		fee_info_pat = r'\D{}\D.*{c} .*\D{}\D.*gas price in Gwei'.format(*fee_info_data, c=self.proto.coin)
		t = self.spawn(f'mmgen-{caller}', self.eth_args + ['-B'] + args)
		if print_listing:
			t.expect(r'add \[l\]abel, .*?:.', 'p', regex=True)
			t.written_to_file('Account balances listing')
		t = self.txcreate_ui_common(
			t,
			menu              = menu,
			caller            = caller,
			input_sels_prompt = 'to spend from',
			inputs            = acct,
			file_desc         = 'transaction',
			bad_input_sels    = True,
			interactive_fee   = interactive_fee,
			fee_info_pat      = fee_info_pat,
			fee_desc          = 'transaction fee or gas price',
			add_comment       = tx_comment_jp,
			tweaks            = tweaks)
		if not no_read:
			t.read()
		return t

	def txsign(self, ni=False, ext='{}.regtest.rawtx', add_args=[], dev_send=False):
		ext = ext.format('-α' if cfg.debug_utf8 else '')
		keyfile = joinpath(self.tmpdir, parity_devkey_fn)
		txfile = self.get_file_with_ext(ext, no_dot=True)
		t = self.spawn(
			'mmgen-txsign',
			self.eth_args
			+ [f'--coin={self.proto.coin}']
			+ ['--rpc-host=bad_host'] # ETH signing must work without RPC
			+ add_args
			+ ([], ['--yes'])[ni]
			+ ([f'--keys-from-file={keyfile}'] if dev_send else [])
			+ [txfile, dfl_words_file])
		return self.txsign_ui_common(t, ni=ni, has_label=True)

	def txsend(self, ext='{}.regtest.sigtx', add_args=[]):
		ext = ext.format('-α' if cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext, no_dot=True)
		t = self.spawn('mmgen-txsend', self.eth_args + add_args + [txfile])
		self.txsend_ui_common(
			t,
			quiet      = not cfg.debug,
			bogus_send = False,
			has_label  = True)
		return t

	def txview(self, ext_fs):
		ext = ext_fs.format('-α' if cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext, no_dot=True)
		return self.spawn('mmgen-tool', ['--verbose', 'txview', txfile])

	def fund_dev_address(self):
		"""
		For Erigon, fund the default (Parity) dev address from the Erigon dev address
		For the others, send a junk TX to keep block counts equal for all daemons
		"""
		dt = namedtuple('data', ['devkey_fn', 'dest', 'amt'])
		d = dt(parity_devkey_fn, burn_addr2, '1')
		t = self.txcreate(
			args    = self.eth_args_noquiet + [
				f'--keys-from-file={joinpath(self.tmpdir, d.devkey_fn)}',
				f'{d.dest},{d.amt}',
			],
			menu    = ['a', 'r'],
			caller  = 'txdo',
			acct    = '1',
			no_read = True)
		self._do_confirm_send(t, quiet=not cfg.debug, sure=False)
		t.read()
		self.get_file_with_ext('sigtx', delete_all=True)
		return t

	def txcreate1(self):
		# include one invalid keypress 'X' -- see EthereumTwUnspentOutputs.key_mappings
		menu = ['a', 'd', 'r', 'M', 'X', 'e', 'm', 'm']
		args = ['98831F3A:E:1,123.456']
		return self.txcreate(args=args, menu=menu, acct='1', tweaks=['confirm_non_mmgen'])
	def txview1_raw(self):
		return self.txview(ext_fs='{}.regtest.rawtx')
	def txsign1(self):
		return self.txsign(add_args=['--use-internal-keccak-module'], dev_send=True)
	def tx_status0_bad(self):
		return self.tx_status(ext='{}.regtest.sigtx', expect_str='neither in mempool nor blockchain', exit_val=1)
	def txsign1_ni(self):
		return self.txsign(ni=True, dev_send=True)
	def txsend1(self):
		return self.txsend()
	def txview1_sig(self): # do after send so that TxID is displayed
		return self.txview(ext_fs='{}.regtest.sigtx')
	def bal1(self):
		return self.bal(n='1')

	def txcreate2(self):
		args = ['98831F3A:E:11,1.234']
		return self.txcreate(args=args, acct='10', tweaks=['confirm_non_mmgen'])
	def txsign2(self):
		return self.txsign(ni=True, ext='1.234,50000]{}.regtest.rawtx', dev_send=True)
	def txsend2(self):
		return self.txsend(ext='1.234,50000]{}.regtest.sigtx')
	def bal2(self):
		return self.bal(n='2')

	def txcreate3(self):
		args = ['98831F3A:E:21,2.345']
		return self.txcreate(args=args, acct='10', tweaks=['confirm_non_mmgen'])
	def txsign3(self):
		return self.txsign(ni=True, ext='2.345,50000]{}.regtest.rawtx', dev_send=True)
	def txsend3(self):
		return self.txsend(ext='2.345,50000]{}.regtest.sigtx')
	def bal3(self):
		return self.bal(n='3')

	def tx_status(self, ext, expect_str, expect_str2='', add_args=[], exit_val=0):
		ext = ext.format('-α' if cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext, no_dot=True)
		t = self.spawn(
			'mmgen-txsend',
			self.eth_args + add_args + ['--status', txfile],
			exit_val = exit_val)
		t.expect(expect_str)
		if expect_str2:
			t.expect(expect_str2)
		return t

	def tx_status1(self):
		return self.tx_status(ext='2.345,50000]{}.regtest.sigtx', expect_str='has 1 confirmation')

	def tx_status1a(self):
		return self.tx_status(ext='2.345,50000]{}.regtest.sigtx', expect_str='has 2 confirmations')

	async def msgsign_chk(self): # NB: Geth only!

		def create_signature_mmgen():
			key = self.keystore_data['key']
			imsg(f'Key:       {key}')
			from mmgen.proto.eth.misc import ec_sign_message_with_privkey
			return ec_sign_message_with_privkey(cfg, self.message, bytes.fromhex(key), 'eth_sign')

		async def create_signature_rpc():
			addr = self.read_from_tmpfile('signer_addr').strip()
			imsg(f'Address:   {addr}')
			rpc = await self.rpc
			return await rpc.call(
				'eth_sign',
				'0x' + addr,
				'0x' + self.message.encode().hex())

		if not self.daemon.id == 'geth':
			return 'skip'

		self.spawn('', msg_only=True)

		sig = '0x' + create_signature_mmgen()
		sig_chk = await create_signature_rpc()

		# Compare signatures
		imsg(f'Message:   {self.message}')
		imsg(f'Signature: {sig}')
		cmp_or_die(sig, sig_chk, 'message signatures')
		imsg('Geth and MMGen signatures match')

		return 'ok'

	def msgcreate(self, add_args=[]):
		t = self.spawn('mmgen-msg', self.eth_args_noquiet + add_args + ['create', self.message, '98831F3A:E:1'])
		t.written_to_file('Unsigned message data')
		return t

	def msgsign(self):
		fn = get_file_with_ext(self.tmpdir, 'rawmsg.json')
		t = self.spawn('mmgen-msg', self.eth_args_noquiet + ['sign', fn, dfl_words_file])
		t.written_to_file('Signed message data')
		return t

	def msgverify(self, fn=None, msghash_type='eth_sign'):
		fn = fn or get_file_with_ext(self.tmpdir, 'sigmsg.json')
		t = self.spawn('mmgen-msg', self.eth_args_noquiet + ['verify', fn])
		t.expect(msghash_type)
		t.expect('1 signature verified')
		return t

	def msgexport(self):
		fn = get_file_with_ext(self.tmpdir, 'sigmsg.json')
		t = self.spawn('mmgen-msg', self.eth_args_noquiet + ['export', fn])
		t.written_to_file('Signature data')
		return t

	def msgverify_export(self):
		return self.msgverify(
			fn = os.path.join(self.tmpdir, 'signatures.json'))

	def msgcreate_raw(self):
		get_file_with_ext(self.tmpdir, 'rawmsg.json', delete_all=True)
		return self.msgcreate(add_args=['--msghash-type=raw'])

	def msgsign_raw(self):
		get_file_with_ext(self.tmpdir, 'sigmsg.json', delete_all=True)
		return self.msgsign()

	def msgverify_raw(self):
		return self.msgverify(msghash_type='raw')

	def msgexport_raw(self):
		get_file_with_ext(self.tmpdir, 'signatures.json', no_dot=True, delete_all=True)
		return self.msgexport()

	def msgverify_export_raw(self):
		return self.msgverify(
			fn = os.path.join(self.tmpdir, 'signatures.json'),
			msghash_type = 'raw')

	def txcreate4(self):
		return self.txcreate(
			args             = ['98831F3A:E:2,23.45495'],
			acct             = '1',
			interactive_fee  = '40G',
			fee_info_data    = ('0.00084', '40'))

	def txbump(self, ext=',40000]{}.regtest.rawtx', fee='50G', add_args=[]):
		ext = ext.format('-α' if cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext, no_dot=True)
		t = self.spawn('mmgen-txbump', self.eth_args + add_args + ['--yes', txfile])
		t.expect('or gas price: ', fee+'\n')
		return t

	def txsign4(self):
		return self.txsign(ni=True, ext='.45495,50000]{}.regtest.rawtx', dev_send=True)
	def txsend4(self):
		return self.txsend(ext='.45495,50000]{}.regtest.sigtx')
	def bal4(self):
		return self.bal(n='4')

	def txcreate5(self):
		args = [burn_addr + ','+amt1]
		return self.txcreate(args=args, acct='10', tweaks=['confirm_non_mmgen'])
	def txsign5(self):
		return self.txsign(ni=True, ext=amt1+',50000]{}.regtest.rawtx', dev_send=True)
	def txsend5(self):
		return self.txsend(ext=amt1+',50000]{}.regtest.sigtx')
	def bal5(self):
		return self.bal(n='5')

	def bal(self, n):
		t = self.spawn('mmgen-tool', self.eth_args + ['twview', 'wide=1'])
		text = t.read(strip_color=True)
		for addr, amt in bals(n):
			pat = r'\D{}\D.*\D{}\D'.format(addr, amt.replace('.', r'\.'))
			assert re.search(pat, text), pat
		ss = f'Total {self.proto.coin}:'
		assert re.search(ss, text), ss
		return t

	def token_bal(self, n=None):
		t = self.spawn('mmgen-tool', self.eth_args + ['--token=mm1', 'twview', 'wide=1'])
		text = t.read(strip_color=True)
		for addr, _amt1, _amt2 in token_bals(n):
			pat = fr'{addr}\b.*\D{_amt1}\D.*\b{_amt2}\D'
			assert re.search(pat, text), pat
		ss = 'Total MM1:'
		assert re.search(ss, text), ss
		return t

	def bal_getbalance(self, sid, idx, etc_adj=False, extra_args=[]):
		bal1 = token_bals_getbalance(idx)[0]
		bal2 = token_bals_getbalance(idx)[1]
		bal1 = Decimal(bal1)
		t = self.spawn('mmgen-tool', self.eth_args + extra_args + ['getbalance'])
		t.expect(rf'{sid}:.*'+str(bal1), regex=True)
		t.expect(r'Non-MMGen:.*'+bal2, regex=True)
		total = strip_ansi_escapes(t.expect_getend(rf'TOTAL {self.proto.coin}')).split()[0]
		assert Decimal(bal1) + Decimal(bal2) == Decimal(total)
		return t

	def add_comment(self, comment, addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['add_label', addr, comment])
		t.expect('Added label.*in tracking wallet', regex=True)
		return t

	def chk_comment(self, comment_pat, addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['listaddresses', 'all_labels=1'])
		t.expect(fr'{addr}\b.*{comment_pat}', regex=True)
		return t

	def add_comment1(self):
		return self.add_comment(comment=tw_comment_zh)
	def chk_comment1(self):
		return self.chk_comment(comment_pat=tw_comment_zh[:3])
	def add_comment2(self):
		return self.add_comment(comment=tw_comment_lat_cyr_gr)
	def chk_comment2(self):
		return self.chk_comment(comment_pat=tw_comment_lat_cyr_gr[:3])

	def remove_comment(self, addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_label', addr])
		t.expect('Removed label.*in tracking wallet', regex=True)
		return t

	def token_compile(self, token_data={}):
		odir = joinpath(self.tmpdir, token_data['symbol'].lower())
		if not self.using_solc:
			imsg(f'Using precompiled contract data in {odir}')
			return 'skip' if os.path.exists(odir) else False
		self.spawn('', msg_only=True)
		cmd_args = [f'--{k}={v}' for k, v in list(token_data.items())]
		imsg("Compiling solidity token contract '{}' with 'solc'".format(token_data['symbol']))
		try:
			os.mkdir(odir)
		except:
			pass
		cmd = [
			'python3',
			'scripts/create-token.py',
			'--coin=' + self.proto.coin,
			'--outdir=' + odir
		] + cmd_args + [self.proto.checksummed_addr(dfl_devaddr)]
		imsg('Executing: {}'.format(' '.join(cmd)))
		cp = run(cmd, stdout=DEVNULL, stderr=PIPE)
		if cp.returncode != 0:
			rmsg('solc failed with the following output:')
			die(2, cp.stderr.decode())
		imsg('ERC20 token {!r} compiled'.format(token_data['symbol']))
		return 'ok'

	def token_compile1(self):
		token_data = {'name':'MMGen Token 1', 'symbol':'MM1', 'supply':10**26, 'decimals':18}
		return self.token_compile(token_data)

	def token_compile2(self):
		token_data = {'name':'MMGen Token 2', 'symbol':'MM2', 'supply':10**18, 'decimals':10}
		return self.token_compile(token_data)

	async def get_tx_receipt(self, txid):
		if self.daemon.id == 'geth': # yet another Geth bug
			await asyncio.sleep(0.5)
		from mmgen.tx import NewTX
		tx = await NewTX(cfg=cfg, proto=self.proto)
		tx.rpc = await self.rpc
		res = await tx.get_receipt(txid)
		imsg(f'Gas sent:  {res.gas_sent.hl():<9} {(res.gas_sent*res.gas_price).hl2(encl="()")}')
		imsg(f'Gas used:  {res.gas_used.hl():<9} {(res.gas_used*res.gas_price).hl2(encl="()")}')
		imsg(f'Gas price: {res.gas_price.hl()}')
		if res.gas_used == res.gas_sent:
			omsg(yellow('Warning: all gas was used!'))
		return res

	async def token_deploy(self, num, key, gas, mmgen_cmd='txdo', tx_fee='8G'):
		keyfile = joinpath(self.tmpdir, parity_devkey_fn)
		fn = joinpath(self.tmpdir, 'mm'+str(num), key+'.bin')
		args = [
			'-B',
			f'--fee={tx_fee}',
			f'--gas={gas}',
			f'--contract-data={fn}',
			f'--inputs={dfl_devaddr}',
			'--yes',
		]
		if mmgen_cmd == 'txdo':
			args += ['-k', keyfile]
		t = self.spawn('mmgen-'+mmgen_cmd, self.eth_args + args)
		if mmgen_cmd == 'txcreate':
			t.written_to_file('transaction')
			ext = '[0,8000]{}.regtest.rawtx'.format('-α' if cfg.debug_utf8 else '')
			txfile = self.get_file_with_ext(ext, no_dot=True)
			t = self.spawn('mmgen-txsign', self.eth_args + ['--yes', '-k', keyfile, txfile], no_msg=True)
			self.txsign_ui_common(t, ni=True)
			txfile = txfile.replace('.rawtx', '.sigtx')
			t = self.spawn('mmgen-txsend', self.eth_args + [txfile], no_msg=True)

		txid = self.txsend_ui_common(t,
			caller = mmgen_cmd,
			quiet  = mmgen_cmd == 'txdo' or not cfg.debug,
			bogus_send = False)
		addr = strip_ansi_escapes(t.expect_getend('Contract address: '))
		if (await self.get_tx_receipt(txid)).status == 0:
			die(2, f'Contract {num}:{key} failed to execute. Aborting')
		if key == 'Token':
			self.write_to_tmpfile(f'token_addr{num}', addr+'\n')
			imsg(f'\nToken MM{num} deployed!')
		return t

	async def token_deploy1a(self):
		return await self.token_deploy(num=1, key='SafeMath', gas=500_000)
	async def token_deploy1b(self):
		return await self.token_deploy(num=1, key='Owned',    gas=1_000_000)
	async def token_deploy1c(self):
		return await self.token_deploy(num=1, key='Token',    gas=4_000_000, tx_fee='7G')

	def tx_status2(self):
		return self.tx_status(
				ext        = self.proto.coin+'[0,7000]{}.regtest.sigtx',
				expect_str = 'successfully executed')

	def bal6(self):
		return self.bal5()

	async def token_deploy2a(self):
		return await self.token_deploy(num=2, key='SafeMath', gas=500_000)
	async def token_deploy2b(self):
		return await self.token_deploy(num=2, key='Owned',   gas=1_000_000)
	async def token_deploy2c(self):
		return await self.token_deploy(num=2, key='Token',   gas=4_000_000)

	async def contract_deploy(self): # test create, sign, send
		return await self.token_deploy(num=2, key='SafeMath', gas=500_000, mmgen_cmd='txcreate')

	async def token_transfer_ops(self, op, amt=1000, num_tokens=2):
		self.spawn('', msg_only=True)
		sid = dfl_sid
		from mmgen.tool.wallet import tool_cmd
		usr_mmaddrs = [f'{sid}:E:{i}' for i in (11, 21)][:num_tokens]

		from mmgen.proto.eth.contract import ResolvedToken
		async def do_transfer(rpc):
			for i in range(num_tokens):
				tk = await ResolvedToken(
					cfg,
					self.proto,
					rpc,
					self.read_from_tmpfile(f'token_addr{i+1}').strip())
				imsg_r('\n' + await tk.info())
				imsg('dev token balance (pre-send): {}'.format(await tk.get_balance(dfl_devaddr)))
				imsg(f'Sending {amt} {self.proto.dcoin} to address {usr_addrs[i]} ({usr_mmaddrs[i]})')
				txid = await tk.transfer(
					dfl_devaddr,
					usr_addrs[i],
					amt,
					dfl_devkey,
					start_gas = self.proto.coin_amt(60000, from_unit='wei'),
					gasPrice  = self.proto.coin_amt(8, from_unit='Gwei'))
				if (await self.get_tx_receipt(txid)).status == 0:
					die(2, 'Transfer of token funds failed. Aborting')

		async def show_bals(rpc):
			for i in range(num_tokens):
				tk = await ResolvedToken(
					cfg,
					self.proto,
					rpc,
					self.read_from_tmpfile(f'token_addr{i+1}').strip())
				imsg('Token: {}'.format(await tk.get_symbol()))
				imsg(f'dev token balance: {await tk.get_balance(dfl_devaddr)}')
				imsg('usr token balance: {} ({} {})'.format(
					await tk.get_balance(usr_addrs[i]),
					usr_mmaddrs[i],
					usr_addrs[i]))

		def gen_addr(addr):
			return tool_cmd(cfg, cmdname='gen_addr', proto=self.proto).gen_addr(addr, dfl_words_file)

		silence()
		usr_addrs = list(map(gen_addr, usr_mmaddrs))
		if op == 'show_bals':
			await show_bals(await self.rpc)
		elif op == 'do_transfer':
			await do_transfer(await self.rpc)
		end_silence()
		return 'ok'

	def token_fund_users(self):
		return self.token_transfer_ops(op='do_transfer')

	def token_user_bals(self):
		return self.token_transfer_ops(op='show_bals')

	def token_addrgen(self, num_tokens=2):
		t = self.addrgen(addrs='11-13')
		if num_tokens == 1:
			return t
		ok_msg()
		return self.addrgen(addrs='21-23')

	def token_addrimport_badaddr1(self):
		t = self.addrimport(
			ext       = '[11-13]{}.regtest.addrs',
			add_args  = ['--token=abc'],
			bad_input = True,
			exit_val  = 2)
		t.expect('could not be resolved')
		return t

	def token_addrimport_badaddr2(self):
		t = self.addrimport(
			ext       = '[11-13]{}.regtest.addrs',
			add_args  = ['--token='+'00deadbeef'*4],
			bad_input = True,
			exit_val  = 2)
		t.expect('could not be resolved')
		return t

	def token_addrimport(self, addr_file, addr_range, expect, extra_args=[]):
		token_addr = self.read_from_tmpfile(addr_file).strip()
		return self.addrimport(
			ext      = f'[{addr_range}]{{}}.regtest.addrs',
			expect   = expect,
			add_args = ['--token-addr='+token_addr]+extra_args)

	def token_addrimport_addr1(self):
		return self.token_addrimport('token_addr1', '11-13', expect='3/3')

	def token_addrimport_addr2(self):
		return self.token_addrimport('token_addr2', '21-23', expect='3/3')

	def token_addrimport_batch(self):
		return self.token_addrimport('token_addr1', '11-13', expect='3 addresses', extra_args=['--batch'])

	def token_addrimport_sym(self):
		return self.addrimport(
			ext      = '[21-23]{}.regtest.addrs',
			expect   = '3/3',
			add_args = ['--token=MM2'])

	def bal7(self):
		return self.bal5()
	def token_bal1(self):
		return self.token_bal(n='1')

	def token_txcreate(self, args=[], token='', inputs='1', fee='50G', file_desc='Unsigned transaction'):
		return self.txcreate_ui_common(
			self.spawn('mmgen-txcreate', self.eth_args + [f'--token={token}', '-B', f'--fee={fee}'] + args),
			menu              = [],
			inputs            = inputs,
			input_sels_prompt = 'to spend from',
			add_comment       = tx_comment_lat_cyr_gr,
			file_desc         = file_desc)
	def token_txsign(self, ext='', token=''):
		return self.txsign(ni=True, ext=ext, add_args=['--token='+token])
	def token_txsend(self, ext='', token=''):
		return self.txsend(ext=ext, add_args=['--token='+token])

	def token_txcreate1(self):
		return self.token_txcreate(args=['98831F3A:E:12,1.23456'], token='mm1')
	def token_txview1_raw(self):
		return self.txview(ext_fs='1.23456,50000]{}.regtest.rawtx')
	def token_txsign1(self):
		return self.token_txsign(ext='1.23456,50000]{}.regtest.rawtx', token='mm1')
	def token_txsend1(self):
		return self.token_txsend(ext='1.23456,50000]{}.regtest.sigtx', token='mm1')
	def token_txview1_sig(self):
		return self.txview(ext_fs='1.23456,50000]{}.regtest.sigtx')

	def tx_status3(self):
		return self.tx_status(
			ext         = '1.23456,50000]{}.regtest.sigtx',
			add_args    = ['--token=mm1'],
			expect_str  = 'successfully executed',
			expect_str2 = 'has 1 confirmation')

	def token_bal2(self):
		return self.token_bal(n='2')

	def twview(self, args=[], expect_str='', tool_args=[]):
		t = self.spawn('mmgen-tool', self.eth_args + args + ['twview'] + tool_args)
		if expect_str:
			t.expect(expect_str, regex=True)
		return t

	def token_txcreate2(self):
		return self.token_txcreate(args=[burn_addr+', '+amt2], token='mm1')
	def token_txbump(self):
		return self.txbump(ext=amt2+',50000]{}.regtest.rawtx', fee='56G', add_args=['--token=mm1'])
	def token_txsign2(self):
		return self.token_txsign(ext=amt2+',50000]{}.regtest.rawtx', token='mm1')
	def token_txsend2(self):
		return self.token_txsend(ext=amt2+',50000]{}.regtest.sigtx', token='mm1')

	def token_bal3(self):
		return self.token_bal(n='3')

	def del_dev_addr(self):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_address', dfl_devaddr])
		t.expect(f"'{dfl_devaddr}' deleted")
		return t

	def bal1_getbalance(self):
		return self.bal_getbalance(dfl_sid, '1', etc_adj=True)

	def addrimport_token_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr, extra_args=['--token=mm1'])

	def token_bal4(self):
		return self.token_bal(n='4')

	def token_bal_getbalance(self):
		return self.bal_getbalance(dfl_sid, '2', extra_args=['--token=mm1'])

	def txcreate_noamt(self):
		return self.txcreate(args=['98831F3A:E:12'])
	def txsign_noamt(self):
		return self.txsign(ext='99.99895,50000]{}.regtest.rawtx')
	def txsend_noamt(self):
		return self.txsend(ext='99.99895,50000]{}.regtest.sigtx')

	def bal8(self):
		return self.bal(n='8')
	def token_bal5(self):
		return self.token_bal(n='5')

	def token_txcreate_noamt(self):
		return self.token_txcreate(args=['98831F3A:E:13'], token='mm1', inputs='2', fee='51G')
	def token_txsign_noamt(self):
		return self.token_txsign(ext='1.23456,51000]{}.regtest.rawtx', token='mm1')
	def token_txsend_noamt(self):
		return self.token_txsend(ext='1.23456,51000]{}.regtest.sigtx', token='mm1')

	def bal9(self):
		return self.bal(n='9')
	def token_bal6(self):
		return self.token_bal(n='6')

	def listaddresses(self, args=[], tool_args=['all_labels=1']):
		return self.spawn('mmgen-tool', self.eth_args + args + ['listaddresses'] + tool_args)

	def listaddresses1(self):
		return self.listaddresses()
	def listaddresses2(self):
		return self.listaddresses(tool_args=['minconf=999999999'])
	def listaddresses3(self):
		return self.listaddresses(tool_args=['sort=amt', 'reverse=1'])
	def listaddresses4(self):
		return self.listaddresses(tool_args=['sort=age', 'showempty=0'])

	def token_listaddresses1(self):
		return self.listaddresses(args=['--token=mm1'])
	def token_listaddresses2(self):
		return self.listaddresses(args=['--token=mm1'], tool_args=['showempty=1'])
	def token_listaddresses3(self):
		return self.listaddresses(args=['--token=mm1'], tool_args=['showempty=0'])
	def token_listaddresses4(self):
		return self.listaddresses(args=['--token=mm2'], tool_args=['sort=age', 'reverse=1'])

	def twview_cached_balances(self):
		return self.twview(args=['--cached-balances'])
	def token_twview_cached_balances(self):
		return self.twview(args=['--token=mm1', '--cached-balances'])

	def txcreate_cached_balances(self):
		args = ['--fee=20G', '--cached-balances', '98831F3A:E:3, 0.1276']
		return self.txcreate(args=args, acct='2')
	def token_txcreate_cached_balances(self):
		args=['--cached-balances', '--fee=12G', '98831F3A:E:12, 1.2789']
		return self.token_txcreate(args=args, token='mm1')

	def txdo_cached_balances(
			self,
			acct          = '2',
			fee_info_data = ('0.00105', '50'),
			add_args      = ['98831F3A:E:3,0.4321']):
		t = self.txcreate(
			args          = ['--fee=20G', '--cached-balances'] + add_args + [dfl_words_file],
			acct          = acct,
			caller        = 'txdo',
			fee_info_data = fee_info_data,
			no_read       = True)
		self._do_confirm_send(t, quiet=not cfg.debug, sure=False)
		return t

	def txcreate_refresh_balances(self):
		return self._txcreate_refresh_balances(
			bals       = ['2', '3'],
			args       = ['-B', '--cached-balances', '-i'],
			total      = vbal5,
			adj_total  = True,
			total_coin = None)

	def _txcreate_refresh_balances(self, bals, args, total, adj_total, total_coin):

		if total_coin is None:
			total_coin = self.proto.coin

		t = self.spawn('mmgen-txcreate', self.eth_args + args)
		for n in bals:
			t.expect('[R]efresh balance:\b', 'R')
			t.expect(' main menu): ', n+'\n')
			t.expect('Is this what you want? (y/N): ', 'y')
		t.expect('[R]efresh balance:\b', 'q')
		t.expect(rf'Total unspent:.*\D{total}\D.*{total_coin}', regex=True)
		return t

	def bal10(self):
		return self.bal(n='10')

	def token_txdo_cached_balances(self):
		return self.txdo_cached_balances(
			acct          = '1',
			fee_info_data = ('0.0026', '50'),
			add_args      = ['--token=mm1', '98831F3A:E:12,43.21'])

	def token_txcreate_refresh_balances(self):
		return self._txcreate_refresh_balances(
			bals       = ['1', '2'],
			args       = ['--token=mm1', '-B', '--cached-balances', '-i'],
			total      = '1000',
			adj_total  = False,
			total_coin = 'MM1')

	def token_bal7(self):
		return self.token_bal(n='7')

	def twview1(self):
		return self.twview()
	def twview2(self):
		return self.twview(tool_args=['wide=1'])
	def twview3(self):
		return self.twview(tool_args=['wide=1', 'sort=age'])
	def twview4(self):
		return self.twview(tool_args=['wide=1', 'minconf=999999999'])
	def twview5(self):
		return self.twview(tool_args=['wide=1', 'minconf=0'])
	def twview6(self):
		return self.twview(expect_str=vbal7)
	def twview7(self):
		return self.twview(args=['--cached-balances'])
	def twview8(self):
		return self.twview()
	def twview9(self):
		return self.twview(args=['--cached-balances'], expect_str=vbal6)

	def token_twview1(self):
		return self.twview(args=['--token=mm1'])
	def token_twview2(self):
		return self.twview(args=['--token=mm1'], tool_args=['wide=1'])
	def token_twview3(self):
		return self.twview(args=['--token=mm1'], tool_args=['wide=1', 'sort=age'])

	def edit_comment(
			self,
			out_num,
			args          = [],
			action        = 'l',
			comment_text  = None,
			changed       = False,
			pexpect_spawn = None):

		t = self.spawn('mmgen-txcreate', self.eth_args + args + ['-B', '-i'], pexpect_spawn=pexpect_spawn)

		menu_prompt = 'efresh balance:\b'

		t.expect(menu_prompt, 'M')
		t.expect(menu_prompt, action)
		t.expect(r'return to main menu): ', out_num+'\n')

		for p, r in (
			('Enter label text.*: ', comment_text+'\n') if comment_text is not None else (r'\(y/N\): ', 'y'),
			(r'\(y/N\): ', 'y') if comment_text == Ctrl_U else (None, None),
		):
			if p:
				t.expect(p, r, regex=True)

		m = (
			'Label for account #{} edited' if changed else
			'Account #{} removed' if action == 'D' else
			'Label added to account #{}' if comment_text and comment_text != Ctrl_U else
			'Label removed from account #{}')

		t.expect(m.format(out_num))
		t.expect(menu_prompt, 'M')
		t.expect(menu_prompt, 'q')

		t.expect('Total unspent:')

		return t

	def edit_comment1(self):
		return self.edit_comment(out_num=del_addrs[0], comment_text=tw_comment_zh[:3])
	def edit_comment2(self):
		spawn = not sys.platform == 'win32'
		return self.edit_comment(
			out_num       = del_addrs[0],
			comment_text  = tw_comment_zh[3:],
			changed       = True,
			pexpect_spawn = spawn)
	def edit_comment3(self):
		return self.edit_comment(out_num=del_addrs[1], comment_text=tw_comment_lat_cyr_gr)
	def edit_comment4(self):
		if self.skip_for_win('no pexpect_spawn'):
			return 'skip'
		return self.edit_comment(out_num=del_addrs[0], comment_text=Ctrl_U, pexpect_spawn=True)

	def token_edit_comment1(self):
		return self.edit_comment(out_num='1', comment_text='Token label #1', args=['--token=mm1'])

	def remove_addr1(self):
		return self.edit_comment(out_num=del_addrs[0], action='D')
	def remove_addr2(self):
		return self.edit_comment(out_num=del_addrs[1], action='D')
	def token_remove_addr1(self):
		return self.edit_comment(out_num=del_addrs[0], args=['--token=mm1'], action='D')
	def token_remove_addr2(self):
		return self.edit_comment(out_num=del_addrs[1], args=['--token=mm1'], action='D')

	def twexport_noamt(self):
		return self.twexport(add_args=['include_amts=0'])

	def twexport(self, add_args=[]):
		t = self.spawn('mmgen-tool', self.eth_args + ['twexport'] + add_args)
		t.written_to_file('JSON data')
		return t

	async def twmove(self):
		self.spawn('', msg_only=True)
		from mmgen.tw.ctl import TwCtl
		twctl = await TwCtl(cfg, self.proto, no_wallet_init=True)
		imsg('Moving tracking wallet')
		fn_bak = twctl.tw_path.with_suffix('.bak.json')
		fn_bak.unlink(missing_ok=True)
		twctl.tw_path.rename(fn_bak)
		return 'ok'

	def twimport(self, add_args=[], expect_str=None):
		from mmgen.tw.json import TwJSON
		fn = joinpath(self.tmpdir, TwJSON.Base(cfg, self.proto).dump_fn)
		t = self.spawn('mmgen-tool', self.eth_args_noquiet + ['twimport', fn] + add_args)
		t.expect('(y/N): ', 'y')
		if expect_str:
			t.expect(expect_str)
		t.written_to_file('tracking wallet data')
		return t

	def twimport_nochksum(self):
		return self.twimport(add_args=['ignore_checksum=true'], expect_str='ignoring incorrect checksum')

	def tw_chktotal(self):
		self.spawn('', msg_only=True)
		from mmgen.tw.json import TwJSON
		fn = joinpath(self.tmpdir, TwJSON.Base(cfg, self.proto).dump_fn)
		res = json.loads(read_from_file(fn))
		cmp_or_die(res['data']['value'], vbal6, 'value in tracking wallet JSON dump')
		return 'ok'

	async def twcompare(self):
		self.spawn('', msg_only=True)
		from mmgen.tw.ctl import TwCtl
		twctl = await TwCtl(cfg, self.proto, no_wallet_init=True)
		fn = twctl.tw_path
		fn_bak = fn.with_suffix('.bak.json')
		imsg('Comparing imported tracking wallet with original')
		data = [json.dumps(json.loads(f.read_text()), sort_keys=True) for f in (fn, fn_bak)]
		cmp_or_die(*data, 'tracking wallets')
		return 'ok'

	def edit_json_twdump(self):
		self.spawn('', msg_only=True)
		from mmgen.tw.json import TwJSON
		fn = TwJSON.Base(cfg, self.proto).dump_fn
		text = json.loads(self.read_from_tmpfile(fn))
		token_addr = self.read_from_tmpfile('token_addr2').strip()
		text['data']['entries']['tokens'][token_addr][2][3] = f'edited comment [фубар] [{gr_uc}]'
		self.write_to_tmpfile(fn, json.dumps(text, indent=4))
		return 'ok'

	def stop(self):
		self.spawn('', msg_only=True)
		if not cfg.no_daemon_stop:
			if not stop_test_daemons(self.proto.coin+'_rt'):
				return False
		set_vt100()
		return 'ok'
