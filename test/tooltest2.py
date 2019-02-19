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

opts_data = lambda: {
	'desc': "Simple test suite for the 'mmgen-tool' utility",
	'usage':'[options] [command]',
	'options': """
-h, --help          Print this help message
-C, --coverage      Produce code coverage info using trace module
--, --longhelp      Print help message for long options (common options)
-l, --list-tests    List the tests in this test suite
-L, --list-tested-cmds Output the 'mmgen-tool' commands that are tested by this test suite
-n, --names         Print command names instead of descriptions
-s, --system        Test scripts and modules installed on system rather than
                    those in the repo root
-f, --fork          Run commands via tool executable instead of importing tool module
-t, --traceback     Run tool inside traceback script
-v, --verbose       Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

tests = (
	('util', 'base conversion, hashing and file utilities',
		(
			('b58chktohex','conversion from base58chk to hex',
				[   (   ['eFGDJPketnz'], 'deadbeef' ),
					(   ['5CizhNNRPYpBjrbYX'], 'deadbeefdeadbeef' ),
					(   ['5qCHTcgbQwprzjWrb'], 'ffffffffffffffff' ),
					(   ['111111114FCKVB'], '0000000000000000' ),
					(   ['3QJmnh'], '' ),
					(   ['1111111111111111111114oLvT2'], '000000000000000000000000000000000000000000' ),
				]),
			('hextob58chk','conversion from hex to base58chk',
				[   (   ['deadbeef'], 'eFGDJPketnz' ),
					(   ['deadbeefdeadbeef'], '5CizhNNRPYpBjrbYX' ),
					(   ['ffffffffffffffff'], '5qCHTcgbQwprzjWrb' ),
					(   ['0000000000000000'], '111111114FCKVB' ),
					(   [''], '3QJmnh' ),
					(   ['000000000000000000000000000000000000000000'], '1111111111111111111114oLvT2' ),
				]),
			('bytespec',"conversion of 'dd'-style byte specifier to bytes",
				[   (   ['1G'], str(1024*1024*1024) ),
					(   ['1234G'], str(1234*1024*1024*1024) ),
					(   ['1GB'], str(1000*1000*1000) ),
					(   ['1234GB'], str(1234*1000*1000*1000) ),
					(   ['1.234MB'], str(1234*1000) ),
					(   ['1.234567M'], str(int(Decimal('1.234567')*1024*1024)) ),
					(   ['1234'], str(1234) ),
				]),
		),
	),
	('wallet', 'MMGen wallet operations',
		(
			('gen_key','generation of single key from wallet',
				[   (   ['98831F3A:11','wallet=test/ref/98831F3A.mmwords'],
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
					),]),
			('gen_addr','generation of single address from wallet',
				[   (   ['98831F3A:11','wallet=test/ref/98831F3A.mmwords'],
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
					),]),
		),
	),
)

def do_cmd(cdata):
	cmd_name,desc,data = cdata
	m = 'Testing {}'.format(cmd_name if opt.names else desc)
	msg_r(green(m)+'\n' if opt.verbose else m)
	for args,out in data:
		if opt.fork:
			cmd = list(tool_cmd) + [cmd_name] + args
			vmsg('{} {}'.format(green('Executing'),cyan(' '.join(cmd))))
			p = Popen(cmd,stdout=PIPE,stderr=PIPE)
			cmd_out = p.stdout.read()
			cmd_err = p.stderr.read()
			if cmd_err: vmsg(cmd_err.strip().decode())
			if p.wait() != 0:
				die(1,'Spawned program exited with error')
		else:
			vmsg('{}: {}'.format(purple('Running'),' '.join([cmd_name]+args)))
			aargs,kwargs = tool._process_args(cmd_name,args)
			cmd_out = tool._get_result(getattr(tc,cmd_name)(*aargs,**kwargs))
		if type(out) == str:
			cmd_out = cmd_out.strip()
			if opt.fork:
				cmd_out = cmd_out.decode()
			vmsg('Output: {}\n'.format(cmd_out))
		else:
			vmsg('Output: {}\n'.format(repr(cmd_out)))
		assert cmd_out == out,"Output ({}) doesn't match expected output ({})".format(cmd_out,out)
		if not opt.verbose: msg_r('.')
	if not opt.verbose:
		msg('OK')

def do_group(garg):
	gid,gdesc,gdata = garg
	msg(blue("Testing {}".format("command group '{}'".format(gid) if opt.names else gdesc)))
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

	if opt.traceback:
		tool_cmd = (os.path.join('scripts','traceback_run.py'),) + tool_cmd

	if opt.coverage:
		d,f = init_coverage()
		tool_cmd = ('python3','-m','trace','--count','--coverdir='+d,'--file='+f) + tool_cmd
	elif g.platform == 'win':
		tool_cmd = ('python3') + tool_cmd
else:
	opt.quiet = True
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
