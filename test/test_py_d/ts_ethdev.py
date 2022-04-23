#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
ts_ethdev.py: Ethdev tests for the test.py test suite
"""

import sys,os,re,shutil
from decimal import Decimal
from collections import namedtuple
from subprocess import run,PIPE,DEVNULL

from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import die
from mmgen.amt import ETHAmt
from mmgen.protocol import CoinProtocol
from ..include.common import *
from .common import *

del_addrs = ('4','1')
dfl_sid = '98831F3A'

# The OpenEthereum dev address with lots of coins.  Create with "ethkey -b info ''":
dfl_devaddr = '00a329c0648769a73afac7f9381e08fb43dbea72'
dfl_devkey = '4d5db4107d237df6a3d58ee5f70ae63d73d7658d4026f2eefd2f204c81682cb7'

prealloc_amt = ETHAmt('1_000_000_000')

burn_addr  = 'deadbeef'*5
burn_addr2 = 'beadcafe'*5

amt1 = '999999.12345689012345678'
amt2 = '888.111122223333444455'

parity_devkey_fn = 'parity.devkey'
erigon_devkey_fn = 'erigon.devkey'

tested_solc_ver = '0.8.7'

def check_solc_ver():
	cmd = 'python3 scripts/create-token.py --check-solc-version'
	try:
		cp = run(cmd.split(),check=False,stdout=PIPE)
	except Exception as e:
		die(4,f'Unable to execute {cmd!r}: {e}')
	res = cp.stdout.decode().strip()
	if cp.returncode == 0:
		omsg(
			orange(f'Found supported solc version {res}') if res == tested_solc_ver else
			yellow(f'WARNING: solc version ({res}) does not match tested version ({tested_solc_ver})')
		)
		return True
	else:
		omsg(yellow(res + '\nUsing precompiled contract data'))
		return False

vbal1 = '1.2288409'
vbal9 = '1.22626295'
vbal2 = '99.997088755'
vbal3 = '1.23142525'
vbal4 = '127.0287909'
vbal5 = '1000126.14828654512345678'

bals = {
	'1': [  ('98831F3A:E:1','123.456')],
	'2': [  ('98831F3A:E:1','123.456'),('98831F3A:E:11','1.234')],
	'3': [  ('98831F3A:E:1','123.456'),('98831F3A:E:11','1.234'),('98831F3A:E:21','2.345')],
	'4': [  ('98831F3A:E:1','100'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11','1.234'),
			('98831F3A:E:21','2.345')],
	'5': [  ('98831F3A:E:1','100'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11','1.234'),
			('98831F3A:E:21','2.345'),
			(burn_addr + r'\s+Non-MMGen',amt1)],
	'8': [  ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11',vbal1,'a1'),
			('98831F3A:E:12','99.99895'),
			('98831F3A:E:21','2.345'),
			(burn_addr + r'\s+Non-MMGen',amt1)],
	'9': [  ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11',vbal1,'a1'),
			('98831F3A:E:12',vbal2),
			('98831F3A:E:21','2.345'),
			(burn_addr + r'\s+Non-MMGen',amt1)],
	'10': [ ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.0218'),
			('98831F3A:E:3','0.4321'),
			('98831F3A:E:11',vbal1,'a1'),
			('98831F3A:E:12',vbal2),
			('98831F3A:E:21','2.345'),
			(burn_addr + r'\s+Non-MMGen',amt1)]
}

token_bals = {
	'1': [  ('98831F3A:E:11','1000','1.234')],
	'2': [  ('98831F3A:E:11','998.76544',vbal3,'a1'),
			('98831F3A:E:12','1.23456','0')],
	'3': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','1.23456','0')],
	'4': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','1.23456','0'),
			(burn_addr + r'\s+Non-MMGen',amt2,amt1)],
	'5': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','1.23456','99.99895'),
			(burn_addr + r'\s+Non-MMGen',amt2,amt1)],
	'6': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','0',vbal2),
			('98831F3A:E:13','1.23456','0'),
			(burn_addr + r'\s+Non-MMGen',amt2,amt1)],
	'7': [  ('98831F3A:E:11','67.444317776666555545',vbal9,'a2'),
			('98831F3A:E:12','43.21',vbal2),
			('98831F3A:E:13','1.23456','0'),
			(burn_addr + r'\s+Non-MMGen',amt2,amt1)]
}
token_bals_getbalance = {
	'1': (vbal4,'999999.12345689012345678'),
	'2': ('111.888877776666555545','888.111122223333444455')
}

from .ts_base import *
from .ts_shared import *

coin = g.coin

class TestSuiteEthdev(TestSuiteBase,TestSuiteShared):
	'Ethereum transacting, token deployment and tracking wallet operations'
	networks = ('eth','etc')
	passthru_opts = ('coin','daemon_id','http_timeout')
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [22]
	color = True
	cmd_group = (
		('setup',                          f'dev mode tests for coin {coin} (start daemon)'),
		('daemon_version',                  'mmgen-tool daemon_version'),
		('wallet_upgrade1',                 'upgrading the tracking wallet (v1 -> v2)'),
		('wallet_upgrade2',                 'upgrading the tracking wallet (v2 -> v3)'),
		('addrgen',                         'generating addresses'),
		('addrimport',                      'importing addresses'),
		('addrimport_dev_addr',             "importing dev faucet address 'Ox00a329c..'"),
		('addrimport_erigon_dev_addr',      'importing Erigon dev faucet address'),

		('fund_dev_address',                'funding the default (Parity dev) address'),
		('txcreate1',                       'creating a transaction (spend from dev address to address :1)'),
		('txview1_raw',                     'viewing the raw transaction'),
		('txsign1',                         'signing the transaction'),
		('txview1_sig',                     'viewing the signed transaction'),
		('tx_status0_bad',                  'getting the transaction status'),
		('txsign1_ni',                      'signing the transaction (non-interactive)'),
		('txsend1',                         'sending the transaction'),
		('bal1',                           f'the {coin} balance'),

		('txcreate2',                       'creating a transaction (spend from dev address to address :11)'),
		('txsign2',                         'signing the transaction'),
		('txsend2',                         'sending the transaction'),
		('bal2',                           f'the {coin} balance'),

		('txcreate3',                       'creating a transaction (spend from dev address to address :21)'),
		('txsign3',                         'signing the transaction'),
		('txsend3',                         'sending the transaction'),
		('bal3',                           f'the {coin} balance'),

		('tx_status1',                      'getting the transaction status'),

		('txcreate4',                       'creating a transaction (spend from MMGen address, low TX fee)'),
		('txbump',                          'bumping the transaction fee'),

		('txsign4',                         'signing the transaction'),
		('txsend4',                         'sending the transaction'),
		('tx_status1a',                     'getting the transaction status'),
		('bal4',                           f'the {coin} balance'),

		('txcreate5',                       'creating a transaction (fund burn address)'),
		('txsign5',                         'signing the transaction'),
		('txsend5',                         'sending the transaction'),

		('addrimport_burn_addr',            'importing burn address'),
		('bal5',                           f'the {coin} balance'),

		('add_label1',                      'adding a UTF-8 label (zh)'),
		('chk_label1',                      'the label'),
		('add_label2',                      'adding a UTF-8 label (lat+cyr+gr)'),
		('chk_label2',                      'the label'),
		('remove_label',                    'removing the label'),

		('token_compile1',                  'compiling ERC20 token #1'),

		('token_deploy1a',                  'deploying ERC20 token #1 (SafeMath)'),
		('token_deploy1b',                  'deploying ERC20 token #1 (Owned)'),
		('token_deploy1c',                  'deploying ERC20 token #1 (Token)'),

		('tx_status2',                      'getting the transaction status'),
		('bal6',                           f'the {coin} balance'),

		('token_compile2',                  'compiling ERC20 token #2'),

		('token_deploy2a',                  'deploying ERC20 token #2 (SafeMath)'),
		('token_deploy2b',                  'deploying ERC20 token #2 (Owned)'),
		('token_deploy2c',                  'deploying ERC20 token #2 (Token)'),

		('contract_deploy',                 'deploying contract (create,sign,send)'),

		('token_fund_users',                'transferring token funds from dev to user'),
		('token_user_bals',                 'show balances after transfer'),
		('token_addrgen',                   'generating token addresses'),
		('token_addrimport_badaddr1',       'importing token addresses (no token address)'),
		('token_addrimport_badaddr2',       'importing token addresses (bad token address)'),
		('token_addrimport_addr1',          'importing token addresses using token address (MM1)'),
		('token_addrimport_addr2',          'importing token addresses using token address (MM2)'),
		('token_addrimport_batch',          'importing token addresses (dummy batch mode) (MM1)'),
		('token_addrimport_sym',            'importing token addresses using token symbol (MM2)'),

		('bal7',                           f'the {coin} balance'),
		('token_bal1',                     f'the {coin} balance and token balance'),

		('token_txcreate1',                 'creating a token transaction'),
		('token_txview1_raw',               'viewing the raw transaction'),
		('token_txsign1',                   'signing the transaction'),
		('token_txsend1',                   'sending the transaction'),
		('token_txview1_sig',               'viewing the signed transaction'),
		('tx_status3',                      'getting the transaction status'),
		('token_bal2',                     f'the {coin} balance and token balance'),

		('token_txcreate2',                 'creating a token transaction (to burn address)'),
		('token_txbump',                    'bumping the transaction fee'),

		('token_txsign2',                   'signing the transaction'),
		('token_txsend2',                   'sending the transaction'),
		('token_bal3',                     f'the {coin} balance and token balance'),

		('del_dev_addr',                    'deleting the dev address'),

		('bal1_getbalance',                f'the {coin} balance (getbalance)'),

		('addrimport_token_burn_addr',      'importing the token burn address'),

		('token_bal4',                     f'the {coin} balance and token balance'),
		('token_bal_getbalance',            'the token balance (getbalance)'),

		('txcreate_noamt',                  'creating a transaction (full amount send)'),
		('txsign_noamt',                    'signing the transaction'),
		('txsend_noamt',                    'sending the transaction'),

		('bal8',                           f'the {coin} balance'),
		('token_bal5',                      'the token balance'),

		('token_txcreate_noamt',            'creating a token transaction (full amount send)'),
		('token_txsign_noamt',              'signing the transaction'),
		('token_txsend_noamt',              'sending the transaction'),

		('bal9',                           f'the {coin} balance'),
		('token_bal6',                      'the token balance'),

		('listaddresses1',                  'listaddresses'),
		('listaddresses2',                  'listaddresses minconf=999999999 (ignored)'),
		('listaddresses3',                  'listaddresses sort=age (ignored)'),
		('listaddresses4',                  'listaddresses showempty=1 sort=age (ignored)'),

		('token_listaddresses1',            'listaddresses --token=mm1'),
		('token_listaddresses2',            'listaddresses --token=mm1 showempty=1'),

		('twview_cached_balances',          'twview (cached balances)'),
		('token_twview_cached_balances',    'token twview (cached balances)'),
		('txcreate_cached_balances',        'txcreate (cached balances)'),
		('token_txcreate_cached_balances',  'token txcreate (cached balances)'),

		('txdo_cached_balances',            'txdo (cached balances)'),
		('txcreate_refresh_balances',       'refreshing balances'),
		('bal10',                          f'the {coin} balance'),

		('token_txdo_cached_balances',      'token txdo (cached balances)'),
		('token_txcreate_refresh_balances', 'refreshing token balances'),
		('token_bal7',                      'the token balance'),

		('twview1',                         'twview'),
		('twview2',                         'twview wide=1'),
		('twview3',                         'twview wide=1 sort=age (ignored)'),
		('twview4',                         'twview wide=1 minconf=999999999 (ignored)'),
		('twview5',                         'twview wide=1 minconf=0 (ignored)'),

		('token_twview1',                   'twview --token=mm1'),
		('token_twview2',                   'twview --token=mm1 wide=1'),
		('token_twview3',                   'twview --token=mm1 wide=1 sort=age (ignored)'),

		('edit_label1',        f'adding label to addr #{del_addrs[0]} in {coin} tracking wallet (zh)'),
		('edit_label2',        f'adding label to addr #{del_addrs[1]} in {coin} tracking wallet (lat+cyr+gr)'),
		('edit_label3',        f'removing label from addr #{del_addrs[0]} in {coin} tracking wallet'),

		('token_edit_label1',  f'adding label to addr #{del_addrs[0]} in {coin} token tracking wallet'),

		('remove_addr1',       f'removing addr #{del_addrs[0]} from {coin} tracking wallet'),
		('remove_addr2',       f'removing addr #{del_addrs[1]} from {coin} tracking wallet'),
		('token_remove_addr1', f'removing addr #{del_addrs[0]} from {coin} token tracking wallet'),
		('token_remove_addr2', f'removing addr #{del_addrs[1]} from {coin} token tracking wallet'),

		('stop',               'stopping daemon'),
	)

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return

		self.erase_input = Ctrl_U if opt.pexpect_spawn else ''

		from mmgen.protocol import init_proto
		self.proto = init_proto(g.coin,network='regtest',need_amt=True)
		from mmgen.daemon import CoinDaemon
		self.rpc_port = CoinDaemon(proto=self.proto,test_suite=True).rpc_port
		self.using_solc = check_solc_ver()

		write_to_file(
			joinpath(self.tmpdir,parity_devkey_fn),
			dfl_devkey+'\n' )

		if g.daemon_id == 'erigon':
			from hashlib import sha256
			from mmgen.tool.api import tool_api
			devkey = sha256(b'erigon devnet key').hexdigest()
			t = tool_api()
			t.init_coin(g.coin,'regtest')
			self.erigon_devaddr = t.wif2addr(devkey)
			write_to_file(
				joinpath(self.tmpdir,erigon_devkey_fn),
				devkey+'\n' )

		os.environ['MMGEN_BOGUS_SEND'] = ''

	def __del__(self):
		os.environ['MMGEN_BOGUS_SEND'] = '1'

	@property
	def eth_args(self):
		return [
			f'--outdir={self.tmpdir}',
			f'--coin={self.proto.coin}',
			f'--rpc-port={self.rpc_port}',
			'--quiet'
		]

	async def setup(self):
		self.spawn('',msg_only=True)

		if not self.using_solc:
			srcdir = os.path.join(self.tr.repo_root,'test','ref','ethereum','bin')
			from shutil import copytree
			for d in ('mm1','mm2'):
				copytree(os.path.join(srcdir,d),os.path.join(self.tmpdir,d))

		if not opt.no_daemon_autostart:
			if g.daemon_id == 'geth':
				self.geth_setup()
				set_vt100()
			if not start_test_daemons(
					self.proto.coin+'_rt',
					remove_datadir = not g.daemon_id in ('geth','erigon') ):
				return False
			from mmgen.rpc import rpc_init
			rpc = await rpc_init(self.proto)
			imsg(f'Daemon: {rpc.daemon.coind_name} v{rpc.daemon_version_str}')

		return 'ok'

	def geth_setup(self):

		def make_key(keystore):
			pwfile = joinpath(self.tmpdir,'account_passwd')
			write_to_file(pwfile,'')
			run(['rm','-rf',keystore])
			cmd = f'geth account new --password={pwfile} --lightkdf --keystore {keystore}'
			cp = run(cmd.split(),stdout=PIPE,stderr=PIPE)
			if cp.returncode:
				die(1,cp.stderr.decode())
			keyfile = os.path.join(keystore,os.listdir(keystore)[0])
			with open(keyfile) as fp:
				return json.loads(fp.read())['address']

		def make_genesis(signer_addr,prealloc_addr):
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
					'clique': {
						'period': 0,
						'epoch': 30000
					}
				},
				'difficulty': '1',
				'gasLimit': '8000000',
				'extradata': '0x' + 64*'0' + signer_addr + 130*'0',
				'alloc': {
					prealloc_addr: { 'balance': str(prealloc_amt.toWei()) }
				}
			}

		def init_genesis(fn):
			cmd = f'geth init --datadir {d.datadir} {fn}'
			cp = run(cmd.split(),stdout=PIPE,stderr=PIPE)
			if cp.returncode:
				die(1,cp.stderr.decode())

		from mmgen.daemon import CoinDaemon
		import json

		d = CoinDaemon(proto=self.proto,test_suite=True)
		d.stop(quiet=True)
		d.remove_datadir()

		imsg(cyan('Initializing Geth:'))

		keystore = os.path.relpath(os.path.join(d.datadir,'keystore'))
		imsg(f'  Keystore:           {keystore}')

		signer_addr = make_key(keystore)
		imsg(f'  Signer address:     {signer_addr}')

		imsg(f'  Faucet:             {dfl_devaddr} ({prealloc_amt} ETH)')

		genesis_data = make_genesis(signer_addr,dfl_devaddr)

		genesis_fn = joinpath(self.tmpdir,'genesis.json')
		imsg(f'  Genesis block data: {genesis_fn}')

		write_to_file( genesis_fn, json.dumps(genesis_data,indent='  ')+'\n' )

		init_genesis(genesis_fn)

	def wallet_upgrade(self,src_file):
		if self.proto.coin == 'ETC':
			msg(f'skipping test {self.test_name!r} for ETC')
			return 'skip'
		src_dir = joinpath(ref_dir,'ethereum')
		dest_dir = joinpath(self.tr.data_dir,'altcoins',self.proto.coin.lower())
		w_from = joinpath(src_dir,src_file)
		w_to = joinpath(dest_dir,'tracking-wallet.json')
		os.makedirs(dest_dir,mode=0o750,exist_ok=True)
		dest = shutil.copy2(w_from,w_to)
		assert dest == w_to, dest
		t = self.spawn('mmgen-tool', self.eth_args + ['twview'])
		t.read()
		os.unlink(w_to)
		return t

	def daemon_version(self):
		t = self.spawn('mmgen-tool', self.eth_args + ['daemon_version'])
		t.expect('version')
		return t

	def wallet_upgrade1(self): return self.wallet_upgrade('tracking-wallet-v1.json')
	def wallet_upgrade2(self): return self.wallet_upgrade('tracking-wallet-v2.json')

	def addrgen(self,addrs='1-3,11-13,21-23'):
		t = self.spawn('mmgen-addrgen', self.eth_args + [dfl_words_file,addrs])
		t.written_to_file('Addresses')
		return t

	def addrimport(self,ext='21-23]{}.regtest.addrs',expect='9/9',add_args=[],bad_input=False):
		ext = ext.format('-α' if g.debug_utf8 else '')
		fn = self.get_file_with_ext(ext,no_dot=True,delete=False)
		t = self.spawn('mmgen-addrimport', self.eth_args[1:-1] + add_args + [fn])
		if bad_input:
			return t
		t.expect('Importing')
		t.expect(expect)
		return t

	def addrimport_one_addr(self,addr=None,extra_args=[]):
		t = self.spawn('mmgen-addrimport', self.eth_args[1:] + extra_args + ['--address='+addr])
		t.expect('OK')
		return t

	def addrimport_dev_addr(self):
		return self.addrimport_one_addr(addr=dfl_devaddr)

	def addrimport_erigon_dev_addr(self):
		if not g.daemon_id == 'erigon':
			return 'skip'
		return self.addrimport_one_addr(addr=self.erigon_devaddr)

	def addrimport_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr)

	def txcreate(self,
			args            = [],
			menu            = [],
			acct            = '1',
			caller          = 'txcreate',
			interactive_fee = '50G',
			eth_fee_res     = None,
			fee_res_data    = ('0.00105','50'),
			fee_desc        = 'gas price',
			no_read         = False,
			tweaks          = [] ):
		fee_res = r'\D{}\D.*{c} .*\D{}\D.*gas price in Gwei'.format( *fee_res_data, c=self.proto.coin )
		t = self.spawn('mmgen-'+caller, self.eth_args + ['-B'] + args)
		t.expect(r'add \[l\]abel, .*?:.','p', regex=True)
		t.written_to_file('Account balances listing')
		t = self.txcreate_ui_common(t,
			menu              = menu,
			caller            = caller,
			input_sels_prompt = 'to spend from',
			inputs            = acct,
			file_desc         = 'transaction',
			bad_input_sels    = True,
			interactive_fee   = interactive_fee,
			fee_res           = fee_res,
			fee_desc          = fee_desc,
			eth_fee_res       = eth_fee_res,
			add_comment       = tx_label_jp,
			tweaks            = tweaks )
		if not no_read:
			t.read()
		return t

	def txsign(self,ni=False,ext='{}.regtest.rawtx',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		keyfile = joinpath(self.tmpdir,parity_devkey_fn)
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn( 'mmgen-txsign',
						[f'--outdir={self.tmpdir}']
						+ [f'--coin={self.proto.coin}']
						+ ['--quiet']
						+ ['--rpc-host=bad_host'] # ETH signing must work without RPC
						+ add_args
						+ ([],['--yes'])[ni]
						+ ['-k', keyfile, txfile, dfl_words_file] )
		return self.txsign_ui_common(t,ni=ni,has_label=True)

	def txsend(self,ni=False,ext='{}.regtest.sigtx',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txsend', self.eth_args + add_args + [txfile])
		txid = self.txsend_ui_common(t,
			quiet      = not g.debug,
			bogus_send = False,
			has_label  = True )
		return t

	def txview(self,ext_fs):
		ext = ext_fs.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		return self.spawn( 'mmgen-tool',['--verbose','txview',txfile] )

	def fund_dev_address(self):
		"""
		For Erigon, fund the default (Parity) dev address from the Erigon dev address
		For the others, send a junk TX to keep block counts equal for all daemons
		"""
		dt = namedtuple('data',['devkey_fn','dest','amt'])
		if g.daemon_id == 'erigon':
			d = dt( erigon_devkey_fn, dfl_devaddr, prealloc_amt )
		else:
			d = dt( parity_devkey_fn, burn_addr2, '1' )
		t = self.txcreate(
			args    = [
				f'--keys-from-file={joinpath(self.tmpdir,d.devkey_fn)}',
				f'{d.dest},{d.amt}',
			],
			menu    = ['a','r'],
			caller  = 'txdo',
			acct    = '1',
			no_read = True )
		self._do_confirm_send(t,quiet=not g.debug,sure=False)
		t.read()
		self.get_file_with_ext('sigtx',delete_all=True)
		return t

	def txcreate1(self):
		if g.daemon_id == 'erigon':
			# delete Erigon devaddr so that wallet is same as for other daemons
			menu = ['a','r','D','1\n','y\n'] # sort by reverse amount
		else:
			# include one invalid keypress 'X' -- see EthereumTwUnspentOutputs.key_mappings
			menu = ['a','d','r','M','X','e','m','m']
		args = ['98831F3A:E:1,123.456']
		return self.txcreate(args=args,menu=menu,acct='1',tweaks=['confirm_non_mmgen'])
	def txview1_raw(self):
		return self.txview(ext_fs='{}.regtest.rawtx')
	def txsign1(self):    return self.txsign(add_args=['--use-internal-keccak-module'])
	def tx_status0_bad(self):
		return self.tx_status(ext='{}.regtest.sigtx',expect_str='neither in mempool nor blockchain',exit_val=1)
	def txsign1_ni(self): return self.txsign(ni=True)
	def txsend1(self):    return self.txsend()
	def txview1_sig(self): # do after send so that TxID is displayed
		return self.txview(ext_fs='{}.regtest.sigtx')
	def bal1(self):       return self.bal(n='1')

	def txcreate2(self):
		args = ['98831F3A:E:11,1.234']
		return self.txcreate(args=args,acct='10',tweaks=['confirm_non_mmgen'])
	def txsign2(self): return self.txsign(ni=True,ext='1.234,50000]{}.regtest.rawtx')
	def txsend2(self): return self.txsend(ext='1.234,50000]{}.regtest.sigtx')
	def bal2(self):    return self.bal(n='2')

	def txcreate3(self):
		args = ['98831F3A:E:21,2.345']
		return self.txcreate(args=args,acct='10',tweaks=['confirm_non_mmgen'])
	def txsign3(self): return self.txsign(ni=True,ext='2.345,50000]{}.regtest.rawtx')
	def txsend3(self): return self.txsend(ext='2.345,50000]{}.regtest.sigtx')
	def bal3(self):    return self.bal(n='3')

	def tx_status(self,ext,expect_str,expect_str2='',add_args=[],exit_val=0):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txsend', self.eth_args + add_args + ['--status',txfile])
		t.expect(expect_str)
		if expect_str2:
			t.expect(expect_str2)
		t.req_exit_val = exit_val
		return t

	def tx_status1(self):
		return self.tx_status(ext='2.345,50000]{}.regtest.sigtx',expect_str='has 1 confirmation')

	def tx_status1a(self):
		return self.tx_status(ext='2.345,50000]{}.regtest.sigtx',expect_str='has 2 confirmations')

	def txcreate4(self):
		return self.txcreate(
			args             = ['98831F3A:E:2,23.45495'],
			acct             = '1',
			interactive_fee  = '40G',
			fee_res_data     = ('0.00084','40'),
			eth_fee_res      = True )

	def txbump(self,ext=',40000]{}.regtest.rawtx',fee='50G',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txbump', self.eth_args + add_args + ['--yes',txfile])
		t.expect('or gas price: ',fee+'\n')
		return t

	def txsign4(self): return self.txsign(ni=True,ext='.45495,50000]{}.regtest.rawtx')
	def txsend4(self): return self.txsend(ext='.45495,50000]{}.regtest.sigtx')
	def bal4(self):    return self.bal(n='4')

	def txcreate5(self):
		args = [burn_addr + ','+amt1]
		return self.txcreate(args=args,acct='10',tweaks=['confirm_non_mmgen'])
	def txsign5(self): return self.txsign(ni=True,ext=amt1+',50000]{}.regtest.rawtx')
	def txsend5(self): return self.txsend(ext=amt1+',50000]{}.regtest.sigtx')
	def bal5(self):    return self.bal(n='5')

	#bal_corr = Decimal('0.0000032') # gas use for token sends varies between ETH and ETC!
	bal_corr = Decimal('0.0000000') # update: OpenEthereum team seems to have corrected this

	def bal(self,n):
		t = self.spawn('mmgen-tool', self.eth_args + ['twview','wide=1'])
		text = strip_ansi_escapes(t.read())
		for b in bals[n]:
			addr,amt,adj = b if len(b) == 3 else b + (False,)
			if adj and self.proto.coin == 'ETC':
				amt = str(Decimal(amt) + Decimal(adj[1]) * self.bal_corr)
			pat = r'\D{}\D.*\D{}\D'.format( addr, amt.replace('.',r'\.') )
			assert re.search(pat,text), pat
		ss = f'Total {self.proto.coin}:'
		assert re.search(ss,text),ss
		return t

	def token_bal(self,n=None):
		t = self.spawn('mmgen-tool', self.eth_args + ['--token=mm1','twview','wide=1'])
		text = strip_ansi_escapes(t.read())
		for b in token_bals[n]:
			addr,_amt1,_amt2,adj = b if len(b) == 4 else b + (False,)
			if adj and self.proto.coin == 'ETC':
				_amt2 = str(Decimal(_amt2) + Decimal(adj[1]) * self.bal_corr)
			pat = fr'{addr}\b.*\D{_amt1}\D.*\b{_amt2}\D'
			assert re.search(pat,text), pat
		ss = 'Total MM1:'
		assert re.search(ss,text),ss
		return t

	def bal_getbalance(self,idx,etc_adj=False,extra_args=[]):
		bal1 = token_bals_getbalance[idx][0]
		bal2 = token_bals_getbalance[idx][1]
		bal1 = Decimal(bal1)
		if etc_adj and self.proto.coin == 'ETC':
			bal1 += self.bal_corr
		t = self.spawn('mmgen-tool', self.eth_args + extra_args + ['getbalance'])
		t.expect(r'\n[0-9A-F]{8}: .*\D'+str(bal1),regex=True)
		t.expect(r'\nNon-MMGen: .*\D'+bal2,regex=True)
		total = strip_ansi_escapes(t.expect_getend(r'\nTOTAL:\s+',regex=True)).split()[0]
		assert Decimal(bal1) + Decimal(bal2) == Decimal(total)
		return t

	def add_label(self,lbl,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['add_label',addr,lbl])
		t.expect('Added label.*in tracking wallet',regex=True)
		return t

	def chk_label(self,lbl_pat,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['listaddresses','all_labels=1'])
		t.expect(fr'{addr}\b.*\S{{30}}\b.*{lbl_pat}\b',regex=True)
		return t

	def add_label1(self): return self.add_label(lbl=tw_label_zh)
	def chk_label1(self): return self.chk_label(lbl_pat=tw_label_zh)
	def add_label2(self): return self.add_label(lbl=tw_label_lat_cyr_gr)
	def chk_label2(self): return self.chk_label(lbl_pat=tw_label_lat_cyr_gr)

	def remove_label(self,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		return t

	def token_compile(self,token_data={}):
		odir = joinpath(self.tmpdir,token_data['symbol'].lower())
		if not self.using_solc:
			imsg(f'Using precompiled contract data in {odir}')
			return 'skip' if os.path.exists(odir) else False
		self.spawn('',msg_only=True)
		cmd_args = [f'--{k}={v}' for k,v in list(token_data.items())]
		imsg("Compiling solidity token contract '{}' with 'solc'".format( token_data['symbol'] ))
		try: os.mkdir(odir)
		except: pass
		cmd = [
			'python3',
			'scripts/exec_wrapper.py',
			'scripts/create-token.py',
			'--coin=' + self.proto.coin,
			'--outdir=' + odir
		] + cmd_args + [self.proto.checksummed_addr(dfl_devaddr)]
		imsg('Executing: {}'.format( ' '.join(cmd) ))
		cp = run(cmd,stdout=DEVNULL,stderr=PIPE)
		if cp.returncode != 0:
			rmsg('solc failed with the following output:')
			die(2,cp.stderr.decode())
		imsg('ERC20 token {!r} compiled'.format( token_data['symbol'] ))
		return 'ok'

	def token_compile1(self):
		token_data = { 'name':'MMGen Token 1', 'symbol':'MM1', 'supply':10**26, 'decimals':18 }
		return self.token_compile(token_data)

	def token_compile2(self):
		token_data = { 'name':'MMGen Token 2', 'symbol':'MM2', 'supply':10**18, 'decimals':10 }
		return self.token_compile(token_data)

	async def get_tx_receipt(self,txid):
		from mmgen.tx import NewTX
		tx = await NewTX(proto=self.proto)
		from mmgen.rpc import rpc_init
		tx.rpc = await rpc_init(self.proto)
		res = await tx.get_receipt(txid)
		imsg(f'Gas sent:  {res.gas_sent.hl():<9} {(res.gas_sent*res.gas_price).hl2(encl="()")}')
		imsg(f'Gas used:  {res.gas_used.hl():<9} {(res.gas_used*res.gas_price).hl2(encl="()")}')
		imsg(f'Gas price: {res.gas_price.hl2()}')
		if res.gas_used == res.gas_sent:
			omsg(yellow(f'Warning: all gas was used!'))
		return res

	async def token_deploy(self,num,key,gas,mmgen_cmd='txdo',tx_fee='8G'):
		keyfile = joinpath(self.tmpdir,parity_devkey_fn)
		fn = joinpath(self.tmpdir,'mm'+str(num),key+'.bin')
		args = [
			'-B',
			f'--tx-fee={tx_fee}',
			f'--tx-gas={gas}',
			f'--contract-data={fn}',
			f'--inputs={dfl_devaddr}',
			'--yes',
		]
		if mmgen_cmd == 'txdo':
			args += ['-k',keyfile]
		t = self.spawn( 'mmgen-'+mmgen_cmd, self.eth_args + args)
		if mmgen_cmd == 'txcreate':
			t.written_to_file('transaction')
			ext = '[0,8000]{}.regtest.rawtx'.format('-α' if g.debug_utf8 else '')
			txfile = self.get_file_with_ext(ext,no_dot=True)
			t = self.spawn('mmgen-txsign', self.eth_args + ['--yes','-k',keyfile,txfile],no_msg=True)
			self.txsign_ui_common(t,ni=True)
			txfile = txfile.replace('.rawtx','.sigtx')
			t = self.spawn('mmgen-txsend', self.eth_args + [txfile],no_msg=True)

		txid = self.txsend_ui_common(t,
			caller = mmgen_cmd,
			quiet  = mmgen_cmd == 'txdo' or not g.debug,
			bogus_send = False )
		addr = strip_ansi_escapes(t.expect_getend('Contract address: '))
		if (await self.get_tx_receipt(txid)).status == 0:
			die(2,f'Contract {num}:{key} failed to execute. Aborting')
		if key == 'Token':
			self.write_to_tmpfile( f'token_addr{num}', addr+'\n' )
			imsg(f'\nToken MM{num} deployed!')
		return t

	async def token_deploy1a(self): return await self.token_deploy(num=1,key='SafeMath',gas=500_000)
	async def token_deploy1b(self): return await self.token_deploy(num=1,key='Owned',   gas=1_000_000)
	async def token_deploy1c(self): return await self.token_deploy(num=1,key='Token',   gas=4_000_000,tx_fee='7G')

	def tx_status2(self):
		return self.tx_status(ext=self.proto.coin+'[0,7000]{}.regtest.sigtx',expect_str='successfully executed')

	def bal6(self): return self.bal5()

	async def token_deploy2a(self): return await self.token_deploy(num=2,key='SafeMath',gas=500_000)
	async def token_deploy2b(self): return await self.token_deploy(num=2,key='Owned',   gas=1_000_000)
	async def token_deploy2c(self): return await self.token_deploy(num=2,key='Token',   gas=4_000_000)

	async def contract_deploy(self): # test create,sign,send
		return await self.token_deploy(num=2,key='SafeMath',gas=500_000,mmgen_cmd='txcreate')

	async def token_transfer_ops(self,op,amt=1000):
		self.spawn('',msg_only=True)
		sid = dfl_sid
		from mmgen.tool.wallet import tool_cmd
		usr_mmaddrs = [f'{sid}:E:{i}' for i in (11,21)]
		usr_addrs = [tool_cmd(cmdname='gen_addr',proto=self.proto).gen_addr(addr,dfl_words_file) for addr in usr_mmaddrs]

		from mmgen.base_proto.ethereum.contract import TokenResolve
		async def do_transfer(rpc):
			for i in range(2):
				tk = await TokenResolve(
					self.proto,
					rpc,
					self.read_from_tmpfile(f'token_addr{i+1}').strip() )
				imsg_r( '\n' + await tk.info() )
				imsg('dev token balance (pre-send): {}'.format( await tk.get_balance(dfl_devaddr) ))
				imsg(f'Sending {amt} {self.proto.dcoin} to address {usr_addrs[i]} ({usr_mmaddrs[i]})')
				txid = await tk.transfer(
					dfl_devaddr,
					usr_addrs[i],
					amt,
					dfl_devkey,
					start_gas = ETHAmt(60000,'wei'),
					gasPrice  = ETHAmt(8,'Gwei') )
				if (await self.get_tx_receipt(txid)).status == 0:
					die(2,'Transfer of token funds failed. Aborting')

		async def show_bals(rpc):
			for i in range(2):
				tk = await TokenResolve(
					self.proto,
					rpc,
					self.read_from_tmpfile(f'token_addr{i+1}').strip() )
				imsg('Token: {}'.format( await tk.get_symbol() ))
				imsg(f'dev token balance: {await tk.get_balance(dfl_devaddr)}')
				imsg('usr token balance: {} ({} {})'.format(
					await tk.get_balance(usr_addrs[i]),
					usr_mmaddrs[i],
					usr_addrs[i] ))

		from mmgen.rpc import rpc_init
		rpc = await rpc_init(self.proto)

		silence()
		if op == 'show_bals':
			await show_bals(rpc)
		elif op == 'do_transfer':
			await do_transfer(rpc)
		end_silence()
		return 'ok'

	def token_fund_users(self):
		return self.token_transfer_ops(op='do_transfer')

	def token_user_bals(self):
		return self.token_transfer_ops(op='show_bals')

	def token_addrgen(self):
		self.addrgen(addrs='11-13')
		ok_msg()
		return self.addrgen(addrs='21-23')

	def token_addrimport_badaddr1(self):
		t = self.addrimport(ext='[11-13]{}.regtest.addrs',add_args=['--token=abc'],bad_input=True)
		t.expect('could not be resolved')
		t.req_exit_val = 2
		return t

	def token_addrimport_badaddr2(self):
		t = self.addrimport(ext='[11-13]{}.regtest.addrs',add_args=['--token='+'00deadbeef'*4],bad_input=True)
		t.expect('could not be resolved')
		t.req_exit_val = 2
		return t

	def token_addrimport(self,addr_file,addr_range,expect,extra_args=[]):
		token_addr = self.read_from_tmpfile(addr_file).strip()
		return self.addrimport(
			ext      = f'[{addr_range}]{{}}.regtest.addrs',
			expect   = expect,
			add_args = ['--token-addr='+token_addr]+extra_args )

	def token_addrimport_addr1(self):
		return self.token_addrimport('token_addr1','11-13',expect='3/3')

	def token_addrimport_addr2(self):
		return self.token_addrimport('token_addr2','21-23',expect='3/3')

	def token_addrimport_batch(self):
		return self.token_addrimport('token_addr1','11-13',expect='OK: 3',extra_args=['--batch'])

	def token_addrimport_sym(self):
		return self.addrimport(
			ext      = '[21-23]{}.regtest.addrs',
			expect   = '3/3',
			add_args = ['--token=MM2'] )

	def bal7(self):       return self.bal5()
	def token_bal1(self): return self.token_bal(n='1')

	def token_txcreate(self,args=[],token='',inputs='1',fee='50G'):
		return self.txcreate_ui_common(
			self.spawn('mmgen-txcreate', self.eth_args + ['--token='+token,'-B','--tx-fee='+fee] + args),
			menu              = [],
			inputs            = inputs,
			input_sels_prompt = 'to spend from',
			add_comment       = tx_label_lat_cyr_gr )
	def token_txsign(self,ext='',token=''):
		return self.txsign(ni=True,ext=ext,add_args=['--token='+token])
	def token_txsend(self,ext='',token=''):
		return self.txsend(ext=ext,add_args=['--token=mm1'])

	def token_txcreate1(self):
		return self.token_txcreate(args=['98831F3A:E:12,1.23456'],token='mm1')
	def token_txview1_raw(self):
		return self.txview(ext_fs='1.23456,50000]{}.regtest.rawtx')
	def token_txsign1(self):
		return self.token_txsign(ext='1.23456,50000]{}.regtest.rawtx',token='mm1')
	def token_txsend1(self):
		return self.token_txsend(ext='1.23456,50000]{}.regtest.sigtx',token='mm1')
	def token_txview1_sig(self):
		return self.txview(ext_fs='1.23456,50000]{}.regtest.sigtx')

	def tx_status3(self):
		return self.tx_status(
			ext='1.23456,50000]{}.regtest.sigtx',
			add_args=['--token=mm1'],
			expect_str='successfully executed',
			expect_str2='has 1 confirmation')

	def token_bal2(self):
		return self.token_bal(n='2')

	def twview(self,args=[],expect_str='',tool_args=[]):
		t = self.spawn('mmgen-tool', self.eth_args + args + ['twview'] + tool_args)
		if expect_str:
			t.expect(expect_str,regex=True)
		return t

	def token_txcreate2(self):
		return self.token_txcreate(args=[burn_addr+','+amt2],token='mm1')
	def token_txbump(self):
		return self.txbump(ext=amt2+',50000]{}.regtest.rawtx',fee='56G',add_args=['--token=mm1'])
	def token_txsign2(self):
		return self.token_txsign(ext=amt2+',50000]{}.regtest.rawtx',token='mm1')
	def token_txsend2(self):
		return self.token_txsend(ext=amt2+',50000]{}.regtest.sigtx',token='mm1')

	def token_bal3(self):
		return self.token_bal(n='3')

	def del_dev_addr(self):
		return self.spawn('mmgen-tool', self.eth_args + ['remove_address',dfl_devaddr])

	def bal1_getbalance(self):
		return self.bal_getbalance('1',etc_adj=True)

	def addrimport_token_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr,extra_args=['--token=mm1'])

	def token_bal4(self):
		return self.token_bal(n='4')

	def token_bal_getbalance(self):
		return self.bal_getbalance('2',extra_args=['--token=mm1'])

	def txcreate_noamt(self):
		return self.txcreate(args=['98831F3A:E:12'],eth_fee_res=True)
	def txsign_noamt(self):
		return self.txsign(ext='99.99895,50000]{}.regtest.rawtx')
	def txsend_noamt(self):
		return self.txsend(ext='99.99895,50000]{}.regtest.sigtx')

	def bal8(self):       return self.bal(n='8')
	def token_bal5(self): return self.token_bal(n='5')

	def token_txcreate_noamt(self):
		return self.token_txcreate(args=['98831F3A:E:13'],token='mm1',inputs='2',fee='51G')
	def token_txsign_noamt(self):
		return self.token_txsign(ext='1.23456,51000]{}.regtest.rawtx',token='mm1')
	def token_txsend_noamt(self):
		return self.token_txsend(ext='1.23456,51000]{}.regtest.sigtx',token='mm1')

	def bal9(self):       return self.bal(n='9')
	def token_bal6(self): return self.token_bal(n='6')

	def listaddresses(self,args=[],tool_args=['all_labels=1']):
		return self.spawn('mmgen-tool', self.eth_args + args + ['listaddresses'] + tool_args)

	def listaddresses1(self):
		return self.listaddresses()
	def listaddresses2(self):
		return self.listaddresses(tool_args=['minconf=999999999'])
	def listaddresses3(self):
		return self.listaddresses(tool_args=['sort=age'])
	def listaddresses4(self):
		return self.listaddresses(tool_args=['sort=age','showempty=1'])

	def token_listaddresses1(self):
		return self.listaddresses(args=['--token=mm1'])
	def token_listaddresses2(self):
		return self.listaddresses(args=['--token=mm1'],tool_args=['showempty=1'])

	def twview_cached_balances(self):
		return self.twview(args=['--cached-balances'])
	def token_twview_cached_balances(self):
		return self.twview(args=['--token=mm1','--cached-balances'])

	def txcreate_cached_balances(self):
		args = ['--tx-fee=20G','--cached-balances','98831F3A:E:3,0.1276']
		return self.txcreate(args=args,acct='2')
	def token_txcreate_cached_balances(self):
		args=['--cached-balances','--tx-fee=12G','98831F3A:E:12,1.2789']
		return self.token_txcreate(args=args,token='mm1')

	def txdo_cached_balances(self,
			acct = '2',
			fee_res_data = ('0.00105','50'),
			add_args = ['98831F3A:E:3,0.4321']):
		args = ['--tx-fee=20G','--cached-balances'] + add_args + [dfl_words_file]
		t = self.txcreate(args=args,acct=acct,caller='txdo',fee_res_data=fee_res_data,no_read=True)
		self._do_confirm_send(t,quiet=not g.debug,sure=False)
		return t

	def txcreate_refresh_balances(self,
			bals=['2','3'],
			args=['-B','--cached-balances','-i'],
			total=vbal5,
			adj_total=True,
			total_coin=None ):

		if total_coin is None:
			total_coin = self.proto.coin

		if self.proto.coin == 'ETC' and adj_total:
			total = str(Decimal(total) + self.bal_corr)
		t = self.spawn('mmgen-txcreate', self.eth_args + args)
		for n in bals:
			t.expect('[R]efresh balance:\b','R')
			t.expect(' main menu): ',n+'\n')
			t.expect('Is this what you want? (y/N): ','y')
		t.expect('[R]efresh balance:\b','q')
		t.expect(rf'Total unspent:.*\D{total}\D.*{total_coin}',regex=True)
		return t

	def bal10(self): return self.bal(n='10')

	def token_txdo_cached_balances(self):
		return self.txdo_cached_balances(
					acct='1',
					fee_res_data=('0.0026','50'),
					add_args=['--token=mm1','98831F3A:E:12,43.21'])

	def token_txcreate_refresh_balances(self):
		return self.txcreate_refresh_balances(
					bals=['1','2'],
					args=['--token=mm1','-B','--cached-balances','-i'],
					total='1000',adj_total=False,total_coin='MM1')

	def token_bal7(self): return self.token_bal(n='7')

	def twview1(self):
		return self.twview()
	def twview2(self):
		return self.twview(tool_args=['wide=1'])
	def twview3(self):
		return self.twview(tool_args=['wide=1','sort=age'])
	def twview4(self):
		return self.twview(tool_args=['wide=1','minconf=999999999'])
	def twview5(self):
		return self.twview(tool_args=['wide=1','minconf=0'])

	def token_twview1(self):
		return self.twview(args=['--token=mm1'])
	def token_twview2(self):
		return self.twview(args=['--token=mm1'],tool_args=['wide=1'])
	def token_twview3(self):
		return self.twview(args=['--token=mm1'],tool_args=['wide=1','sort=age'])

	def edit_label(self,out_num,args=[],action='l',label_text=None):
		t = self.spawn('mmgen-txcreate', self.eth_args + args + ['-B','-i'])
		p1,p2 = ('efresh balance:\b','return to main menu): ')
		p3,r3 = (p2,label_text+'\n') if label_text is not None else ('(y/N): ','y')
		p4,r4 = (('(y/N): ',),('y',)) if label_text == self.erase_input else ((),())
		for p,r in zip((p1,p1,p2,p3)+p4,('M',action,out_num+'\n',r3)+r4):
			t.expect(p,r)
		m = (   'Account #{} removed' if action == 'D' else
				'Label added to account #{}' if label_text and label_text != self.erase_input else
				'Label removed from account #{}' )
		t.expect(m.format(out_num))
		for p,r in zip((p1,p1),('M','q')):
			t.expect(p,r)
		t.expect('Total unspent:')
		return t

	def edit_label1(self):
		return self.edit_label(out_num=del_addrs[0],label_text=tw_label_zh)
	def edit_label2(self):
		return self.edit_label(out_num=del_addrs[1],label_text=tw_label_lat_cyr_gr)
	def edit_label3(self):
		return self.edit_label(out_num=del_addrs[0],label_text=self.erase_input)

	def token_edit_label1(self):
		return self.edit_label(out_num='1',label_text='Token label #1',args=['--token=mm1'])

	def remove_addr1(self):
		return self.edit_label(out_num=del_addrs[0],action='D')
	def remove_addr2(self):
		return self.edit_label(out_num=del_addrs[1],action='D')
	def token_remove_addr1(self):
		return self.edit_label(out_num=del_addrs[0],args=['--token=mm1'],action='D')
	def token_remove_addr2(self):
		return self.edit_label(out_num=del_addrs[1],args=['--token=mm1'],action='D')

	def stop(self):
		self.spawn('',msg_only=True)
		if not opt.no_daemon_stop:
			if not stop_test_daemons(self.proto.coin+'_rt'):
				return False
		set_vt100()
		return 'ok'
