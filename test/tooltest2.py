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
test/tooltest2.py: Simple tests for the 'mmgen-tool' utility
"""

# TODO: move all non-interactive 'mmgen-tool' tests in 'cmdtest.py' here
# TODO: move all(?) tests in 'tooltest.py' here (or duplicate them?)

import sys,os,time,importlib
from subprocess import run,PIPE
from decimal import Decimal

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from test.include.common import set_globals,end_msg,sample_text,init_coverage

from mmgen.cfg import Config
from mmgen.color import green,blue,purple,cyan
from mmgen.util import msg,msg_r,Msg,is_hex_str,async_run,die

from mmgen.bip39 import is_bip39_mnemonic
from mmgen.baseconv import is_mmgen_mnemonic,is_b58_str
from mmgen.xmrseed import is_xmrseed

skipped_tests = ['mn2hex_interactive']

NL = ('\n','\r\n')[sys.platform=='win32']

def is_str(s):
	return isinstance(s,str)

from mmgen.key import is_wif
from mmgen.addr import is_coin_addr
def is_wif_loc(s):
	return is_wif(proto,s)
def is_coin_addr_loc(s):
	return is_coin_addr(proto,s)

def md5_hash(s):
	from hashlib import md5
	return md5(s.encode()).hexdigest()

def md5_hash_strip(s):
	import re
	s = re.sub('\x1b' + r'\[[;0-9]+?m','',s) # strip ANSI color sequences
	s = s.replace(NL,'\n')             # fix DOS newlines
	return md5_hash(s.strip())

opts_data = {
	'text': {
		'desc': "Simple test suite for the 'mmgen-tool' utility",
		'usage':'[options] [command]...',
		'options': """
-h, --help           Print this help message
-A, --tool-api       Test the tool_api subsystem
-C, --coverage       Produce code coverage info using trace module
-d, --die-on-missing Abort if no test data found for given command
--, --longhelp       Print help message for long options (common options)
-l, --list-tests     List the test groups in this test suite
-L, --list-tested-cmds Output the 'mmgen-tool' commands that are tested by this test suite
-n, --names          Print command names instead of descriptions
-q, --quiet          Produce quieter output
-t, --type=          Specify coin type
-f, --fork           Run commands via tool executable instead of importing tool module
-v, --verbose        Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
	}
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cfg = Config(
	opts_data = opts_data,
	init_opts = {
		'usr_randchars': 0,
		'hash_preset': '1',
		'passwd_file': 'test/ref/keyaddrfile_password',
	})

set_globals(cfg)

sample_text_hexdump = (
	'000000: 5468 6520 5469 6d65 7320 3033 2f4a 616e{n}' +
	'000010: 2f32 3030 3920 4368 616e 6365 6c6c 6f72{n}' +
	'000020: 206f 6e20 6272 696e 6b20 6f66 2073 6563{n}' +
	'000030: 6f6e 6420 6261 696c 6f75 7420 666f 7220{n}' +
	'000040: 6261 6e6b 73').format(n=NL)

kafile_opts = ['-p1','-Ptest/ref/keyaddrfile_password']

from test.unit_tests_d.ut_baseconv import unit_test as ut_baseconv
from test.unit_tests_d.ut_bip39 import unit_test as ut_bip39
from test.unit_tests_d.ut_xmrseed import unit_test as ut_xmrseed

btc_wif1 = '5HwzecKMWD82ppJK3qMKpC7ohXXAwcyAN5VgdJ9PLFaAzpBG4sX'
btc_wif2 = 'KwojSzt1VvW343mQfWQi3J537siAt5ktL2qbuCg1ZyKR8BLQ6UJm'

privhex1 = '0000000000000000000000000000000000000000000000000000000000000001'
privhex2 = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
privhex3 = '0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
privhex4 = '00000000000000000000000000000000000000000000000000000000000000ff'
privhex5 = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0f'
privhex6 = 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef'
privhex7 = '118089d66b4a5853765e94923abdd5de4616c6e5118089d66b4a5853765e9492'

btc_addr1 = '1C5VPtgq9xQ6AcTgMAR3J6GDrs72HC4pS1'
btc_addr2 = '1Kz9fVSUMshzPejpzW9D95kScgA3rY6QxF'
btc_addr3 = '3AhjTiWHhVJAi1s5CfKMcLzYps12x3gZhg'
btc_addr4 = 'bc1q6pqnfwwakuuejpm9w52ds342f9d5u36v0qnz7c'
btc_addr5 = '12bYUGXS8SRArZneQDN9YEEYAtEa59Rykm'
btc_addr6 = 'bc1qxptlvmwaymaxa7pxkr2u5pn7c0508stcncv7ms'
btc_addr7 = '3Eevao3DRVXnYym3tdrJDqS3Wc39PQzahn'

eth_addr1 = '7e5f4552091a69125d5dfcb7b8c2659029395bdf'
eth_addr2 = 'b92702b3eefb3c2049aeb845b0335b283e11e9c6'
eth_addr3 = 'ad30adc7451c1dace34c5d1f328f8a74a4947534'
eth_addr4 = '5044a80bd3eff58302e638018534bbda8896c48a'
eth_addr5 = '8b10f977e27611516f186980d8161b25f8adca5e'
eth_addr6 = 'c96aaa54e2d44c299564da76e1cd3184a2386b8d'

xmr_addr1 = '42nsXK8WbVGTNayQ6Kjw5UdgqbQY5KCCufdxdCgF7NgTfjC69Mna7DJSYyie77hZTQ8H92G2HwgFhgEUYnDzrnLnQdF28r3'
xmr_addr2 = '49voQEbjouUQSDikRWKUt1PGbS47TBde4hiGyftN46CvTDd8LXCaimjHRGtofCJwY5Ed5QhYwc12P15AH5w7SxUAMCz1nr1'
xmr_addr3 = '45Ee1yJSjXBKuf8aaihf6KgSRGtMBN6NNDtkd9fLJzHiK4ar4NyNxDk6afc7MTRoruAsg6J6792tCJazHqs1sjbv7LuEsLx'
xmr_addr4 = '43aZyywWW4MYt2Az32XioQYirxyT8xeRBP84EBNA7Cra5SqQNmca6iD9pM487pcR9JAEiKrnw2QwvA5uWiFNokEzLJ5coZ9'
xmr_addr5 = '4AeR1owefiJGbrAdSKCbVL73ME4FGv2cpczjV2peqqkxagm5D4gBqAHJta6NpbtxyuRe3ywaTj6QCHD59savvPW69wfW9my'
xmr_addr6 = '41i7saPWA53EoHenmJVRt34dubPxsXwoWMnw8AdMyx4mTD1svf7qYzcVjxxRfteLNdYrAxWUMmiPegFW9EfoNgXx7vDMExv'

zec_addr1 = 'zceQDpyNwek7dKqF5ZuFGj7YrNVxh7X1aPkrVxDLVxWSiZAFDEuy5C7XNV8VhyZ3ghTPQ61xjCGiyLT3wqpiN1Yi6mdmaCq'
zec_addr2 = 'zcY1hqJ3P5ifjnWk1BcXpjrLG5XeJZUSPCiiVTF9LXrejxBzAsFWcNyr6PudwQHm8DnQpD8HEaM3dh8sB6cf91ciAa53YQ1'
zec_addr4 = 'zcck12KgVY34LJwVEDLN8sXhL787zmjKqPsP1uBYRHs75bL9sQu4P7wcc5ZJTjKsL376zaSpsYqGxK94JbiYcNoH8DkeGbN'
zec_addr5 = 'zcJ9hEezG1Jeye5dciqiMDh6SXtYbUsircGmpVyhHWyzyxDVRRDs5Q8M7hG3c7nDcvd5Pw4u4wV9RAQmq5RCBZq5wVyMQV8'
zec_addr6 = 'zchFELwBxqsAubsLQ8yZgPCDDGukjXJssgCbiTPwFNmFwn9haLnDatzfhLdZzJT4PcU4o2yr92B52UFirUzEdF6ZYM2gBkM'

redeem_script1 = '0014d04134b9ddb7399907657514d846aa495b4e474c'

btc_pubhex1 = '024281a85c9ce87279e028410b851410d65136304cfbbbeaaa8e2e3931cf4e9727'
btc_pubhex2 = '044281a85c9ce87279e028410b851410d65136304cfbbbeaaa8e2e3931cf4e972757f3254c322eeaa3cb6bf97cc5ecf8d4387b0df2c0b1e6ee18fe3a6977a7d57a'

eth_pubhex1 = '0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8' # Bitcoin-style '04'-prefixed pubkey
eth_pubhex2 = '9166c289b9f905e55f9e3df9f69d7f356b4a22095f894f4715714aa4b56606aff181eb966be4acb5cff9e16b66d809be94e214f06c93fd091099af98499255e7'   # raw pubkey
xmr_pubhex1 = '1ed49357e217e79dab3c5503822f2bdb561e302e24476ee6ff33242c7551d4e78944790c0cfa9998c2f196061be89b2b8387f9d397db20ea8e049899cdc947d1'
zec_pubhex1 = 'e6a4edbff547f21bcc2a825b6cf70f06e266a452d2da9d6dc5c1da3d99d7e996f488704dcdfe8d92cafe47772b3f692a98d59de1e99e00ff815f64ae59910f0c'

tests = {
	'Mnemonic': {
		'hex2mn': (
			[([a[0]],b) for a,b in ut_baseconv.vectors['mmgen']] +
			[([a,'fmt=bip39'],b) for a,b in ut_bip39.vectors] +
			[([a,'fmt=xmrseed'],b) for a,b in ut_xmrseed.vectors]
		),
		'mn2hex': (
			[([b,'fmt=mmgen'],a[0]) for a,b in ut_baseconv.vectors['mmgen']] +
			[([b,'fmt=bip39'],a) for a,b in ut_bip39.vectors] +
			[([b,'fmt=xmrseed'],a) for a,b in ut_xmrseed.vectors]
		),
		'mn_rand128': [
			( [], is_mmgen_mnemonic, ['-r0']),
			( ['fmt=mmgen'], is_mmgen_mnemonic, ['-r0']),
			( ['fmt=bip39'], is_bip39_mnemonic, ['-r0']),
		],
		'mn_rand192': [
			( ['fmt=mmgen'], is_mmgen_mnemonic, ['-r0']),
			( ['fmt=bip39'], is_bip39_mnemonic, ['-r0']),
		],
		'mn_rand256': [
			( ['fmt=mmgen'], is_mmgen_mnemonic, ['-r0']),
			( ['fmt=bip39'], is_bip39_mnemonic, ['-r0']),
			( ['fmt=xmrseed'], is_xmrseed, ['-r0']),
		],
		'mn_stats': [
			( [], is_str ),
			( ['fmt=mmgen'], is_str ),
			( ['fmt=bip39'], is_str ),
			( ['fmt=xmrseed'], is_str ),
		],
		'mn_printlist': [
			( [], is_str ),
			( ['fmt=mmgen'], is_str ),
			( ['fmt=bip39'], is_str ),
			( ['fmt=xmrseed','enum=true'], is_str ),
		],
	},
	'Util': {
		'hextob32': [
			( ['deadbeef'], 'DPK3PXP' ),
			( ['deadbeefdeadbeef'], 'N5LN657PK3PXP' ),
			( ['ffffffffffffffff'], 'P777777777777' ),
			( ['0000000000000000'], 'A' ),
			( ['0000000000000000','pad=10'], 'AAAAAAAAAA' ),
			( ['ff','pad=10'], 'AAAAAAAAH7' ),
		],
		'b32tohex': [
			( ['DPK3PXP'], 'deadbeef' ),
			( ['N5LN657PK3PXP'], 'deadbeefdeadbeef' ),
			( ['P777777777777'], 'ffffffffffffffff' ),
			( ['A','pad=16'], '0000000000000000' ),
			( ['AAAAAAAAAA','pad=16'], '0000000000000000' ),
			( ['AAAAAAAAH7','pad=2'], 'ff' ),
		],
		'hextob6d': [
			( ['deadbeef'], '25255 24636 426' ),
			( ['deadbeefdeadbeef'], '43263 51255 35545 36422 42642' ),
			( ['ffffffffffffffff'], '46316 33121 21321 15553 55534' ),
			( ['0000000000000000'], '1' ),
			( ['0000000000000000','pad=10'], '11111 11111' ),
			( ['ff','pad=10'], '11111 12214' ),
			( ['ff'*16],
				'34164 46464 12666 61652 46515 46546 53354 43666 45555 21414' ),
			( ['ff'*24],
				'24611 14114 33323 36422 24655 66552 32465 25661 21541 62342 '
				'61351 63525 45161 35543 13654' ),
			( ['ff'*32],
				'21325 21653 31261 31341 45131 42346 54146 36252 11413 12253 '
				'24246 31114 16424 56513 41632 24121 46151 43214 22425 65134' ),
		],
		'b6dtohex': [
			( ['25255 24636 426'], 'deadbeef' ),
			( ['43263 51255 35545 36422 42642'], 'deadbeefdeadbeef' ),
			( ['46316 33121 21321 15553 55534'], 'ffffffffffffffff' ),
			( ['1','pad=16'], '0000000000000000' ),
			( ['11111 11111','pad=16'], '0000000000000000' ),
			( ['11111 12214','pad=2'], 'ff' ),
			( ['22222 22222'], 'b88733' ),
			( ['66666 66666'], '039aa3ff' ),
			( ['6'*50], {
				'len': 34,
				'value':'0260154fc36cbf42778f23ffffffffffff' # 130 bits
				} ),
			( ['6'*75], {
				'len': 50,
				'value':'03a92ef1c3432e71a7679561bb6817d7ffffffffffffffffff' # 194 bits
				} ),
			( ['6'*100], {
				'len': 66,
				'value':'05a4653ca673768565b41f775d6947d55cf3813d0fffffffffffffffffffffffff' # 259 bits
				} ),
		],
		'hextob58chk': [
			( ['deadbeef'], 'eFGDJPketnz' ),
			( ['deadbeefdeadbeef'], '5CizhNNRPYpBjrbYX' ),
			( ['ffffffffffffffff'], '5qCHTcgbQwprzjWrb' ),
			( ['0000000000000000'], '111111114FCKVB' ),
			( ['00'], '1Wh4bh' ),
			( ['000000000000000000000000000000000000000000'], '1111111111111111111114oLvT2' ),
		],
		'b58chktohex': [
			( ['eFGDJPketnz'], 'deadbeef' ),
			( ['5CizhNNRPYpBjrbYX'], 'deadbeefdeadbeef' ),
			( ['5qCHTcgbQwprzjWrb'], 'ffffffffffffffff' ),
			( ['111111114FCKVB'], '0000000000000000' ),
			( ['3QJmnh'], '' ),
			( ['1111111111111111111114oLvT2'], '000000000000000000000000000000000000000000' ),
		],
		'bytestob58': [
			( [b'\xde\xad\xbe\xef'], '6h8cQN' ),
			( [b'\xde\xad\xbe\xef\xde\xad\xbe\xef'], 'eFGDJURJykA' ),
			( [b'\xff\xff\xff\xff\xff\xff\xff\xff'], 'jpXCZedGfVQ' ),
			( [b'\x00\x00\x00\x00\x00\x00\x00\x00'], '1' ),
			( [b'\x00\x00\x00\x00\x00\x00\x00\x00','pad=10'], '1111111111' ),
			( [b'\xff','pad=10'], '111111115Q' ),
		],
		'b58tobytes': [
			( ['6h8cQN'], b'\xde\xad\xbe\xef' ),
			( ['eFGDJURJykA'], b'\xde\xad\xbe\xef\xde\xad\xbe\xef' ),
			( ['jpXCZedGfVQ'], b'\xff\xff\xff\xff\xff\xff\xff\xff' ),
			( ['1','pad=8'], b'\x00\x00\x00\x00\x00\x00\x00\x00' ),
			( ['1111111111','pad=8'], b'\x00\x00\x00\x00\x00\x00\x00\x00' ),
			( ['111111115Q','pad=1'], b'\xff' ),
		],
		'hextob58': [
			( ['deadbeef'], '6h8cQN' ),
			( ['deadbeefdeadbeef'], 'eFGDJURJykA' ),
			( ['ffffffffffffffff'], 'jpXCZedGfVQ' ),
			( ['0000000000000000'], '1' ),
			( ['0000000000000000','pad=10'], '1111111111' ),
			( ['ff','pad=10'], '111111115Q' ),
		],
		'b58tohex': [
			( ['6h8cQN'], 'deadbeef' ),
			( ['eFGDJURJykA'], 'deadbeefdeadbeef' ),
			( ['jpXCZedGfVQ'], 'ffffffffffffffff' ),
			( ['1','pad=16'], '0000000000000000' ),
			( ['1111111111','pad=16'], '0000000000000000' ),
			( ['111111115Q','pad=2'], 'ff' ),
		],
		'bytespec': [
			( ['1G'],        str(1024*1024*1024) ),
			( ['1GB'],       str(1000*1000*1000) ),
			( ['1234GB'],    str(1234*1000*1000*1000) ),
			( ['1234G'],     str(1234*1024*1024*1024) ),
			( ['1234TB'],    str(1234*1000*1000*1000*1000) ),
			( ['1234T'],     str(1234*1024*1024*1024*1024) ),
			( ['1234PB'],    str(1234*1000*1000*1000*1000*1000) ),
			( ['1234P'],     str(1234*1024*1024*1024*1024*1024) ),
			( ['1234EB'],    str(1234*1000*1000*1000*1000*1000*1000) ),
			( ['1234E'],     str(1234*1024*1024*1024*1024*1024*1024) ),
			( ['1.234MB'],   str(1234*1000) ),
			( ['1.234567M'], str(int(Decimal('1.234567')*1024*1024)) ),
			( ['1234'],      str(1234) ),
		],
		'to_bytespec': [
			( [str(1024*1024*1024),'G'],                               '1.00G' ),
			( [str(1024*1024*1024),'G','fmt=0.0'],                     '1G' ),
			( [str(1024*1024*1024),'G','fmt=08.5'],                    '01.00000G' ),
			( [str(1234*1000*1000*1000),'GB'],                         '1234.00GB' ),
			( [str(1234*1000*1000*1000),'GB','strip=True'],            '1234.0GB' ),
			( [str(1234*1000*1000*1000),'GB','add_space=True'],        '1234.00 GB' ),
			( [str(1234*1024*1024*1024),'G'],                          '1234.00G', ),
			( [str(1000*1000*1000*1000*1000),'PB'],                    '1.00PB' ),
			( [str(1024*1024*1024*1024*1024),'P'],                     '1.00P' ),
			( [str(1024*1024*1024*1024*1024*1024),'E'],                '1.00E' ),
			( [str(int(Decimal('1.234567')*1024*1024)),'M','fmt=0.6'], '1.234567M' ),
			( ['1234','c','fmt=0.0','print_sym=false'],                '1234' ),
		],
		'hash160': [ # TODO: check that hextob58chk(hash160) = pubhex2addr
			( ['deadbeef'], 'f04df4c4b30d2b7ac6e1ed2445aeb12a9cb4d2ec' ),
			( ['000000000000000000000000000000000000000000'], '2db95e704e2d9b0474acf76182f3f985b7064a8a' ),
			( [''], 'b472a266d0bd89c13706a4132ccfb16f7c3b9fcb' ),
			( ['ffffffffffffffff'], 'f86221f5a1fca059a865c0b7d374dfa9d5f3aeb4' ),
		],
		'hash256': [
			( ['deadbeef'], 'e107944e77a688feae4c2d4db5951923812dd0f72026a11168104ee1b248f8a9' ),
			(
				['000000000000000000000000000000000000000000'],
				'fd5181fcd097a334ab340569e5edcd09f702fef7994abab01f4b66e86b32ebbe'
			),
			( [''], '5df6e0e2761359d30a8275058e299fcc0381534545f55cf43e41983f5d4c9456' ),
			( ['ffffffffffffffff'], '57b2d2c3455e0f76c61c5237ff04fc9fc0f3fe691e587ea9c951949e1a5e0fed' ),
		],
		'hexdump': [
			( [sample_text.encode()], sample_text_hexdump ),
		],
		'unhexdump': [
			( [sample_text_hexdump.encode()], sample_text.encode() ),
		],
		'hexlify': [
			( [b'foobar'], '666f6f626172' ),
		],
		'unhexlify': [
			( ['666f6f626172'], 'foobar' ),
		],
		'hexreverse': [
			( ['deadbeefcafe'], 'fecaefbeadde' ),
		],
		'id6': [
			( [sample_text.encode()], 'a6d72b' ),
		],
		'id8': [
			( [sample_text.encode()], '687C09C2' ),
		],
		'str2id6': [
			( ['74ev zjeq Zw2g DspF RKpE 7H'], '70413d' ), # checked
		],
		'randhex': [
			( [], {'boolfunc':is_hex_str,'len':64}, ['-r0'] ),
			( ['nbytes=16'], {'boolfunc':is_hex_str,'len':32}, ['-r0'] ),
			( ['nbytes=6'], {'boolfunc':is_hex_str,'len':12}, ['-r0'] ),
		],
		'randb58': [
			( [], {'boolfunc':is_b58_str}, ['-r0'] ),
			( ['nbytes=16'], {'boolfunc':is_b58_str}, ['-r0'] ),
			( ['nbytes=12','pad=0'], is_b58_str, ['-r0'] ),
		],
	},
	'Wallet': {
		'gen_key': [
			(   ['98831F3A:11','wallet=test/ref/98831F3A.mmwords'],
				'5JKLcdYbhP6QQ4BXc9HtjfqJ79FFRXP2SZTKUyEuyXJo9QSFUkv'
			),
			(   ['98831F3A:C:11','wallet=test/ref/98831F3A.mmwords'],
				'L2LwXv94XTU2HjCbJPXCFuaHjrjucGipWPWUi1hkM5EykgektyqR'
			),
			(   ['98831F3A:B:11','wallet=test/ref/98831F3A.mmwords'],
				'L2K4Y9MWb5oUfKKZtwdgCm6FLZdUiWJDHjh9BYxpEvtfcXt4iM5g'
			),
			(   ['98831F3A:S:11','wallet=test/ref/98831F3A.mmwords'],
				'KwmkkfC9GghnJhnKoRXRn5KwGCgXrCmDw6Uv83NzE4kJS5axCR9A'
			),
		],
		'gen_addr': [
			(   ['98831F3A:11','wallet=test/ref/98831F3A.mmwords'], btc_addr5 ),
			(   ['98831F3A:L:11','wallet=test/ref/98831F3A.mmwords'], btc_addr5 ),
			(   ['98831F3A:C:11','wallet=test/ref/98831F3A.mmwords'],
				'1MPsZ7BY9qikqfPxqmrovE8gLDX2rYArZk'
			),
			(   ['98831F3A:B:11','wallet=test/ref/98831F3A.mmwords'], btc_addr6 ),
			(   ['98831F3A:S:11','wallet=test/ref/98831F3A.mmwords'], btc_addr7 ),
		],
		'get_subseed': [
			(   ['3s','wallet=test/ref/98831F3A.mmwords'], '4018EB17' ),
			(   ['200','wallet=test/ref/98831F3A.mmwords'], '2B05AE73' ),
		],
		'get_subseed_by_seed_id': [
			(   ['4018EB17','wallet=test/ref/98831F3A.mmwords'], '3S' ),
			(   ['2B05AE73','wallet=test/ref/98831F3A.mmwords'], None ),
			(   ['2B05AE73','wallet=test/ref/98831F3A.mmwords','last_idx=200'], '200L' ),
		],
		'list_subseeds': [
			(   ['1-5','wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip,'996c047e8543d5dde6f82efc3214a6a1')
			),
		],
		'list_shares': [
			(   ['3','wallet=test/ref/98831F3A.bip39'],
				(md5_hash_strip,'84e8bdaebf9c816a8a3bd2ebec5a2e12')
			),
			(   ['3','id_str=default','wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip,'84e8bdaebf9c816a8a3bd2ebec5a2e12')
			),
			(   ['3','id_str=foo','wallet=test/ref/98831F3A.bip39'],
				(md5_hash_strip,'d2ac20823c4ea26f15234b5ca8df5d6f')
			),
			(   ['3','id_str=foo','master_share=0','wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip,'d2ac20823c4ea26f15234b5ca8df5d6f')
			),
			(   ['3','id_str=foo','master_share=5','wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip,'c4feedce40bb5959011ee4a996710832')
			),
			(   ['3','id_str=βαρ','master_share=5','wallet=test/ref/98831F3A.mmwords'],
				(md5_hash_strip,'f7d254798fe2e34b94b5f4ff312998db')
			),
			(   ['4','id_str=βαρ','master_share=5','wallet=test/ref/98831F3A.bip39'],
				(md5_hash_strip,'d3e479f55792181372a9f32a569c04e5')
			),
		],
	},
	'Coin': {
		'addr2pubhash': {
			'btc_mainnet': [
				( [ btc_addr5 ], '118089d66b4a5853765e94923abdd5de4616c6e5' ),
				( [ btc_addr6 ], '3057f66ddd26fa6ef826b0d5ca067ec3e8f3c178' ),
			],
		},
		'eth_checksummed_addr': {
			'eth_mainnet': [
				( ['00a329c0648769a73afac7f9381e08fb43dbea72'], '00a329c0648769A73afAc7F9381E08FB43dBEA72' ),
				( ['deadbeef'*5], 'DeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF' ),
				( ['ffffffff'*5], 'FFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF' ),
				( ['0'*39 + '1'], '0'*39 + '1' ),
			],
		},
		'pubhash2addr': {
			'btc_mainnet': [
				( ['118089d66b4a5853765e94923abdd5de4616c6e5'], btc_addr5, None, 'legacy' ),
				( ['8e34586186551f6320fa3eb2d238a9c61ab8264b'], '37ZBgCBjjz9WSEzp1Zjv8sqdgmNie3Kd5s',
					['--type=segwit'], 'segwit' ),
				( ['3057f66ddd26fa6ef826b0d5ca067ec3e8f3c178'], btc_addr6, ['--type=bech32'], 'bech32' ),
			],
		},
		'addr2scriptpubkey': {
			'btc_mainnet': [
				( [ btc_addr5 ], '76a914118089d66b4a5853765e94923abdd5de4616c6e588ac' ),
				( [ btc_addr7 ], 'a9148e34586186551f6320fa3eb2d238a9c61ab8264b87' ),
				( [ btc_addr6 ], '00143057f66ddd26fa6ef826b0d5ca067ec3e8f3c178' ),
			],
		},
		'scriptpubkey2addr': {
			'btc_mainnet': [
				( ['76a914118089d66b4a5853765e94923abdd5de4616c6e588ac'], btc_addr5 ),
				( ['a9148e34586186551f6320fa3eb2d238a9c61ab8264b87'], btc_addr7 ),
				( ['00143057f66ddd26fa6ef826b0d5ca067ec3e8f3c178'], btc_addr6 ),
			],
		},
		'hex2wif': {
			'btc_mainnet': [
				( [ privhex7 ], btc_wif1, None, 'legacy' ),
				( [ privhex7 ], btc_wif2, ['--type=compressed'], 'compressed' ),
				( [ privhex7 ], btc_wif2, ['--type=segwit'], 'segwit' ),
				( [ privhex7 ], btc_wif2, ['--type=bech32'], 'bech32' ),
			],
		},
		'privhex2addr': {
			'btc_mainnet': [
				( [ privhex7 ], btc_addr1, None, 'legacy' ),
				( [ privhex7 ], btc_addr2, ['--type=compressed'], 'compressed' ),
				( [ privhex7 ], btc_addr3, ['--type=segwit'], 'segwit' ),
				( [ privhex7 ], btc_addr4, ['--type=bech32'], 'bech32' ),
			],
			'eth_mainnet': [
				( [ privhex1 ], eth_addr1 ),
				( [ privhex2 ], eth_addr2 ),
				( [ privhex3 ], eth_addr3 ),
				( [ privhex4 ], eth_addr4 ),
				( [ privhex5 ], eth_addr5 ),
				( [ privhex6 ], eth_addr6 ),
			],
			'xmr_mainnet': [
				( [ privhex1 ], xmr_addr1 ),
				( [ privhex2 ], xmr_addr2 ),
				( [ privhex3 ], xmr_addr3 ),
				( [ privhex4 ], xmr_addr4 ),
				( [ privhex5 ], xmr_addr5 ),
				( [ privhex6 ], xmr_addr6 ),
			],
			'zec_mainnet': [
				( [ privhex1 ], zec_addr1, ['--type=zcash_z'], 'zcash_z' ),
				( [ privhex2 ], zec_addr2, ['--type=zcash_z'], 'zcash_z' ),
				( [ privhex3 ], zec_addr2, ['--type=zcash_z'], 'zcash_z' ),
				( [ privhex4 ], zec_addr4, ['--type=zcash_z'], 'zcash_z' ),
				( [ privhex5 ], zec_addr5, ['--type=zcash_z'], 'zcash_z' ),
				( [ privhex6 ], zec_addr6, ['--type=zcash_z'], 'zcash_z' ),
			],
		},
		'privhex2pubhex': {
			'btc_mainnet': [
				( [ privhex7 ], btc_pubhex2, None, 'legacy' ),
				( [ privhex7 ], btc_pubhex1, ['--type=compressed'], 'compressed' ),
				( [ privhex7 ], btc_pubhex1, ['--type=segwit'], 'segwit' ),
				( [ privhex7 ], btc_pubhex1, ['--type=bech32'], 'bech32' ),
			],
			'eth_mainnet': [
				( [ privhex1 ], eth_pubhex1 ),
			],
			'xmr_mainnet': [
				( [ privhex1 ], xmr_pubhex1 ),
			],
			'zec_mainnet': [
				( [ privhex1 ], zec_pubhex1, ['--type=zcash_z'], 'zcash_z' ),
			],
		},
		'pubhex2addr': {
			'btc_mainnet': [
				( [ btc_pubhex2 ], btc_addr1, None, 'legacy' ),
				( [ btc_pubhex1 ], btc_addr2, ['--type=compressed'], 'compressed' ),
				( [ btc_pubhex1 ], btc_addr3, ['--type=segwit'], 'segwit' ),
				( [ btc_pubhex1 ], btc_addr4, ['--type=bech32'], 'bech32' ),
			],
			'eth_mainnet': [
				( [ eth_pubhex1 ], eth_addr1 ),
				( [ eth_pubhex2 ], eth_addr2 ),
			],
			'xmr_mainnet': [
				( [ xmr_pubhex1 ], xmr_addr1 ),
			],
			'zec_mainnet': [
				( [ zec_pubhex1 ], zec_addr1, ['--type=zcash_z'], 'zcash_z' ),
			],
		},
		'pubhex2redeem_script': {
			'btc_mainnet': [
				( [ btc_pubhex1 ], redeem_script1, ['--type=segwit'], 'segwit' ),
			],
		},
		'redeem_script2addr': {
			'btc_mainnet': [
				( [ redeem_script1 ], btc_addr3, ['--type=segwit'], 'segwit' ),
			],
		},
		'randpair': {
			'btc_mainnet': [ ( [], [is_wif_loc,is_coin_addr_loc], ['-r0'] ) ],
			'btc_testnet': [ ( [], [is_wif_loc,is_coin_addr_loc], ['-r0'] ) ],
		},
		'randwif': {
			'btc_mainnet': [ ( [], is_wif_loc, ['-r0'] ) ],
			'btc_testnet': [ ( [], is_wif_loc, ['-r0'] ) ],
		},
		'wif2addr': {
			'btc_mainnet': [
				( [ btc_wif1 ], btc_addr1, ['--type=legacy'], 'legacy' ),
				( [ btc_wif2 ], btc_addr2, ['--type=compressed'], 'compressed' ),
				( [ btc_wif2 ], btc_addr3, ['--type=segwit'], 'segwit' ),
				( [ btc_wif2 ], btc_addr4, ['--type=bech32'], 'bech32' ),
			],
			'eth_mainnet': [
				( [ privhex1 ], eth_addr1 ),
				( ['000000000000000000000000000000014551231950b75fc4402da1732fc9bebe'], eth_addr2 ),
				( [ privhex3 ], eth_addr3 ),
				( [ privhex4 ], eth_addr4 ),
				( ['000000000000000000000000000000014551231950b75fc4402da1732fc9bdce'], eth_addr5 ),
				( [ privhex6 ], eth_addr6 ),
			],
			'xmr_mainnet': [
				( [ privhex1 ], xmr_addr1 ),
				( ['1c95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f'], xmr_addr2 ),
				( ['2c94988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0f'], xmr_addr3 ),
				( ['1d95988d7431ecd670cf7d73f45befc6feffffffffffffffffffffffffffff0e'], xmr_addr4 ),
				( [ privhex5 ], xmr_addr5 ),
				( ['e8164dda6d42bd1e261a3406b2038dcbddadbeefdeadbeefdeadbeefdeadbe0f'], xmr_addr6 ),
			],
			'zec_mainnet': [
				( ['SKxny894fJe2rmZjeuoE6GVfNkWoXfPp8337VrLLNWG56FjqVUYR'],
					zec_addr1, ['--type=zcash_z'], 'zcash_z' ),
				( ['SKxv1peuQvMT4TvqPLqKy1px3oqLm98Evi948VU8N8VKcf7C2umc'],
					zec_addr2, ['--type=zcash_z'], 'zcash_z' ),
				( ['SKxny894fJe2rmZjeuoE6GVfNkWoXfPp8337VrLLNWG56kQw4qjm'],
					zec_addr4, ['--type=zcash_z'], 'zcash_z' ),
				( ['SKxv1peuQvMT4TvqPLqKy1px3oqLm98Evi948VU8N8VKcBwrLwiu'],
					zec_addr5, ['--type=zcash_z'], 'zcash_z' ),
				( ['SKxuS56e99jpCeD9mMQ5o63zoGPakNdM9HCvt4Vt2cypvRjCdvGJ'],
					zec_addr6, ['--type=zcash_z'], 'zcash_z' ),
			],
		},
		'wif2hex': {
			'btc_mainnet': [
				( [ btc_wif1 ], privhex7, None, 'legacy' ),
				( [ btc_wif2 ], privhex7, ['--type=compressed'], 'compressed' ),
				( [ btc_wif2 ], privhex7, ['--type=segwit'], 'segwit' ),
				( [ btc_wif2 ], privhex7, ['--type=bech32'], 'bech32' ),
			],
		},
		'wif2redeem_script': {
			'btc_mainnet': [
				( [ btc_wif2 ], redeem_script1, ['--type=segwit'], 'segwit' ),
			],
		},
		'wif2segwit_pair': {
			'btc_mainnet': [
				( [ btc_wif2 ], (redeem_script1, btc_addr3), ['--type=segwit'], 'segwit' ),
			],
		},
	},
	# TODO: compressed address files are missing
	#		'addrfile_compressed_chk':
	#			'btc': ('A33C 4FDE F515 F5BC','6C48 AA57 2056 C8C8'),
	#			'ltc': ('3FC0 8F03 C2D6 BD19','4C0A 49B6 2DD1 1BE0'),
	'File': {
		'addrfile_chksum': {
			'btc_mainnet': [
				( ['test/ref/98831F3A[1,31-33,500-501,1010-1011].addrs'],
					'6FEF 6FB9 7B13 5D91'),
				( ['test/ref/98831F3A-S[1,31-33,500-501,1010-1011].addrs'],
					'06C1 9C87 F25C 4EE6'),
				( ['test/ref/98831F3A-B[1,31-33,500-501,1010-1011].addrs'],
					'9D2A D4B6 5117 F02E'),
			],
			'btc_testnet': [
				( ['test/ref/98831F3A[1,31-33,500-501,1010-1011].testnet.addrs'],
					'424E 4326 CFFE 5F51'),
				( ['test/ref/98831F3A-S[1,31-33,500-501,1010-1011].testnet.addrs'],
					'072C 8B07 2730 CB7A'),
				( ['test/ref/98831F3A-B[1,31-33,500-501,1010-1011].testnet.addrs'],
					'0527 9C39 6C1B E39A'),
			],
			'ltc_mainnet': [
				( ['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].addrs'],
					'AD52 C3FE 8924 AAF0'),
				( ['test/ref/litecoin/98831F3A-LTC-S[1,31-33,500-501,1010-1011].addrs'],
					'63DF E42A 0827 21C3'),
				( ['test/ref/litecoin/98831F3A-LTC-B[1,31-33,500-501,1010-1011].addrs'],
					'FF1C 7939 5967 AB82'),
			],
			'ltc_testnet': [
				( ['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].testnet.addrs'],
					'4EBE 2E85 E969 1B30'),
				( ['test/ref/litecoin/98831F3A-LTC-S[1,31-33,500-501,1010-1011].testnet.addrs'],
					'5DD1 D186 DBE1 59F2'),
				( ['test/ref/litecoin/98831F3A-LTC-B[1,31-33,500-501,1010-1011].testnet.addrs'],
					'ED3D 8AA4 BED4 0B40'),
			],
			'zec_mainnet': [
				( ['test/ref/zcash/98831F3A-ZEC-C[1,31-33,500-501,1010-1011].addrs'],'903E 7225 DD86 6E01'),
				( ['test/ref/zcash/98831F3A-ZEC-Z[1,31-33,500-501,1010-1011].addrs'], '9C7A 72DC 3D4A B3AF',
					['--type=zcash_z'], 'zcash_z' ),
			],
			'xmr_mainnet': [
				( ['test/ref/monero/98831F3A-XMR-M[1,31-33,500-501,1010-1011].addrs'],'4369 0253 AC2C 0E38'), ],
			'dash_mainnet': [
				( ['test/ref/dash/98831F3A-DASH-C[1,31-33,500-501,1010-1011].addrs'],'FBC1 6B6A 0988 4403'), ],
			'eth_mainnet': [
				( ['test/ref/ethereum/98831F3A-ETH[1,31-33,500-501,1010-1011].addrs'],'E554 076E 7AF6 66A3'), ],
			'etc_mainnet': [
				( ['test/ref/ethereum_classic/98831F3A-ETC[1,31-33,500-501,1010-1011].addrs'],
					'E97A D796 B495 E8BC'), ],
		},
		'viewkeyaddrfile_chksum': {
			'xmr_mainnet': [
				( ['test/ref/monero/98831F3A-XMR-M[1-3].vkeys'], '40C9 0E61 B743 229C' ),
			],
		},
		'keyaddrfile_chksum': {
			'btc_mainnet': [
				( ['test/ref/98831F3A[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'9F2D D781 1812 8BAD', kafile_opts ),
			],
			'btc_testnet': [
				( ['test/ref/98831F3A[1,31-33,500-501,1010-1011].testnet.akeys.mmenc'],
					'88CC 5120 9A91 22C2', kafile_opts ),
			],
			'ltc_mainnet': [
				( ['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'B804 978A 8796 3ED4', kafile_opts ),
			],
			'ltc_testnet': [
				( ['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].testnet.akeys.mmenc'],
					'98B5 AC35 F334 0398', kafile_opts ),
			],
			'zec_mainnet': [
				( ['test/ref/zcash/98831F3A-ZEC-C[1,31-33,500-501,1010-1011].akeys.mmenc'],
				'F05A 5A5C 0C8E 2617', kafile_opts ),
				( ['test/ref/zcash/98831F3A-ZEC-Z[1,31-33,500-501,1010-1011].akeys.mmenc'], '6B87 9B2D 0D8D 8D1E',
					kafile_opts + ['--type=zcash_z'], 'zcash_z' ),
			],
			'xmr_mainnet': [
				( ['test/ref/monero/98831F3A-XMR-M[1,31-33,500-501,1010-1011].akeys.mmenc'],
				'E0D7 9612 3D67 404A', kafile_opts ), ],
			'dash_mainnet': [
				( ['test/ref/dash/98831F3A-DASH-C[1,31-33,500-501,1010-1011].akeys.mmenc'],
				'E83D 2C63 FEA2 4142', kafile_opts ), ],
			'eth_mainnet': [
				( ['test/ref/ethereum/98831F3A-ETH[1,31-33,500-501,1010-1011].akeys.mmenc'],
				'E400 70D9 0AE3 C7C2', kafile_opts ), ],
			'etc_mainnet': [
				( ['test/ref/ethereum_classic/98831F3A-ETC[1,31-33,500-501,1010-1011].akeys.mmenc'],
				'EF49 967D BD6C FE45', kafile_opts ), ],
		},
		'passwdfile_chksum': {
			'btc_mainnet': [
				( ['test/ref/98831F3A-фубар@crypto.org-b58-20[1,4,1100].pws'],
					'DDD9 44B0 CA28 183F', kafile_opts ), ],
		},
		'txview': {
			'btc_mainnet': [ ( ['test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'], None ), ],
			'btc_testnet': [ ( ['test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx'], None ), ],
			'bch_mainnet': [ ( ['test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx'], None ), ],
			'bch_testnet': [ ( ['test/ref/359FD5-BCH[6.68868,tl=1320969600].testnet.rawtx'], None ), ],
			'ltc_mainnet': [ ( ['test/ref/litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx'], None ), ],
			'ltc_testnet': [ ( ['test/ref/litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx'],
									None ), ],
			'eth_mainnet': [ ( ['test/ref/ethereum/88FEFD-ETH[23.45495,40000].rawtx'], None ), ],
			'eth_testnet': [ ( [
				'test/ref/ethereum/B472BD-ETH[23.45495,40000].testnet.rawtx',
				'test/ref/ethereum/B472BD-ETH[23.45495,40000].testnet.sigtx'
				], None ), ],
			'mm1_mainnet': [ ( ['test/ref/ethereum/5881D2-MM1[1.23456,50000].rawtx'], None ), ],
			'mm1_testnet': [ ( ['test/ref/ethereum/6BDB25-MM1[1.23456,50000].testnet.rawtx'], None ), ],
			'etc_mainnet': [ ( ['test/ref/ethereum_classic/ED3848-ETC[1.2345,40000].rawtx'], None ), ],
		},
	},
}

coin_dependent_groups = ('Coin','File')

def fork_cmd(cmd_name,args,opts,stdin_input):
	cmd = (
		tool_cmd_preargs +
		tool_cmd +
		(opts or []) +
		[cmd_name] + args
	)
	vmsg('{} {}'.format(
		green('Executing'),
		cyan(' '.join(cmd)) ))
	cp = run(cmd,input=stdin_input or None,stdout=PIPE,stderr=PIPE)
	try:
		cmd_out = cp.stdout.decode()
	except:
		cmd_out = cp.stdout
	if cp.stderr:
		vmsg(cp.stderr.strip().decode())
	if cp.returncode != 0:
		import re
		m = re.search(b'tool command returned (None|False)',cp.stdout)
		if m:
			return { b'None': None, b'False': False }[m.group(1)]
		else:
			die(2,f'Spawned program exited with error: {cp.stderr}')

	return cmd_out.strip()

async def call_method(cls,method,cmd_name,args,mmtype,stdin_input):
	vmsg('{a}: {b}{c}'.format(
		a = purple('Running'),
		b = ' '.join([cmd_name]+[repr(e) for e in args]),
		c = ' '+mmtype if mmtype else '' ))
	aargs,kwargs = main_tool.process_args(cmd_name,args,cls)
	oq_save = bool(cfg.quiet)
	if not cfg.verbose:
		cfg.quiet = True
	if stdin_input:
		fd0,fd1 = os.pipe()
		if os.fork(): # parent
			os.close(fd1)
			stdin_save = os.dup(0)
			os.dup2(fd0,0)
			cmd_out = method(*aargs,**kwargs)
			os.dup2(stdin_save,0)
			os.wait()
			cfg.quiet = oq_save
			return cmd_out
		else: # child
			os.close(fd0)
			os.write(fd1,stdin_input)
			vmsg(f'Input: {stdin_input!r}')
			sys.exit(0)
	else:
		ret = method(*aargs,**kwargs)
		if type(ret).__name__ == 'coroutine':
			ret = await ret
		cfg.quiet = oq_save
		return ret

def tool_api(cls,cmd_name,args,opts):
	from mmgen.tool.api import tool_api
	tool = tool_api(cfg)
	if opts:
		for o in opts:
			if o.startswith('--type='):
				tool.addrtype = o.split('=')[1]
	pargs,kwargs = main_tool.process_args(cmd_name,args,cls)
	return getattr(tool,cmd_name)(*pargs,**kwargs)

def check_output(out,chk):
	if isinstance(chk,str):
		chk = chk.encode()
	if isinstance(out,int):
		out = str(out).encode()
	if isinstance(out,str):
		out = out.encode()
	err_fs = "Output ({!r}) doesn't match expected output ({!r})"
	try:
		outd = out.decode()
	except:
		outd = None

	if type(chk).__name__ == 'function':
		assert chk(outd), f'{chk.__name__}({outd}) failed!'
	elif isinstance(chk,dict):
		for k,v in chk.items():
			if k == 'boolfunc':
				assert v(outd), f'{v.__name__}({outd}) failed!'
			elif k == 'value':
				assert outd == v, err_fs.format(outd,v)
			else:
				outval = getattr(__builtins__,k)(out)
				if outval != v:
					die(1,f'{k}({out}) returned {outval}, not {v}!')
	elif chk is not None:
		assert out == chk, err_fs.format(out,chk)

async def run_test(cls,gid,cmd_name):
	data = tests[gid][cmd_name]

	# behavior is like cmdtest.py: run coin-dependent tests only if proto.testnet or proto.coin != BTC
	if gid in coin_dependent_groups:
		k = '{}_{}'.format(
			( cfg.token.lower() if proto.tokensym else proto.coin.lower() ),
			('mainnet','testnet')[proto.testnet] )
		if k in data:
			data = data[k]
			m2 = f' ({k})'
		else:
			qmsg(f'-- no data for {cmd_name} ({k}) - skipping')
			return
	else:
		if proto.coin != 'BTC' or proto.testnet:
			return
		m2 = ''

	m = '{} {}{}'.format(
		purple('Testing'),
		cmd_name if cfg.names else docstring_head(getattr(cls,cmd_name)),
		m2 )

	msg_r(green(m)+'\n' if cfg.verbose else m)

	for d in data:
		args,out,opts,mmtype = d + tuple([None] * (4-len(d)))
		stdin_input = None
		if args and isinstance(args[0],bytes):
			stdin_input = args[0]
			args[0] = '-'

		if cfg.tool_api:
			if args and args[0 ]== '-':
				continue
			cmd_out = tool_api(cls,cmd_name,args,opts)
		elif cfg.fork:
			cmd_out = fork_cmd(cmd_name,args,opts,stdin_input)
		else:
			if stdin_input and sys.platform == 'win32':
				msg('Skipping for MSWin - no os.fork()')
				continue
			method = getattr(cls(cfg,cmdname=cmd_name,proto=proto,mmtype=mmtype),cmd_name)
			cmd_out = await call_method(cls,method,cmd_name,args,mmtype,stdin_input)

		try:
			vmsg(f'Output:\n{cmd_out}\n')
		except:
			vmsg(f'Output:\n{cmd_out!r}\n')

		if isinstance(out,tuple) and type(out[0]).__name__ == 'function':
			func_out = out[0](cmd_out)
			assert func_out == out[1],(
				'{}({}) == {} failed!\nOutput: {}'.format(
					out[0].__name__,
					cmd_out,
					out[1],
					func_out ))
		elif isinstance(out,(list,tuple)):
			for co,o in zip(cmd_out.split(NL) if cfg.fork else cmd_out,out):
				check_output(co,o)
		else:
			check_output(cmd_out,out)

		if not cfg.verbose:
			msg_r('.')

	if not cfg.verbose:
		msg('OK')

def docstring_head(obj):
	return obj.__doc__.strip().split('\n')[0] if obj.__doc__ else None

async def do_group(gid):
	desc = f'command group {gid!r}'
	cls = main_tool.get_mod_cls(gid.lower())
	qmsg(blue('Testing ' +
		desc if cfg.names else
		( docstring_head(cls) or desc )
	))

	for cmdname in cls(cfg).user_commands:
		if cmdname in skipped_tests:
			continue
		if cmdname not in tests[gid]:
			m = f'No test for command {cmdname!r} in group {gid!r}!'
			if cfg.die_on_missing:
				die(1,m+'  Aborting')
			else:
				msg(m)
				continue
		await run_test(cls,gid,cmdname)

async def do_cmd_in_group(cmdname):
	cls = main_tool.get_cmd_cls(cmdname)
	for gid,cmds in tests.items():
		for cmd in cmds:
			if cmd == cmdname:
				await run_test(cls,gid,cmdname)
				return True
	return False

def list_tested_cmds():
	for gid in tests:
		Msg('\n'.join(tests[gid]))

qmsg = cfg._util.qmsg
vmsg = cfg._util.vmsg

proto = cfg._proto

if cfg.tool_api:
	del tests['Wallet']
	del tests['File']

from mmgen import main_tool

if cfg.list_tests:
	Msg('Available tests:')
	for modname,cmdlist in main_tool.mods.items():
		cls = getattr(importlib.import_module(f'mmgen.tool.{modname}'),'tool_cmd')
		Msg(f'  {modname:6} - {docstring_head(cls)}')
	sys.exit(0)

if cfg.list_tested_cmds:
	list_tested_cmds()
	sys.exit(0)

tool_exec = os.path.relpath(os.path.join('cmds','mmgen-tool'))

if cfg.fork:
	passthru_args = ['coin','type','testnet','token']
	tool_cmd = [ tool_exec, '--skip-cfg-file' ] + [
		'--{}{}'.format(
			k.replace('_','-'),
			'='+getattr(cfg,k) if getattr(cfg,k) is not True else '')
		for k in passthru_args if getattr(cfg,k) ]

	if cfg.coverage:
		d,f = init_coverage()
		tool_cmd_preargs = ['python3','-m','trace','--count','--coverdir='+d,'--file='+f]
	else:
		tool_cmd_preargs = ['python3','scripts/exec_wrapper.py']

start_time = int(time.time())

async def main():
	try:
		if cfg._args:
			for cmd in cfg._args:
				if cmd in tests:
					await do_group(cmd)
				else:
					if not await do_cmd_in_group(cmd):
						die(1,f'{cmd!r}: not a recognized test or test group')
		else:
			for garg in tests:
				await do_group(garg)
	except KeyboardInterrupt:
		die(1,green('\nExiting at user request'))

if __name__ == '__main__':
	async_run(main())
	end_msg(int(time.time()) - start_time)
