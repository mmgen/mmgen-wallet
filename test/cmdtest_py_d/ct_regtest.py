#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
test.cmdtest_py_d.ct_regtest: Regtest tests for the cmdtest.py test suite
"""

import sys,os,json,time,re
from decimal import Decimal

from mmgen.color import yellow
from mmgen.util import msg_r,die,gmsg,capfirst,fmt_list
from mmgen.protocol import init_proto
from mmgen.addrlist import AddrList
from mmgen.wallet import Wallet,get_wallet_cls

from ..include.common import (
	cfg,
	imsg,
	omsg,
	stop_test_daemons,
	joinpath,
	silence,
	end_silence,
	cmp_or_die,
	strip_ansi_escapes,
	gr_uc,
	getrandhex
)
from .common import (
	ok_msg,
	get_file_with_ext,
	get_comment,
	tw_comment_lat_cyr_gr,
	tw_comment_zh,
	tx_comment_jp,
	get_env_without_debug_vars
)
from .ct_base import CmdTestBase
from .ct_shared import CmdTestShared

pat_date = r'\b\d\d-\d\d-\d\d\b'
pat_date_time = r'\b\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d\b'

dfl_wcls = get_wallet_cls('mmgen')

tx_fee = rtFundAmt = rtFee = rtBals = rtBals_gb = rtBobOp3 = rtAmts = {} # pylint
rt_pw = 'abc-α'
rt_data = {
	'tx_fee': {'btc':'0.0001','bch':'0.001','ltc':'0.01'},
	'rtFundAmt': {'btc':'500','bch':'500','ltc':'5500'},
	'rtFee': {
		'btc': ('20s','10s','60s','31s','10s','20s'),
		'bch': ('20s','10s','60s','0.0001','10s','20s'),
		'ltc': ('1000s','500s','1500s','0.05','400s','1000s')
	},
	'rtBals': {
		'btc': ('499.9999488','399.9998282','399.9998147','399.9996877',
				'52.99980410','946.99933647','999.99914057','52.9999',
				'946.99933647','0.4169328','6.24987417'),
		'bch': ('499.9999484','399.9999194','399.9998972','399.9997692',
				'46.78890380','953.20966920','999.99857300','46.789',
				'953.2096692','0.4169328','39.58187387'),
		'ltc': ('5499.99744','5399.994425','5399.993885','5399.987535',
				'52.98520500','10946.93753500','10999.92274000','52.99',
				'10946.937535','0.41364','6.24846787'),
	},
	'rtBals_gb': {
		'btc': {
			'0conf0': {
				'mmgen': ('283.22339537','283.22339537'),
				'nonmm': ('16.77647763','116.77629233'),
				'total': ('299.999873','399.9996877'),
			},
			'0conf1': {
				'mmgen': ('283.22339537','0'),
				'nonmm': ('16.77647763','99.9998147'),
				'total': ('299.999873','99.9998147'),
			},
			'1conf1': {
				'mmgen': ('0','283.22339537'),
				'nonmm': ('0','116.77629233'),
				'total': ('0','399.9996877'),
			},
			'1conf2': {
				'mmgen': ('0','283.22339537','0'),
				'nonmm': ('0','16.77647763','99.9998147'),
				'total': ('0','299.999873','99.9998147'),
			},
		},
		'bch': {
			'0conf0': {
				'mmgen': ('283.22339437','283.22339437'),
				'nonmm': ('16.77647763','116.77637483'),
				'total': ('299.999872','399.9997692'),
			},
			'0conf1': {
				'mmgen': ('283.22339437','0'),
				'nonmm': ('16.77647763','99.9998972'),
				'total': ('299.999872','99.9998972'),
			},
			'1conf1': {
				'mmgen': ('0','283.22339437'),
				'nonmm': ('0','116.77637483'),
				'total': ('0','399.9997692'),
			},
			'1conf2': {
				'mmgen': ('0','283.22339437','0'),
				'nonmm': ('0','16.77647763','99.9998972'),
				'total': ('0','299.999872','99.9998972'),
			},
		},
		'ltc': {
			'0conf0': {
				'mmgen': ('283.21717237','283.21717237'),
				'nonmm': ('16.77647763','5116.77036263'),
				'total': ('299.99365','5399.987535'),
			},
			'0conf1': {
				'mmgen': ('283.21717237','0'),
				'nonmm': ('16.77647763','5099.993885'),
				'total': ('299.99365','5099.993885'),
			},
			'1conf1': {
				'mmgen': ('0','283.21717237'),
				'nonmm': ('0','5116.77036263'),
				'total': ('0','5399.987535'),
			},
			'1conf2': {
				'mmgen': ('0','283.21717237','0'),
				'nonmm': ('0','16.77647763','5099.993885'),
				'total': ('0','299.99365','5099.993885'),
			},
		}
	},
	'rtBobOp3': {'btc':'S:2','bch':'L:3','ltc':'S:2'},
	'rtAmts': {
		'btc': ('500','500'),
		'bch': ('500','560'),
		'ltc': ('5500','5500')
	}
}

def make_burn_addr(proto):
	from mmgen.tool.coin import tool_cmd
	return tool_cmd(
		cfg     = cfg,
		cmdname = 'pubhash2addr',
		proto   = proto,
		mmtype  = 'compressed' ).pubhash2addr('00'*20)

class CmdTestRegtest(CmdTestBase,CmdTestShared):
	'transacting and tracking wallet operations via regtest mode'
	networks = ('btc','ltc','bch')
	passthru_opts = ('coin','rpc_backend')
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [17]
	color = True
	deterministic = False
	test_rbf = False
	proto = None # pylint

	cmd_group_in = (
		('setup',                   'regtest (Bob and Alice) mode setup'),
		('subgroup.misc',           []),
		('subgroup.init_bob',       []),
		('subgroup.init_alice',     []),
		('subgroup.fund_users',     ['init_bob','init_alice']),
		('subgroup.msg',            ['init_bob']),
		('subgroup.twexport',       ['fund_users']),
		('subgroup.rescan',         ['fund_users']),
		('subgroup.main',           ['fund_users']),
		('subgroup.twprune',        ['main']),
		('subgroup.txhist',         ['main']),
		('subgroup.label',          ['main']),
		('subgroup.view',           ['label']),
		('subgroup._auto_chg_deps', ['twexport','label']),
		('subgroup.auto_chg',       ['_auto_chg_deps']),
		('stop',                    'stopping regtest daemon'),
	)
	cmd_subgroups = {
	'misc': (
		'miscellaneous commands',
		('daemon_version',         'mmgen-tool daemon_version'),
		('halving_calculator_bob', 'halving calculator (Bob)'),
	),
	'init_bob': (
		'creating Bob’s MMGen wallet and tracking wallet',
		('walletgen_bob',  'wallet generation (Bob)'),
		('addrgen_bob',    'address generation (Bob)'),
		('addrimport_bob', "importing Bob's addresses"),
	),
	'init_alice': (
		'creating Alice’s MMGen wallet and tracking wallet',
		('walletgen_alice',  'wallet generation (Alice)'),
		('addrgen_alice',    'address generation (Alice)'),
		('addrimport_alice', "importing Alice's addresses"),
	),
	'fund_users': (
		'funding Bob and Alice’s wallets',
		('bob_import_miner_addr',        "importing miner’s coinbase addr into Bob’s wallet"),
		('fund_bob_deterministic',       "funding Bob’s first MMGen address (deterministic method)"),
		('fund_alice_deterministic',     "funding Alice’s first MMGen address (deterministic method)"),
		('bob_recreate_tracking_wallet', 'creation of new tracking wallet (Bob)'),
		('addrimport_bob2',              "reimporting Bob's addresses"),
		('fund_bob',                     "funding Bob's wallet"),
		('fund_alice',                   "funding Alice's wallet"),
		('generate',                     'mining a block'),
		('bob_bal1',                     "Bob's balance"),
		('generate_extra_deterministic', "generate extra blocks for deterministic run"),
	),
	'msg': (
		'message signing',
		('bob_msgcreate',               'creating a message file for signing'),
		('bob_msgsign',                 'signing the message file (default wallet)'),
		('bob_walletconv_words',        'creating an MMGen mnemonic wallet'),
		('bob_subwalletgen_bip39',      'creating a BIP39 mnemonic subwallet'),
		('bob_msgsign_userwallet',      'signing the message file (user-specified wallet)'),
		('bob_msgsign_userwallets',     'signing the message file (user-specified wallets)'),
		('bob_msgverify',               'verifying the message file (all addresses)'),
		('bob_msgverify_raw',           'verifying the raw message file (all addresses)'),
		('bob_msgverify_single',        'verifying the message file (single address)'),
		('bob_msgexport_single',        'exporting the message file (single address)'),
		('bob_msgexport',               'exporting the message file (all addresses)'),
		('bob_msgverify_export',        'verifying the exported JSON data (all addresses)'),
		('bob_msgverify_export_single', 'verifying the exported JSON data (single address)'),
	),
	'twexport': (
		'exporting and importing tracking wallet to JSON',
		('bob_twexport',            'exporting a tracking wallet to JSON'),
		('carol_twimport',          'importing a tracking wallet JSON dump'),
		('carol_delete_wallet',     'unloading and deleting Carol’s tracking wallet'),
		('bob_twexport_noamt',      'exporting a tracking wallet to JSON (include_amts=0)'),
		('carol_twimport_nochksum', 'importing a tracking wallet JSON dump (ignore_checksum=1)'),
		('carol_delete_wallet',     'unloading and deleting Carol’s tracking wallet'),
		('carol_twimport_batch',    'importing a tracking wallet JSON dump (batch=1)'),
		('bob_twexport_pretty',     'exporting a tracking wallet to JSON (pretty=1)'),
		('bob_edit_json_twdump',    'editing a tracking wallet JSON dump'),
		('carol_delete_wallet',     'unloading and deleting Carol’s tracking wallet'),
		('carol_twimport_pretty',   'importing an edited tracking wallet JSON dump (ignore_checksum=1)'),
		('carol_listaddresses',     'viewing Carol’s tracking wallet'),
		('carol_delete_wallet',     'unloading and deleting Carol’s tracking wallet'),
	),
	'rescan': (
		'rescanning address and blockchain',
		('bob_resolve_addr',          'resolving an address in the tracking wallet'),
		('bob_rescan_addr',           'rescanning an address'),
		('bob_rescan_blockchain_all', 'rescanning the blockchain (full rescan)'),
		('bob_rescan_blockchain_gb',  'rescanning the blockchain (Genesis block)'),
		('bob_rescan_blockchain_one', 'rescanning the blockchain (single block)'),
		('bob_rescan_blockchain_ss',  'rescanning the blockchain (range of blocks)'),
	),
	'main': (
		'creating, signing, sending and bumping transactions',
		('bob_add_comment1',           "adding an 80-screen-width label (lat+cyr+gr)"),
		('bob_twview1',                "viewing Bob's tracking wallet"),
		('bob_split1',                 "splitting Bob's funds"),
		('generate',                   'mining a block'),
		('bob_bal2',                   "Bob's balance"),
		('bob_rbf_1output_create',     'creating RBF tx with one output'),
		('bob_rbf_1output_bump',       'bumping RBF tx with one output'),
		('bob_bal2a',                  "Bob's balance (age_fmt=confs)"),
		('bob_bal2b',                  "Bob's balance (showempty=1)"),
		('bob_bal2c',                  "Bob's balance (showempty=1 minconf=2 age_fmt=days)"),
		('bob_bal2d',                  "Bob's balance (minconf=2)"),
		('bob_bal2e',                  "Bob's balance (showempty=1 sort=age)"),
		('bob_bal2f',                  "Bob's balance (showempty=1 sort=age,reverse)"),
		('bob_send_maybe_rbf',         'sending funds to Alice (RBF, if supported)'),
		('get_mempool1',               'mempool (before RBF bump)'),
		('bob_rbf_status1',            'getting status of transaction'),
		('bob_rbf_bump',               'bumping RBF transaction'),
		('get_mempool2',               'mempool (after RBF bump)'),
		('bob_rbf_status2',            'getting status of transaction after replacement'),
		('bob_rbf_status3',            'getting status of replacement transaction (mempool)'),
		('generate',                   'mining a block'),
		('bob_rbf_status4',            'getting status of transaction after confirmed (1) replacement'),
		('bob_rbf_status5',            'getting status of replacement transaction (confirmed)'),
		('generate',                   'mining a block'),
		('bob_rbf_status6',            'getting status of transaction after confirmed (2) replacement'),
		('bob_bal3',                   "Bob's balance"),
		('bob_pre_import',             'sending to non-imported address'),
		('generate',                   'mining a block'),
		('bob_import_addr',            'importing non-MMGen address'),
		('bob_bal4',                   "Bob's balance (after import)"),
		('bob_import_list',            'importing flat address list'),
		('bob_import_list_rescan',     'importing flat address list with --rescan'),
		('bob_import_list_rescan_aio', 'importing flat address list with --rescan (aiohttp backend)'),

		('bob_split2',                 "splitting Bob's funds"),
		('bob_0conf0_getbalance',      "Bob's balance (unconfirmed, minconf=0)"),
		('bob_0conf1_getbalance',      "Bob's balance (unconfirmed, minconf=1)"),
		('generate',                   'mining a block'),
		('bob_1conf1_getbalance',      "Bob's balance (confirmed, minconf=1)"),
		('bob_1conf2_getbalance',      "Bob's balance (confirmed, minconf=2)"),
		('bob_bal5',                   "Bob's balance"),
		('bob_send_non_mmgen',         'sending funds to Alice (from non-MMGen addrs)'),
		('generate',                   'mining a block'),
		('alice_send_estimatefee',     'tx creation with no fee on command line'),
		('generate',                   'mining a block'),
		('bob_bal6',                   "Bob's balance"),

		('bob_subwallet_addrgen1',     "generating Bob's addrs from subwallet 29L"),
		('bob_subwallet_addrgen2',     "generating Bob's addrs from subwallet 127S"),
		('bob_subwallet_addrimport1',  "importing Bob's addrs from subwallet 29L"),
		('bob_subwallet_addrimport2',  "importing Bob's addrs from subwallet 127S"),
		('bob_subwallet_fund',         "funding Bob's subwallet addrs"),
		('generate',                   'mining a block'),
		('bob_twview2',                "viewing Bob's tracking wallet"),
		('bob_twview3',                "viewing Bob's tracking wallet"),
		('bob_subwallet_txcreate',     'creating a transaction with subwallet inputs'),
		('bob_subwallet_txsign',       'signing a transaction with subwallet inputs'),
		('bob_subwallet_txdo',         "sending from Bob's subwallet addrs"),
		('generate',                   'mining a block'),
		('bob_twview4',                "viewing Bob's tracking wallet"),

		('bob_alice_bal',              "Bob and Alice's balances"),

		('bob_nochg_burn',             'zero-change transaction to burn address'),
		('generate',                   'mining a block'),
	),
	'twprune': (
		'exporting a pruned tracking wallet to JSON',
		('bob_twprune_noask',    'pruning a tracking wallet'),
		('bob_twprune_skip',     'pruning a tracking wallet (skip pruning)'),
		('bob_twprune_all',      'pruning a tracking wallet (pruning all addrs)'),
		('bob_twprune_skipamt',  'pruning a tracking wallet (skipping addrs with amt)'),
		('bob_twprune_skipused', 'pruning a tracking wallet (skipping used addrs)'),
		('bob_twprune_allamt',   'pruning a tracking wallet (pruning addrs with amt)'),
		('bob_twprune_allused',  'pruning a tracking wallet (pruning used addrs)'),
		('bob_twprune1',         'pruning a tracking wallet (selective prune)'),
		('bob_twprune2',         'pruning a tracking wallet (selective prune)'),
		('bob_twprune3',         'pruning a tracking wallet (selective prune)'),
		('bob_twprune4',         'pruning a tracking wallet (selective prune)'),
		('bob_twprune5',         'pruning a tracking wallet (selective prune)'),
		('bob_twprune6',         'pruning a tracking wallet (selective prune)'),
	),
	'txhist': (
		'viewing transaction history',
		('bob_txhist1',            "viewing Bob's transaction history (sort=age)"),
		('bob_txhist2',            "viewing Bob's transaction history (sort=blockheight reverse=1)"),
		('bob_txhist3',            "viewing Bob's transaction history (sort=blockheight sinceblock=-7)"),
		('bob_txhist4',            "viewing Bob's transaction history (sinceblock=399 detail=1)"),
		('bob_txhist_interactive', "viewing Bob's transaction history (age_fmt=date_time interactive=true)"),
	),
	'label': (
		'adding, removing and editing labels',
		('alice_bal2',                 "Alice's balance"),
		('alice_add_comment1',         'adding a label'),
		('alice_chk_comment1',         'the label'),
		('alice_add_comment2',         'adding a label'),
		('alice_chk_comment2',         'the label'),
		('alice_edit_comment1',        'editing a label (zh)'),
		('alice_edit_comment2',        'editing a label (lat+cyr+gr)'),
		('alice_chk_comment3',         'the label'),
		('alice_remove_comment1',      'removing a label'),
		('alice_chk_comment4',         'the label'),
		('alice_add_comment_coinaddr', 'adding a label using the coin address'),
		('alice_chk_comment_coinaddr', 'the label'),
		('alice_add_comment_badaddr1', 'adding a label with invalid address'),
		('alice_add_comment_badaddr2', 'adding a label with invalid address for this chain'),
		('alice_add_comment_badaddr3', 'adding a label with wrong MMGen address'),
		('alice_add_comment_badaddr4', 'adding a label with wrong coin address'),
	),
	'view': (
		'viewing addresses and unspent outputs',
		('alice_listaddresses_scroll',    'listaddresses (--scroll, interactive=1)'),
		('alice_listaddresses_empty',     'listaddresses (no data)'),
		('alice_listaddresses_menu',      'listaddresses (menu items)'),
		('alice_listaddresses1',          'listaddresses'),
		('alice_listaddresses_days',      'listaddresses (age_fmt=days)'),
		('alice_listaddresses_date',      'listaddresses (age_fmt=date)'),
		('alice_listaddresses_date_time', 'listaddresses (age_fmt=date_time)'),
		('alice_twview1',                 'twview'),
		('alice_twview_days',             'twview (age_fmt=days)'),
		('alice_twview_date',             'twview (age_fmt=date)'),
		('alice_twview_date_time',        'twview (age_fmt=date_time)'),
		('alice_txcreate_info',           'txcreate -i'),
		('alice_txcreate_info_term',      'txcreate -i (pexpect_spawn)'),
		('bob_send_to_alice_2addr',       'sending a TX to 2 addresses in Alice’s wallet'),
		('bob_send_to_alice_reuse',       'sending a TX to a used address in Alice’s wallet'),
		('generate',                      'mining a block'),
		('alice_twview_grouped',          'twview (testing ‘grouped’ option for TX and address)'),
	),
	'_auto_chg_deps': (
		'automatic change address selection dependencies',
		('bob_auto_chg_split',    'splitting Bob’s funds (auto-chg-addr dependency)'),
		('bob_auto_chg_generate', 'mining a block (auto-chg-addr dependency)'),
	),
	'auto_chg': (
		'automatic change address selection',
		('bob_auto_chg1',     'creating an automatic change address transaction (C)'),
		('bob_auto_chg2',     'creating an automatic change address transaction (B)'),
		('bob_auto_chg3',     'creating an automatic change address transaction (S)'),
		('bob_auto_chg4',     'creating an automatic change address transaction (single address)'),
		('bob_auto_chg_addrtype1', 'creating an automatic change address transaction by addrtype (C)'),
		('bob_auto_chg_addrtype2', 'creating an automatic change address transaction by addrtype (B)'),
		('bob_auto_chg_addrtype3', 'creating an automatic change address transaction by addrtype (S)'),
		('bob_auto_chg_addrtype4', 'creating an automatic change address transaction by addrtype (single address)'),
		('bob_add_comment_uua1',   'adding a comment for unused address in tracking wallet (C)'),
		('bob_auto_chg5',          'creating an auto-chg-address TX, skipping unused address with label (C)'),
		('bob_auto_chg_addrtype5', 'creating an auto-chg-address TX by addrtype, skipping unused address '
									'with label (C)'),
		('bob_auto_chg6',          'creating an auto-chg-address TX, using unused address with label (C)'),
		('bob_auto_chg_addrtype6', 'creating an auto-chg-address TX by addrtype, using unused address with '
									'label (C)'),
		('bob_remove_comment_uua1', 'removing a comment for unused address in tracking wallet (C)'),
		('bob_auto_chg_bad1',       'error handling for auto change address transaction (bad ID FFFFFFFF:C)'),
		('bob_auto_chg_bad2',       'error handling for auto change address transaction (bad ID 00000000:C)'),
		('bob_auto_chg_bad3',       'error handling for auto change address transaction (no unused addresses)'),
		('bob_auto_chg_bad4',       'error handling for auto change address transaction by addrtype '
									'(no unused addresses)'),
		('carol_twimport2',          'recreating Carol’s tracking wallet from JSON dump'),
		('carol_rescan_blockchain',  'rescanning the blockchain (full rescan)'),
		('carol_auto_chg1',          'creating an automatic change address transaction (C)'),
		('carol_auto_chg2',          'creating an automatic change address transaction (B)'),
		('carol_auto_chg3',          'creating an automatic change address transaction (S)'),
		('carol_auto_chg_addrtype1', 'creating an automatic change address transaction by addrtype (C)'),
		('carol_auto_chg_addrtype2', 'creating an automatic change address transaction by addrtype (B)'),
		('carol_auto_chg_addrtype3', 'creating an automatic change address transaction by addrtype (S)'),
		('carol_auto_chg_bad1',      'error handling for auto change address transaction (no unused addresses)'),
		('carol_auto_chg_bad2',      'error handling for auto change address transaction by addrtype '
									'(no unused addresses)'),
		('carol_delete_wallet',      'unloading and deleting Carol’s tracking wallet'),
	),
	}

	def __init__(self,trunner,cfgs,spawn):
		CmdTestBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return
		if self.proto.testnet:
			die(2,'--testnet and --regtest options incompatible with regtest test suite')
		self.proto = init_proto( cfg, self.proto.coin, network='regtest', need_amt=True )
		coin = self.proto.coin.lower()

		for k in rt_data:
			setattr( sys.modules[__name__], k, rt_data[k][coin] if coin in rt_data[k] else None )

		if self.proto.coin == 'BTC':
			self.test_rbf = True # tests are non-coin-dependent, so run just once for BTC
			if cfg.test_suite_deterministic:
				self.deterministic = True
				self.miner_addr = 'bcrt1qaq8t3pakcftpk095tnqfv5cmmczysls024atnd' # regtest.create_hdseed()
				self.miner_wif = 'cTyMdQ2BgfAsjopRVZrj7AoEGp97pKfrC2NkqLuwHr4KHfPNAKwp'

		self.spawn_env['MMGEN_BOGUS_SEND'] = ''
		self.write_to_tmpfile('wallet_password',rt_pw)

		self.dfl_mmtype = 'C' if self.proto.coin == 'BCH' else 'B'
		self.burn_addr = make_burn_addr(self.proto)
		self.user_sids = {}

	def _add_comments_to_addr_file(self,addrfile,outfile,use_comments=False):
		silence()
		gmsg(f'Adding comments to address file {addrfile!r}')
		a = AddrList( cfg, self.proto, addrfile )
		for n,idx in enumerate(a.idxs(),1):
			if use_comments:
				a.set_comment(idx,get_comment())
			else:
				if n % 2:
					a.set_comment(idx,f'Test address {n}')
		a.file.format(add_comments=True)
		from mmgen.fileutil import write_data_to_file
		write_data_to_file(
			cfg,
			outfile           = outfile,
			data              = a.file.fmt_data,
			quiet             = True,
			ignore_opt_outdir = True )

		end_silence()

	def setup(self):
		stop_test_daemons(self.proto.network_id,force=True,remove_datadir=True)
		from shutil import rmtree
		try:
			rmtree(joinpath(self.tr.data_dir,'regtest'))
		except:
			pass
		t = self.spawn('mmgen-regtest',['-n','setup'])
		for s in ('Starting','Creating','Creating','Creating','Mined','Setup complete'):
			t.expect(s)
		return t

	def daemon_version(self):
		t = self.spawn('mmgen-tool', ['--bob','daemon_version'])
		t.expect('version')
		return t

	def halving_calculator_bob(self):
		t = self.spawn('halving-calculator.py',['--bob'],cmd_dir='examples')
		t.expect('time until halving')
		return t

	def walletgen(self,user):
		t = self.spawn('mmgen-walletgen',['-q','-r0','-p1','--'+user])
		t.passphrase_new('new '+dfl_wcls.desc,rt_pw)
		t.label()
		t.expect('move it to the data directory? (Y/n): ','y')
		t.written_to_file(capfirst(dfl_wcls.desc))
		return t

	def walletgen_bob(self):
		return self.walletgen('bob')
	def walletgen_alice(self):
		return self.walletgen('alice')

	def _user_dir(self,user,coin=None):
		return joinpath(self.tr.data_dir,'regtest',coin or self.proto.coin.lower(),user)

	def _user_sid(self,user):
		if user in self.user_sids:
			return self.user_sids[user]
		else:
			self.user_sids[user] = os.path.basename(get_file_with_ext(self._user_dir(user),'mmdat'))[:8]
			return self.user_sids[user]

	def _get_user_subsid(self,user,subseed_idx):
		fn = get_file_with_ext(self._user_dir(user),dfl_wcls.ext)
		silence()
		w = Wallet( cfg, fn=fn, passwd_file=os.path.join(self.tmpdir,'wallet_password') )
		end_silence()
		return w.seed.subseed(subseed_idx).sid

	def addrgen(
			self,
			user,
			wf          = None,
			addr_range  = '1-5',
			subseed_idx = None,
			mmtypes     = []):
		from mmgen.addr import MMGenAddrType
		for mmtype in mmtypes or self.proto.mmtypes:
			t = self.spawn(
				'mmgen-addrgen',
				['--quiet','--'+user,'--type='+mmtype,f'--outdir={self._user_dir(user)}'] +
				([wf] if wf else []) +
				(['--subwallet='+subseed_idx] if subseed_idx else []) +
				[addr_range],
				extra_desc = '({})'.format( MMGenAddrType.mmtypes[mmtype].name ))
			t.passphrase(dfl_wcls.desc,rt_pw)
			t.written_to_file('Addresses')
			ok_msg()
		t.skip_ok = True
		return t

	def addrgen_bob(self):
		return self.addrgen('bob')
	def addrgen_alice(self):
		return self.addrgen('alice')

	def addrimport(
			self,
			user,
			sid        = None,
			addr_range = '1-5',
			num_addrs  = 5,
			mmtypes    = [],
			batch      = True,
			quiet      = True):
		id_strs = { 'legacy':'', 'compressed':'-C', 'segwit':'-S', 'bech32':'-B' }
		if not sid:
			sid = self._user_sid(user)
		from mmgen.addr import MMGenAddrType
		for mmtype in mmtypes or self.proto.mmtypes:
			desc = MMGenAddrType.mmtypes[mmtype].name
			addrfile = joinpath(self._user_dir(user),
				'{}{}{}[{}]{x}.regtest.addrs'.format(
					sid,self.altcoin_pfx,id_strs[desc],addr_range,
					x='-α' if cfg.debug_utf8 else ''))
			if mmtype == self.proto.mmtypes[0] and user == 'bob':
				self._add_comments_to_addr_file(addrfile,addrfile,use_comments=True)
			t = self.spawn(
				'mmgen-addrimport',
				args = (
					(['--quiet'] if quiet else []) +
					['--'+user] +
					(['--batch'] if batch else []) +
					[addrfile] ),
				extra_desc = f'({desc})' )
			if cfg.debug:
				t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
			t.expect('Importing')
			if batch:
				t.expect(f'{num_addrs} addresses imported')
			else:
				t.expect('import completed OK')
			t.ok()

		t.skip_ok = True
		return t

	def addrimport_bob(self):
		return self.addrimport('bob')
	def addrimport_alice(self):
		return self.addrimport('alice',batch=False,quiet=False)

	def bob_import_miner_addr(self):
		if not self.deterministic:
			return 'skip'
		return self.spawn(
			'mmgen-addrimport',
			[ '--bob', '--rescan', '--quiet', f'--address={self.miner_addr}' ] )

	def fund_wallet_deterministic(self,addr,utxo_nums,skip_passphrase=False):
		"""
		the deterministic funding method using specific inputs
		"""
		if not self.deterministic:
			return 'skip'
		self.write_to_tmpfile('miner.key',f'{self.miner_wif}\n')
		keyfile = joinpath(self.tmpdir,'miner.key')

		return self.user_txdo(
			'bob', '40s',
			[ f'{addr},{rtFundAmt}', self.burn_addr ],
			utxo_nums,
			extra_args = [f'--keys-from-file={keyfile}'],
			skip_passphrase = skip_passphrase )

	def fund_bob_deterministic(self):
		return self.fund_wallet_deterministic( f'{self._user_sid("bob")}:C:1', '1-11' )

	def fund_alice_deterministic(self):
		sid = self._user_sid('alice')
		mmtype = ('L','S')[self.proto.cap('segwit')]
		addr = self.get_addr_from_addrlist('alice',sid,mmtype,0,addr_range='1-5')
		return self.fund_wallet_deterministic( addr, '1-11', skip_passphrase=True )

	def generate_extra_deterministic(self):
		if not self.deterministic:
			return 'skip'
		return self.generate(num_blocks=2) # do this so block count matches non-deterministic run

	async def bob_recreate_tracking_wallet(self):
		if not self.deterministic:
			return 'skip'
		self.spawn('',msg_only=True)
		from mmgen.proto.btc.regtest import MMGenRegtest
		rt = MMGenRegtest(cfg,self.proto.coin)
		await rt.stop()
		from shutil import rmtree
		imsg('Deleting Bob’s old tracking wallet')
		rmtree(os.path.join(rt.d.datadir,'regtest','wallets','bob'),ignore_errors=True)
		rt.init_daemon()
		rt.d.start(silent=True)
		imsg('Creating Bob’s new tracking wallet')
		await rt.rpc_call('createwallet','bob',True,True,None,False,False,False)
		await rt.stop()
		await rt.start()
		return 'ok'

	def addrimport_bob2(self):
		if not self.deterministic:
			return 'skip'
		return self.addrimport('bob')

	def fund_wallet(self,user,mmtype,amt,sid=None,addr_range='1-5'):
		if self.deterministic:
			return 'skip'
		if not sid:
			sid = self._user_sid(user)
		addr = self.get_addr_from_addrlist(user,sid,mmtype,0,addr_range=addr_range)
		t = self.spawn('mmgen-regtest', ['send',str(addr),str(amt)])
		t.expect(f'Sending {amt} miner {self.proto.coin}')
		t.expect('Mined 1 block')
		return t

	def fund_bob(self):
		return self.fund_wallet('bob','C',rtFundAmt)

	def fund_alice(self):
		return self.fund_wallet('alice',('L','S')[self.proto.cap('segwit')],rtFundAmt)

	def user_twview(self,user,chk,sort='age'):
		t = self.spawn('mmgen-tool',['--'+user,'twview','sort='+sort])
		if chk:
			t.expect(r'{}\b.*\D{}\b'.format(*chk),regex=True)
		return t

	def bob_twview1(self):
		return self.user_twview('bob', chk = ('1',rtAmts[0]) )

	def user_bal(self,user,bal,args=['showempty=1'],skip_check=False):
		t = self.spawn('mmgen-tool',['--'+user,'listaddresses'] + args)
		if not skip_check:
			cmp_or_die(f'{bal} {self.proto.coin}',strip_ansi_escapes(t.expect_getend('TOTAL: ')))
		return t

	def alice_bal1(self):
		return self.user_bal('alice',rtFundAmt)

	def alice_bal2(self):
		return self.user_bal('alice',rtBals[8])

	def bob_bal1(self):
		return self.user_bal('bob',rtFundAmt)

	def bob_bal2(self):
		return self.user_bal('bob',rtBals[0])

	def bob_bal2a(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','age_fmt=confs'])

	def bob_bal2b(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1'])

	def bob_bal2c(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','minconf=2','age_fmt=days'],skip_check=True)

	def bob_bal2d(self):
		return self.user_bal('bob',rtBals[0],args=['minconf=2'],skip_check=True)

	def bob_bal2e(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','sort=amt'])

	def bob_bal2f(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=0','sort=twmmid','reverse=1'])

	def bob_bal3(self):
		return self.user_bal('bob',rtBals[1])

	def bob_bal4(self):
		return self.user_bal('bob',rtBals[2])

	def bob_bal5(self):
		return self.user_bal('bob',rtBals[3])

	def bob_bal6(self):
		return self.user_bal('bob',rtBals[7])

	def bob_subwallet_addrgen1(self):
		return self.addrgen('bob',subseed_idx='29L',mmtypes=['C'])  # 29L: 2FA7BBA8

	def bob_subwallet_addrgen2(self):
		return self.addrgen('bob',subseed_idx='127S',mmtypes=['C']) # 127S: '09E8E286'

	def subwallet_addrimport(self,user,subseed_idx):
		sid = self._get_user_subsid(user,subseed_idx)
		return self.addrimport(user,sid=sid,mmtypes=['C'])

	def bob_subwallet_addrimport1(self):
		return self.subwallet_addrimport('bob','29L')
	def bob_subwallet_addrimport2(self):
		return self.subwallet_addrimport('bob','127S')

	def bob_subwallet_fund(self):
		sid1 = self._get_user_subsid('bob','29L')
		sid2 = self._get_user_subsid('bob','127S')
		chg_addr = self._user_sid('bob') + (':B:1',':L:1')[self.proto.coin=='BCH']
		return self.user_txdo(
			user               = 'bob',
			fee                = rtFee[1],
			outputs_cl         = [sid1+':C:2,0.29',sid2+':C:3,0.127',chg_addr],
			outputs_list       = ('3','1')[self.proto.coin=='BCH'],
			extra_args         = ['--subseeds=127'],
			used_chg_addr_resp = (None,'y')[self.proto.coin=='BCH'] )

	def bob_twview2(self):
		sid1 = self._get_user_subsid('bob','29L')
		return self.user_twview('bob',chk=(sid1+':C:2','0.29'),sort='twmmid')

	def bob_twview3(self):
		sid2 = self._get_user_subsid('bob','127S')
		return self.user_twview('bob',chk=(sid2+':C:3','0.127'),sort='amt')

	def bob_subwallet_txcreate(self):
		sid1 = self._get_user_subsid('bob','29L')
		sid2 = self._get_user_subsid('bob','127S')
		outputs_cl = [sid1+':C:5,0.0159',sid2+':C:5']
		t = self.spawn('mmgen-txcreate',['-d',self.tmpdir,'-B','--bob'] + outputs_cl)
		return self.txcreate_ui_common(t,
			menu            = ['a'],
			inputs          = ('1,2','2,3')[self.proto.coin=='BCH'],
			interactive_fee = '0.00001')

	def bob_subwallet_txsign(self):
		fn = get_file_with_ext(self.tmpdir,'rawtx')
		t = self.spawn('mmgen-txsign',['-d',self.tmpdir,'--bob','--subseeds=127',fn])
		t.view_tx('t')
		t.passphrase(dfl_wcls.desc,rt_pw)
		t.do_comment(None)
		t.expect('(Y/n): ','y')
		t.written_to_file('Signed transaction')
		return t

	def bob_subwallet_txdo(self):
		outputs_cl = [self._user_sid('bob')+':L:5']
		inputs = ('1,2','2,3')[self.proto.coin=='BCH']
		return self.user_txdo('bob',rtFee[5],outputs_cl,inputs,menu=['a'],extra_args=['--subseeds=127']) # sort: amt

	def bob_twview4(self):
		sid = self._user_sid('bob')
		return self.user_twview('bob',chk=(sid+':L:5',rtBals[9]),sort='twmmid')

	def user_txhist(self,user,args,expect):
		t = self.spawn('mmgen-tool',['--'+user,'txhist'] + args)
		m = re.search( expect, t.read(strip_color=True), re.DOTALL )
		assert m, f'Expected: {expect}'
		return t

	def bob_txhist1(self):
		return self.user_txhist('bob',
			args = ['sort=age'],
			expect = fr'\s1\).*\s{rtFundAmt}\s' )

	def bob_txhist2(self):
		return self.user_txhist('bob',
			args = ['sort=blockheight','reverse=1','age_fmt=block'],
			expect = fr'\s1\).*:{self.dfl_mmtype}:1\s' )

	def bob_txhist3(self):
		return self.user_txhist('bob',
			args = ['sort=blockheight','sinceblock=-7','age_fmt=block'],
			expect = fr'Displaying transactions since block 399.*\s6\)\s+405\s.*\s{rtBals[9]}\s.*:L:5.*\s7\)'
		)

	def bob_txhist4(self):
		return self.user_txhist('bob',
			args = ['sort=blockheight','sinceblock=399','age_fmt=block','detail=1'],
			expect = fr'Displaying transactions since block 399.*\s7\).*Block:.*406.*Value:.*{rtBals[10]}'
		)

	def bob_txhist_interactive(self):
		self.get_file_with_ext('out',delete_all=True)
		t = self.spawn('mmgen-tool',
			['--bob',f'--outdir={self.tmpdir}','txhist','age_fmt=date_time','interactive=true'] )
		for resp in ('u','i','t','a','m','T','A','r','r','D','D','D','D','p','P','n','V'):
			t.expect('draw:\b',resp,regex=True)
		if t.pexpect_spawn:
			t.expect(r'Block:.*394',regex=True)
			time.sleep(1)
			t.send('q')
			time.sleep(0.2)
			t.send('n')
			t.expect('draw:\b','q',regex=True)
		else:
			txnum,idx = (8,1) if self.proto.coin == 'BCH' else (9,3)
			t.expect(rf'\s{txnum}\).*Inputs:.*:L:{idx}.*Outputs \(3\):.*:C:2.*\s10\)','q',regex=True)
		return t

	def bob_getbalance(self,bals,confs=1):
		for i in range(len(bals['mmgen'])):
			assert Decimal(bals['mmgen'][i]) + Decimal(bals['nonmm'][i]) == Decimal(bals['total'][i])
		sid = self._user_sid('bob')
		t = self.spawn('mmgen-tool',['--bob','getbalance',f'minconf={confs}'])
		t.expect('Wallet')
		for k,lbl in (
			('mmgen',f'{sid}:'),
			('nonmm','Non-MMGen:'),
			('total',f'TOTAL {self.proto.coin}')
		):
			ret = strip_ansi_escapes(t.expect_getend(lbl + ' '))
			cmp_or_die(
				' '.join(bals[k]),
				' '.join(ret.split()),
				desc = k,
			)
		return t

	def bob_0conf0_getbalance(self):
		return self.bob_getbalance(rtBals_gb['0conf0'],confs=0)
	def bob_0conf1_getbalance(self):
		return self.bob_getbalance(rtBals_gb['0conf1'],confs=1)
	def bob_1conf1_getbalance(self):
		return self.bob_getbalance(rtBals_gb['1conf1'],confs=1)
	def bob_1conf2_getbalance(self):
		return self.bob_getbalance(rtBals_gb['1conf2'],confs=2)

	def bob_nochg_burn(self):
		return self.user_txdo('bob',
			fee          = '0.00009713',
			outputs_cl   = [self.burn_addr],
			outputs_list = '1' )

	def bob_alice_bal(self):
		t = self.spawn('mmgen-regtest',['balances'])
		ret = t.expect_getend("Bob's balance:").strip()
		cmp_or_die(rtBals[4],ret)
		ret = t.expect_getend("Alice's balance:").strip()
		cmp_or_die(rtBals[5],ret)
		ret = t.expect_getend("Total balance:").strip()
		cmp_or_die(rtBals[6],ret)
		return t

	def user_txsend_status(self,user,tx_file,exp1='',exp2='',extra_args=[]):
		t = self.spawn('mmgen-txsend',['-d',self.tmpdir,'--'+user,'--status'] + extra_args + [tx_file])
		if exp1:
			t.expect(exp1,regex=True)
		if exp2:
			t.expect(exp2,regex=True)
		return t

	def user_txdo(
			self,
			user,
			fee,
			outputs_cl,
			outputs_list,
			extra_args         = [],
			wf                 = None,
			bad_locktime       = False,
			menu               = ['M'],
			skip_passphrase    = False,
			used_chg_addr_resp = None):

		t = self.spawn('mmgen-txdo',
			['-d',self.tmpdir,'-B','--'+user] +
			(['--fee='+fee] if fee else []) +
			extra_args + ([],[wf])[bool(wf)] + outputs_cl)

		self.txcreate_ui_common(
				t,
				caller             = 'txdo',
				menu               = menu,
				inputs             = outputs_list,
				file_desc          = 'Signed transaction',
				interactive_fee    = (tx_fee,'')[bool(fee)],
				add_comment        = tx_comment_jp,
				view               = 't',
				save               = True,
				used_chg_addr_resp = used_chg_addr_resp)

		if not skip_passphrase:
			t.passphrase(dfl_wcls.desc,rt_pw)

		t.written_to_file('Signed transaction')
		self._do_confirm_send(t)
		s,exit_val = (('Transaction sent',0),("can't be included",1))[bad_locktime]
		t.expect(s)
		t.req_exit_val = exit_val
		return t

	def bob_split1(self):
		sid = self._user_sid('bob')
		outputs_cl = [sid+':C:1,100', sid+':L:2,200',sid+':'+rtBobOp3]
		return self.user_txdo('bob',rtFee[0],outputs_cl,'1')

	def get_addr_from_addrlist(self,user,sid,mmtype,idx,addr_range='1-5'):
		id_str = { 'L':'', 'S':'-S', 'C':'-C', 'B':'-B' }[mmtype]
		ext = '{}{}{}[{}]{x}.regtest.addrs'.format(
			sid,self.altcoin_pfx,id_str,addr_range,x='-α' if cfg.debug_utf8 else '')
		addrfile = get_file_with_ext(self._user_dir(user),ext,no_dot=True)
		silence()
		addr = AddrList( cfg, self.proto, addrfile ).data[idx].addr
		end_silence()
		return addr

	def _create_tx_outputs(self,user,data):
		sid = self._user_sid(user)
		return [self.get_addr_from_addrlist(user,sid,mmtype,idx-1)+amt_str for mmtype,idx,amt_str in data]

	def bob_rbf_1output_create(self):
		if not self.test_rbf:
			return 'skip'
		out_addr = self._create_tx_outputs('alice',(('B',5,''),))
		t = self.spawn('mmgen-txcreate',['-d',self.tr.trash_dir,'-B','--bob','--rbf'] + out_addr)
		return self.txcreate_ui_common(t,menu=[],inputs='3',interactive_fee='3s') # out amt: 199.99999343

	def bob_rbf_1output_bump(self):
		if not self.test_rbf:
			return 'skip'
		ext = '9343,3]{x}.regtest.rawtx'.format(x='-α' if cfg.debug_utf8 else '')
		txfile = get_file_with_ext(self.tr.trash_dir,ext,delete=False,no_dot=True)
		return self.user_txbump('bob',
			self.tr.trash_dir,
			txfile,
			'8s',
			has_label  = False,
			signed_tx  = False,
			one_output = True )

	def bob_send_maybe_rbf(self):
		outputs_cl = self._create_tx_outputs('alice',(('L',1,',60'),('C',1,',40'))) # alice_sid:L:1, alice_sid:C:1
		outputs_cl += [self._user_sid('bob')+':'+rtBobOp3]
		return self.user_txdo('bob',rtFee[1],outputs_cl,'3',
					extra_args = ([],['--rbf'])[self.proto.cap('rbf')],
					used_chg_addr_resp = 'y' )

	def bob_send_non_mmgen(self):
		outputs_cl = self._create_tx_outputs('alice',(
			(('L','S')[self.proto.cap('segwit')],2,',10'),
			(('L','S')[self.proto.cap('segwit')],3,'')
		)) # alice_sid:S:2, alice_sid:S:3
		keyfile = joinpath(self.tmpdir,'non-mmgen.keys')
		return self.user_txdo('bob',rtFee[3],outputs_cl,'1,4-10',
			extra_args=['--keys-from-file='+keyfile,'--vsize-adj=1.02'])

	def alice_send_estimatefee(self):
		outputs_cl = self._create_tx_outputs('bob',(('L',1,''),)) # bob_sid:L:1
		return self.user_txdo('alice',None,outputs_cl,'1') # fee=None

	def user_txbump(
			self,
			user,
			outdir,
			txfile,
			fee,
			add_args   = [],
			has_label  = True,
			signed_tx  = True,
			one_output = False):
		if not self.proto.cap('rbf'):
			return 'skip'
		t = self.spawn('mmgen-txbump',
			['-d',outdir,'--'+user,'--fee='+fee,'--output-to-reduce=c'] + add_args + [txfile])
		if not one_output:
			t.expect('OK? (Y/n): ','y') # output OK?
		t.expect('OK? (Y/n): ','y') # fee OK?
		t.do_comment(False,has_label=has_label)
		if signed_tx:
			t.passphrase(dfl_wcls.desc,rt_pw)
			t.written_to_file('Signed transaction')
			self.txsend_ui_common(t,caller='txdo',bogus_send=False,file_desc='Signed transaction')
		else:
			t.expect('Save fee-bumped transaction? (y/N): ','y')
			t.written_to_file('Fee-bumped transaction')
		return t

	def bob_rbf_bump(self):
		ext = ',{}]{x}.regtest.sigtx'.format(rtFee[1][:-1],x='-α' if cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,delete=False,no_dot=True)
		return self.user_txbump('bob',self.tmpdir,txfile,rtFee[2],add_args=['--send'])

	def generate(self,num_blocks=1):
		int(num_blocks)
		t = self.spawn('mmgen-regtest',['generate',str(num_blocks)])
		t.expect(f'Mined {num_blocks} block')
		return t

	def _get_mempool(self):
		ret = self.spawn(
			'mmgen-regtest',
			['mempool'],
			env = os.environ if cfg.debug_utf8 else get_env_without_debug_vars(),
		).read()
		m = re.search(r'(\[\s*"[a-f0-9]{64}"\s*])',ret) # allow for extra output by handler at end
		return json.loads(m.group(1))

	def get_mempool1(self):
		mp = self._get_mempool()
		if len(mp) != 1:
			die(4,'Mempool has more or less than one TX!')
		self.write_to_tmpfile('rbf_txid',mp[0]+'\n')
		return 'ok'

	def bob_rbf_status(self,fee,exp1,exp2=''):
		if not self.proto.cap('rbf'):
			return 'skip'
		ext = ',{}]{x}.regtest.sigtx'.format(fee[:-1],x='-α' if cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,delete=False,no_dot=True)
		return self.user_txsend_status('bob',txfile,exp1,exp2)

	def bob_rbf_status1(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self.bob_rbf_status(rtFee[1],'in mempool, replaceable')

	def get_mempool2(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		mp = self._get_mempool()
		if len(mp) != 1:
			die(4,'Mempool has more or less than one TX!')
		chk = self.read_from_tmpfile('rbf_txid')
		if chk.strip() == mp[0]:
			die(4,'TX in mempool has not changed!  RBF bump failed')
		self.write_to_tmpfile('rbf_txid2',mp[0]+'\n')
		return 'ok'

	def bob_rbf_status2(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		new_txid = self.read_from_tmpfile('rbf_txid2').strip()
		return self.bob_rbf_status(rtFee[1],
			'Transaction has been replaced',f'{new_txid} in mempool')

	def bob_rbf_status3(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self.bob_rbf_status(rtFee[2],'status: in mempool, replaceable')

	def bob_rbf_status4(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		new_txid = self.read_from_tmpfile('rbf_txid2').strip()
		return self.bob_rbf_status(rtFee[1],
			'Replacement transaction has 1 confirmation',
			rf'Replacing transactions:\s+{new_txid}' )

	def bob_rbf_status5(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self.bob_rbf_status(rtFee[2],'Transaction has 1 confirmation')

	def bob_rbf_status6(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		new_txid = self.read_from_tmpfile('rbf_txid2').strip()
		return self.bob_rbf_status(rtFee[1],
			'Replacement transaction has 2 confirmations',
			rf'Replacing transactions:\s+{new_txid}' )

	def _gen_pairs(self,n):
		from mmgen.tool.api import tool_api
		t = tool_api(cfg)
		t.init_coin(self.proto.coin,self.proto.network)

		def gen_addr(Type):
			t.addrtype = Type
			wif = t.hex2wif(getrandhex(32))
			return ( wif, t.wif2addr(wif) )

		return [gen_addr('legacy')] + [gen_addr('compressed') for i in range(n-1)]

	def bob_pre_import(self):
		pairs = self._gen_pairs(5)
		self.write_to_tmpfile('non-mmgen.keys','\n'.join([a[0] for a in pairs])+'\n')
		self.write_to_tmpfile('non-mmgen.addrs','\n'.join([a[1] for a in pairs])+'\n')
		return self.user_txdo('bob',rtFee[4],[pairs[0][1]],'3')

	def user_import(self,user,args,nAddr):
		t = self.spawn('mmgen-addrimport',['--'+user]+args)
		if cfg.debug:
			t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
		t.expect(f'Importing {nAddr} address')
		if '--rescan' in args:
			if not '--quiet' in args:
				t.expect('Continue? (Y/n): ','y')
			t.expect('Rescanning block')
		return t

	def bob_import_addr(self):
		addr = self.read_from_tmpfile('non-mmgen.addrs').split()[0]
		return self.user_import('bob',['--quiet','--address='+addr],nAddr=1)

	def bob_import_list_rescan_aio(self):
		addrfile = joinpath(self.tmpdir,'non-mmgen.addrs')
		return self.user_import('bob',['--rescan','--rpc-backend=aio','--addrlist',addrfile],nAddr=5)

	def bob_resolve_addr(self):
		mmaddr = '{}:C:1'.format(self._user_sid('bob'))
		t = self.spawn('mmgen-tool',['--bob','resolve_address',mmaddr])
		coinaddr = t.read().split()[0].strip()
		t = self.spawn('mmgen-tool',['--bob','resolve_address',coinaddr],no_msg=True)
		mmaddr_res = t.read().split()[0].strip()
		assert mmaddr == mmaddr_res, f'{mmaddr} != {mmaddr_res}'
		return t

	def bob_import_list(self):
		addrfile = joinpath(self.tmpdir,'non-mmgen.addrs')
		return self.user_import('bob',['--quiet','--addrlist',addrfile],nAddr=5)

	def bob_import_list_rescan(self):
		addrfile = joinpath(self.tmpdir,'non-mmgen.addrs')
		return self.user_import('bob',['--quiet','--rescan','--addrlist',addrfile],nAddr=5)

	def bob_rescan_addr(self):
		sid = self._user_sid('bob')
		t = self.spawn('mmgen-tool',['--bob','rescan_address',f'{sid}:C:1'])
		t.expect('Found 1 unspent output')
		t.expect('updated successfully')
		return t

	def _usr_rescan_blockchain(self,user,add_args,expect=None):
		t = self.spawn('mmgen-tool',[f'--{user}','rescan_blockchain'] + add_args)
		if expect:
			t.expect(f'Scanning blocks {expect}')
		t.expect('Done')
		return t

	def bob_rescan_blockchain_all(self):
		return self._usr_rescan_blockchain('bob',[],'300-396')

	def bob_rescan_blockchain_gb(self):
		return self._usr_rescan_blockchain('bob',['start_block=0','stop_block=0'],'0-0')

	def bob_rescan_blockchain_one(self):
		return self._usr_rescan_blockchain('bob',['start_block=300','stop_block=300'],'300-300')

	def bob_rescan_blockchain_ss(self):
		return self._usr_rescan_blockchain('bob',['start_block=300','stop_block=302'],'300-302')

	def bob_twexport(self,add_args=[]):
		t = self.spawn('mmgen-tool',['--bob',f'--outdir={self.tmpdir}','twexport'] + add_args)
		t.written_to_file('JSON data')
		return t

	def bob_twexport_noamt(self):
		return self.bob_twexport(add_args=['include_amts=0'])

	def bob_twexport_pretty(self):
		return self.bob_twexport(add_args=['pretty=1'])

	def _bob_twprune(
			self,
			prune_spec,
			npruned,
			expect_menu   = (),
			expect        = (),
			expect2       = (),
			warn_used     = False,
			non_segwit_ok = False):

		if not (non_segwit_ok or self.proto.cap('segwit')):
			return 'skip'

		t = self.spawn(
			'mmgen-tool',
			['--bob',f'--outdir={self.tr.trash_dir}','twexport','prune=1']
			+ (['warn_used=1'] if warn_used else []) )

		for s in expect_menu:
			t.expect('prune list:\b',s)

		t.expect('prune list:\b','p')
		t.expect('addresses to prune: ',f'{prune_spec}\n')

		for p,s in expect:
			t.expect(p,s,regex=True)

		t.expect('prune list:\b','q')

		for p,s in expect2:
			t.expect(p,s,regex=True)

		if npruned:
			t.expect(f'Pruned {npruned} addresses')

		taddr = 35 if self.proto.cap('segwit') else 25
		t.expect(f'Exporting {taddr-npruned} addresses')
		t.written_to_file('JSON data')
		return t

	def bob_twprune_noask(self):
		return self._bob_twprune(
			expect_menu = 'a', # sort by amt to make address order deterministic
			prune_spec  = '35,12,18,3-5',
			npruned     = 6 )

	def bob_twprune_all(self):
		taddr = 35 if self.proto.cap('segwit') else 25
		return self._bob_twprune(
			prune_spec = f'1-{taddr}',
			npruned    = taddr,
			expect     = [('all with balance: ','P')],
			non_segwit_ok = True )

	def bob_twprune_skip(self):
		return self._bob_twprune(
			prune_spec = '',
			npruned    = 0,
			non_segwit_ok = True )

	def bob_twprune_skipamt(self):
		return self._bob_twprune(
			prune_spec = '1-35',
			npruned    = 32,
			expect     = [('all with balance: ','S')] )

	def bob_twprune_skipused(self):
		return self._bob_twprune(
			prune_spec = '1-35',
			npruned    = 18,
			expect     = [('all used: ','S')],
			warn_used  = True )

	def bob_twprune_allamt(self):
		return self._bob_twprune(
			prune_spec = '1-35',
			npruned    = 35,
			expect     = [('all with balance: ','P')],
			expect2    = [('Warning: pruned address .* has a balance',None)] )

	def bob_twprune_allused(self):
		return self._bob_twprune(
			prune_spec = '1-35',
			npruned    = 32,
			expect     = [('all used: ','P'),('all with balance: ','S')],
			expect2    = [('Warning: pruned address .* used',None)],
			warn_used  = True )

	@property
	def _b_start(self):
		"""
		SIDs sort non-deterministically, so we must search for start of main (not subseeds) group, i.e. ':B:1'
		"""
		assert self.proto.cap('segwit')
		if not hasattr(self,'_b_start_'):
			t = self.spawn( 'mmgen-tool', ['--color=0','--bob','listaddresses'], no_msg=True )
			self._b_start_ = int([e for e in t.read().split('\n') if ':B:1' in e][0].split()[0].rstrip(')'))
			t.close()
		return self._b_start_

	def _bob_twprune_selected(self,resp,npruned):
		if not self.proto.cap('segwit'):
			return 'skip'
		B = self._b_start
		a,b,c,d,e,f = resp
		return self._bob_twprune(
			expect_menu = 'a', # sort by amt to make address order deterministic
			prune_spec  = f'31-32,{B+14},{B+9},{B}-{B+4}',
			npruned     = npruned,
			expect      = [
				('all used: ',         a),
				('all used: ',         b),
				('all with balance: ', c),
				('all with balance: ', d),
				('all used: ',         e),
				('all used: ',         f),
			],
			warn_used   = True )

	def bob_twprune1(self):
		return self._bob_twprune_selected(resp='sssssS',npruned=3)

	def bob_twprune2(self):
		return self._bob_twprune_selected(resp='sppPsS',npruned=3)

	def bob_twprune3(self):
		return self._bob_twprune_selected(resp='sssPpS',npruned=3)

	def bob_twprune4(self):
		return self._bob_twprune_selected(resp='sssPpP',npruned=9)

	def bob_twprune5(self):
		return self._bob_twprune_selected(resp='pppPpP',npruned=9)

	def bob_twprune6(self):
		return self._bob_twprune_selected(resp='sssSpP',npruned=7)

	def bob_edit_json_twdump(self):
		self.spawn('',msg_only=True)
		from mmgen.tw.json import TwJSON
		fn = TwJSON.Base(cfg,self.proto).dump_fn
		text = json.loads(self.read_from_tmpfile(fn))
		text['data']['entries'][3][3] = f'edited comment [фубар] [{gr_uc}]'
		self.write_to_tmpfile( fn, json.dumps(text,indent=4) )
		return 'ok'

	def carol_twimport(
			self,
			rpc_backend = 'http',
			add_parms   = [],
			expect_str  = None,
			expect_str2 = 'Found 1 unspent output'):
		from mmgen.tw.json import TwJSON
		fn = joinpath( self.tmpdir, TwJSON.Base(cfg,self.proto).dump_fn )
		t = self.spawn(
			'mmgen-tool',
			([f'--rpc-backend={rpc_backend}'] if rpc_backend else [])
			+ ['--carol','twimport',fn]
			+ add_parms )
		t.expect('(y/N): ','y')
		if expect_str:
			t.expect(expect_str)
		elif 'batch=true' in add_parms:
			t.expect('{} addresses imported'.format(10 if self.proto.coin == 'BCH' else 20))
		else:
			t.expect('import completed OK')
		t.expect(expect_str2)
		return t

	def carol_twimport_nochksum(self):
		return self.carol_twimport(rpc_backend=None,add_parms=['ignore_checksum=true'])

	def carol_twimport_batch(self):
		return self.carol_twimport(add_parms=['batch=true'])

	def carol_twimport_pretty(self):
		return self.carol_twimport(add_parms=['ignore_checksum=true'],expect_str='ignoring incorrect checksum')

	def carol_listaddresses(self):
		return self.spawn('mmgen-tool',['--carol','listaddresses','showempty=1'])

	async def carol_delete_wallet(self):
		imsg('Unloading Carol’s tracking wallet')
		t = self.spawn('mmgen-regtest',['cli','unloadwallet','carol'])
		t.ok()
		from mmgen.rpc import rpc_init
		rpc = await rpc_init(cfg,self.proto)
		wdir = joinpath(rpc.daemon.network_datadir,'wallets','carol')
		from shutil import rmtree
		imsg('Deleting Carol’s tracking wallet')
		rmtree(wdir)
		return 'silent'

	def bob_split2(self):
		addrs = self.read_from_tmpfile('non-mmgen.addrs').split()
		amts = (1.12345678,2.87654321,3.33443344,4.00990099,5.43214321)
		outputs1 = list(map('{},{}'.format,addrs,amts))
		sid = self._user_sid('bob')
		l1,l2 = (
			(':S',':B') if 'B' in self.proto.mmtypes else
			(':S',':S') if self.proto.cap('segwit') else
			(':L',':L') )
		outputs2 = [sid+':C:2,6.333', sid+':L:3,6.667',sid+l1+':4,0.123',sid+l2+':5']
		return self.user_txdo('bob',rtFee[5],outputs1+outputs2,'1-2')

	def user_add_comment(self,user,addr,comment):
		t = self.spawn('mmgen-tool',['--'+user,'add_label',addr,comment])
		t.expect('Added label.*in tracking wallet',regex=True)
		return t

	def user_remove_comment(self,user,addr):
		t = self.spawn('mmgen-tool',['--'+user,'remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		return t

	def bob_add_comment1(self):
		sid = self._user_sid('bob')
		return self.user_add_comment('bob',sid+':C:1',tw_comment_lat_cyr_gr)

	def alice_add_comment1(self):
		sid = self._user_sid('alice')
		return self.user_add_comment('alice',sid+':C:1','Original Label - 月へ')

	def alice_add_comment2(self):
		sid = self._user_sid('alice')
		return self.user_add_comment('alice',sid+':C:1','Replacement Label')

	def _user_chk_comment(self,user,addr,comment,extra_args=[]):
		t = self.spawn('mmgen-tool',['--'+user,'listaddresses','all_labels=1']+extra_args)
		ret = strip_ansi_escapes(t.expect_getend(addr)).strip().split(None,2)[2]
		cmp_or_die( # squeezed display, double-width chars, so truncate to min field width
			ret[:3].strip(),
			comment[:3].strip())
		return t

	def alice_add_comment_coinaddr(self):
		mmid = self._user_sid('alice') + (':S:1',':L:1')[self.proto.coin=='BCH']
		t = self.spawn('mmgen-tool',['--alice','listaddress',mmid,'wide=true'],no_msg=True)
		addr = [i for i in strip_ansi_escapes(t.read()).splitlines() if re.search(rf'\b{mmid}\b',i)][0].split()[3]
		return self.user_add_comment('alice',addr,'Label added using coin address of MMGen address')

	def alice_chk_comment_coinaddr(self):
		mmid = self._user_sid('alice') + (':S:1',':L:1')[self.proto.coin=='BCH']
		return self._user_chk_comment('alice',mmid,'Label added using coin address of MMGen address')

	def alice_add_comment_badaddr(self,addr,reply,exit_val):
		if os.getenv('PYTHONOPTIMIZE'):
			omsg(yellow(f'PYTHONOPTIMIZE set, skipping test {self.test_name!r}'))
			return 'skip'
		t = self.spawn('mmgen-tool',['--alice','add_label',addr,'(none)'])
		t.expect(reply,regex=True)
		t.req_exit_val = exit_val
		return t

	def alice_add_comment_badaddr1(self):
		return self.alice_add_comment_badaddr( rt_pw, 'invalid address', 2 )

	def alice_add_comment_badaddr2(self):
		# mainnet zero address:
		addr = init_proto( cfg, self.proto.coin, network='mainnet' ).pubhash2addr(bytes(20),False)
		return self.alice_add_comment_badaddr( addr, 'invalid address', 2 )

	def alice_add_comment_badaddr3(self):
		addr = self._user_sid('alice') + ':C:123'
		return self.alice_add_comment_badaddr( addr, f'MMGen address {addr!r} not found in tracking wallet', 2 )

	def alice_add_comment_badaddr4(self):
		addr = self.proto.pubhash2addr(bytes(20),False) # regtest (testnet) zero address
		return self.alice_add_comment_badaddr( addr, f'Coin address {addr!r} not found in tracking wallet', 2 )

	def alice_remove_comment1(self):
		sid = self._user_sid('alice')
		mmid = sid + (':S:3',':L:3')[self.proto.coin=='BCH']
		return self.user_remove_comment('alice',mmid)

	def alice_chk_comment1(self):
		sid = self._user_sid('alice')
		return self._user_chk_comment('alice',sid+':C:1','Original Label - 月へ')

	def alice_chk_comment2(self):
		sid = self._user_sid('alice')
		return self._user_chk_comment('alice',sid+':C:1','Replacement Label',extra_args=['age_fmt=block'])

	def alice_edit_comment1(self):
		return self.user_edit_comment('alice','4',tw_comment_lat_cyr_gr)
	def alice_edit_comment2(self):
		return self.user_edit_comment('alice','3',tw_comment_zh)

	def alice_chk_comment3(self):
		sid = self._user_sid('alice')
		mmid = sid + (':S:3',':L:3')[self.proto.coin=='BCH']
		return self._user_chk_comment('alice',mmid,tw_comment_lat_cyr_gr,extra_args=['age_fmt=date'])

	def alice_chk_comment4(self):
		sid = self._user_sid('alice')
		mmid = sid + (':S:3',':L:3')[self.proto.coin=='BCH']
		return self._user_chk_comment('alice',mmid,'-',extra_args=['age_fmt=date_time'])

	def user_edit_comment(self,user,output,comment):
		t = self.spawn('mmgen-txcreate',['-B','--'+user,'-i'])
		t.expect(r'add \[l\]abel:.','M',regex=True)
		t.expect(r'add \[l\]abel:.','l',regex=True)
		t.expect(r"Enter unspent.*return to main menu\):.",output+'\n',regex=True)
		t.expect(r"Enter label text.*:.",comment+'\n',regex=True)
		t.expect(r'\[q\]uit menu, .*?:.','q',regex=True)
		return t

	def alice_listaddresses_scroll(self):
		t = self.spawn(
			'mmgen-tool', [
				'--alice',
				'--scroll',
				f'--outdir={self.tr.trash_dir}',
				'listaddresses',
				'interactive=1',
			]
		)
		t.expect('abel:\b','p')
		ret = t.expect([ 'abel:\b', 'to confirm: ' ])
		if ret == 1:
			t.send('YES\n')
			t.expect('abel:\b')
		t.send('l')
		t.expect(
			'main menu): ',
			'{}\n'.format(2 if self.proto.coin == 'BCH' else 1) )
		t.expect('for address.*: ','\n',regex=True)
		t.expect('unchanged')
		t.expect('abel:\b','q')
		return t

	def _alice_listaddresses_interactive(self,expect=(),expect_menu=()):
		t = self.spawn('mmgen-tool',['--alice','listaddresses','interactive=1'])
		for s in expect_menu:
			t.expect('abel:\b',s)
		for p,s in expect:
			t.expect(p,s)
		return t

	def alice_listaddresses_empty(self):
		return self._alice_listaddresses_interactive(expect_menu='uuEq')

	def alice_listaddresses_menu(self):
		return self._alice_listaddresses_interactive(expect_menu='aAMrDDDDLeq')

	def alice_listaddresses(self,args,expect):
		t = self.spawn('mmgen-tool',['--alice','listaddresses','showempty=1'] + args)
		expect_str = r'\D{}\D.*\b{}'.format(*expect)
		t.expect(expect_str,regex=True)
		return t

	def alice_listaddresses1(self):
		return self.alice_listaddresses(
			args = [],
			expect = (rtAmts[1],r'\d+') )

	def alice_listaddresses_days(self):
		return self.alice_listaddresses(
			args = ['age_fmt=days'],
			expect = (rtAmts[1],r'\d+') )

	def alice_listaddresses_date(self):
		return self.alice_listaddresses(
			args = ['age_fmt=date'],
			expect = (rtAmts[1],pat_date) )

	def alice_listaddresses_date_time(self):
		return self.alice_listaddresses(
			args = ['age_fmt=date_time'],
			expect = (rtAmts[1],pat_date_time) )

	def alice_twview(self,args,expect):
		t = self.spawn('mmgen-tool',['--alice','twview'] + args)
		expect_str = r'\D{}\D.*\b{}'.format(*expect)
		t.expect(expect_str,regex=True)
		return t

	def alice_twview1(self):
		return self.alice_twview(
			args = [],
			expect = (rtAmts[0],r'\d+') )

	def alice_twview_days(self):
		return self.alice_twview(
			args = ['age_fmt=days'],
			expect = (rtAmts[0],r'\d+') )

	def alice_twview_date(self):
		return self.alice_twview(
			args = ['age_fmt=date'],
			expect = (rtAmts[0],pat_date) )

	def alice_twview_date_time(self):
		return self.alice_twview(
			args = ['age_fmt=date_time'],
			expect = (rtAmts[0],pat_date_time) )

	def alice_txcreate_info(self,pexpect_spawn=False):
		t = self.spawn('mmgen-txcreate',['--alice','-Bi'],pexpect_spawn=pexpect_spawn)
		pats = (
			( r'\d+',    'w'),
			( r'\d+',    'D'),
			( r'\d+',    'D'),
			( r'\d+',    'D'),
			( pat_date, 'q'),
		)
		for d,s in pats:
			t.expect(
				r'\D{}\D.*\b{}\b'.format( rtAmts[0], d ),
				s,
				regex=True )
			if t.pexpect_spawn and s == 'w':
				t.expect(r'Total.*','q',regex=True,delay=1 if cfg.exact_output else t.send_delay)
				time.sleep(t.send_delay)
				t.send('e')
		return t

	def alice_txcreate_info_term(self):
		if self.skip_for_win():
			return 'skip'
		return self.alice_txcreate_info(pexpect_spawn=True)

	# send one TX to 2 addrs in Alice’s wallet - required for alice_twview_grouped()
	def bob_send_to_alice_2addr(self):
		outputs_cl = self._create_tx_outputs('alice',[('C',1,',0.02'),('C',2,',0.2')])
		outputs_cl += [self._user_sid('bob')+':C:5']
		return self.user_txdo('bob','25s',outputs_cl,'1')

	# send to a used addr in Alice’s wallet - required for alice_twview_grouped()
	def bob_send_to_alice_reuse(self):
		outputs_cl = self._create_tx_outputs('alice',[('C',1,',0.0111')])
		outputs_cl += [self._user_sid('bob')+':C:5']
		return self.user_txdo('bob','25s',outputs_cl,'1')

	def alice_twview_grouped(self):
		t = self.spawn('mmgen-tool',['--alice','twview','interactive=1'])
		prompt = 'abel:\b'
		for s,dots in (
				('o',False),
				('M',False),
				('t',True),
				('q',True),
			):
			if dots:
				t.expect('........')
			t.expect(prompt,s)
		return t

	def bob_msgcreate(self):
		sid1 = self._user_sid('bob')
		sid2 = self._get_user_subsid('bob','29L')
		return self.spawn(
			'mmgen-msg', [
				'--bob',
				f'--outdir={self.tmpdir}',
				'create',
				'16/3/2022 Earthquake strikes Fukushima coast',
				f'{sid1}:{self.dfl_mmtype}:1-4',
				f'{sid2}:C:3-7,87,98'
			])

	def bob_msgsign(self,wallets=[]):
		fn = get_file_with_ext(self.tmpdir,'rawmsg.json')
		t = self.spawn(
			'mmgen-msg', [
				'--bob',
				f'--outdir={self.tmpdir}',
				'sign',
				fn
			] + wallets )
		if not wallets:
			t.passphrase(dfl_wcls.desc,rt_pw)
		return t

	def bob_walletconv_words(self):
		t = self.spawn(
			'mmgen-walletconv', [ '--bob', f'--outdir={self.tmpdir}', '--out-fmt=words' ] )
		t.passphrase(dfl_wcls.desc,rt_pw)
		t.written_to_file('data')
		return t

	def bob_subwalletgen_bip39(self):
		t = self.spawn(
			'mmgen-subwalletgen', [ '--bob', f'--outdir={self.tmpdir}', '--out-fmt=bip39', '29L' ] )
		t.passphrase(dfl_wcls.desc,rt_pw)
		t.written_to_file('data')
		return t

	def bob_msgsign_userwallet(self):
		fn1 = get_file_with_ext(self.tmpdir,'mmwords')
		return self.bob_msgsign([fn1])

	def bob_msgsign_userwallets(self):
		fn1 = get_file_with_ext(self.tmpdir,'mmwords')
		fn2 = get_file_with_ext(self.tmpdir,'bip39')
		return self.bob_msgsign([fn2,fn1])

	def bob_msgverify(self,addr=None,ext='sigmsg.json',cmd='verify',msgfile=None):
		return self.spawn(
			'mmgen-msg', [
				'--bob',
				f'--outdir={self.tmpdir}',
				cmd,
				msgfile or get_file_with_ext(self.tmpdir,ext),
			] + ([addr] if addr else []) )

	def bob_msgverify_raw(self):
		t = self.bob_msgverify(ext='rawmsg.json')
		t.expect('No signatures')
		t.req_exit_val = 1
		return t

	def bob_msgverify_single(self):
		sid = self._user_sid('bob')
		return self.bob_msgverify(addr=f'{sid}:{self.dfl_mmtype}:1')

	def bob_msgexport(self,addr=None):
		t = self.bob_msgverify( addr=addr, cmd='export' )
		t.written_to_file('data')
		return t

	def bob_msgexport_single(self):
		sid = self._user_sid('bob')
		return self.bob_msgexport(addr=f'{sid}:{self.dfl_mmtype}:1')

	def bob_msgverify_export(self):
		return self.bob_msgverify(
			msgfile = os.path.join(self.tmpdir,'signatures.json')
		)

	def bob_msgverify_export_single(self):
		sid = self._user_sid('bob')
		mmid = f'{sid}:{self.dfl_mmtype}:1'
		args = [ '--bob', '--color=0', 'listaddress', mmid, 'wide=true' ]
		imsg(f'Running mmgen-tool {fmt_list(args,fmt="bare")}')
		t = self.spawn('mmgen-tool', args, no_msg=True)
		addr = t.expect_getend(mmid).split()[1]
		t.close()
		return self.bob_msgverify(
			addr = addr,
			msgfile = os.path.join(self.tmpdir,'signatures.json')
		)

	def bob_auto_chg_split(self):
		if not self.proto.cap('segwit'):
			return 'skip'
		sid = self._user_sid('bob')
		return self.user_txdo(
			user = 'bob',
			fee = '23s',
			outputs_cl = [sid+':C:5,0.0135', sid+':L:4'],
			outputs_list = '1' )

	def bob_auto_chg_generate(self):
		if not self.proto.cap('segwit'):
			return 'skip'
		return self.generate()

	def _usr_auto_chg(
			self,
			user,
			mmtype,
			idx,
			by_mmtype     = False,
			include_dest  = True,
			ignore_labels = False):
		if mmtype in ('S','B') and not self.proto.cap('segwit'):
			return 'skip'
		sid = self._user_sid('bob')
		t = self.spawn(
			'mmgen-txcreate',
				[f'--outdir={self.tr.trash_dir}', '--no-blank', f'--{user}'] +
				(['--autochg-ignore-labels'] if ignore_labels else []) +
				[mmtype if by_mmtype else f'{sid}:{mmtype}'] +
				([self.burn_addr+',0.01'] if include_dest else [])
			)
		return self.txcreate_ui_common(t,
			menu            = [],
			inputs          = '1',
			interactive_fee = '20s',
			auto_chg_addr   = f'{sid}:{mmtype}:{idx}')

	def bob_auto_chg1(self):
		return self._usr_auto_chg( 'bob', 'C', '3' )

	def bob_auto_chg2(self):
		return self._usr_auto_chg( 'bob', 'B', '2' )

	def bob_auto_chg3(self):
		return self._usr_auto_chg( 'bob', 'S', '1' )

	def bob_auto_chg4(self):
		return self._usr_auto_chg( 'bob', 'C', '3', include_dest=False )

	def bob_auto_chg_addrtype1(self):
		return self._usr_auto_chg( 'bob', 'C', '3', True )

	def bob_auto_chg_addrtype2(self):
		return self._usr_auto_chg( 'bob', 'B', '2', True )

	def bob_auto_chg_addrtype3(self):
		return self._usr_auto_chg( 'bob', 'S', '1', True )

	def bob_auto_chg_addrtype4(self):
		return self._usr_auto_chg( 'bob', 'C', '3', True, include_dest=False )

	def _bob_add_comment_uua(self,addrspec,comment):
		sid = self._user_sid('bob')
		return self.user_add_comment('bob',sid+addrspec,comment)

	def bob_add_comment_uua1(self):
		return self._bob_add_comment_uua(':C:3','comment for unused address')

	def bob_auto_chg5(self):
		return self._usr_auto_chg( 'bob', 'C', '4' )

	def bob_auto_chg_addrtype5(self):
		return self._usr_auto_chg( 'bob', 'C', '4', True )

	def bob_auto_chg6(self):
		return self._usr_auto_chg( 'bob', 'C', '3', ignore_labels=True )

	def bob_auto_chg_addrtype6(self):
		return self._usr_auto_chg( 'bob', 'C', '3', True, ignore_labels=True )

	def _bob_remove_comment_uua(self,addrspec):
		sid = self._user_sid('bob')
		return self.user_remove_comment('bob',sid+addrspec)

	def bob_remove_comment_uua1(self):
		return self._bob_remove_comment_uua(':C:3')

	def _usr_auto_chg_bad(self,user,al_id,expect):
		t = self.spawn(
			'mmgen-txcreate',
			['-d',self.tr.trash_dir,'-B',f'--{user}', self.burn_addr+',0.01', al_id] )
		t.req_exit_val = 2
		t.expect(expect)
		return t

	def bob_auto_chg_bad1(self):
		return self._usr_auto_chg_bad(
			'bob',
			'FFFFFFFF:C',
			'contains no addresses' )

	def bob_auto_chg_bad2(self):
		return self._usr_auto_chg_bad(
			'bob',
			'00000000:C',
			'contains no addresses' )

	def bob_auto_chg_bad3(self):
		return self._usr_auto_chg_bad(
			'bob',
			self._user_sid('bob') + ':L',
			'contains no unused addresses from address list' )

	def bob_auto_chg_bad4(self):
		return self._usr_auto_chg_bad(
			'bob',
			'L',
			'contains no unused addresses of address type' )

	def carol_twimport2(self):
		u,b = (4,3) if self.proto.cap('segwit') else (3,2)
		return self.carol_twimport(
			rpc_backend = None,
			add_parms   = ['ignore_checksum=true'],
			expect_str2 =  f'Found {u} unspent outputs in {b} blocks' )

	def carol_rescan_blockchain(self):
		return self._usr_rescan_blockchain('carol',[])

	def carol_auto_chg1(self):
		return self._usr_auto_chg( 'carol', 'C', '3' )

	def carol_auto_chg2(self):
		return self._usr_auto_chg( 'carol', 'B', '2' )

	def carol_auto_chg3(self):
		return self._usr_auto_chg( 'carol', 'S', '1' )

	def carol_auto_chg_addrtype1(self):
		return self._usr_auto_chg( 'carol', 'C', '3', True )

	def carol_auto_chg_addrtype2(self):
		return self._usr_auto_chg( 'carol', 'B', '2', True )

	def carol_auto_chg_addrtype3(self):
		return self._usr_auto_chg( 'carol', 'S', '1', True )

	def carol_auto_chg_bad1(self):
		return self._usr_auto_chg_bad(
			'carol',
			self._user_sid('bob') + ':L',
			'contains no unused addresses from address list' )

	def carol_auto_chg_bad2(self):
		return self._usr_auto_chg_bad(
			'carol',
			'L',
			'contains no unused addresses of address type' )

	def stop(self):
		if cfg.no_daemon_stop:
			self.spawn('',msg_only=True)
			msg_r('(leaving daemon running by user request)')
			return 'ok'
		else:
			return self.spawn('mmgen-regtest',['stop'])
