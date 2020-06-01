#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_btc_mainnet: BTC mainnet test vectors for MMGen data objects
"""

from mmgen.obj import *
from mmgen.seed import *
from .ot_common import *

from mmgen.protocol import init_proto
proto = init_proto('btc')
tw_pfx = proto.base_coin.lower() + ':'

ssm = str(SeedShareCount.max_val)

tests = {
	'Int': {
		'arg1': 'n',
		'bad':  ('1L',0.0,'0.0','1.0',1.0,'s',1.1,'1.1'),
		'good': (
			('0',0),('-1',-1),('7',7),-1,0,1,9999999,
			{'n':'0x0','base':16,'ret':0},
			{'n':'0x1','base':16,'ret':1},
			{'n':'0xf','base':16,'ret':15},
			{'n':'0xff','base':16,'ret':255},
		)
	},
	'AddrIdx': {
		'arg1': 'n',
		'bad':  ('s',1.1,10000000,-1,0),
		'good': (('7',7),(1,1),(9999999,9999999))
	},
	'SeedShareIdx': {
		'arg1': 'n',
		'bad':  ('s',1.1,1025,-1,0),
		'good': (('7',7),(1,1),(1024,1024))
	},
	'SeedShareCount': {
		'arg1': 'n',
		'bad':  ('s',2.1,1025,-1,0,1),
		'good': (('7',7),(2,2),(1024,1024))
	},
	'MasterShareIdx': {
		'arg1': 'n',
		'bad':  ('s',1.1,1025,-1,0),
		'good': (('7',7),(1,1),(1024,1024))
	},
	'AddrIdxList': {
		'arg1': 'fmt_str',
		'bad':  ('x','5,9,1-2-3','8,-11','66,3-2'),
		'good': (
			('3,2,2',[2,3]),
			('101,1,3,5,2-7,99',[1,2,3,4,5,6,7,99,101]),
			({'idx_list':AddrIdxList('1-5')},[1,2,3,4,5])
		)
	},
	'SubSeedIdxRange': {
		'bad':  (33,'x','-11','66,3','0','3-2','8000000','100000000',(1,2,3)),
		'good': (
			('3',(3,3)),
			((3,5),(3,5)),
			('1-2',(1,2)),
			(str(g.subseeds),(g.subseeds,g.subseeds)),
			(str(SubSeedIdxRange.max_idx),(SubSeedIdxRange.max_idx,SubSeedIdxRange.max_idx)),
		)
	},
	'BTCAmt': {
		'arg1': 'num',
		'bad':  ('-3.2','0.123456789',123,'123L','22000000',20999999.12345678,
					{'num':'1','from_decimal':True},
					{'num':1,'from_decimal':True},
				),
		'good': (('20999999.12345678',Decimal('20999999.12345678')),
				{'num':Decimal('1.23456789623456789'),'from_decimal':True,'ret':Decimal('1.23456790')}, # rounding
				{'num':Decimal('1.234'),'from_decimal':True,'ret':Decimal('1.234')},
				{'num':Decimal('0.0'),'from_decimal':True,'ret':Decimal('0')},
				# emulate network fee estimation:
				#                  BTC/kB         tx_fee_adj       tx size
				{   'num':Decimal('0.00053249') * Decimal('0.9') * 109 / 1024 , # ≈53 sat/byte
					'from_decimal':True,
					'ret':Decimal('0.00005101') },
				{   'num':Decimal('0.00003249') * Decimal('1.1') * 109 / 1024 , # ≈3 sat/byte
					'from_decimal':True,
					'ret':Decimal('0.00000380') },
				{   'num':Decimal('0.00011249') * Decimal('1.0') * 221 / 1024 , # ≈11 sat/byte
					'from_decimal':True,
					'ret':Decimal('0.00002428') },
				{'num':1234,'from_unit':'satoshi','ret':Decimal('0.00001234')},
		)
	},
	'CoinAddr': {
		'arg1': 'addr',
		'good':  (
			{'addr':'1MjjELEy6EJwk8fSNfpS8b5teFRo4X5fZr', 'proto':proto},
			{'addr':'32GiSWo9zJQgkCmjAaLRrbPwXhKry2jHhj', 'proto':proto},
		),
		'bad':  (
			{'addr':1,   'proto':proto},
			{'addr':'x', 'proto':proto},
			{'addr':'я', 'proto':proto},
		),
	},
	'SeedID': {
		'arg1': 'sid',
		'bad':  (
			{'sid':'я'},
			{'sid':'F00F00'},
			{'sid':'xF00F00x'},
			{'sid':1},
			{'sid':'F00BAA123'},
			{'sid':'f00baa12'},
			'я',r32,'abc'
			),
		'good': (
			{'sid':'F00BAA12'},
			{'seed': Seed(r16),    'ret': SeedID(seed=Seed(r16))},
			{'sid': Seed(r16).sid, 'ret': SeedID(seed=Seed(r16))}
			)
	},
	'SubSeedIdx': {
		'arg1': 's',
		'bad':  (33,'x','я','1x',200,'1ss','L','s','200LS','30ll','s100',str(SubSeedIdxRange.max_idx+1),'0'),
		'good': (('1','1L'),('1s','1S'),'20S','30L',('300l','300L'),('200','200L'),str(SubSeedIdxRange.max_idx)+'S')
	},
	'MMGenID': {
		'arg1': 'id_str',
		'bad':  (
			{'id_str':'x',             'proto':proto},
			{'id_str':1,               'proto':proto},
			{'id_str':'f00f00f',       'proto':proto},
			{'id_str':'a:b',           'proto':proto},
			{'id_str':'x:L:3',         'proto':proto},
			{'id_str':'F00BAA12',      'proto':proto},
			{'id_str':'F00BAA12:Z:99', 'proto':proto},
		),
		'good':  (
			{'id_str':'F00BAA12:99',   'proto':proto, 'ret':'F00BAA12:L:99'},
			{'id_str':'F00BAA12:L:99', 'proto':proto},
			{'id_str':'F00BAA12:S:99', 'proto':proto},
		),
	},
	'TwMMGenID': {
		'arg1': 'id_str',
		'bad':  (
			{'id_str':'x',             'proto':proto},
			{'id_str':'я',             'proto':proto},
			{'id_str':'я:я',           'proto':proto},
			{'id_str':1,               'proto':proto},
			{'id_str':'f00f00f',       'proto':proto},
			{'id_str':'a:b',           'proto':proto},
			{'id_str':'x:L:3',         'proto':proto},
			{'id_str':'F00BAA12:0',    'proto':proto},
			{'id_str':'F00BAA12:Z:99', 'proto':proto},
			{'id_str':tw_pfx,          'proto':proto},
			{'id_str':tw_pfx+'я',      'proto':proto},
		),
		'good':  (
			{'id_str':tw_pfx+'x',           'proto':proto},
			{'id_str':'F00BAA12:99',        'proto':proto, 'ret':'F00BAA12:L:99'},
			{'id_str':'F00BAA12:L:99',      'proto':proto},
			{'id_str':'F00BAA12:S:9999999', 'proto':proto},
		),
	},
	'TwLabel': {
		'arg1': 'proto',
		'exc_name': 'BadTwLabel',
		'bad':  (
			{'text':'x x',           'proto':proto},
			{'text':'x я',           'proto':proto},
			{'text':'я:я',           'proto':proto},
			{'text':1,               'proto':proto},
			{'text':'f00f00f',       'proto':proto},
			{'text':'a:b',           'proto':proto},
			{'text':'x:L:3',         'proto':proto},
			{'text':'F00BAA12:0 x',  'proto':proto},
			{'text':'F00BAA12:Z:99', 'proto':proto},
			{'text':tw_pfx+' x',     'proto':proto},
			{'text':tw_pfx+'я x',    'proto':proto},
			{'text':utf8_ctrl[:40],  'proto':proto},
			{'text':'F00BAA12:S:1 '+ utf8_ctrl[:40], 'proto':proto, },
		),
		'good':  (
			{'text':'F00BAA12:99 a comment',            'proto':proto, 'ret':'F00BAA12:L:99 a comment'},
			{'text':'F00BAA12:L:99 a comment',          'proto':proto},
			{'text': 'F00BAA12:L:99 comment (UTF-8) α', 'proto':proto},
			{'text':'F00BAA12:S:9999999 comment',       'proto':proto},
			{'text':tw_pfx+'x comment',                 'proto':proto},
		),
	},
	'MMGenTxID': {
		'arg1': 's',
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00','F00F0012'),
		'good': ('DEADBE','F00BAA')
	},
	'CoinTxID':{
		'arg1': 's',
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00','F00F0012',r16.hex(),r32.hex()+'ee'),
		'good': (r32.hex(),)
	},
	'WifKey': {
		'arg1': 'proto',
		'bad': (
			{'proto':proto, 'wif':1},
			{'proto':proto, 'wif':[]},
			{'proto':proto, 'wif':'\0'},
			{'proto':proto, 'wif':'\1'},
			{'proto':proto, 'wif':'я'},
			{'proto':proto, 'wif':'g'},
			{'proto':proto, 'wif':'gg'},
			{'proto':proto, 'wif':'FF'},
			{'proto':proto, 'wif':'f00'},
			{'proto':proto, 'wif':r16.hex()},
			{'proto':proto, 'wif':'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'},
		),
		'good': (
			{'proto':proto, 'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb',  'ret_idx':1},
			{'proto':proto, 'wif':'KwWr9rDh8KK5TtDa3HLChEvQXNYcUXpwhRFUPc5uSNnMtqNKLFhk', 'ret_idx':1},
		)
	},
	'PubKey': {
		'arg1': 's',
		'bad':  ({'arg':1,'compressed':False},{'arg':'F00BAA12','compressed':False},),
		'good': ({'arg':'deadbeef','compressed':True},) # TODO: add real pubkeys
	},
	'PrivKey': {
		'arg1': 'proto',
		'bad': (
			{'proto':proto, 'wif':1},
			{'proto':proto, 'wif':'1'},
			{'proto':proto, 'wif':'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'},
			{'proto':proto, 's':r32,'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'proto':proto, 'pubkey_type':'std'},
			{'proto':proto, 's':r32},
			{'proto':proto, 's':r32,'compressed':'yes'},
			{'proto':proto, 's':r32,'compressed':'yes','pubkey_type':'std'},
			{'proto':proto, 's':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'proto':proto, 's':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'proto':proto, 'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb',
			'ret':'e0aef965b905a2fedf907151df8e0a6bac832aa697801c51f58bd2ecb4fd381c'},
			{'proto':proto, 'wif':'KwWr9rDh8KK5TtDa3HLChEvQXNYcUXpwhRFUPc5uSNnMtqNKLFhk',
			'ret':'08d0ed83b64b68d56fa064be48e2385060ed205be2b1e63cd56d218038c3a05f'},
			{'proto':proto, 's':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'proto':proto, 's':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	},
	'AddrListID': { # a rather pointless test, but do it anyway
		'arg1': 'sid',
		'bad':  (
			{'sid':SeedID(sid='F00BAA12'),'mmtype':'Z','ret':'F00BAA12:Z'},
		),
		'good':  (
			{'sid':SeedID(sid='F00BAA12'),'mmtype':proto.addr_type(id_str='S'),'ret':'F00BAA12:S'},
			{'sid':SeedID(sid='F00BAA12'),'mmtype':proto.addr_type(id_str='L'),'ret':'F00BAA12:L'},
		)
	},
	'MMGenWalletLabel': {
		'arg1': 's',
		'bad': (utf8_text[:49],utf8_combining[:48],utf8_ctrl[:48],gr_uc_w_ctrl),
		'good':  (utf8_text[:48],)
	},
	'TwComment': {
		'exc_name': 'BadTwComment',
		'arg1': 's',
		'bad': (    utf8_combining[:40],
					utf8_ctrl[:40],
					text_jp[:41],
					text_zh[:41],
					gr_uc_w_ctrl,
					utf8_text[:81] ),
		'good': (   utf8_text[:80],
					(ru_uc + gr_uc + utf8_text)[:80],
					text_jp[:40],
					text_zh[:40] )
	},
	'MMGenTxLabel':{
		'arg1': 's',
		'bad': (utf8_text[:73],utf8_combining[:72],utf8_ctrl[:72],gr_uc_w_ctrl),
		'good':  (utf8_text[:72],)
	},
	'MMGenPWIDString': { # forbidden = list(u' :/\\')
		'arg1': 's',
		'bad': ('foo/','foo:','foo:\\'),
		'good': ('qwerty@яяя',)
	},
	'MMGenAddrType': {
		'arg1': 'proto',
		'bad':  (
			{'proto':proto, 'id_str':'U',        'ret':'L'},
			{'proto':proto, 'id_str':'z',        'ret':'L'},
			{'proto':proto, 'id_str':'xx',       'ret':'C'},
			{'proto':proto, 'id_str':'dogecoin', 'ret':'C'},
		),
		'good':  (
			{'proto':proto, 'id_str':'legacy',    'ret':'L'},
			{'proto':proto, 'id_str':'L',         'ret':'L'},
			{'proto':proto, 'id_str':'compressed','ret':'C'},
			{'proto':proto, 'id_str':'C',         'ret':'C'},
			{'proto':proto, 'id_str':'segwit',    'ret':'S'},
			{'proto':proto, 'id_str':'S',         'ret':'S'},
			{'proto':proto, 'id_str':'bech32',    'ret':'B'},
			{'proto':proto, 'id_str':'B',         'ret':'B'}
		)
	},
	'MMGenPasswordType': {
		'arg1': 'proto',
		'bad':  (
			{'proto':proto, 'id_str':'U',        'ret':'L'},
			{'proto':proto, 'id_str':'z',        'ret':'L'},
			{'proto':proto, 'id_str':'я',        'ret':'C'},
			{'proto':proto, 'id_str':1,          'ret':'C'},
			{'proto':proto, 'id_str':'passw0rd', 'ret':'C'},
		),
		'good': (
			{'proto':proto, 'id_str':'password', 'ret':'P'},
			{'proto':proto, 'id_str':'P',        'ret':'P'},
		)
	},
	'SeedSplitSpecifier': {
		'arg1': 's',
		'bad': ('M','αβ:2',1,'0:1','1:1','2:1','3:2','1:2000','abc:0:2'),
		'good': (
			('1:2','2:2','alice:2:2','αβ:2:2','1:'+ssm,ssm+':'+ssm)
		)
	},
}
