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
test/objtest.py: Test MMGen data objects
"""

import os, re

try:
	from include import test_init
except ImportError:
	from test.include import test_init

# for objtest, violate MMGen Project best practices and allow use of the dev tools
# in production code:
from mmgen.devtools import pmsg
if not os.getenv('MMGEN_DEVTOOLS'):
	from mmgen.devinit import init_dev
	init_dev()

from mmgen.cfg import Config
from mmgen.util import msg, msg_r, gmsg, capfirst, die
from mmgen.color import red, yellow, blue, green, orange, purple, gray, nocolor
from mmgen.obj import get_obj

opts_data = {
	'sets': [('super_silent', True, 'silent', True)],
	'text': {
		'desc': 'Test MMGen data objects',
		'usage':'[options] [object]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long (global) options
-g, --getobj       Instantiate objects with get_obj() wrapper
-q, --quiet        Produce quieter output
-s, --silent       Silence output of tested objects
-S, --super-silent Silence all output except for errors
-v, --verbose      Produce more verbose output
"""
	}
}

cfg = Config(opts_data=opts_data)

if cfg.verbose:
	from mmgen.objmethods import MMGenObject

from test.include.common import set_globals
set_globals(cfg)

def run_test(mod, test, arg, input_data, arg1, exc_name):

	arg_copy, ret_chk, ret_idx, kwargs = (arg, arg, None, {})

	if input_data == 'good' and isinstance(arg, tuple):
		arg, ret_chk = arg

	match arg:
		case dict(): # pass one arg + kwargs to constructor
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
			if 'exc_name' in arg:
				exc_name = arg['exc_name']
				del arg['exc_name']
				del arg_copy['exc_name']
			if 'ret_idx' in arg:
				ret_idx = arg['ret_idx']
				del arg['ret_idx']
				del arg_copy['ret_idx']
			kwargs.update(arg)
		case tuple():
			args = arg
		case _:
			args = [arg]

	if cfg.getobj:
		if args:
			assert len(args) == 1, 'objtest_chk1: only one positional arg is allowed'
			kwargs.update( { arg1: args[0] } )
		if cfg.silent:
			kwargs.update( { 'silent': True } )

	try:
		if not cfg.super_silent:
			arg_disp = repr(arg_copy[0] if isinstance(arg_copy, tuple) else arg_copy)
			if cfg.test_suite_deterministic and isinstance(arg_copy, dict):
				arg_disp = re.sub(r'object at 0x[0-9a-f]+', 'object at [SCRUBBED]', arg_disp)
			msg_r((green if input_data=='good' else orange)(f'{arg_disp+":":<22}'))
		cls = getattr(mod, test)

		if cfg.getobj:
			ret = get_obj(getattr(mod, test), **kwargs)
		else:
			ret = cls(*args, **kwargs)

		bad_ret = [] if issubclass(cls, list) else None

		if isinstance(ret_chk, str):
			ret_chk = ret_chk.encode()

		if isinstance(ret, str):
			ret = ret.encode()

		if cfg.getobj:
			if input_data == 'bad':
				assert ret is False, 'non-False return on bad input data'
		else:
			if (cfg.silent and input_data=='bad' and ret!=bad_ret) or (not cfg.silent and input_data=='bad'):
				raise UserWarning(f"Non-'None' return value {ret!r} with bad input data")

		if cfg.silent and input_data=='good' and ret==bad_ret:
			raise UserWarning("'None' returned with good input data")

		if input_data=='good':
			if ret_idx:
				ret_chk = arg[list(arg.keys())[ret_idx]].encode()
			if ret != ret_chk and repr(ret) != repr(ret_chk):
				raise UserWarning(f"Return value ({ret!r}) doesn't match expected value ({ret_chk!r})")

		if cfg.super_silent:
			return

		if cfg.getobj and (not cfg.silent and input_data == 'bad'):
			pass
		else:
			try:
				ret_disp = ret.decode()
			except:
				ret_disp = ret
			msg(f'==> {ret_disp!r}')

		if cfg.verbose and issubclass(cls, MMGenObject):
			ret.pmsg() if hasattr(ret, 'pmsg') else pmsg(ret)

	except UserWarning as e:
		msg(f'==> {ret!r}')
		die(2, red(str(e)))
	except Exception as e:
		if input_data == 'good':
			raise ValueError(f'Error on good input data: {e}') from e
		if not type(e).__name__ == exc_name:
			msg(f'Incorrect exception: expected {exc_name} but got {type(e).__name__}')
			raise
		if cfg.super_silent:
			pass
		elif cfg.silent:
			msg(f'==> {exc_name}')
		else:
			msg( yellow(f' {exc_name}:') + str(e) )
	except SystemExit as e:
		if input_data == 'good':
			raise ValueError('Error on good input data') from e
		if cfg.verbose:
			msg(f'exitval: {e.code}')

def do_loop():
	import importlib
	modname = f'test.objtest_d.{proto.coin.lower()}_{proto.network}'
	mod = importlib.import_module(modname)
	test_data = getattr(mod, 'tests')
	gmsg(f'Running data object tests for {proto.coin} {proto.network}')

	clr = None
	utests = cfg._args
	for test in test_data:
		arg1 = test_data[test].get('arg1')
		if utests and test not in utests:
			continue
		nl = ('\n', '')[bool(cfg.super_silent) or clr is None]
		clr = (blue, nocolor)[bool(cfg.super_silent)]

		if cfg.getobj and arg1 is None:
			msg(gray(f'{nl}Skipping {test}'))
			continue

		msg(clr(f'{nl}Testing {test}'))

		for k in ('bad', 'good'):
			if not cfg.super_silent:
				msg(purple(capfirst(k)+' input:'))
			for arg in test_data[test][k]:
				run_test(
					mod,
					test,
					arg,
					input_data = k,
					arg1       = arg1,
					exc_name   = test_data[test].get('exc_name') or ('ObjectInitError', 'None')[k=='good'])

proto = cfg._proto

if __name__ == '__main__':
	do_loop()
