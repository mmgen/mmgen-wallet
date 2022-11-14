#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>

"""
test.objattrtest_py_d.oat_btc_mainnet: BTC mainnet test vectors for MMGen data objects
"""

from .oat_common import *
from mmgen.protocol import init_proto
from mmgen.amt import BTCAmt

proto = init_proto('btc',need_amt=True)

sample_objs.update({
	'PrivKey':   PrivKey(proto,seed_bin,compressed=True,pubkey_type='std'),
	'WifKey':    WifKey(proto,'5HwzecKMWD82ppJK3qMKpC7ohXXAwcyAN5VgdJ9PLFaAzpBG4sX'),
	'CoinAddr':  CoinAddr(proto,'1111111111111111111114oLvT2'),
	'BTCAmt':    BTCAmt('0.01'),
	'MMGenID':   MMGenID(proto,'F00F00BB:B:1'),
	'TwMMGenID': TwMMGenID(proto,'F00F00BB:S:23'),
})

tests = {
	# addr.py
	'AddrListEntry': atd({
		'addr':          (0b001, CoinAddr),
		'idx':           (0b001, AddrIdx),
		'comment':       (0b101, TwComment),
		'sec':           (0b001, PrivKey),
#		'viewkey':       (0b001, ViewKey),        # TODO
#		'wallet_passwd': (0b001, WalletPassword), # TODO
		},
		(proto,),
		{}
	),
	'PasswordListEntry': atd({
		'passwd': (0b001, str),
		'idx':    (0b001, AddrIdx),
		'comment':(0b101, TwComment),
		'sec':    (0b001, PrivKey),
		},
		(proto,),
		{'passwd':'ΑlphaΩmega', 'idx':1 },
	),
	# obj.py
	'PrivKey': atd({
		'compressed': (0b001, bool),
		'wif':        (0b001, WifKey),
		},
		(proto,seed_bin),
		{'compressed':True, 'pubkey_type':'std'},
	),
	'MMGenAddrType': atd({
		'name':        (0b001, str),
		'pubkey_type': (0b001, str),
		'compressed':  (0b001, bool),
		'gen_method':  (0b001, str),
		'addr_fmt':    (0b001, str),
		'wif_label':   (0b001, str),
		'extra_attrs': (0b001, tuple),
		'desc':        (0b001, str),
		},
		(proto,'S'),
		{},
	),
	# seed.py
	'SeedBase': atd({
		'data': (0b001, bytes),
		'sid':  (0b001, SeedID),
		},
		[seed_bin],
		{},
	),
	'SubSeed': atd({
		'idx':    (0b001, int),
		'nonce':  (0b001, int),
		'ss_idx': (0b001, SubSeedIdx),
		},
		[sample_objs['SubSeedList'],1,1,'short'],
		{},
	),
	'SeedShareList': atd({
		'count':  (0b001, SeedShareCount),
		'id_str': (0b001, SeedSplitIDString),
		},
		[sample_objs['Seed'],sample_objs['SeedShareCount']],
		{},
	),
	'SeedShareLast': atd({
		'idx': (0b001, SeedShareIdx),
		},
		[sample_objs['SeedShareList']],
		{},
	),
	'SeedShareMaster': atd({
		'idx':   (0b001, MasterShareIdx),
		'nonce': (0b001, int),
		},
		[sample_objs['SeedShareList'],7,0],
		{},
	),
	'SeedShareMasterJoining': atd({
		'id_str': (0b001, SeedSplitIDString),
		'count':  (0b001, SeedShareCount),
		},
		[sample_objs['MasterShareIdx'], sample_objs['Seed'], 'foo', 2],
		{},
	),
	# twuo.py
	'BitcoinTwUnspentOutputs.MMGenTwUnspentOutput': atd({
		'txid':         (0b001, CoinTxID),
		'vout':         (0b001, int),
		'amt':          (0b001, BTCAmt),
		'amt2':         (0b001, BTCAmt),
		'comment':      (0b101, TwComment),
		'twmmid':       (0b001, TwMMGenID),
		'addr':         (0b001, CoinAddr),
		'confs':        (0b001, int),
		'scriptPubKey': (0b001, HexStr),
		'skip':         (0b101, str),
		},
		(proto,),
		{
			'amt':BTCAmt('0.01'),
			'twmmid':'F00F00BB:B:17',
			'addr':'1111111111111111111114oLvT2',
			'confs': 100000,
			'scriptPubKey':'ff',
		},
	),
	# tx.py
	'Base.Input': atd({
		'vout':         (0b001, int),
		'amt':          (0b001, BTCAmt),
		'comment':      (0b101, TwComment),
		'mmid':         (0b001, MMGenID),
		'addr':         (0b001, CoinAddr),
		'confs':        (0b001, int),
		'txid':         (0b001, CoinTxID),
		'have_wif':     (0b011, bool),
		'scriptPubKey': (0b001, HexStr),
		'sequence':     (0b001, int),
		},
		(proto,),
		{ 'amt':BTCAmt('0.01'), 'addr':sample_objs['CoinAddr'] },
	),
	'Base.Output': atd({
		'vout':         (0b001, int),
		'amt':          (0b001, BTCAmt),
		'comment':      (0b101, TwComment),
		'mmid':         (0b001, MMGenID),
		'addr':         (0b001, CoinAddr),
		'confs':        (0b001, int),
		'txid':         (0b001, CoinTxID),
		'have_wif':     (0b011, bool),
		'is_chg':       (0b001, bool),
		},
		(proto,),
		{ 'amt':BTCAmt('0.01'), 'addr':sample_objs['CoinAddr'] },
	),
}

tests['MMGenPasswordType'] = atd(tests['MMGenAddrType'].attrs, [proto,'P'], {})
