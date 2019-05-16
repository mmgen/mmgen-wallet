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
test/objtest.py:  Test MMGen data objects
"""

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.obj import *
from mmgen.altcoins.eth.obj import *
from mmgen.seed import *

opts_data = {
	'sets': [('super_silent', True, 'silent', True)],
	'text': {
		'desc': 'Test MMGen data objects',
		'usage':'[options] [object]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long options (common options)
-q, --quiet        Produce quieter output
-s, --silent       Silence output of tested objects
-S, --super-silent Silence all output except for errors
-v, --verbose      Produce more verbose output
"""
	}
}

cmd_args = opts.init(opts_data)

def run_test(test,arg,input_data):
	arg_copy = arg
	kwargs = {'on_fail':'silent'} if opt.silent else {}
	ret_chk = arg
	if input_data == 'good' and type(arg) == tuple: arg,ret_chk = arg
	if type(arg) == dict: # pass one arg + kwargs to constructor
		arg_copy = arg.copy()
		if 'arg' in arg:
			args = [arg['arg']]
			ret_chk = args[0]
			del arg['arg']
		else:
			args = []
			ret_chk = list(arg.values())[0] # assume only one key present
		if 'ret' in arg:
			ret_chk = arg['ret']
			del arg['ret']
			del arg_copy['ret']
		kwargs.update(arg)
	elif type(arg) == tuple:
		args = arg
	else:
		args = [arg]
	try:
		if not opt.super_silent:
			msg_r((orange,green)[input_data=='good']('{:<22}'.format(repr(arg_copy)+':')))
		cls = globals()[test]
		ret = cls(*args,**kwargs)
		bad_ret = list() if issubclass(cls,list) else None

		if issubclass(type(ret_chk),str): ret_chk = ret_chk.encode()
		if issubclass(type(ret),str): ret = ret.encode()

		if (opt.silent and input_data=='bad' and ret!=bad_ret) or (not opt.silent and input_data=='bad'):
			raise UserWarning("Non-'None' return value {} with bad input data".format(repr(ret)))
		if opt.silent and input_data=='good' and ret==bad_ret:
			raise UserWarning("'None' returned with good input data")
		if input_data=='good' and ret != ret_chk and repr(ret) != repr(ret_chk):
			raise UserWarning("Return value ({!r}) doesn't match expected value ({!r})".format(ret,ret_chk))
		if not opt.super_silent:
			msg('==> {}'.format(ret))
		if opt.verbose and issubclass(cls,MMGenObject):
			ret.pmsg() if hasattr(ret,'pmsg') else pmsg(ret)
	except SystemExit as e:
		if input_data == 'good':
			raise ValueError('Error on good input data')
		if opt.verbose:
			msg('exitval: {}'.format(e.code))
	except UserWarning as e:
		msg('==> {!r}'.format(ret))
		die(2,red('{}'.format(e.args[0])))

r32,r24,r16,r17,r18 = os.urandom(32),os.urandom(24),os.urandom(16),os.urandom(17),os.urandom(18)
tw_pfx = g.proto.base_coin.lower()+':'
utf8_text           = '[α-$ample UTF-8 text-ω]' * 10   # 230 chars, unicode types L,N,P,S,Z
utf8_text_combining = '[α-$ámple UTF-8 téxt-ω]' * 10   # L,N,P,S,Z,M
utf8_text_control   = '[α-$ample\nUTF-8\ntext-ω]' * 10 # L,N,P,S,Z,C

from collections import OrderedDict

tests = { 'BTC': {}, 'LTC': {} }

tests['BTC']['mainnet'] = OrderedDict([
	('AddrIdx', {
		'bad':  ('s',1.1,12345678,-1),
		'good': (('7',7),)
	}),
	('AddrIdxList', {
		'bad':  ('x','5,9,1-2-3','8,-11','66,3-2'),
		'good': (
			('3,2,2',[2,3]),
			('101,1,3,5,2-7,99',[1,2,3,4,5,6,7,99,101]),
			({'idx_list':AddrIdxList('1-5')},[1,2,3,4,5])
		)
	}),
	('SubSeedIdxRange', {
		'bad':  (33,'x','-11','66,3','0','3-2','8000000','100000000',(1,2,3)),
		'good': (
			('3',(3,3)),
			((3,5),(3,5)),
			('1-2',(1,2)),
			(str(g.subseeds),(g.subseeds,g.subseeds)),
			(str(SubSeedIdxRange.max_idx),(SubSeedIdxRange.max_idx,SubSeedIdxRange.max_idx)),
		)
	}),
	('BTCAmt', {
		'bad':  ('-3.2','0.123456789',123,'123L','22000000',20999999.12345678),
		'good': (('20999999.12345678',Decimal('20999999.12345678')),)
	}),
	('CoinAddr', {
		'bad':  (1,'x','я'),
		'good': ('1MjjELEy6EJwk8fSNfpS8b5teFRo4X5fZr','32GiSWo9zJQgkCmjAaLRrbPwXhKry2jHhj'),
	}),
	('SeedID', {
		'bad':  (
			{'sid':'я'},
			{'sid':'F00F00'},
			{'sid':'xF00F00x'},
			{'sid':1},
			{'sid':'F00BAA123'},
			{'sid':'f00baa12'},
			'я',r32,'abc'),
		'good': (({'sid':'F00BAA12'},'F00BAA12'),(Seed(r16),Seed(r16).sid))
	}),
	('SubSeedIdx', {
		'bad':  (33,'x','я','1x',200,'1ss','L','s','200LS','30ll','s100',str(SubSeedIdxRange.max_idx+1),'0'),
		'good': (('1','1L'),('1s','1S'),'20S','30L',('300l','300L'),('200','200L'),str(SubSeedIdxRange.max_idx)+'S')
	}),
	('MMGenID', {
		'bad':  ('x',1,'f00f00f','a:b','x:L:3','F00BAA12:0','F00BAA12:Z:99'),
		'good': (('F00BAA12:99','F00BAA12:L:99'),'F00BAA12:L:99','F00BAA12:S:99')
	}),
	('TwMMGenID', {
		'bad':  ('x','я','я:я',1,'f00f00f','a:b','x:L:3','F00BAA12:0','F00BAA12:Z:99',tw_pfx,tw_pfx+'я'),
		'good': (('F00BAA12:99','F00BAA12:L:99'),'F00BAA12:L:99','F00BAA12:S:9999999',tw_pfx+'x')
	}),
	('TwLabel', {
		'bad':  ('x x','x я','я:я',1,'f00f00f','a:b','x:L:3','F00BAA12:0 x',
				'F00BAA12:Z:99',tw_pfx+' x',tw_pfx+'я x'),
		'good': (
			('F00BAA12:99 a comment','F00BAA12:L:99 a comment'),
			'F00BAA12:L:99 comment (UTF-8) α',
			'F00BAA12:S:9999999 comment',
			tw_pfx+'x comment')
	}),
	('MMGenTxID', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00','F00F0012'),
		'good': ('DEADBE','F00BAA')
	}),
	('CoinTxID',{
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00','F00F0012',r16.hex(),r32.hex()+'ee'),
		'good': (r32.hex(),)
	}),
	('WifKey', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb',
				'KwWr9rDh8KK5TtDa3HLChEvQXNYcUXpwhRFUPc5uSNnMtqNKLFhk'),
	}),
	('PubKey', {
		'bad':  ({'arg':1,'compressed':False},{'arg':'F00BAA12','compressed':False},),
		'good': ({'arg':'deadbeef','compressed':True},) # TODO: add real pubkeys
	}),
	('PrivKey', {
		'bad': (
			{'wif':1},
			{'wif':'1'},
			{'wif':'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'},
			{'s':r32,'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'pubkey_type':'std'},
			{'s':r32},
			{'s':r32,'compressed':'yes'},
			{'s':r32,'compressed':'yes','pubkey_type':'std'},
			{'s':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'s':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb',
			'ret':'e0aef965b905a2fedf907151df8e0a6bac832aa697801c51f58bd2ecb4fd381c'},
			{'wif':'KwWr9rDh8KK5TtDa3HLChEvQXNYcUXpwhRFUPc5uSNnMtqNKLFhk',
			'ret':'08d0ed83b64b68d56fa064be48e2385060ed205be2b1e63cd56d218038c3a05f'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	}),
	('AddrListID', { # a rather pointless test, but do it anyway
		'bad':  (
			{'sid':SeedID(sid='F00BAA12'),'mmtype':'Z','ret':'F00BAA12:Z'},
		),
		'good':  (
			{'sid':SeedID(sid='F00BAA12'),'mmtype':MMGenAddrType('S'),'ret':'F00BAA12:S'},
			{'sid':SeedID(sid='F00BAA12'),'mmtype':MMGenAddrType('L'),'ret':'F00BAA12:L'},
		)
	}),
	('MMGenWalletLabel', {
		'bad': (utf8_text[:49],utf8_text_combining[:48],utf8_text_control[:48]),
		'good':  (utf8_text[:48],)
	}),
	('TwComment', {
		'bad': (utf8_text[:41],utf8_text_combining[:40],utf8_text_control[:40]),
		'good':  (utf8_text[:40],)
	}),
	('MMGenTXLabel',{
		'bad': (utf8_text[:73],utf8_text_combining[:72],utf8_text_control[:72]),
		'good':  (utf8_text[:72],)
	}),
	('MMGenPWIDString', { # forbidden = list(u' :/\\')
		'bad': ('foo/','foo:','foo:\\'),
		'good': ('qwerty@яяя',)
	}),
	('MMGenAddrType', {
		'bad': ('U','z','xx',1,'dogecoin'),
		'good':  (
			{'s':'legacy','ret':'L'},
			{'s':'L','ret':'L'},
			{'s':'compressed','ret':'C'},
			{'s':'C','ret':'C'},
			{'s':'segwit','ret':'S'},
			{'s':'S','ret':'S'},
			{'s':'bech32','ret':'B'},
			{'s':'B','ret':'B'}
		)
	}),
	('MMGenPasswordType', {
		'bad': ('U','z','я',1,'passw0rd'),
		'good': (
			{'s':'password','ret':'P'},
			{'s':'P','ret':'P'},
		)
	}),
	('ETHNonce', {
		'bad': ('U','z','я',-1),
		'good':  (('0',0),('1',1),('100',100),1,100)
	}),
])

tests['BTC']['testnet'] = OrderedDict([
	('CoinAddr', {
		'bad':  (1,'x','я'),
		'good': ('n2FgXPKwuFkCXF946EnoxWJDWF2VwQ6q8J','2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
	}),
	('WifKey', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('93HsQEpH75ibaUJYi3QwwiQxnkW4dUuYFPXZxcbcKds7XrqHkY6',
				'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'),
	}),
	('PrivKey', {
		'bad': (
			{'wif':1},
			{'wif':'1'},
			{'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'s':r32,'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'pubkey_type':'std'},
			{'s':r32},
			{'s':r32,'compressed':'yes'},
			{'s':r32,'compressed':'yes','pubkey_type':'std'},
			{'s':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'s':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'wif':'93HsQEpH75ibaUJYi3QwwiQxnkW4dUuYFPXZxcbcKds7XrqHkY6',
			'ret':'e0aef965b905a2fedf907151df8e0a6bac832aa697801c51f58bd2ecb4fd381c'},
			{'wif':'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR',
			'ret':'08d0ed83b64b68d56fa064be48e2385060ed205be2b1e63cd56d218038c3a05f'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	})
])

tests['LTC']['mainnet'] = OrderedDict([
	('LTCAmt', {
		'bad':  ('-3.2','0.123456789',123,'123L','88000000',80999999.12345678),
		'good': (('80999999.12345678',Decimal('80999999.12345678')),)
	}),
	('CoinAddr', {
		'bad':  (1,'x','я'),
		'good': ('LXYx4j8PDGE8GEwDFnEQhcLyHFGsRxSJwt','MEnuCzUGHaQx9fK5WYvLwR1NK4SAo8HmSr'),
	}),
	('WifKey', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('6udBAGS6B9RfGyvEQDkVDsWy3Kqv9eTULqtEfVkJtTJyHdLvojw',
				'T7kCSp5E71jzV2zEJW4q5qU1SMB5CSz8D9VByxMBkamv1uM3Jjca'),
	}),
	('PrivKey', {
		'bad': (
			{'wif':1},
			{'wif':'1'},
			{'wif':'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'},
			{'s':r32,'wif':'6ufJhtQQiRYA3w2QvDuXNXuLgPFp15i3HR1Wp8An2mx1JnhhJAh'},
			{'pubkey_type':'std'},
			{'s':r32},
			{'s':r32,'compressed':'yes'},
			{'s':r32,'compressed':'yes','pubkey_type':'std'},
			{'s':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'s':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'wif':'6ufJhtQQiRYA3w2QvDuXNXuLgPFp15i3HR1Wp8An2mx1JnhhJAh',
			'ret':'470a974ffca9fca1299b706b09142077bea3acbab6d6480b87dbba79d5fd279b'},
			{'wif':'T41Fm7J3mtZLKYPMCLVSFARz4QF8nvSDhLAfW97Ds56Zm9hRJgn8',
			'ret':'1c6feab55a4c3b4ad1823d4ecacd1565c64228c01828cf44fb4db1e2d82c3d56'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	}),
])

tests['LTC']['testnet'] = OrderedDict([
	('CoinAddr', {
		'bad':  (1,'x','я'),
		'good': ('n2D3joAy3yE5fqxUeCp38X6uPUcVn7EFw9','QN59YbnHsPQcbKWSq9PmTpjrhBnHGQqRmf')
	}),
	('WifKey', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('936Fd4qs3Zy2ZiYHH7vZ3UpT23KtCAiGiG2xBTkjHo7jE9aWA2f',
				'cQY3EumdaSNuttvDSUuPdiMYLyw8aVmYfFqxo9kdPuWbJBN4Ny66')
	}),
	('PrivKey', {
		'bad': (
			{'wif':1},
			{'wif':'1'},
			{'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'s':r32,'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'pubkey_type':'std'},
			{'s':r32},
			{'s':r32,'compressed':'yes'},
			{'s':r32,'compressed':'yes','pubkey_type':'std'},
			{'s':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'s':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'wif':'92iqzh6NqiKawyB1ronw66YtEHrU4rxRJ5T4aHniZqvuSVZS21f',
			'ret':'95b2aa7912550eacdd3844dcc14bee08ce7bc2434ad4858beb136021e945afeb'},
			{'wif':'cSaJAXBAm9ooHpVJgoxqjDG3AcareFy29Cz8mhnNTRijjv2HLgta',
			'ret':'94fa8b90c11fea8fb907c9376b919534b0a75b9a9621edf71a78753544b4101c'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	}),
])

def do_loop():
	utests = cmd_args
	network = ('mainnet','testnet')[bool(g.testnet)]
	all_tests = tests[g.coin][network]
	for test in all_tests:
		if utests and test not in utests: continue
		msg((blue,nocolor)[bool(opt.super_silent)]('Testing {}'.format(test)))
		for k in ('bad','good'):
			for arg in all_tests[test][k]:
				run_test(test,arg,input_data=k)

do_loop()
