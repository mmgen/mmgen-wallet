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
devinit: Developer tools initialization for the MMGen suite
"""

devtools_funcs = {
	'pfmt':              lambda *args, **kwargs: devtools_call('pfmt', *args, **kwargs),
	'pmsg':              lambda *args, **kwargs: devtools_call('pmsg', *args, **kwargs),
	'pmsg_r':            lambda *args, **kwargs: devtools_call('pmsg_r', *args, **kwargs),
	'pdie':              lambda *args, **kwargs: devtools_call('pdie', *args, **kwargs),
	'pexit':             lambda *args, **kwargs: devtools_call('pexit', *args, **kwargs),
	'Pmsg':              lambda *args, **kwargs: devtools_call('Pmsg', *args, **kwargs),
	'Pdie':              lambda *args, **kwargs: devtools_call('Pdie', *args, **kwargs),
	'Pexit':             lambda *args, **kwargs: devtools_call('Pexit', *args, **kwargs),
	'print_stack_trace': lambda *args, **kwargs: devtools_call('print_stack_trace', *args, **kwargs),
	'get_diff':          lambda *args, **kwargs: devtools_call('get_diff', *args, **kwargs),
	'print_diff':        lambda *args, **kwargs: devtools_call('print_diff', *args, **kwargs),
	'get_ndiff':         lambda *args, **kwargs: devtools_call('get_ndiff', *args, **kwargs),
	'print_ndiff':       lambda *args, **kwargs: devtools_call('print_ndiff', *args, **kwargs),
}

def devtools_call(funcname, *args, **kwargs):
	from . import devtools
	return getattr(devtools, funcname)(*args, **kwargs)

def MMGenObject_call(methodname, *args, **kwargs):
	from .devtools import MMGenObjectMethods
	return getattr(MMGenObjectMethods, methodname)(*args, **kwargs)

class MMGenObjectDevTools:

	pmsg  = lambda *args, **kwargs: MMGenObject_call('pmsg', *args, **kwargs)
	pdie  = lambda *args, **kwargs: MMGenObject_call('pdie', *args, **kwargs)
	pexit = lambda *args, **kwargs: MMGenObject_call('pexit', *args, **kwargs)
	pfmt  = lambda *args, **kwargs: MMGenObject_call('pfmt', *args, **kwargs)

	# Check that all immutables have been initialized.  Expensive, so do only when testing.
	def immutable_attr_init_check(self):

		cls = type(self)

		for attrname in self.valid_attrs:

			for o in (cls, cls.__bases__[0]): # assume there's only one base class
				if attrname in o.__dict__:
					attr = o.__dict__[attrname]
					break
			else:
				from .util import die
				die(4, f'unable to find descriptor {cls.__name__}.{attrname}')

			if type(attr).__name__ == 'ImmutableAttr' and attrname not in self.__dict__:
				from .util import die
				die(4, f'attribute {attrname!r} of {cls.__name__} has not been initialized in constructor!')

def init_dev():
	import builtins
	# MMGenObject is added to the namespace by objmethods.py, so we must name the builtin differently
	# to avoid inadvertently adding MMGenObject to the global namespace here:
	setattr(builtins, 'MMGenObjectDevTools', MMGenObjectDevTools)
	for funcname, func in devtools_funcs.items():
		setattr(builtins, funcname, func)
