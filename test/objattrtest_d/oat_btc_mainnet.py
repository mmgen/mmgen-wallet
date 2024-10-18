#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>

"""
test.objattrtest_d.oat_btc_mainnet: BTC mainnet test vectors for MMGen data objects
"""

from .oat_common import sample_objs, seed_bin, atd
from ..include.common import cfg
from mmgen.protocol import init_proto

proto = init_proto(cfg, 'btc', need_amt=True)

from mmgen.key import PrivKey, WifKey
from mmgen.addr import CoinAddr, MMGenID, AddrIdx, MMGenAddrType, MMGenPasswordType
from mmgen.amt import BTCAmt
from mmgen.tw.shared import TwMMGenID

sample_objs.update({
	'PrivKey':   PrivKey(proto, seed_bin, compressed=True, pubkey_type='std'),
	'WifKey':    WifKey(proto, '5HwzecKMWD82ppJK3qMKpC7ohXXAwcyAN5VgdJ9PLFaAzpBG4sX'),
	'CoinAddr':  CoinAddr(proto, '1111111111111111111114oLvT2'),
	'BTCAmt':    BTCAmt('0.01'),
	'MMGenID':   MMGenID(proto, 'F00F00BB:B:1'),
	'TwMMGenID': TwMMGenID(proto, 'F00F00BB:S:23'),
})

from mmgen.addrlist import AddrListEntry
from mmgen.passwdlist import PasswordListEntry
from mmgen.obj import TwComment, CoinTxID, HexStr
from mmgen.seed import SeedID, SeedBase
from mmgen.subseed import SubSeed, SubSeedIdx
from mmgen.seedsplit import (
	SeedShareCount,
	SeedSplitIDString,
	SeedShareIdx,
	MasterShareIdx,
	SeedShareList,
	SeedShareLast,
	SeedShareMaster,
	SeedShareMasterJoining
)
from mmgen.proto.btc.tw.unspent import BitcoinTwUnspentOutputs
from mmgen.tx.base import Base

tests = {
	# addr.py
	'AddrListEntry': atd({
		'addr':          (0b01001, CoinAddr),
		'idx':           (0b01001, AddrIdx),
		'comment':       (0b01101, TwComment),
		'sec':           (0b01001, PrivKey),
#		'viewkey':       (0b01001, ViewKey),        # TODO
#		'wallet_passwd': (0b01001, WalletPassword), # TODO
		},
		(proto,),
		{}
	),
	'PasswordListEntry': atd({
		'passwd':  (0b00001, str),
		'idx':     (0b01001, AddrIdx),
		'comment': (0b01101, TwComment),
		'sec':     (0b01001, PrivKey),
		},
		(proto,),
		{'passwd': 'ΑlphaΩmega', 'idx': 1},
	),
	# obj.py
	'PrivKey': atd({
		'compressed': (0b00001, bool),
		'wif':        (0b00001, WifKey),
		},
		(proto, seed_bin),
		{'compressed': True, 'pubkey_type': 'std'},
	),
	'MMGenAddrType': atd({
		'name':        (0b01001, str),
		'pubkey_type': (0b01001, str),
		'compressed':  (0b11001, bool),
		'gen_method':  (0b11001, str),
		'addr_fmt':    (0b11001, str),
		'wif_label':   (0b11001, str),
		'extra_attrs': (0b11001, tuple),
		'desc':        (0b01001, str),
		},
		(proto, 'S'),
		{},
	),
	# seed.py
	'SeedBase': atd({
		'data': (0b00001, bytes),
		'sid':  (0b00001, SeedID),
		},
		[cfg, seed_bin],
		{},
	),
	'SubSeed': atd({
		'idx':    (0b00001, int),
		'nonce':  (0b00001, int),
		'ss_idx': (0b01001, SubSeedIdx),
		},
		[sample_objs['SubSeedList'], 1, 1, 'short'],
		{},
	),
	'SeedShareList': atd({
		'count':  (0b01001, SeedShareCount),
		'id_str': (0b01001, SeedSplitIDString),
		},
		[sample_objs['Seed'], sample_objs['SeedShareCount']],
		{},
	),
	'SeedShareLast': atd({
		'idx': (0b01001, SeedShareIdx),
		},
		[sample_objs['SeedShareList']],
		{},
	),
	'SeedShareMaster': atd({
		'idx':   (0b01001, MasterShareIdx),
		'nonce': (0b00001, int),
		},
		[sample_objs['SeedShareList'], 7, 0],
		{},
	),
	'SeedShareMasterJoining': atd({
		'id_str': (0b01001, SeedSplitIDString),
		'count':  (0b01001, SeedShareCount),
		},
		[cfg, sample_objs['MasterShareIdx'], sample_objs['Seed'], 'foo', 2],
		{},
	),
	# twuo.py
	'BitcoinTwUnspentOutputs.MMGenTwUnspentOutput': atd({
		'txid':         (0b01001, CoinTxID),
		'vout':         (0b01001, int),
		'amt':          (0b01001, BTCAmt),
		'amt2':         (0b01001, BTCAmt),
		'comment':      (0b01101, TwComment),
		'twmmid':       (0b01001, TwMMGenID),
		'addr':         (0b01001, CoinAddr),
		'confs':        (0b00001, int),
		'scriptPubKey': (0b01001, HexStr),
		'skip':         (0b00101, str),
		},
		(proto,),
		{
			'amt': BTCAmt('0.01'),
			'twmmid': 'F00F00BB:B:17',
			'addr': '1111111111111111111114oLvT2',
			'confs': 100000,
			'scriptPubKey': 'ff',
		},
	),
	# tx.py
	'Base.Input': atd({
		'vout':         (0b01001, int),
		'amt':          (0b01001, BTCAmt),
		'comment':      (0b01101, TwComment),
		'mmid':         (0b01001, MMGenID),
		'addr':         (0b01001, CoinAddr),
		'confs':        (0b01001, int),
		'txid':         (0b01001, CoinTxID),
		'have_wif':     (0b00011, bool),
		'scriptPubKey': (0b01001, HexStr),
		'sequence':     (0b00001, int),
		},
		(proto,),
		{'amt': BTCAmt('0.01'), 'addr': sample_objs['CoinAddr']},
	),
	'Base.Output': atd({
		'vout':         (0b01001, int),
		'amt':          (0b01001, BTCAmt),
		'comment':      (0b01101, TwComment),
		'mmid':         (0b01001, MMGenID),
		'addr':         (0b01001, CoinAddr),
		'confs':        (0b01001, int),
		'txid':         (0b01001, CoinTxID),
		'have_wif':     (0b00011, bool),
		'is_chg':       (0b00001, bool),
		},
		(proto,),
		{'amt': BTCAmt('0.01'), 'addr': sample_objs['CoinAddr']},
	),
}

tests['MMGenPasswordType'] = atd(tests['MMGenAddrType'].attrs, [proto, 'P'], {})
