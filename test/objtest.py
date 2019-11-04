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

os.environ['MMGEN_TEST_SUITE'] = '1'

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
	kwargs = {'on_fail':'silent'} if opt.silent else {'on_fail':'die'}
	ret_chk = arg
	exc_type = None
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
		if 'ExcType' in arg:
			exc_type = arg['ExcType']
			del arg['ExcType']
			del arg_copy['ExcType']
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

		if isinstance(ret_chk,str): ret_chk = ret_chk.encode()
		if isinstance(ret,str): ret = ret.encode()

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
	except Exception as e:
		if not type(e).__name__ == exc_type:
			raise
		if not opt.super_silent:
			msg_r(' {}'.format(yellow(exc_type+':')))
			msg(e.args[0])
	except SystemExit as e:
		if input_data == 'good':
			raise ValueError('Error on good input data')
		if opt.verbose:
			msg('exitval: {}'.format(e.code))
	except UserWarning as e:
		msg('==> {!r}'.format(ret))
		die(2,red('{}'.format(e.args[0])))

def do_loop():
	import importlib
	modname = 'test.objtest_py_d.ot_{}_{}'.format(g.coin.lower(),g.network)
	test_data = importlib.import_module(modname).tests
	gmsg('Running data object tests for {} {}'.format(g.coin,g.network))

	clr = None
	utests = cmd_args
	for test in test_data:
		if utests and test not in utests: continue
		nl = ('\n','')[bool(opt.super_silent) or clr == None]
		clr = (blue,nocolor)[bool(opt.super_silent)]
		msg(clr('{}Testing {}'.format(nl,test)))
		for k in ('bad','good'):
			if not opt.silent:
				msg(purple(capfirst(k)+' input:'))
			for arg in test_data[test][k]:
				run_test(test,arg,input_data=k)

do_loop()
