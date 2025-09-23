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
test/objattrtest.py: Test immutable attributes of MMGen data objects
"""

# TODO: test 'typeconv' during instance creation

from collections import namedtuple

try:
	from include import test_init
except ImportError:
	from test.include import test_init

from mmgen.cfg import Config
from mmgen.util import msg, msg_r, gmsg, die
from mmgen.color import red, yellow, green, blue, purple, nocolor
from mmgen.obj import ListItemAttr

opts_data = {
	'sets': [
		('show_descriptor_type', True, 'verbose', True),
	],
	'text': {
		'desc': 'Test immutable attributes of MMGen data objects',
		'usage':'[options] [object]',
		'options': """
-h, --help                  Print this help message
--, --longhelp              Print help message for long (global) options
-d, --show-descriptor-type  Display the attribute's descriptor type
-v, --verbose               Produce more verbose output
"""
	}
}

cfg = Config(opts_data=opts_data)

from test.include.common import set_globals
set_globals(cfg)

from test.objattrtest_d.common import sample_objs

pd = namedtuple('attr_bits', ['read_ok', 'delete_ok', 'reassign_ok', 'typeconv', 'set_none_ok'])
perm_bits = ('read_ok', 'delete_ok', 'reassign_ok')
attr_dfls = {
	'reassign_ok': False,
	'delete_ok': False,
	'typeconv': True,
	'set_none_ok': False,
}

def parse_attrbits(bits):
	return pd(
		bool(0b00001 & bits), # read
		bool(0b00010 & bits), # delete
		bool(0b00100 & bits), # reassign
		bool(0b01000 & bits), # typeconv
		bool(0b10000 & bits), # set_none
	)

def get_descriptor_obj(objclass, attrname):
	for o in (objclass, objclass.__bases__[0]): # assume there's only one base class
		if attrname in o.__dict__:
			return o.__dict__[attrname]
	die(4, f'unable to find descriptor {objclass.__name__}.{attrname}')

def test_attr_perm(obj, attrname, perm_name, perm_value, dobj, attrval_type):

	class SampleObjError(Exception):
		pass

	pname = perm_name.replace('_ok', '')
	pstem = pname.rstrip('e')

	try:
		match perm_name:
			case 'read_ok': # non-existent perm
				getattr(obj, attrname)
			case 'reassign_ok':
				try:
					so = sample_objs[attrval_type.__name__]
				except Exception as e:
					raise SampleObjError(f'unable to find sample object of type {attrval_type.__name__!r}') from e
				# ListItemAttr allows setting an attribute if its value is None
				if type(dobj) is ListItemAttr and getattr(obj, attrname) is None:
					setattr(obj, attrname, so)
				setattr(obj, attrname, so)
			case 'delete_ok':
				delattr(obj, attrname)
	except SampleObjError as e:
		die(4, f'Test script error ({e})')
	except Exception as e:
		if perm_value is True:
			fs = '{!r}: unable to {} attribute {!r}, though {}ing is allowed ({})'
			die(4, fs.format(type(obj).__name__, pname, attrname, pstem, e))
	else:
		if perm_value is False:
			fs = '{!r}: attribute {!r} is {n}able, though {n}ing is forbidden'
			die(4, fs.format(type(obj).__name__, attrname, n=pstem))

def test_attr(data, obj, attrname, dobj, bits, attrval_type):
	if hasattr(obj, attrname): # TODO
		td_attrval_type = data.attrs[attrname][1]

		if attrval_type not in (td_attrval_type, type(None)):
			fs = '\nattribute {!r} of {!r} instance has incorrect type {!r} (should be {!r})'
			die(4, fs.format(attrname, type(obj).__name__, attrval_type.__name__, td_attrval_type.__name__))

	if hasattr(dobj, '__dict__'):
		d = dobj.__dict__
		bits = bits._asdict()
		colors = {
			'reassign_ok': purple,
			'delete_ok': red,
			'typeconv': green,
			'set_none_ok': yellow,
		}
		for k in bits:
			if k in d:
				if d[k] != bits[k]:
					fs = 'init value {iv}={a} for attr {n!r} does not match test data ({iv}={b})'
					die(4, fs.format(iv=k, n=attrname, a=d[k], b=bits[k]))
				if cfg.verbose and d[k] != attr_dfls[k]:
					msg_r(colors[k](f' {k}={d[k]!r}'))

def test_object(mod, test_data, objname):

	if '.' in objname:
		on1, on2 = objname.split('.')
		cls = getattr(getattr(mod, on1), on2)
	else:
		cls = getattr(mod, objname)

	fs = 'Testing attribute ' + ('{!r:<15}{dt:13}' if cfg.show_descriptor_type else '{!r}')
	data = test_data[objname]
	obj = cls(*data.args, **data.kwargs)

	for attrname, adata in data.attrs.items():
		dobj = get_descriptor_obj(type(obj), attrname)
		if cfg.verbose:
			msg_r(fs.format(attrname, dt=type(dobj).__name__.replace('MMGen', '')))
		bits = parse_attrbits(adata[0])
		test_attr(data, obj, attrname, dobj, bits, adata[1])
		for bit_name, bit_value in bits._asdict().items():
			if bit_name in perm_bits:
				test_attr_perm(obj, attrname, bit_name, bit_value, dobj, adata[1])
		cfg._util.vmsg('')

def do_loop():
	import importlib
	modname = f'test.objattrtest_d.{proto.coin.lower()}_{proto.network}'
	mod = importlib.import_module(modname)
	test_data = getattr(mod, 'tests')
	gmsg(f'Running immutable attribute tests for {proto.coin} {proto.network}')

	utests = cfg._args
	for obj in test_data:
		if utests and obj not in utests:
			continue
		msg((blue if cfg.verbose else nocolor)(f'Testing {obj}'))
		test_object(mod, test_data, obj)

proto = cfg._proto

if __name__ == '__main__':
	do_loop()
