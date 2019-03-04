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
ts_regtest.py: Regtest tests for the test.py test suite
"""

import os,subprocess
from decimal import Decimal
from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import die,gmsg,write_data_to_file
from mmgen.protocol import CoinProtocol
from mmgen.addr import AddrList
from test.common import *
from test.test_py_d.common import *

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
				'52.99990000','946.99933647','999.99923647','52.9999',
				'946.99933647'),
		'bch': ('499.9999484','399.9999194','399.9998972','399.9997692',
				'46.78900000','953.20966920','999.99866920','46.789',
				'953.2096692'),
		'ltc': ('5499.99744','5399.994425','5399.993885','5399.987535',
				'52.99000000','10946.93753500','10999.92753500','52.99',
				'10946.937535'),
	},
	'rtBals_gb': {
		'btc': ('116.77629233','283.22339537'),
		'bch': ('116.77637483','283.22339437'),
		'ltc': ('5116.77036263','283.21717237')
	},
	'rtBobOp3': {'btc':'S:2','bch':'L:3','ltc':'S:2'},
	'rtAmts': {
		'btc': ('500',),
		'bch': ('500',),
		'ltc': ('5500',)
	}
}

from test.test_py_d.ts_base import *
from test.test_py_d.ts_shared import *

class TestSuiteRegtest(TestSuiteBase,TestSuiteShared):
	'transacting and tracking wallet operations via regtest mode'
	networks = ('btc','ltc','bch')
	passthru_opts = ('coin',)
	tmpdir_nums = [17]
	cmd_group = (
		('setup',                    'regtest (Bob and Alice) mode setup'),
		('walletgen_bob',            'wallet generation (Bob)'),
		('walletgen_alice',          'wallet generation (Alice)'),
		('addrgen_bob',              'address generation (Bob)'),
		('addrgen_alice',            'address generation (Alice)'),
		('addrimport_bob',           "importing Bob's addresses"),
		('addrimport_alice',         "importing Alice's addresses"),
		('fund_bob',                 "funding Bob's wallet"),
		('fund_alice',               "funding Alice's wallet"),
		('bob_bal1',                 "Bob's balance"),
		('bob_add_label',            "adding a 40-character UTF-8 encoded label"),
		('bob_twview',               "viewing Bob's tracking wallet"),
		('bob_split1',               "splitting Bob's funds"),
		('generate',                 'mining a block'),
		('bob_bal2',                 "Bob's balance"),
		('bob_bal2a',                "Bob's balance (age_fmt=confs)"),
		('bob_bal2b',                "Bob's balance (showempty=1)"),
		('bob_bal2c',                "Bob's balance (showempty=1 minconf=2 age_fmt=days)"),
		('bob_bal2d',                "Bob's balance (minconf=2)"),
		('bob_bal2e',                "Bob's balance (showempty=1 sort=age)"),
		('bob_bal2f',                "Bob's balance (showempty=1 sort=age,reverse)"),
		('bob_rbf_send',             'sending funds to Alice (RBF)'),
		('get_mempool1',             'mempool (before RBF bump)'),
		('bob_rbf_bump',             'bumping RBF transaction'),
		('get_mempool2',             'mempool (after RBF bump)'),
		('generate',                 'mining a block'),
		('bob_bal3',                 "Bob's balance"),
		('bob_pre_import',           'sending to non-imported address'),
		('generate',                 'mining a block'),
		('bob_import_addr',          'importing non-MMGen address with --rescan'),
		('bob_bal4',                 "Bob's balance (after import with rescan)"),
		('bob_import_list',          'importing flat address list'),
		('bob_split2',               "splitting Bob's funds"),
		('generate',                 'mining a block'),
		('bob_bal5',                 "Bob's balance"),
		('bob_bal5_getbalance',      "Bob's balance"),
		('bob_send_non_mmgen',       'sending funds to Alice (from non-MMGen addrs)'),
		('generate',                 'mining a block'),
		('alice_add_label1',         'adding a label'),
		('alice_chk_label1',         'the label'),
		('alice_add_label2',         'adding a label'),
		('alice_chk_label2',         'the label'),
		('alice_edit_label1',        'editing a label'),
		('alice_chk_label3',         'the label'),
		('alice_remove_label1',      'removing a label'),
		('alice_chk_label4',         'the label'),
		('alice_add_label_coinaddr', 'adding a label using the coin address'),
		('alice_chk_label_coinaddr', 'the label'),
		('alice_add_label_badaddr1', 'adding a label with invalid address'),
		('alice_add_label_badaddr2', 'adding a label with invalid address for this chain'),
		('alice_add_label_badaddr3', 'adding a label with wrong MMGen address'),
		('alice_add_label_badaddr4', 'adding a label with wrong coin address'),
		('alice_bal_rpcfail',        'RPC failure code'),
		('alice_send_estimatefee',   'tx creation with no fee on command line'),
		('generate',                 'mining a block'),
		('bob_bal6',                 "Bob's balance"),
		('bob_alice_bal',            "Bob and Alice's balances"),
		('alice_bal2',               "Alice's balance"),
		('stop',                     'stopping regtest daemon'),
	)

	def __init__(self,trunner,cfgs,spawn):
		coin = g.coin.lower()
		for k in rt_data:
			globals()[k] = rt_data[k][coin] if coin in rt_data[k] else None
		return TestSuiteBase.__init__(self,trunner,cfgs,spawn)

	def _add_comments_to_addr_file(self,addrfile,outfile,use_labels=False):
		silence()
		gmsg("Adding comments to address file '{}'".format(addrfile))
		a = AddrList(addrfile)
		for n,idx in enumerate(a.idxs(),1):
			if use_labels:
				a.set_comment(idx,get_label())
			else:
				if n % 2: a.set_comment(idx,'Test address {}'.format(n))
		a.format(enable_comments=True)
		write_data_to_file(outfile,a.fmt_data,silent=True,ignore_opt_outdir=True)
		end_silence()

	def setup(self):
		os.environ['MMGEN_BOGUS_WALLET_DATA'] = ''
		if g.testnet:
			die(2,'--testnet option incompatible with regtest test suite')
		try: shutil.rmtree(joinpath(self.tr.data_dir,'regtest'))
		except: pass
		os.environ['MMGEN_TEST_SUITE'] = '' # mnemonic is piped to stdin, so stop being a terminal
		t = self.spawn('mmgen-regtest',['-n','setup'])
		os.environ['MMGEN_TEST_SUITE'] = '1'
		for s in ('Starting setup','Creating','Mined','Creating','Creating','Setup complete'):
			t.expect(s)
		return t

	def walletgen(self,user):
		t = self.spawn('mmgen-walletgen',['-q','-r0','-p1','--'+user])
		t.passphrase_new('new MMGen wallet',rt_pw)
		t.label()
		t.expect('move it to the data directory? (Y/n): ','y')
		t.written_to_file('MMGen wallet')
		return t

	def walletgen_bob(self):   return self.walletgen('bob')
	def walletgen_alice(self): return self.walletgen('alice')

	def _user_dir(self,user,coin=None):
		return joinpath(self.tr.data_dir,'regtest',coin or g.coin.lower(),user)

	def _user_sid(self,user):
		return os.path.basename(get_file_with_ext(self._user_dir(user),'mmdat'))[:8]

	def addrgen(self,user,wf=None,addr_range='1-5'):
		from mmgen.addr import MMGenAddrType
		for mmtype in g.proto.mmtypes:
			t = self.spawn('mmgen-addrgen',
				['--quiet','--'+user,'--type='+mmtype,'--outdir={}'.format(self._user_dir(user))] +
				([],[wf])[bool(wf)] + [addr_range],
				extra_desc='({})'.format(MMGenAddrType.mmtypes[mmtype]['name']))
			t.passphrase('MMGen wallet',rt_pw)
			t.written_to_file('Addresses')
			ok_msg()
		t.skip_ok = True
		return t

	def addrgen_bob(self):   return self.addrgen('bob')
	def addrgen_alice(self): return self.addrgen('alice')

	def addrimport(self,user,sid=None,addr_range='1-5',num_addrs=5):
		id_strs = { 'legacy':'', 'compressed':'-C', 'segwit':'-S', 'bech32':'-B' }
		if not sid: sid = self._user_sid(user)
		from mmgen.addr import MMGenAddrType
		for mmtype in g.proto.mmtypes:
			desc = MMGenAddrType.mmtypes[mmtype]['name']
			addrfile = joinpath(self._user_dir(user),
				'{}{}{}[{}]{x}.testnet.addrs'.format(
					sid,self.altcoin_pfx,id_strs[desc],addr_range,
					x='-α' if g.debug_utf8 else ''))
			if mmtype == g.proto.mmtypes[0] and user == 'bob':
				psave = g.proto
				g.proto = CoinProtocol(g.coin,True)
				self._add_comments_to_addr_file(addrfile,addrfile,use_labels=True)
				g.proto = psave
			t = self.spawn( 'mmgen-addrimport',
							['--quiet', '--'+user, '--batch', addrfile],
							extra_desc='({})'.format(desc))
			if g.debug:
				t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
			t.expect('Importing')
			t.expect('{} addresses imported'.format(num_addrs))
			ok_msg()

		t.skip_ok = True
		return t

	def addrimport_bob(self):   return self.addrimport('bob')
	def addrimport_alice(self): return self.addrimport('alice')

	def fund_wallet(self,user,mmtype,amt,sid=None,addr_range='1-5'):
		if not sid: sid = self._user_sid(user)
		addr = self.get_addr_from_addrlist(user,sid,mmtype,0,addr_range=addr_range)
		t = self.spawn('mmgen-regtest', ['send',str(addr),str(amt)])
		t.expect('Sending {} {}'.format(amt,g.coin))
		t.expect('Mined 1 block')
		return t

	def fund_bob(self):   return self.fund_wallet('bob','C',rtFundAmt)
	def fund_alice(self): return self.fund_wallet('alice',('L','S')[g.proto.cap('segwit')],rtFundAmt)

	def user_twview(self,user):
		t = self.spawn('mmgen-tool',['--'+user,'twview'])
		t.expect(r'1\).*\b{}\b'.format(rtAmts[0]),regex=True)
		t.read()
		return t

	def bob_twview(self):
		return self.user_twview('bob')

	def user_bal(self,user,bal,args=['showempty=1'],skip_check=False,exit_val=0):
		t = self.spawn('mmgen-tool',['--'+user,'listaddresses'] + args)
		if skip_check:
			t.read()
		else:
			total = t.expect_getend('TOTAL: ')
			cmp_or_die('{} {}'.format(bal,g.coin),total)
		t.req_exit_val = exit_val
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
		return self.user_bal('bob',rtBals[0],args=['showempty=1','sort=age'])

	def bob_bal2f(self):
		return self.user_bal('bob',rtBals[0],args=['showempty=1','sort=age,reverse'])

	def bob_bal3(self):
		return self.user_bal('bob',rtBals[1])

	def bob_bal4(self):
		return self.user_bal('bob',rtBals[2])

	def bob_bal5(self):
		return self.user_bal('bob',rtBals[3])

	def bob_bal6(self):
		return self.user_bal('bob',rtBals[7])

	def bob_bal5_getbalance(self):
		t_ext,t_mmgen = rtBals_gb[0],rtBals_gb[1]
		assert Decimal(t_ext) + Decimal(t_mmgen) == Decimal(rtBals[3])
		t = self.spawn('mmgen-tool',['--bob','getbalance'])
		t.expect(r'\n[0-9A-F]{8}: .* '+t_mmgen,regex=True)
		t.expect(r'\nNon-MMGen: .* '+t_ext,regex=True)
		t.expect(r'\nTOTAL: .* '+rtBals[3],regex=True)
		t.read()
		return t

	def bob_alice_bal(self):
		t = self.spawn('mmgen-regtest',['get_balances'])
		t.expect('Switching')
		ret = t.expect_getend("Bob's balance:").strip()
		cmp_or_die(rtBals[4],ret)
		ret = t.expect_getend("Alice's balance:").strip()
		cmp_or_die(rtBals[5],ret)
		ret = t.expect_getend("Total balance:").strip()
		cmp_or_die(rtBals[6],ret)
		return t

	def user_txdo(  self, user, fee, outputs_cl, outputs_list,
					extra_args   = [],
					wf           = None,
					do_label     = False,
					bad_locktime = False,
					full_tx_view = False ):
		os.environ['MMGEN_BOGUS_SEND'] = ''
		t = self.spawn('mmgen-txdo',
			['-d',self.tmpdir,'-B','--'+user] +
			(['--tx-fee='+fee] if fee else []) +
			extra_args + ([],[wf])[bool(wf)] + outputs_cl)
		os.environ['MMGEN_BOGUS_SEND'] = '1'

		self.txcreate_ui_common(t,
								caller          = 'txdo',
								menu            = ['M'],
								inputs          = outputs_list,
								file_desc       = 'Signed transaction',
								interactive_fee = (tx_fee,'')[bool(fee)],
								add_comment     = ref_tx_label_jp,
								view            = 't',save=True)

		t.passphrase('MMGen wallet',rt_pw)
		t.written_to_file('Signed transaction')
		self._do_confirm_send(t)
		s,exit_val = (('Transaction sent',0),("can't be included",1))[bad_locktime]
		t.expect(s)
		t.req_exit_val = exit_val
		return t

	def bob_split1(self):
		sid = self._user_sid('bob')
		outputs_cl = [sid+':C:1,100', sid+':L:2,200',sid+':'+rtBobOp3]
		return self.user_txdo('bob',rtFee[0],outputs_cl,'1',do_label=True,full_tx_view=True)

	def get_addr_from_addrlist(self,user,sid,mmtype,idx,addr_range='1-5'):
		id_str = { 'L':'', 'S':'-S', 'C':'-C', 'B':'-B' }[mmtype]
		ext = '{}{}{}[{}]{x}.testnet.addrs'.format(
			sid,self.altcoin_pfx,id_str,addr_range,x='-α' if g.debug_utf8 else '')
		addrfile = get_file_with_ext(self._user_dir(user),ext,no_dot=True)
		psave = g.proto
		g.proto = CoinProtocol(g.coin,True)
		if hasattr(g.proto,'bech32_hrp_rt'):
			g.proto.bech32_hrp = g.proto.bech32_hrp_rt
		silence()
		addr = AddrList(addrfile).data[idx].addr
		end_silence()
		g.proto = psave
		return addr

	def _create_tx_outputs(self,user,data):
		sid = self._user_sid(user)
		return [self.get_addr_from_addrlist(user,sid,mmtype,idx-1)+amt_str for mmtype,idx,amt_str in data]

	def bob_rbf_send(self):
		outputs_cl = self._create_tx_outputs('alice',(('L',1,',60'),('C',1,',40'))) # alice_sid:L:1, alice_sid:C:1
		outputs_cl += [self._user_sid('bob')+':'+rtBobOp3]
		return self.user_txdo('bob',rtFee[1],outputs_cl,'3',
					extra_args=([],['--rbf'])[g.proto.cap('rbf')])

	def bob_send_non_mmgen(self):
		outputs_cl = self._create_tx_outputs('alice',(
			(('L','S')[g.proto.cap('segwit')],2,',10'),
			(('L','S')[g.proto.cap('segwit')],3,'')
		)) # alice_sid:S:2, alice_sid:S:3
		keyfile = joinpath(self.tmpdir,'non-mmgen.keys')
		return self.user_txdo('bob',rtFee[3],outputs_cl,'1,4-10',
			extra_args=['--keys-from-file='+keyfile,'--vsize-adj=1.02'])

	def alice_send_estimatefee(self):
		outputs_cl = self._create_tx_outputs('bob',(('L',1,''),)) # bob_sid:L:1
		return self.user_txdo('alice',None,outputs_cl,'1') # fee=None

	def user_txbump(self,user,txfile,fee,red_op):
		if not g.proto.cap('rbf'):
			msg('Skipping RBF'); return 'skip'
		os.environ['MMGEN_BOGUS_SEND'] = ''
		t = self.spawn('mmgen-txbump',
			['-d',self.tmpdir,'--send','--'+user,'--tx-fee='+fee,'--output-to-reduce='+red_op] + [txfile])
		os.environ['MMGEN_BOGUS_SEND'] = '1'
		t.expect('OK? (Y/n): ','y') # output OK?
		t.expect('OK? (Y/n): ','y') # fee OK?
		t.do_comment(False,has_label=True)
		t.passphrase('MMGen wallet',rt_pw)
		t.written_to_file('Signed transaction')
		self.txsend_ui_common(t,caller='txdo',bogus_send=False,file_desc='Signed transaction')
		t.read()
		return t

	def bob_rbf_bump(self):
		ext = ',{}]{x}.testnet.sigtx'.format(rtFee[1][:-1],x='-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,delete=False,no_dot=True)
		return self.user_txbump('bob',txfile,rtFee[2],'c')

	def generate(self,coin=None,num_blocks=1):
		int(num_blocks)
		if coin: opt.coin = coin
		t = self.spawn('mmgen-regtest',['generate',str(num_blocks)])
		t.expect('Mined {} block'.format(num_blocks))
		return t

	def _get_mempool(self):
		disable_debug()
		ret = self.spawn('mmgen-regtest',['show_mempool']).read()
		restore_debug()
		from ast import literal_eval
		return literal_eval(ret.split('\n')[0]) # allow for extra output by handler at end

	def get_mempool1(self):
		mp = self._get_mempool()
		if len(mp) != 1:
			rdie(2,'Mempool has more or less than one TX!')
		self.write_to_tmpfile('rbf_txid',mp[0]+'\n')
		return 'ok'

	def get_mempool2(self):
		if not g.proto.cap('rbf'):
			msg('Skipping post-RBF mempool check'); return 'skip'
		mp = self._get_mempool()
		if len(mp) != 1:
			rdie(2,'Mempool has more or less than one TX!')
		chk = self.read_from_tmpfile('rbf_txid')
		if chk.strip() == mp[0]:
			rdie(2,'TX in mempool has not changed!  RBF bump failed')
		return 'ok'

	@staticmethod
	def _gen_pairs(n):
		disable_debug()
		ret = [subprocess.check_output(
						['python3',joinpath('cmds','mmgen-tool'),'--testnet=1'] +
						(['--type=compressed'],[])[i==0] +
						['-r0','randpair']
					).decode().split() for i in range(n)]
		restore_debug()
		return ret

	def bob_pre_import(self):
		pairs = self._gen_pairs(5)
		self.write_to_tmpfile('non-mmgen.keys','\n'.join([a[0] for a in pairs])+'\n')
		self.write_to_tmpfile('non-mmgen.addrs','\n'.join([a[1] for a in pairs])+'\n')
		return self.user_txdo('bob',rtFee[4],[pairs[0][1]],'3')

	def user_import(self,user,args):
		t = self.spawn('mmgen-addrimport',['--quiet','--'+user]+args)
		if g.debug:
			t.expect("Type uppercase 'YES' to confirm: ",'YES\n')
		t.expect('Importing')
		t.expect('OK')
		return t

	def bob_import_addr(self):
		addr = self.read_from_tmpfile('non-mmgen.addrs').split()[0]
		return self.user_import('bob',['--rescan','--address='+addr])

	def bob_import_list(self):
		addrfile = joinpath(self.tmpdir,'non-mmgen.addrs')
		return self.user_import('bob',['--addrlist',addrfile])

	def bob_split2(self):
		addrs = self.read_from_tmpfile('non-mmgen.addrs').split()
		amts = (1.12345678,2.87654321,3.33443344,4.00990099,5.43214321)
		outputs1 = list(map('{},{}'.format,addrs,amts))
		sid = self._user_sid('bob')
		l1,l2 = (':S',':B') if 'B' in g.proto.mmtypes else (':S',':S') if g.proto.cap('segwit') else (':L',':L')
		outputs2 = [sid+':C:2,6.333', sid+':L:3,6.667',sid+l1+':4,0.123',sid+l2+':5']
		return self.user_txdo('bob',rtFee[5],outputs1+outputs2,'1-2')

	def user_add_label(self,user,addr,label):
		t = self.spawn('mmgen-tool',['--'+user,'add_label',addr,label])
		t.expect('Added label.*in tracking wallet',regex=True)
		return t

	def user_remove_label(self,user,addr):
		t = self.spawn('mmgen-tool',['--'+user,'remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		return t

	def bob_add_label(self):
		sid = self._user_sid('bob')
		return self.user_add_label('bob',sid+':C:1',utf8_label)

	def alice_add_label1(self):
		sid = self._user_sid('alice')
		return self.user_add_label('alice',sid+':C:1','Original Label - 月へ')

	def alice_add_label2(self):
		sid = self._user_sid('alice')
		return self.user_add_label('alice',sid+':C:1','Replacement Label')

	def alice_add_label_coinaddr(self):
		mmaddr = self._user_sid('alice') + ':C:2'
		t = self.spawn('mmgen-tool',['--alice','listaddress',mmaddr],no_msg=True)
		btcaddr = [i for i in t.read().splitlines() if i.lstrip()[0:len(mmaddr)] == mmaddr][0].split()[1]
		return self.user_add_label('alice',btcaddr,'Label added using coin address')

	def alice_chk_label_coinaddr(self):
		sid = self._user_sid('alice')
		return self.user_chk_label('alice',sid+':C:2','Label added using coin address')

	def alice_add_label_badaddr(self,addr,reply):
		t = self.spawn('mmgen-tool',['--alice','add_label',addr,'(none)'])
		t.expect(reply,regex=True)
		return t

	def alice_add_label_badaddr1(self):
		return self.alice_add_label_badaddr(rt_pw,'Invalid coin address for this chain: '+rt_pw)

	def alice_add_label_badaddr2(self):
		addr = g.proto.pubhash2addr(b'00'*20,False) # mainnet zero address
		return self.alice_add_label_badaddr(addr,'Invalid coin address for this chain: '+addr)

	def alice_add_label_badaddr3(self):
		addr = self._user_sid('alice') + ':C:123'
		return self.alice_add_label_badaddr(addr,
			"MMGen address '{}' not found in tracking wallet".format(addr))

	def alice_add_label_badaddr4(self):
		addr = CoinProtocol(g.coin,True).pubhash2addr(b'00'*20,False) # testnet zero address
		return self.alice_add_label_badaddr(addr,
			"Address '{}' not found in tracking wallet".format(addr))

	def alice_bal_rpcfail(self):
		addr = self._user_sid('alice') + ':C:2'
		os.environ['MMGEN_RPC_FAIL_ON_COMMAND'] = 'listunspent'
		t = self.spawn('mmgen-tool',['--alice','getbalance'])
		os.environ['MMGEN_RPC_FAIL_ON_COMMAND'] = ''
		t.expect('Method not found')
		t.read()
		t.req_exit_val = 3
		return t

	def alice_remove_label1(self):
		sid = self._user_sid('alice')
		return self.user_remove_label('alice',sid+':C:1')

	def user_chk_label(self,user,addr,label,label_pat=None):
		t = self.spawn('mmgen-tool',['--'+user,'listaddresses','all_labels=1'])
		t.expect(r'{}\s+\S{{30}}\S+\s+{}\s+'.format(addr,(label_pat or label)),regex=True)
		return t

	def alice_chk_label1(self):
		sid = self._user_sid('alice')
		return self.user_chk_label('alice',sid+':C:1','Original Label - 月へ')

	def alice_chk_label2(self):
		sid = self._user_sid('alice')
		return self.user_chk_label('alice',sid+':C:1','Replacement Label')

	def alice_edit_label1(self):
		return self.user_edit_label('alice','1',utf8_label)

	def alice_chk_label3(self):
		sid = self._user_sid('alice')
		return self.user_chk_label('alice',sid+':C:1',utf8_label,label_pat=utf8_label_pat)

	def alice_chk_label4(self):
		sid = self._user_sid('alice')
		return self.user_chk_label('alice',sid+':C:1','-')

	def user_edit_label(self,user,output,label):
		t = self.spawn('mmgen-txcreate',['-B','--'+user,'-i'])
		t.expect(r'add \[l\]abel:.','M',regex=True)
		t.expect(r'add \[l\]abel:.','l',regex=True)
		t.expect(r"Enter unspent.*return to main menu\):.",output+'\n',regex=True)
		t.expect(r"Enter label text.*return to main menu\):.",label+'\n',regex=True)
		t.expect(r'\[q\]uit view, .*?:.','q',regex=True)
		return t

	def stop(self):
		if opt.no_daemon_stop:
			self.spawn('',msg_only=True)
			msg_r('(leaving daemon running by user request)')
			return 'ok'
		else:
			return self.spawn('mmgen-regtest',['stop'])
