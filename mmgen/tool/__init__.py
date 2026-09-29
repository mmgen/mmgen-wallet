#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tool.__init__: initialization functions for the ‘mmgen-tool’ utility and others
"""

import sys, os

from ..cfg import gc
from ..util import die

from .common import fstr

# provide this for backwards compatibility:
def tool_api(*args, **kwargs):
	from .api import tool_api
	return tool_api(*args, **kwargs)

def get_cmds(mods):
	return [cmd for mod, cmds in mods.items() if mod != 'help' for cmd in cmds]

def create_call_sig(cmd, cls, *, as_string=False):

	m = getattr(cls, cmd)

	if 'varargs_call_sig' in m.__code__.co_varnames: # hack
		flag = 'VAR_ARGS'
		va = m.__defaults__[0]
		args, dfls, ann = va['args'], va['dfls'], va['annots']
	else:
		flag = None
		c = m.__code__
		args = c.co_varnames[1:c.co_argcount + c.co_posonlyargcount + c.co_kwonlyargcount]
		dfls = (
			(m.__defaults__ or ()) +
			tuple(m.__kwdefaults__[k] for k in args if k in (m.__kwdefaults__ or ())))
		ann  = m.__annotations__

	nargs = len(args) - len(dfls)
	dfl_types = tuple(
		ann[a] if a in ann and isinstance(ann[a], type) else type(dfls[i])
			for i, a in enumerate(args[nargs:]))

	if as_string:
		get_type_from_ann = lambda x: 'str or STDIN' if ann[x] == fstr else ann[x].__name__
		return ' '.join(
			[f'{a} [{get_type_from_ann(a)}]' for a in args[:nargs]] +
			[f'{a} [{dfl_types[n].__name__}={dfls[n]!r}]' for n, a in enumerate(args[nargs:])])
	else:
		get_type_from_ann = lambda x: 'str' if ann[x] == fstr else ann[x].__name__
		return (
			[(a, get_type_from_ann(a)) for a in args[:nargs]],          # c_args
			{a: dfls[n] for n, a in enumerate(args[nargs:])},           # c_kwargs
			{a: dfl_types[n] for n, a in enumerate(args[nargs:])},      # c_kwargs_types
			('STDIN_OK' if nargs and ann[args[0]] == fstr else flag),   # flag
			ann)                                                        # ann

def process_args(cmd, cmd_args, cls):
	c_args, c_kwargs, c_kwargs_types, flag, _ = create_call_sig(cmd, cls)
	have_stdin_input = False
	from ..util import msg, suf

	def usage_die(s):
		msg(s)
		from .help import usage
		usage(cmd)

	if flag != 'VAR_ARGS':
		if len(cmd_args) < len(c_args):
			usage_die(f'Command requires exactly {len(c_args)} non-keyword argument{suf(c_args)}')

		u_args = cmd_args[:len(c_args)]

		# If we're reading from a pipe, replace '-' with output of previous command
		if flag == 'STDIN_OK' and u_args and u_args[0] == '-':
			if sys.stdin.isatty():
				die('BadFilename', "Standard input is a TTY.  Can't use '-' as a filename")
			else:
				from ..util2 import parse_bytespec
				max_dlen_spec = '10kB' # limit input to 10KB for now
				max_dlen = parse_bytespec(max_dlen_spec)
				u_args[0] = os.read(0, max_dlen)
				have_stdin_input = True
				if len(u_args[0]) >= max_dlen:
					die(2, f'Maximum data input for this command is {max_dlen_spec}')
				if not u_args[0]:
					die(2, f'{cmd}: ERROR: no output from previous command in pipe')

	u_nkwargs = len(cmd_args) - len(c_args)
	u_kwargs = {}
	if flag == 'VAR_ARGS':
		cmd_args = ['dummy_arg'] + cmd_args
		t = [a.split('=', 1) for a in cmd_args if '=' in a]
		tk = [a[0] for a in t]
		tk_bad = [a for a in tk if a not in c_kwargs]
		if set(tk_bad) != set(tk[:len(tk_bad)]): # permit non-kw args to contain '='
			die(1, f'{tk_bad[-1]!r}: illegal keyword argument')
		u_kwargs = dict(t[len(tk_bad):])
		u_args = cmd_args[:-len(u_kwargs) or None]
	elif u_nkwargs > 0:
		u_kwargs = dict([a.split('=', 1) for a in cmd_args[len(c_args):] if '=' in a])
		if len(u_kwargs) != u_nkwargs:
			usage_die(f'Command requires exactly {len(c_args)} non-keyword argument{suf(c_args)}')
		if len(u_kwargs) > len(c_kwargs):
			usage_die(f'Command accepts no more than {len(c_kwargs)} keyword argument{suf(c_kwargs)}')

	for k in u_kwargs:
		if k not in c_kwargs:
			usage_die(f'{k!r}: invalid keyword argument')

	def conv_type(arg, arg_name, arg_type):
		if arg_type == 'bytes' and not isinstance(arg, bytes):
			die(1, "'Binary input data must be supplied via STDIN")

		if have_stdin_input and arg_type == 'str' and isinstance(arg, bytes):
			NL = '\r\n' if gc.platform == 'win32' else '\n'
			arg = arg.decode()
			if arg[-len(NL):] == NL: # rstrip one newline
				arg = arg[:-len(NL)]

		if arg_type == 'bool':
			if arg.lower() in ('true', 'yes', '1', 'on'):
				arg = True
			elif arg.lower() in ('false', 'no', '0', 'off'):
				arg = False
			else:
				usage_die(f'{arg!r}: invalid boolean value for keyword argument')

		try:
			return __builtins__[arg_type](arg)
		except:
			die(1, f'{arg!r}: Invalid argument for argument {arg_name} ({arg_type!r} required)')

	if flag == 'VAR_ARGS':
		args = [conv_type(u_args[i], c_args[0][0], c_args[0][1]) for i in range(len(u_args))]
	else:
		args = [conv_type(u_args[i], c_args[i][0], c_args[i][1]) for i in range(len(c_args))]
	kwargs = {k: conv_type(v, k, c_kwargs_types[k].__name__) for k, v in u_kwargs.items()}

	return (args, kwargs)
