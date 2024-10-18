#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
devtools: Developer tools for the MMGen suite
"""

import sys

color_funcs = {
	name: lambda s, n=n: f'\033[{n};1m{s}\033[0m'
		for name, n in (
			('red',    31),
			('green',  32),
			('yellow', 33),
			('blue',   34),
			('purple', 35))
}

def pfmt(*args, color=None):
	import pprint
	ret = pprint.PrettyPrinter(indent=4, width=116).pformat(
		args if len(args) > 1 else '' if not args else args[0])
	return color_funcs[color](ret) if color else ret

def pmsg(*args, color=None):
	sys.stderr.write(pfmt(*args, color=color) + '\n')

def pmsg_r(*args, color=None):
	sys.stderr.write(pfmt(*args, color=color))

def pdie(*args, exit_val=1):
	pmsg(*args, color='red' if exit_val else None)
	sys.exit(exit_val)

def pexit(*args):
	pdie(*args, exit_val=0)

def Pmsg(*args, color=None):
	sys.stdout.write(pfmt(*args, color=color) + '\n')

def Pdie(*args, exit_val=1):
	Pmsg(*args, color=('yellow' if exit_val == 1 else 'red' if exit_val else None))
	sys.exit(exit_val)

def Pexit(*args):
	Pdie(*args, exit_val=0)

def print_stack_trace(message=None, fh_list=[], nl='\n', sep='\n  ', trim=4):
	if not fh_list:
		import os
		fh_list.append(open(f'devtools.trace.{os.getpid()}', 'w'))
		nl = ''
	res = get_stack_trace(message, nl, sep, trim)
	sys.stderr.write(res)
	fh_list[0].write(res)

def get_stack_trace(message=None, nl='\n', sep='\n  ', trim=3):

	import os, re, traceback

	tb = [t for t in traceback.extract_stack() if t.filename[:1] != '<']
	fs = '{}:{}: in {}:\n    {}'
	out = [
		fs.format(
			re.sub(r'^\./', '', os.path.relpath(t.filename)),
			t.lineno,
			(t.name+'()' if t.name[-1] != '>' else t.name),
			t.line or '(none)')
		for t in (tb[:-trim] if trim else tb)]

	return f'{nl}STACK TRACE {message or "[unnamed]"}:{sep}{sep.join(out)}\n'

def print_diff(*args, **kwargs):
	sys.stderr.write(get_diff(*args, **kwargs))

def get_diff(a, b, a_fn='', b_fn='', from_json=True):

	if from_json:
		import json
		a = json.dumps(json.loads(a), indent=4)
		b = json.dumps(json.loads(b), indent=4)

	from difflib import unified_diff
	# chunk headers have trailing newlines, hence the rstrip()
	return '  DIFF:\n    {}\n'.format(
		'\n    '.join(a.rstrip('\n') for a in unified_diff(
			a.split('\n'),
			b.split('\n'),
			a_fn,
			b_fn)))

def print_ndiff(*args, **kwargs):
	sys.stderr.write(get_ndiff(*args, **kwargs))

def get_ndiff(a, b):
	from difflib import ndiff
	return list(ndiff(
		a.split('\n'),
		b.split('\n')))

class MMGenObjectMethods: # mixin class for MMGenObject

	# Pretty-print an MMGenObject instance, recursing into sub-objects - WIP
	def pmsg(self, color=None):
		sys.stdout.write('\n'+self.pfmt(color=color))

	def pdie(self, exit_val=1):
		self.pmsg(color='red' if exit_val else None)
		sys.exit(exit_val)

	def pexit(self):
		self.pdie(exit_val=0)

	def pfmt(self, lvl=0, id_list=[], color=None):

		from decimal import Decimal
		scalars = (str, int, float, Decimal)

		def isDict(obj):
			return isinstance(obj, dict)
		def isList(obj):
			return isinstance(obj, list)
		def isScalar(obj):
			return isinstance(obj, scalars)

		def do_list(out, e, lvl=0, is_dict=False):
			out.append('\n')
			for i in e:
				el = i if not is_dict else e[i]
				if is_dict:
#					out.append('{s}{:<{l}}'.format(i, s=' '*(4*lvl+8), l=10, l2=8*(lvl+1)+8))
					out.append('{s1}{i}{s2}'.format(
						i  = i,
						s1 = ' ' * (4*lvl+8),
						s2 = ' ' * 10))
				if hasattr(el, 'pfmt'):
					out.append('{:>{l}}{}'.format(
						'',
						el.pfmt(lvl=lvl+1, id_list=id_list+[id(self)]),
						l = (lvl+1)*8))
				elif isinstance(el, scalars):
					if isList(e):
						out.append('{:>{l}}{!r:16}\n'.format('', el, l=lvl*8))
					else:
						out.append(f' {el!r}')
				elif isList(el) or isDict(el):
					indent = 1 if is_dict else lvl*8+4
					out.append('{:>{l}}{:16}'.format('', f'<{type(el).__name__}>', l=indent))
					if isList(el) and isinstance(el[0], scalars):
						out.append('\n')
					do_list(out, el, lvl=lvl+1, is_dict=isDict(el))
				else:
					out.append('{:>{l}}{:16} {!r}\n'.format('', f'<{type(el).__name__}>', el, l=(lvl*8)+8))
				out.append('\n')

			if not e:
				out.append(f'{e!r}\n')

		out = [f'<{type(self).__name__}>{" "+repr(self) if isScalar(self) else ""}\n']

		if id(self) in id_list:
			return out[-1].rstrip() + ' [RECURSION]\n'
		if isList(self) or isDict(self):
			do_list(out, self, lvl=lvl, is_dict=isDict(self))

		for k in self.__dict__:
			e = getattr(self, k)
			if isList(e) or isDict(e):
				out.append('{:>{l}}{:<10} {:16}'.format('', k, f'<{type(e).__name__}>', l=(lvl*8)+4))
				do_list(out, e, lvl=lvl, is_dict=isDict(e))
			elif hasattr(e, 'pfmt') and callable(e.pfmt) and not isinstance(e, type):
				out.append('{:>{l}}{:10} {}'.format(
					'',
					k,
					e.pfmt(lvl=lvl+1, id_list=id_list+[id(self)]),
					l = (lvl*8)+4))
			else:
				out.append('{:>{l}}{:<10} {:16} {}\n'.format(
					'',
					k,
					f'<{type(e).__name__}>',
					repr(e),
					l=(lvl*8)+4))

		import re
		ret = re.sub('\n+', '\n', ''.join(out))
		return color_funcs[color](ret) if color else ret
