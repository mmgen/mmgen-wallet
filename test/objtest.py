#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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

import sys,os,re

from include.tests_header import repo_root
from test.overlay import overlay_setup
sys.path.insert(0,overlay_setup(repo_root))

os.environ['MMGEN_TEST_SUITE'] = '1'

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.obj import *
from mmgen.altcoins.eth.obj import *
from mmgen.seedsplit import *
from mmgen.addr import *
from mmgen.addrlist import *
from mmgen.addrdata import *
from mmgen.amt import *
from mmgen.key import *
from mmgen.rpc import IPPort

opts_data = {
	'sets': [('super_silent', True, 'silent', True)],
	'text': {
		'desc': 'Test MMGen data objects',
		'usage':'[options] [object]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long options (common options)
-g, --getobj       Instantiate objects with get_obj() wrapper
-q, --quiet        Produce quieter output
-s, --silent       Silence output of tested objects
-S, --super-silent Silence all output except for errors
-v, --verbose      Produce more verbose output
"""
	}
}

cmd_args = opts.init(opts_data)

def run_test(test,arg,input_data,arg1,exc_name):
	arg_copy = arg
	kwargs = {}
	ret_chk = arg
	ret_idx = None
	if input_data == 'good' and type(arg) == tuple:
		arg,ret_chk = arg
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
		if 'exc_name' in arg:
			exc_name = arg['exc_name']
			del arg['exc_name']
			del arg_copy['exc_name']
		if 'ret_idx' in arg:
			ret_idx = arg['ret_idx']
			del arg['ret_idx']
			del arg_copy['ret_idx']
		kwargs.update(arg)
	elif type(arg) == tuple:
		args = arg
	else:
		args = [arg]

	if opt.getobj:
		if args:
			assert len(args) == 1, 'objtest_chk1: only one positional arg is allowed'
			kwargs.update( { arg1: args[0] } )
		if opt.silent:
			kwargs.update( { 'silent': True } )

	try:
		if not opt.super_silent:
			arg_disp = repr(arg_copy[0] if type(arg_copy) == tuple else arg_copy)
			if g.test_suite_deterministic and isinstance(arg_copy,dict):
				arg_disp = re.sub(r'object at 0x[0-9a-f]+','object at [SCRUBBED]',arg_disp)
			msg_r((green if input_data=='good' else orange)(f'{arg_disp+":":<22}'))
		cls = globals()[test]

		if opt.getobj:
			ret = get_obj(globals()[test],**kwargs)
		else:
			ret = cls(*args,**kwargs)

		bad_ret = list() if issubclass(cls,list) else None

		if isinstance(ret_chk,str): ret_chk = ret_chk.encode()
		if isinstance(ret,str): ret = ret.encode()

		if opt.getobj:
			if input_data == 'bad':
				assert ret == False, 'non-False return on bad input data'
		else:
			if (opt.silent and input_data=='bad' and ret!=bad_ret) or (not opt.silent and input_data=='bad'):
				raise UserWarning(f"Non-'None' return value {ret!r} with bad input data")

		if opt.silent and input_data=='good' and ret==bad_ret:
			raise UserWarning("'None' returned with good input data")

		if input_data=='good':
			if ret_idx:
				ret_chk = arg[list(arg.keys())[ret_idx]].encode()
			if ret != ret_chk and repr(ret) != repr(ret_chk):
				raise UserWarning(f"Return value ({ret!r}) doesn't match expected value ({ret_chk!r})")

		if opt.super_silent:
			return

		if opt.getobj and (not opt.silent and input_data == 'bad'):
			pass
		else:
			try: ret_disp = ret.decode()
			except: ret_disp = ret
			msg(f'==> {ret_disp!r}')

		if opt.verbose and issubclass(cls,MMGenObject):
			ret.pmsg() if hasattr(ret,'pmsg') else pmsg(ret)

	except Exception as e:
		if input_data == 'good':
			raise ValueError('Error on good input data')
		if not type(e).__name__ == exc_name:
			msg(f'Incorrect exception: expected {exc_name} but got {type(e).__name__}')
			raise
		if opt.super_silent:
			pass
		elif opt.silent:
			msg(f'==> {exc_name}')
		else:
			msg( yellow(f' {exc_name}:') + str(e) )
	except SystemExit as e:
		if input_data == 'good':
			raise ValueError('Error on good input data')
		if opt.verbose:
			msg(f'exitval: {e.code}')
	except UserWarning as e:
		msg(f'==> {ret!r}')
		die(2,red(str(e)))

def do_loop():
	import importlib
	modname = f'test.objtest_py_d.ot_{proto.coin.lower()}_{proto.network}'
	test_data = importlib.import_module(modname).tests
	gmsg(f'Running data object tests for {proto.coin} {proto.network}')

	clr = None
	utests = cmd_args
	for test in test_data:
		arg1 = test_data[test].get('arg1')
		if utests and test not in utests: continue
		nl = ('\n','')[bool(opt.super_silent) or clr == None]
		clr = (blue,nocolor)[bool(opt.super_silent)]

		if opt.getobj and arg1 is None:
			msg(gray(f'{nl}Skipping {test}'))
			continue
		else:
			msg(clr(f'{nl}Testing {test}'))

		for k in ('bad','good'):
			if not opt.super_silent:
				msg(purple(capfirst(k)+' input:'))
			for arg in test_data[test][k]:
				run_test(
					test,
					arg,
					input_data = k,
					arg1       = arg1,
					exc_name   = test_data[test].get('exc_name') or ('ObjectInitError','None')[k=='good'],
				)

from mmgen.protocol import init_proto_from_opts
proto = init_proto_from_opts()
do_loop()
