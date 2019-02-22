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
test/tooltest2.py:  Simple tests for the 'mmgen-tool' utility
"""

# TODO: move all non-interactive 'mmgen-tool' tests in 'test.py' here
# TODO: move all(?) tests in 'tooltest.py' here (or duplicate them?)

import sys,os,time
from subprocess import Popen,PIPE
from decimal import Decimal

repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path[0] = repo_root
os.environ['MMGEN_TEST_SUITE'] = '1'

# Import these _after_ prepending repo_root to sys.path
from mmgen.common import *
from mmgen.test import *
from mmgen.obj import is_wif,is_coin_addr

opts_data = lambda: {
	'desc': "Simple test suite for the 'mmgen-tool' utility",
	'usage':'[options] [command]',
	'options': """
-h, --help           Print this help message
-C, --coverage       Produce code coverage info using trace module
-d, --coin-dependent Run only coin-dependent tests
-D, --non-coin-dependent Run only non-coin-dependent tests
--, --longhelp       Print help message for long options (common options)
-l, --list-tests     List the tests in this test suite
-L, --list-tested-cmds Output the 'mmgen-tool' commands that are tested by this test suite
-n, --names          Print command names instead of descriptions
-q, --quiet          Produce quieter output
-s, --system         Test scripts and modules installed on system rather than
                     those in the repo root
-t, --type=          Specify coin type
-f, --fork           Run commands via tool executable instead of importing tool module
-t, --traceback      Run tool inside traceback script
-v, --verbose        Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

tests = (
	('util', 'base conversion, hashing and file utilities',
		(
			('b58chktohex','conversion from base58chk to hex', [
				( ['eFGDJPketnz'], 'deadbeef' ),
				( ['5CizhNNRPYpBjrbYX'], 'deadbeefdeadbeef' ),
				( ['5qCHTcgbQwprzjWrb'], 'ffffffffffffffff' ),
				( ['111111114FCKVB'], '0000000000000000' ),
				( ['3QJmnh'], '' ),
				( ['1111111111111111111114oLvT2'], '000000000000000000000000000000000000000000' ),
			]),
			('hextob58chk','conversion from hex to base58chk', [
				( ['deadbeef'], 'eFGDJPketnz' ),
				( ['deadbeefdeadbeef'], '5CizhNNRPYpBjrbYX' ),
				( ['ffffffffffffffff'], '5qCHTcgbQwprzjWrb' ),
				( ['0000000000000000'], '111111114FCKVB' ),
				( [''], '3QJmnh' ),
				( ['000000000000000000000000000000000000000000'], '1111111111111111111114oLvT2' ),
			]),
			('bytespec',"conversion of 'dd'-style byte specifier to bytes", [
				( ['1G'], str(1024*1024*1024) ),
				( ['1234G'], str(1234*1024*1024*1024) ),
				( ['1GB'], str(1000*1000*1000) ),
				( ['1234GB'], str(1234*1000*1000*1000) ),
				( ['1.234MB'], str(1234*1000) ),
				( ['1.234567M'], str(int(Decimal('1.234567')*1024*1024)) ),
				( ['1234'], str(1234) ),
			]),
		),
	),
	('wallet', 'MMGen wallet operations',
		(
			('gen_key','generation of single key from wallet', [
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
			]),
			('gen_addr','generation of single address from wallet', [
				(   ['98831F3A:11','wallet=test/ref/98831F3A.mmwords'],
					'12bYUGXS8SRArZneQDN9YEEYAtEa59Rykm'
				),
				(   ['98831F3A:L:11','wallet=test/ref/98831F3A.mmwords'],
					'12bYUGXS8SRArZneQDN9YEEYAtEa59Rykm'
				),
				(   ['98831F3A:C:11','wallet=test/ref/98831F3A.mmwords'],
					'1MPsZ7BY9qikqfPxqmrovE8gLDX2rYArZk'
				),
				(   ['98831F3A:B:11','wallet=test/ref/98831F3A.mmwords'],
					'bc1qxptlvmwaymaxa7pxkr2u5pn7c0508stcncv7ms'
				),
				(   ['98831F3A:S:11','wallet=test/ref/98831F3A.mmwords'],
					'3Eevao3DRVXnYym3tdrJDqS3Wc39PQzahn'
				),
			]),
		),
	),
	('cryptocoin', 'coin-dependent utilities',
		(
			('randwif','random WIF key', {
				'btc_mainnet': [ ( [], is_wif, ['-r0'] ) ],
				'btc_testnet': [ ( [], is_wif, ['-r0'] ) ],
			}),
			('randpair','random key/address pair', {
				'btc_mainnet': [ ( [], [is_wif,is_coin_addr], ['-r0'] ) ],
				'btc_testnet': [ ( [], [is_wif,is_coin_addr], ['-r0'] ) ],
			}),
			('wif2addr','WIF-to-address conversion', {
				'btc_mainnet': [
					( ['5JKLcdYbhP6QQ4BXc9HtjfqJ79FFRXP2SZTKUyEuyXJo9QSFUkv'],
						'12bYUGXS8SRArZneQDN9YEEYAtEa59Rykm', ['--type=legacy'], 'opt.type="legacy"' ),
					( ['L2LwXv94XTU2HjCbJPXCFuaHjrjucGipWPWUi1hkM5EykgektyqR'],
						'1MPsZ7BY9qikqfPxqmrovE8gLDX2rYArZk', ['--type=compressed'], 'opt.type="compressed"' ),
					( ['KwmkkfC9GghnJhnKoRXRn5KwGCgXrCmDw6Uv83NzE4kJS5axCR9A'],
						'3Eevao3DRVXnYym3tdrJDqS3Wc39PQzahn', ['--type=segwit'], 'opt.type="segwit"' ),
					( ['L2K4Y9MWb5oUfKKZtwdgCm6FLZdUiWJDHjh9BYxpEvtfcXt4iM5g'],
						'bc1qxptlvmwaymaxa7pxkr2u5pn7c0508stcncv7ms', ['--type=bech32'], 'opt.type="bech32"' ),
				],
			}),
		),
	),
# TODO: compressed address files are missing
# 		'addrfile_compressed_chk': {
# 			'btc': ('A33C 4FDE F515 F5BC','6C48 AA57 2056 C8C8'),
# 			'ltc': ('3FC0 8F03 C2D6 BD19','4C0A 49B6 2DD1 1BE0'),
	('file', 'Operations with MMGen files',
		(
			('addrfile_chksum','address file checksums', {
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
					( ['test/ref/zcash/98831F3A-ZEC-C[1,31-33,500-501,1010-1011].addrs'],'903E 7225 DD86 6E01'), ],
				'zec_z_mainnet': [
					( ['test/ref/zcash/98831F3A-ZEC-Z[1,31-33,500-501,1010-1011].addrs'],'9C7A 72DC 3D4A B3AF'), ],
				'xmr_mainnet': [
					( ['test/ref/monero/98831F3A-XMR-M[1,31-33,500-501,1010-1011].addrs'],'4369 0253 AC2C 0E38'), ],
				'dash_mainnet': [
					( ['test/ref/dash/98831F3A-DASH-C[1,31-33,500-501,1010-1011].addrs'],'FBC1 6B6A 0988 4403'), ],
				'eth_mainnet': [
					( ['test/ref/ethereum/98831F3A-ETH[1,31-33,500-501,1010-1011].addrs'],'E554 076E 7AF6 66A3'), ],
				'etc_mainnet': [
					( ['test/ref/ethereum_classic/98831F3A-ETC[1,31-33,500-501,1010-1011].addrs'],
						'E97A D796 B495 E8BC'), ],
			}),
			('txview','transaction file view', {
				'btc_mainnet': [ ( ['test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'], None ), ],
				'btc_testnet': [ ( ['test/ref/0C7115[15.86255,14,tl=1320969600].testnet.rawtx'], None ), ],
				'bch_mainnet': [ ( ['test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx'], None ), ],
				'bch_testnet': [ ( ['test/ref/359FD5-BCH[6.68868,tl=1320969600].testnet.rawtx'], None ), ],
				'ltc_mainnet': [ ( ['test/ref/litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx'], None ), ],
				'ltc_testnet': [ ( ['test/ref/litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx'],
										None ), ],
				'eth_mainnet': [ ( ['test/ref/ethereum/88FEFD-ETH[23.45495,40000].rawtx'], None ), ],
				'eth_testnet': [ ( ['test/ref/ethereum/B472BD-ETH[23.45495,40000].testnet.rawtx'], None ), ],
				'mm1_mainnet': [ ( ['test/ref/ethereum/5881D2-MM1[1.23456,50000].rawtx'], None ), ],
				'mm1_testnet': [ ( ['test/ref/ethereum/6BDB25-MM1[1.23456,50000].testnet.rawtx'], None ), ],
				'etc_mainnet': [ ( ['test/ref/ethereum_classic/ED3848-ETC[1.2345,40000].rawtx'], None ), ],
			}),
		),
	),
)

def do_cmd(cdata):
	cmd_name,desc,data = cdata
	if type(data) == dict:
		if opt.non_coin_dependent: return
		k = '{}_{}net'.format((g.token.lower() if g.token else g.coin.lower()),('main','test')[g.testnet])
		if k in data:
			data = data[k]
			m2 = ' ({})'.format(k)
		else:
			msg("-- no data for {} ({}) - skipping".format(cmd_name,k))
			return
	else:
		if opt.coin_dependent: return
		m2 = ''
	m = '{} {}{}'.format(cyan('Testing'),cmd_name if opt.names else desc,m2)
	msg_r(green(m)+'\n' if opt.verbose else m)
	for d in data:
		args,out,opts,exec_code = d + tuple([None] * (4-len(d)))
		if opt.fork:
			cmd = list(tool_cmd) + (opts or []) + [cmd_name] + args
			vmsg('{} {}'.format(green('Executing'),cyan(' '.join(cmd))))
			p = Popen(cmd,stdout=PIPE,stderr=PIPE)
			cmd_out = p.stdout.read()
			if type(out) != bytes:
				cmd_out = cmd_out.strip().decode()
			cmd_err = p.stderr.read()
			if cmd_err: vmsg(cmd_err.strip().decode())
			if p.wait() != 0:
				die(1,'Spawned program exited with error')
		else:
			vmsg('{}: {}'.format(purple('Running'),' '.join([cmd_name]+args)))
			if exec_code: exec(exec_code)
			aargs,kwargs = tool._process_args(cmd_name,args)
			oq_save = opt.quiet
			if not opt.verbose: opt.quiet = True
			cmd_out = tool._process_result(getattr(tc,cmd_name)(*aargs,**kwargs))
			opt.quiet = oq_save

		if type(out) != bytes:
			cmd_out = cmd_out.strip()
			vmsg('Output: {}\n'.format(cmd_out))
		else:
			vmsg('Output: {}\n'.format(repr(cmd_out)))

		if type(out).__name__ == 'function':
			assert out(cmd_out),"{}({}) failed!".format(out.__name__,cmd_out)
		elif type(out) == list and type(out[0]).__name__ == 'function':
			for i in range(len(out)):
				s = cmd_out.split('\n')[i]
				assert out[i](s),"{}({}) failed!".format(out[i].__name__,s)
		elif out is not None:
			assert cmd_out == out,"Output ({}) doesn't match expected output ({})".format(cmd_out,out)

		if not opt.verbose: msg_r('.')
	if not opt.verbose:
		msg('OK')

def do_group(garg):
	gid,gdesc,gdata = garg
	qmsg(blue("Testing {}".format("command group '{}'".format(gid) if opt.names else gdesc)))
	for cdata in gdata:
		do_cmd(cdata)

def do_cmd_in_group(cmd):
	for g in tests:
		for cdata in g[2]:
			if cdata[0] == cmd:
				do_cmd(cdata)
				return True
	return False

def list_tested_cmds():
	for g in tests:
		for cdata in g[2]:
			Msg(cdata[0])

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cmd_args = opts.init(opts_data)

if opt.list_tests:
	Msg('Available commands:')
	for gid,gdesc,gdata in tests:
		Msg('  {:12} - {}'.format(gid,gdesc))
	sys.exit(0)

if opt.list_tested_cmds:
	list_tested_cmds()
	sys.exit(0)

if opt.system:
	tool_exec = 'mmgen-tool'
	sys.path.pop(0)
else:
	os.environ['PYTHONPATH'] = repo_root
	tool_exec = os.path.relpath(os.path.join('cmds','mmgen-tool'))

if opt.fork:
	tool_cmd = (tool_exec,'--skip-cfg-file')

	passthru_args = ['coin','type','testnet','token']
	tool_cmd += tuple(['--{}{}'.format(k.replace('_','-'),
		'='+getattr(opt,k) if getattr(opt,k) != True else ''
		) for k in passthru_args if getattr(opt,k)])

	if opt.traceback:
		tool_cmd = (os.path.join('scripts','traceback_run.py'),) + tool_cmd

	if opt.coverage:
		d,f = init_coverage()
		tool_cmd = ('python3','-m','trace','--count','--coverdir='+d,'--file='+f) + tool_cmd
	elif g.platform == 'win':
		tool_cmd = ('python3') + tool_cmd
else:
	opt.usr_randchars = 0
	import mmgen.tool as tool
	tc = tool.MMGenToolCmd()

start_time = int(time.time())

try:
	if cmd_args:
		if len(cmd_args) != 1:
			die(1,'Only one command may be specified')
		cmd = cmd_args[0]
		group = [e for e in tests if e[0] == cmd]
		if group:
			do_group(group[0])
		else:
			if not do_cmd_in_group(cmd):
				die(1,"'{}': not a recognized test or test group".format(cmd))
	else:
		for garg in tests:
			do_group(garg)
except KeyboardInterrupt:
	die(1,green('\nExiting at user request'))

t = int(time.time()) - start_time
gmsg('All requested tests finished OK, elapsed time: {:02}:{:02}'.format(t//60,t%60))
