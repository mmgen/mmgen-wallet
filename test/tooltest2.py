#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
test/tooltest2.py: Test the 'mmgen-tool' utility
"""

# TODO: move all non-interactive 'mmgen-tool' tests in 'cmdtest.py' here
# TODO: move all(?) tests in 'tooltest.py' here (or duplicate them?)

import sys, os, time, importlib, asyncio
from subprocess import run, PIPE

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from test.include.common import set_globals, end_msg, init_coverage

from mmgen import main_tool
from mmgen.cfg import Config
from mmgen.color import green, blue, purple, cyan, gray
from mmgen.util import msg, msg_r, Msg, die, isAsync

skipped_tests = ['mn2hex_interactive']
coin_dependent_groups = ('Coin', 'File')

opts_data = {
	'text': {
		'desc': "Simple test suite for the 'mmgen-tool' utility",
		'usage':'[options] [command]...',
		'options': """
-h, --help           Print this help message
-a, --no-altcoin     Skip altcoin tests
-A, --tool-api       Test the tool_api subsystem
-C, --coverage       Produce code coverage info using trace module
-d, --die-on-missing Abort if no test data found for given command
--, --longhelp       Print help message for long (global) options
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

from test.tooltest2_d.data import *

def fork_cmd(cmd_name, args, opts, stdin_input):
	cmd = (
		tool_cmd_preargs +
		tool_cmd +
		(opts or []) +
		[cmd_name] + args
	)
	vmsg('{} {}'.format(
		green('Executing'),
		cyan(' '.join(cmd))))
	cp = run(cmd, input=stdin_input or None, stdout=PIPE, stderr=PIPE)
	try:
		cmd_out = cp.stdout.decode()
	except:
		cmd_out = cp.stdout
	if cp.stderr:
		vmsg(cp.stderr.strip().decode())
	if cp.returncode != 0:
		import re
		m = re.search(b'tool command returned (None|False)', cp.stderr)
		if m:
			return eval(m.group(1))
		else:
			die(2, f'Spawned program exited with error: {cp.stderr}')

	return cmd_out.strip()

def call_method(cls, method, cmd_name, args, mmtype, stdin_input):
	vmsg('{a}: {b}{c}'.format(
		a = purple('Running'),
		b = ' '.join([cmd_name]+[repr(e) for e in args]),
		c = ' '+mmtype if mmtype else ''))
	aargs, kwargs = main_tool.process_args(cmd_name, args, cls)
	oq_save = bool(cfg.quiet)
	if not cfg.verbose:
		cfg._set_quiet(True)
	if stdin_input:
		fd0, fd1 = os.pipe()
		if os.fork(): # parent
			os.close(fd1)
			stdin_save = os.dup(0)
			os.dup2(fd0, 0)
			cmd_out = method(*aargs, **kwargs)
			os.dup2(stdin_save, 0)
			os.wait()
			cfg._set_quiet(oq_save)
			return cmd_out
		else: # child
			os.close(fd0)
			os.write(fd1, stdin_input)
			vmsg(f'Input: {stdin_input!r}')
			sys.exit(0)
	else:
		ret = asyncio.run(method(*aargs, **kwargs)) if isAsync(method) else method(*aargs, **kwargs)
		cfg._set_quiet(oq_save)
		return ret

def tool_api(cls, cmd_name, args, opts):
	from mmgen.tool.api import tool_api
	tool = tool_api(cfg)
	if opts:
		for o in opts:
			if o.startswith('--type='):
				tool.addrtype = o.split('=')[1]
	pargs, kwargs = main_tool.process_args(cmd_name, args, cls)
	return getattr(tool, cmd_name)(*pargs, **kwargs)

def check_output(out, chk):

	match chk:
		case str():
			chk = chk.encode()

	match out:
		case int():
			out = str(out).encode()
		case str():
			out = out.encode()

	try:
		outd = out.decode()
	except:
		outd = None

	err_fs = "Output ({!r}) doesn't match expected output ({!r})"

	match type(chk).__name__:
		case 'NoneType':
			pass
		case 'function':
			assert chk(outd), f'{chk.__name__}({outd}) failed!'
		case 'dict':
			for k, v in chk.items():
				match k:
					case 'boolfunc':
						assert v(outd), f'{v.__name__}({outd}) failed!'
					case 'value':
						assert outd == v, err_fs.format(outd, v)
					case _:
						if (outval := getattr(__builtins__, k)(out)) != v:
							die(1, f'{k}({out}) returned {outval}, not {v}!')
		case _:
			assert out == chk, err_fs.format(out, chk)

def run_test(cls, gid, cmd_name):
	data = tests[gid][cmd_name]

	# behavior is like cmdtest.py: run coin-dependent tests only if proto.testnet or proto.coin != BTC
	if gid in coin_dependent_groups:
		k = '{}_{}'.format(
			(cfg.token.lower() if proto.tokensym else proto.coin.lower()),
			proto.network)
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
		cmd_name if cfg.names else docstring_head(getattr(cls, cmd_name)),
		m2)

	msg_r(green(m)+'\n' if cfg.verbose else m)
	skipping = False

	for n, d in enumerate(data):
		args, out, opts, mmtype = d + tuple([None] * (4-len(d)))
		if 'fmt=xmrseed' in args and cfg.no_altcoin:
			if not skipping:
				qmsg('')
			skip_msg = f'Skipping altcoin test {cmd_name} {args}'
			qmsg(('' if n else '\n') + gray(skip_msg if len(skip_msg) <= 100 else skip_msg[:97] + '...'))
			skipping = True
			continue
		skipping = False
		stdin_input = None
		if args and isinstance(args[0], bytes):
			stdin_input = args[0]
			args[0] = '-'

		if cfg.tool_api:
			if args and args[0]== '-':
				continue
			cmd_out = tool_api(cls, cmd_name, args, opts)
		elif cfg.fork:
			cmd_out = fork_cmd(cmd_name, args, opts, stdin_input)
		else:
			if stdin_input and sys.platform == 'win32':
				msg(gray('Skipping for MSWin - no os.fork()'))
				continue
			method = getattr(cls(cfg, cmdname=cmd_name, proto=proto, mmtype=mmtype), cmd_name)
			cmd_out = call_method(cls, method, cmd_name, args, mmtype, stdin_input)

		try:
			vmsg(f'Output:\n{cmd_out}\n')
		except:
			vmsg(f'Output:\n{cmd_out!r}\n')

		if isinstance(out, tuple) and type(out[0]).__name__ == 'function':
			func_out = out[0](cmd_out)
			assert func_out == out[1], (
				'{}({}) == {} failed!\nOutput: {}'.format(
					out[0].__name__,
					cmd_out,
					out[1],
					func_out))
		elif isinstance(out, list | tuple):
			for co, o in zip(cmd_out.split(NL) if cfg.fork else cmd_out, out):
				check_output(co, o)
		else:
			check_output(cmd_out, out)

		if not cfg.verbose:
			msg_r('.')

	if not cfg.verbose:
		msg('OK')

def docstring_head(obj):
	return obj.__doc__.strip().split('\n')[0] if obj.__doc__ else None

def do_group(gid):
	desc = f'command group {gid!r}'
	cls = main_tool.get_mod_cls(gid.lower())
	qmsg(blue('Testing ' +
		desc if cfg.names else
		(docstring_head(cls) or desc)
	))

	for cmdname in cls(cfg).user_commands:
		if cmdname in skipped_tests:
			continue
		if cmdname not in tests[gid]:
			m = f'No test for command {cmdname!r} in group {gid!r}!'
			if cfg.die_on_missing:
				die(1, m+'  Aborting')
			else:
				msg(m)
				continue
		run_test(cls, gid, cmdname)

def do_cmd_in_group(cmdname):
	cls = main_tool.get_cmd_cls(cmdname)
	for gid, cmds in tests.items():
		for cmd in cmds:
			if cmd == cmdname:
				run_test(cls, gid, cmdname)
				return True
	return False

def list_tested_cmds():
	for gid in tests:
		Msg('\n'.join(tests[gid]))

def main():
	if cfg._args:
		for cmd in cfg._args:
			if cmd in tests:
				do_group(cmd)
			else:
				if not do_cmd_in_group(cmd):
					die(1, f'{cmd!r}: not a recognized test or test group')
	else:
		for garg in tests:
			do_group(garg)

qmsg = cfg._util.qmsg
vmsg = cfg._util.vmsg

proto = cfg._proto

if cfg.tool_api:
	del tests['Wallet']
	del tests['File']

if cfg.list_tests:
	Msg('Available tests:')
	for modname, cmdlist in main_tool.mods.items():
		cls = getattr(importlib.import_module(f'mmgen.tool.{modname}'), 'tool_cmd')
		Msg(f'  {modname:6} - {docstring_head(cls)}')
	sys.exit(0)

if cfg.list_tested_cmds:
	list_tested_cmds()
	sys.exit(0)

tool_exec = os.path.relpath(os.path.join('cmds', 'mmgen-tool'))

if cfg.fork:
	passthru_args = ['coin', 'type', 'testnet', 'token']
	tool_cmd = [tool_exec, '--skip-cfg-file'] + [
		'--{}{}'.format(
			k.replace('_', '-'),
			'='+getattr(cfg, k) if getattr(cfg, k) is not True else '')
		for k in passthru_args if getattr(cfg, k)]

	if cfg.coverage:
		d, f = init_coverage()
		tool_cmd_preargs = ['python3', '-m', 'trace', '--count', '--coverdir='+d, '--file='+f]
	else:
		tool_cmd_preargs = ['python3', 'scripts/exec_wrapper.py']

from mmgen.main import launch
start_time = int(time.time())
launch(func=main)
end_msg(int(time.time()) - start_time)
