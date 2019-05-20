#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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

import sys,os,subprocess,re,shutil
from decimal import Decimal
from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import die
from mmgen.exception import *
from test.common import *
from test.test_py_d.common import *

del_addrs = ('4','1')
dfl_sid = '98831F3A'

# The Parity dev address with lots of coins.  Create with "ethkey -b info ''":
dfl_addr = '00a329c0648769a73afac7f9381e08fb43dbea72'
dfl_addr_chk = '00a329c0648769A73afAc7F9381E08FB43dBEA72'
dfl_privkey = '4d5db4107d237df6a3d58ee5f70ae63d73d7658d4026f2eefd2f204c81682cb7'
burn_addr = 'deadbeef'*5
amt1 = '999999.12345689012345678'
amt2 = '888.111122223333444455'

parity_pid_fn = 'parity.pid'
parity_key_fn = 'parity.devkey'

# Token sends require varying amounts of gas, depending on compiler version
try:
	solc_ver = re.search(r'Version:\s*(.*)',
					subprocess.Popen(['solc','--version'],stdout=subprocess.PIPE
						).stdout.read().decode()).group(1)
except:
	solc_ver = '' # no solc on system - prompt for precompiled v0.5.3 contract files

if re.match(r'\b0.5.1\b',solc_ver): # Raspbian Stretch
	vbal1 = '1.2288337'
	vbal2 = '99.997085083'
	vbal3 = '1.23142165'
	vbal4 = '127.0287837'
elif solc_ver == '' or re.match(r'\b0.5.3\b',solc_ver): # Ubuntu Bionic
	vbal1 = '1.2288487'
	vbal2 = '99.997092733'
	vbal3 = '1.23142915'
	vbal4 = '127.0287987'

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
			(burn_addr + '\s+Non-MMGen',amt1)],
	'8': [  ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11',vbal1,'a'),
			('98831F3A:E:12','99.99895'),
			('98831F3A:E:21','2.345'),
			(burn_addr + '\s+Non-MMGen',amt1)],
	'9': [  ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11',vbal1,'a'),
			('98831F3A:E:12',vbal2),
			('98831F3A:E:21','2.345'),
			(burn_addr + '\s+Non-MMGen',amt1)]
}
token_bals = {
	'1': [  ('98831F3A:E:11','1000','1.234')],
	'2': [  ('98831F3A:E:11','998.76544',vbal3,'a'),
			('98831F3A:E:12','1.23456','0')],
	'3': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a'),
			('98831F3A:E:12','1.23456','0')],
	'4': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a'),
			('98831F3A:E:12','1.23456','0'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)],
	'5': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a'),
			('98831F3A:E:12','1.23456','99.99895'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)],
	'6': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a'),
			('98831F3A:E:12','0',vbal2),
			('98831F3A:E:13','1.23456','0'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)]
}
token_bals_getbalance = {
	'1': (vbal4,'999999.12345689012345678'),
	'2': ('111.888877776666555545','888.111122223333444455')
}

from test.test_py_d.ts_base import *
from test.test_py_d.ts_shared import *

class TestSuiteEthdev(TestSuiteBase,TestSuiteShared):
	'Ethereum transacting, token deployment and tracking wallet operations'
	networks = ('eth','etc')
	passthru_opts = ('coin',)
	tmpdir_nums = [22]
	cmd_group = (
		('setup',               'Ethereum Parity dev mode tests for coin {} (start parity)'.format(g.coin)),
		('addrgen',             'generating addresses'),
		('addrimport',          'importing addresses'),
		('addrimport_dev_addr', "importing Parity dev address 'Ox00a329c..'"),

		('txcreate1',           'creating a transaction (spend from dev address to address :1)'),
		('txsign1',             'signing the transaction'),
		('txsign1_ni',          'signing the transaction (non-interactive)'),
		('txsend1',             'sending the transaction'),
		('bal1',                'the {} balance'.format(g.coin)),

		('txcreate2',           'creating a transaction (spend from dev address to address :11)'),
		('txsign2',             'signing the transaction'),
		('txsend2',             'sending the transaction'),
		('bal2',                'the {} balance'.format(g.coin)),

		('txcreate3',           'creating a transaction (spend from dev address to address :21)'),
		('txsign3',             'signing the transaction'),
		('txsend3',             'sending the transaction'),
		('bal3',                'the {} balance'.format(g.coin)),

		('tx_status1',          'getting the transaction status'),

		('txcreate4',           'creating a transaction (spend from MMGen address, low TX fee)'),
		('txbump',              'bumping the transaction fee'),

		('txsign4',             'signing the transaction'),
		('txsend4',             'sending the transaction'),
		('bal4',                'the {} balance'.format(g.coin)),

		('txcreate5',           'creating a transaction (fund burn address)'),
		('txsign5',             'signing the transaction'),
		('txsend5',             'sending the transaction'),

		('addrimport_burn_addr',"importing burn address"),
		('bal5',                'the {} balance'.format(g.coin)),

		('add_label',           'adding a UTF-8 label'),
		('chk_label',           'the label'),
		('remove_label',        'removing the label'),

		('token_compile1',       'compiling ERC20 token #1'),

		('token_deploy1a',       'deploying ERC20 token #1 (SafeMath)'),
		('token_deploy1b',       'deploying ERC20 token #1 (Owned)'),
		('token_deploy1c',       'deploying ERC20 token #1 (Token)'),

		('tx_status2',           'getting the transaction status'),
		('bal6',                 'the {} balance'.format(g.coin)),

		('token_compile2',       'compiling ERC20 token #2'),

		('token_deploy2a',       'deploying ERC20 token #2 (SafeMath)'),
		('token_deploy2b',       'deploying ERC20 token #2 (Owned)'),
		('token_deploy2c',       'deploying ERC20 token #2 (Token)'),

		('contract_deploy',      'deploying contract (create,sign,send)'),

		('token_fund_users',     'transferring token funds from dev to user'),
		('token_user_bals',      'show balances after transfer'),
		('token_addrgen',        'generating token addresses'),
		('token_addrimport_badaddr1','importing token addresses (no token address)'),
		('token_addrimport_badaddr2','importing token addresses (bad token address)'),
		('token_addrimport',    'importing token addresses'),

		('bal7',                'the {} balance'.format(g.coin)),
		('token_bal1',          'the {} balance and token balance'.format(g.coin)),

		('token_txcreate1',     'creating a token transaction'),
		('token_txsign1',       'signing the transaction'),
		('token_txsend1',       'sending the transaction'),
		('token_bal2',          'the {} balance and token balance'.format(g.coin)),

		('token_txcreate2',     'creating a token transaction (to burn address)'),
		('token_txbump',        'bumping the transaction fee'),

		('token_txsign2',       'signing the transaction'),
		('token_txsend2',       'sending the transaction'),
		('token_bal3',          'the {} balance and token balance'.format(g.coin)),

		('del_dev_addr',        "deleting the dev address"),

		('bal1_getbalance',     'the {} balance (getbalance)'.format(g.coin)),

		('addrimport_token_burn_addr',"importing the token burn address"),

		('token_bal4',          'the {} balance and token balance'.format(g.coin)),
		('token_bal_getbalance','the token balance (getbalance)'),

		('txcreate_noamt',     'creating a transaction (full amount send)'),
		('txsign_noamt',       'signing the transaction'),
		('txsend_noamt',       'sending the transaction'),

		('bal8',                'the {} balance'.format(g.coin)),
		('token_bal5',          'the token balance'),

		('token_txcreate_noamt', 'creating a token transaction (full amount send)'),
		('token_txsign_noamt',   'signing the transaction'),
		('token_txsend_noamt',   'sending the transaction'),

		('bal9',                'the {} balance'.format(g.coin)),
		('token_bal6',          'the token balance'),

		('listaddresses1',      'listaddresses'),
		('listaddresses2',      'listaddresses minconf=999999999 (ignored)'),
		('listaddresses3',      'listaddresses sort=age (ignored)'),
		('listaddresses4',      'listaddresses showempty=1 sort=age (ignored)'),

		('token_listaddresses1','listaddresses --token=mm1'),
		('token_listaddresses2','listaddresses --token=mm1 showempty=1'),

		('twview1','twview'),
		('twview2','twview wide=1'),
		('twview3','twview wide=1 sort=age (ignored)'),
		('twview4','twview wide=1 minconf=999999999 (ignored)'),
		('twview5','twview wide=1 minconf=0 (ignored)'),
		('twview6','twview age_fmt=days (ignored)'),

		('token_twview1','twview --token=mm1'),
		('token_twview2','twview --token=mm1 wide=1'),
		('token_twview3','twview --token=mm1 wide=1 sort=age (ignored)'),

		('edit_label1','adding label to addr #{} in {} tracking wallet'.format(del_addrs[0],g.coin)),
		('edit_label2','adding label to addr #{} in {} tracking wallet'.format(del_addrs[1],g.coin)),
		('edit_label3','removing label from addr #{} in {} tracking wallet'.format(del_addrs[0],g.coin)),

		('remove_addr1','removing addr #{} from {} tracking wallet'.format(del_addrs[0],g.coin)),
		('remove_addr2','removing addr #{} from {} tracking wallet'.format(del_addrs[1],g.coin)),
		('remove_token_addr1','removing addr #{} from {} token tracking wallet'.format(del_addrs[0],g.coin)),
		('remove_token_addr2','removing addr #{} from {} token tracking wallet'.format(del_addrs[1],g.coin)),

		('stop',                'stopping parity'),
	)

	@property
	def eth_args(self):
		return ['--outdir={}'.format(self.tmpdir),'--coin='+g.coin,'--rpc-port=8549','--quiet']

	def setup(self):
		self.spawn('',msg_only=True)
		os.environ['MMGEN_BOGUS_WALLET_DATA'] = ''
		opts = ['--ports-shift=4','--config=dev']
		lf_arg = '--log-file=' + joinpath(self.tr.data_dir,'parity.log')
		if g.platform == 'win':
			dc_dir = joinpath(os.environ['LOCALAPPDATA'],'Parity','Ethereum','chains','DevelopmentChain')
			shutil.rmtree(dc_dir,ignore_errors=True)
			m1 = 'Please start parity on another terminal as follows:\n'
			m2 = ['parity',lf_arg] + opts
			m3 = '\nPress ENTER to continue: '
			my_raw_input(m1 + ' '.join(m2) + m3)
		elif subprocess.call(['which','parity'],stdout=subprocess.PIPE) == 0:
			ss = 'parity.*--log-file=test/data_dir.*/parity.log' # allow for UTF8_DEBUG
			try:
				pid = subprocess.check_output(['pgrep','-af',ss]).split()[0]
				os.kill(int(pid),9)
			except: pass
			# '--base-path' doesn't work together with daemon mode, so we have to clobber the main dev chain
			dc_dir = joinpath(os.environ['HOME'],'.local/share/io.parity.ethereum/chains/DevelopmentChain')
			shutil.rmtree(dc_dir,ignore_errors=True)
			bdir = joinpath(self.tr.data_dir,'parity')
			try: os.mkdir(bdir)
			except: pass
			redir = None if opt.exact_output else subprocess.PIPE
			pidfile = joinpath(self.tmpdir,parity_pid_fn)
			subprocess.check_call(['parity',lf_arg] + opts + ['daemon',pidfile],stderr=redir,stdout=redir)
			time.sleep(3) # race condition
			pid = self.read_from_tmpfile(parity_pid_fn)
		elif subprocess.call('netstat -tnl | grep -q 127.0.0.1:8549',shell=True) == 0:
			m1 = 'No parity executable found on system, but port 8549 is active!'
			m2 = 'Before continuing, you should probably run the command'
			m3 = 'test/test.py -X setup ethdev'
			m4 = 'on the remote host.'
			sys.stderr.write('{}\n{}\n{} {}\n'.format(m1,m2,cyan(m3),m4))
			confirm_continue()
		else:
			die(1,'No parity executable found!')
		return 'ok'

	def addrgen(self,addrs='1-3,11-13,21-23'):
		from mmgen.addr import MMGenAddrType
		t = self.spawn('mmgen-addrgen', self.eth_args + [dfl_words_file,addrs])
		t.written_to_file('Addresses')
		t.read()
		return t

	def addrimport(self,ext='21-23]{}.addrs',expect='9/9',add_args=[],bad_input=False):
		ext = ext.format('-α' if g.debug_utf8 else '')
		fn = self.get_file_with_ext(ext,no_dot=True,delete=False)
		t = self.spawn('mmgen-addrimport', self.eth_args[1:] + add_args + [fn])
		if bad_input:
			t.read()
			t.req_exit_val = 2
			return t
		if g.debug: t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
		t.expect('Importing')
		t.expect(expect)
		t.read()
		return t

	def addrimport_one_addr(self,addr=None,extra_args=[]):
		t = self.spawn('mmgen-addrimport', self.eth_args[1:] + extra_args + ['--address='+addr])
		t.expect('OK')
		return t

	def addrimport_dev_addr(self):
		return self.addrimport_one_addr(addr=dfl_addr)

	def addrimport_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr)

	def txcreate(self,args=[],menu=[],acct='1',non_mmgen_inputs=0,
						interactive_fee = '50G',
						eth_fee_res     = None,
						fee_res_fs      = '0.00105 {} (50 gas price in Gwei)',
						fee_desc        = 'gas price' ):
		fee_res = fee_res_fs.format(g.coin)
		t = self.spawn('mmgen-txcreate', self.eth_args + ['-B'] + args)
		t.expect(r'add \[l\]abel, .*?:.','p', regex=True)
		t.written_to_file('Account balances listing')
		return self.txcreate_ui_common( t, menu=menu,
										input_sels_prompt = 'to spend from',
										inputs            = acct,
										file_desc         = 'Ethereum transaction',
										bad_input_sels    = True,
										non_mmgen_inputs  = non_mmgen_inputs,
										interactive_fee   = interactive_fee,
										fee_res           = fee_res,
										fee_desc          = fee_desc,
										eth_fee_res       = eth_fee_res,
										add_comment       = ref_tx_label_jp )

	def txsign(self,ni=False,ext='{}.rawtx',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		keyfile = joinpath(self.tmpdir,parity_key_fn)
		write_to_file(keyfile,dfl_privkey+'\n')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn( 'mmgen-txsign',
						self.eth_args
						+ add_args
						+ ([],['--yes'])[ni]
						+ ['-k', keyfile, txfile, dfl_words_file] )
		return self.txsign_ui_common(t,ni=ni,has_label=True)

	def txsend(self,ni=False,bogus_send=False,ext='{}.sigtx',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = ''
		t = self.spawn('mmgen-txsend', self.eth_args + add_args + [txfile])
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = '1'
		txid = self.txsend_ui_common(t,quiet=True,bogus_send=bogus_send,has_label=True)
		return t

	def txcreate1(self):
		# valid_keypresses = EthereumTwUnspentOutputs.key_mappings.keys()
		menu = ['a','d','r','M','D','e','m','m'] # include one invalid keypress, 'D'
		args = ['98831F3A:E:1,123.456']
		return self.txcreate(args=args,menu=menu,acct='1',non_mmgen_inputs=1)

	def txsign1(self):    return self.txsign(add_args=['--use-internal-keccak-module'])
	def txsign1_ni(self): return self.txsign(ni=True)
	def txsend1(self):    return self.txsend()
	def bal1(self):       return self.bal(n='1')

	def txcreate2(self):
		args = ['98831F3A:E:11,1.234']
		return self.txcreate(args=args,acct='10',non_mmgen_inputs=1)
	def txsign2(self): return self.txsign(ni=True,ext='1.234,50000]{}.rawtx')
	def txsend2(self): return self.txsend(ext='1.234,50000]{}.sigtx')
	def bal2(self):    return self.bal(n='2')

	def txcreate3(self):
		args = ['98831F3A:E:21,2.345']
		return self.txcreate(args=args,acct='10',non_mmgen_inputs=1)
	def txsign3(self): return self.txsign(ni=True,ext='2.345,50000]{}.rawtx')
	def txsend3(self): return self.txsend(ext='2.345,50000]{}.sigtx')
	def bal3(self):    return self.bal(n='3')

	def tx_status(self,ext,expect_str):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txsend', self.eth_args + ['--status',txfile])
		t.expect(expect_str)
		t.read()
		return t

	def tx_status1(self):
		return self.tx_status(ext='2.345,50000]{}.sigtx',expect_str='has 1 confirmation')

	def txcreate4(self):
		args = ['98831F3A:E:2,23.45495']
		interactive_fee='40G'
		fee_res_fs='0.00084 {} (40 gas price in Gwei)'
		return self.txcreate(   args             = args,
								acct             = '1',
								non_mmgen_inputs = 0,
								interactive_fee  = interactive_fee,
								fee_res_fs       = fee_res_fs,
								eth_fee_res      = True)

	def txbump(self,ext=',40000]{}.rawtx',fee='50G',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txbump', self.eth_args + add_args + ['--yes',txfile])
		t.expect('or gas price: ',fee+'\n')
		t.read()
		return t

	def txsign4(self): return self.txsign(ni=True,ext='.45495,50000]{}.rawtx')
	def txsend4(self): return self.txsend(ext='.45495,50000]{}.sigtx')
	def bal4(self):    return self.bal(n='4')

	def txcreate5(self):
		args = [burn_addr + ','+amt1]
		return self.txcreate(args=args,acct='10',non_mmgen_inputs=1)
	def txsign5(self): return self.txsign(ni=True,ext=amt1+',50000]{}.rawtx')
	def txsend5(self): return self.txsend(ext=amt1+',50000]{}.sigtx')
	def bal5(self):    return self.bal(n='5')

	bal_corr = Decimal('0.0000032') # gas use for token sends varies between ETH and ETC!
	def bal(self,n=None):
		t = self.spawn('mmgen-tool', self.eth_args + ['twview','wide=1'])
		for b in bals[n]:
			addr,amt,adj = b if len(b) == 3 else b + (False,)
			if adj and g.coin == 'ETC': amt = str(Decimal(amt) + self.bal_corr)
			pat = r'{}\s+{}\s'.format(addr,amt.replace('.',r'\.'))
			t.expect(pat,regex=True)
		t.read()
		return t

	def token_bal(self,n=None):
		t = self.spawn('mmgen-tool', self.eth_args + ['--token=mm1','twview','wide=1'])
		for b in token_bals[n]:
			addr,_amt1,_amt2,adj = b if len(b) == 4 else b + (False,)
			if adj and g.coin == 'ETC': _amt2 = str(Decimal(_amt2) + self.bal_corr)
			pat = r'{}\s+{}\s+{}\s'.format(addr,_amt1.replace('.',r'\.'),_amt2.replace('.',r'\.'))
			t.expect(pat,regex=True)
		t.read()
		return t

	def bal_getbalance(self,idx,etc_adj=False,extra_args=[]):
		bal1 = token_bals_getbalance[idx][0]
		bal2 = token_bals_getbalance[idx][1]
		bal1 = Decimal(bal1)
		if etc_adj and g.coin == 'ETC': bal1 += self.bal_corr
		t = self.spawn('mmgen-tool', self.eth_args + extra_args + ['getbalance'])
		t.expect(r'\n[0-9A-F]{8}: .* '+str(bal1),regex=True)
		t.expect(r'\nNon-MMGen: .* '+bal2,regex=True)
		total = t.expect_getend(r'\nTOTAL:\s+',regex=True).split()[0]
		t.read()
		assert Decimal(bal1) + Decimal(bal2) == Decimal(total)
		return t

	def add_label(self,addr='98831F3A:E:3',lbl=utf8_label):
		t = self.spawn('mmgen-tool', self.eth_args + ['add_label',addr,lbl])
		t.expect('Added label.*in tracking wallet',regex=True)
		return t

	def chk_label(self,addr='98831F3A:E:3',label_pat=utf8_label_pat):
		t = self.spawn('mmgen-tool', self.eth_args + ['listaddresses','all_labels=1'])
		t.expect(r'{}\s+\S{{30}}\S+\s+{}\s+'.format(addr,(label_pat or label)),regex=True)
		return t

	def remove_label(self,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		return t

	def token_compile(self,token_data={}):
		odir = joinpath(self.tmpdir,token_data['symbol'].lower())
		if self.skip_for_win():
			m ='Copy solc v0.5.3 contract data for token {} to directory {} and hit ENTER: '
			input(m.format(token_data['symbol'],odir))
			return 'skip'
		self.spawn('',msg_only=True)
		cmd_args = ['--{}={}'.format(k,v) for k,v in list(token_data.items())]
		imsg("Compiling solidity token contract '{}' with 'solc'".format(token_data['symbol']))
		try: os.mkdir(odir)
		except: pass
		cmd = ['scripts/create-token.py','--coin='+g.coin,'--outdir='+odir] + cmd_args + [dfl_addr_chk]
		imsg("Executing: {}".format(' '.join(cmd)))
		subprocess.check_output(cmd,stderr=subprocess.STDOUT)
		imsg("ERC20 token '{}' compiled".format(token_data['symbol']))
		return 'ok'

	def token_compile1(self):
		token_data = { 'name':'MMGen Token 1', 'symbol':'MM1', 'supply':10**26, 'decimals':18 }
		return self.token_compile(token_data)

	def token_compile2(self):
		token_data = { 'name':'MMGen Token 2', 'symbol':'MM2', 'supply':10**18, 'decimals':10 }
		return self.token_compile(token_data)

	def _rpc_init(self):
		g.proto.rpc_port = 8549
		rpc_init()

	def token_deploy(self,num,key,gas,mmgen_cmd='txdo',tx_fee='8G'):
		self._rpc_init()
		keyfile = joinpath(self.tmpdir,parity_key_fn)
		fn = joinpath(self.tmpdir,'mm'+str(num),key+'.bin')
		os.environ['MMGEN_BOGUS_SEND'] = ''
		args = ['-B',
				'--tx-fee='+tx_fee,
				'--tx-gas={}'.format(gas),
				'--contract-data='+fn,
				'--inputs='+dfl_addr,
				'--yes' ]
		if mmgen_cmd == 'txdo': args += ['-k',keyfile]
		t = self.spawn( 'mmgen-'+mmgen_cmd, self.eth_args + args)
		if mmgen_cmd == 'txcreate':
			t.written_to_file('Ethereum transaction')
			ext = '[0,8000]{}.rawtx'.format('-α' if g.debug_utf8 else '')
			txfile = self.get_file_with_ext(ext,no_dot=True)
			t = self.spawn('mmgen-txsign', self.eth_args + ['--yes','-k',keyfile,txfile],no_msg=True)
			self.txsign_ui_common(t,ni=True)
			txfile = txfile.replace('.rawtx','.sigtx')
			t = self.spawn('mmgen-txsend', self.eth_args + [txfile],no_msg=True)

		os.environ['MMGEN_BOGUS_SEND'] = '1'
		txid = self.txsend_ui_common(t,caller=mmgen_cmd,quiet=True,bogus_send=False)
		addr = t.expect_getend('Contract address: ')
		from mmgen.altcoins.eth.tx import EthereumMMGenTX as etx
		assert etx.get_exec_status(txid,True) != 0,(
			"Contract '{}:{}' failed to execute. Aborting".format(num,key))
		if key == 'Token':
			self.write_to_tmpfile('token_addr{}'.format(num),addr+'\n')
			imsg('\nToken MM{} deployed!'.format(num))
		return t

	def token_deploy1a(self): return self.token_deploy(num=1,key='SafeMath',gas=200000)
	def token_deploy1b(self): return self.token_deploy(num=1,key='Owned',gas=250000)
	def token_deploy1c(self): return self.token_deploy(num=1,key='Token',gas=1100000,tx_fee='7G')

	def tx_status2(self):
		return self.tx_status(ext=g.coin+'[0,7000]{}.sigtx',expect_str='successfully executed')

	def bal6(self): return self.bal5()

	def token_deploy2a(self): return self.token_deploy(num=2,key='SafeMath',gas=200000)
	def token_deploy2b(self): return self.token_deploy(num=2,key='Owned',gas=250000)
	def token_deploy2c(self): return self.token_deploy(num=2,key='Token',gas=1100000)

	def contract_deploy(self): # test create,sign,send
		return self.token_deploy(num=2,key='SafeMath',gas=1100000,mmgen_cmd='txcreate')

	def token_transfer_ops(self,op,amt=1000):
		self.spawn('',msg_only=True)
		sid = dfl_sid
		from mmgen.tool import MMGenToolCmd
		usr_mmaddrs = ['{}:E:{}'.format(sid,i) for i in (11,21)]
		usr_addrs = [MMGenToolCmd().gen_addr(addr,dfl_words_file) for addr in usr_mmaddrs]
		self._rpc_init()

		from mmgen.altcoins.eth.contract import Token
		from mmgen.altcoins.eth.tx import EthereumMMGenTX as etx
		def do_transfer():
			for i in range(2):
				tk = Token(self.read_from_tmpfile('token_addr{}'.format(i+1)).strip())
				imsg_r('\n'+tk.info())
				imsg('dev token balance (pre-send): {}'.format(tk.balance(dfl_addr)))
				imsg('Sending {} {} to address {} ({})'.format(amt,g.coin,usr_addrs[i],usr_mmaddrs[i]))
				from mmgen.obj import ETHAmt
				txid = tk.transfer( dfl_addr, usr_addrs[i], amt, dfl_privkey,
									start_gas = ETHAmt(60000,'wei'),
									gasPrice  = ETHAmt(8,'Gwei') )
				assert etx.get_exec_status(txid,True) != 0,'Transfer of token funds failed. Aborting'

		def show_bals():
			for i in range(2):
				tk = Token(self.read_from_tmpfile('token_addr{}'.format(i+1)).strip())
				imsg('Token: {}'.format(tk.symbol()))
				imsg('dev token balance: {}'.format(tk.balance(dfl_addr)))
				imsg('usr token balance: {} ({} {})'.format(
						tk.balance(usr_addrs[i]),usr_mmaddrs[i],usr_addrs[i]))

		silence()
		if op == 'show_bals': show_bals()
		elif op == 'do_transfer': do_transfer()
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
		t = self.addrimport(ext='[11-13]{}.addrs',add_args=['--token=abc'],bad_input=True)
		t.req_exit_val = 2
		return t

	def token_addrimport_badaddr2(self):
		t = self.addrimport(ext='[11-13]{}.addrs',add_args=['--token='+'00deadbeef'*4],bad_input=True)
		t.req_exit_val = 2
		return t

	def token_addrimport(self):
		for n,r in ('1','11-13'),('2','21-23'):
			tk_addr = self.read_from_tmpfile('token_addr'+n).strip()
			t = self.addrimport(ext='['+r+']{}.addrs',expect='3/3',add_args=['--token='+tk_addr])
			t.p.wait()
			ok_msg()
		t.skip_ok = True
		return t

	def bal7(self):       return self.bal5()
	def token_bal1(self): return self.token_bal(n='1')

	def token_txcreate(self,args=[],token='',inputs='1',fee='50G'):
		t = self.spawn('mmgen-txcreate', self.eth_args + ['--token='+token,'-B','--tx-fee='+fee] + args)
		return self.txcreate_ui_common( t,
										menu              = [],
										inputs            = inputs,
										input_sels_prompt = 'to spend from',
										file_desc         = 'Ethereum token transaction',
										add_comment       = ref_tx_label_lat_cyr_gr)
	def token_txsign(self,ext='',token=''):
		return self.txsign(ni=True,ext=ext,add_args=['--token='+token])
	def token_txsend(self,ext='',token=''):
		return self.txsend(ext=ext,add_args=['--token=mm1'])

	def token_txcreate1(self):
		return self.token_txcreate(args=['98831F3A:E:12,1.23456'],token='mm1')
	def token_txsign1(self):
		return self.token_txsign(ext='1.23456,50000]{}.rawtx',token='mm1')
	def token_txsend1(self):
		return self.token_txsend(ext='1.23456,50000]{}.sigtx',token='mm1')
	def token_bal2(self):
		return self.token_bal(n='2')

	def twview(self,args=[],expect_str='',tool_args=[],exit_val=0):
		t = self.spawn('mmgen-tool', self.eth_args + args + ['twview'] + tool_args)
		if expect_str:
			t.expect(expect_str,regex=True)
		t.read()
		t.req_exit_val = exit_val
		return t

	def token_txcreate2(self):
		return self.token_txcreate(args=[burn_addr+','+amt2],token='mm1')
	def token_txbump(self):
		return self.txbump(ext=amt2+',50000]{}.rawtx',fee='56G',add_args=['--token=mm1'])
	def token_txsign2(self):
		return self.token_txsign(ext=amt2+',50000]{}.rawtx',token='mm1')
	def token_txsend2(self):
		return self.token_txsend(ext=amt2+',50000]{}.sigtx',token='mm1')

	def token_bal3(self):
		return self.token_bal(n='3')

	def del_dev_addr(self):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_address',dfl_addr])
		t.read() # TODO
		return t

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
		return self.txsign(ext='99.99895,50000]{}.rawtx')
	def txsend_noamt(self):
		return self.txsend(ext='99.99895,50000]{}.sigtx')

	def bal8(self):       return self.bal(n='8')
	def token_bal5(self): return self.token_bal(n='5')

	def token_txcreate_noamt(self):
		return self.token_txcreate(args=['98831F3A:E:13'],token='mm1',inputs='2',fee='51G')
	def token_txsign_noamt(self):
		return self.token_txsign(ext='1.23456,51000]{}.rawtx',token='mm1')
	def token_txsend_noamt(self):
		return self.token_txsend(ext='1.23456,51000]{}.sigtx',token='mm1')

	def bal9(self):       return self.bal(n='9')
	def token_bal6(self): return self.token_bal(n='6')

	def listaddresses(self,args=[],tool_args=['all_labels=1'],exit_val=0):
		t = self.spawn('mmgen-tool', self.eth_args + args + ['listaddresses'] + tool_args)
		t.read()
		t.req_exit_val = exit_val
		return t

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
	def twview6(self):
		return self.twview(tool_args=['age_fmt=days'])

	def token_twview1(self):
		return self.twview(args=['--token=mm1'])
	def token_twview2(self):
		return self.twview(args=['--token=mm1'],tool_args=['wide=1'])
	def token_twview3(self):
		return self.twview(args=['--token=mm1'],tool_args=['wide=1','sort=age'])

	def edit_label(self,out_num,args=[],action='l',label_text=None):
		t = self.spawn('mmgen-txcreate', self.eth_args + args + ['-B','-i'])
		p1,p2 = ('emove address:\b','return to main menu): ')
		p3,r3 = (p2,label_text+'\n') if label_text is not None else ('(y/N): ','y')
		p4,r4 = (('(y/N): ',),('y',)) if label_text == '' else ((),())
		for p,r in zip((p1,p1,p2,p3)+p4+(p1,p1),('M',action,out_num+'\n',r3)+r4+('M','q')):
			t.expect(p,r)
		return t

	def edit_label1(self):
		return self.edit_label(out_num=del_addrs[0],label_text='First added label-α')
	def edit_label2(self):
		return self.edit_label(out_num=del_addrs[1],label_text='Second added label')
	def edit_label3(self):
		return self.edit_label(out_num=del_addrs[0],label_text='')

	def remove_addr1(self):
		return self.edit_label(out_num=del_addrs[0],action='R')
	def remove_addr2(self):
		return self.edit_label(out_num=del_addrs[1],action='R')
	def remove_token_addr1(self):
		return self.edit_label(out_num=del_addrs[0],args=['--token=mm1'],action='R')
	def remove_token_addr2(self):
		return self.edit_label(out_num=del_addrs[1],args=['--token=mm1'],action='R')

	def stop(self):
		self.spawn('',msg_only=True)
		if g.platform == 'win':
			my_raw_input('Please stop parity and Press ENTER to continue: ')
		elif subprocess.call(['which','parity'],stdout=subprocess.PIPE) == 0:
			pid = self.read_from_tmpfile(parity_pid_fn)
			if opt.no_daemon_stop:
				msg_r('(leaving daemon running by user request)')
			else:
				subprocess.check_call(['kill',pid])
		else:
			imsg('No parity executable found on system. Ignoring')
		return 'ok'
