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
test/objattrtest.py:  Test immutable attributes of MMGen data objects
"""

# TODO: test 'typeconv' during instance creation

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

os.environ['MMGEN_TEST_SUITE'] = '1'

# Import these _after_ local path's been added to sys.path
from test.objattrtest_py_d.oat_common import *
from mmgen.common import *
from mmgen.addrlist import *
from mmgen.passwdlist import *
from mmgen.tx.base import Base
from mmgen.proto.btc.tw.unspent import BitcoinTwUnspentOutputs

opts_data = {
	'sets': [
		('show_nonstandard_init', True, 'verbose', True),
		('show_descriptor_type', True, 'verbose', True),
	],
	'text': {
		'desc': 'Test immutable attributes of MMGen data objects',
		'usage':'[options] [object]',
		'options': """
-h, --help                  Print this help message
--, --longhelp              Print help message for long options (common options)
-i, --show-nonstandard-init Display non-standard attribute initialization info
-d, --show-descriptor-type  Display the attribute's descriptor type
-v, --verbose               Produce more verbose output
"""
	}
}

cmd_args = opts.init(opts_data)

pd = namedtuple('permission_bits', ['read_ok','delete_ok','reassign_ok'])

def parse_permbits(bits):
	return pd(
		bool(0b001 & bits), # read
		bool(0b010 & bits), # delete
		bool(0b100 & bits), # reassign
	)

def get_descriptor_obj(objclass,attrname):
	for o in (objclass,objclass.__bases__[0]): # assume there's only one base class
		if attrname in o.__dict__:
			return o.__dict__[attrname]
	die(4,f'unable to find descriptor {objclass.__name__}.{attrname}')

def test_attr_perm(obj,attrname,perm_name,perm_value,dobj,attrval_type):

	class SampleObjError(Exception): pass

	pname = perm_name.replace('_ok','')
	pstem = pname.rstrip('e')

	try:
		if perm_name == 'read_ok':
			getattr(obj,attrname)
		elif perm_name == 'reassign_ok':
			try:
				so = sample_objs[attrval_type.__name__]
			except:
				die( 'SampleObjError', f'unable to find sample object of type {attrval_type.__name__!r}' )
			# ListItemAttr allows setting an attribute if its value is None
			if type(dobj) == ListItemAttr and getattr(obj,attrname) == None:
				setattr(obj,attrname,so)
			setattr(obj,attrname,so)
		elif perm_name == 'delete_ok':
			delattr(obj,attrname)
	except SampleObjError as e:
		die(4,f'Test script error ({e})')
	except Exception as e:
		if perm_value == True:
			fs = '{!r}: unable to {} attribute {!r}, though {}ing is allowed ({})'
			die(4,fs.format(type(obj).__name__,pname,attrname,pstem,e))
	else:
		if perm_value == False:
			fs = '{!r}: attribute {!r} is {n}able, though {n}ing is forbidden'
			die(4,fs.format(type(obj).__name__,attrname,n=pstem))

def test_attr(data,obj,attrname,dobj,bits,attrval_type):
	if hasattr(obj,attrname): # TODO
		td_attrval_type = data.attrs[attrname][1]

		if attrval_type not in (td_attrval_type,type(None)):
			fs = '\nattribute {!r} of {!r} instance has incorrect type {!r} (should be {!r})'
			die(4,fs.format(attrname,type(obj).__name__,attrval_type.__name__,td_attrval_type.__name__))

	if hasattr(dobj,'__dict__'):
		d = dobj.__dict__
		bits = bits._asdict()
		for k in ('reassign_ok','delete_ok'):
			if k in d:
				if d[k] != bits[k]:
					fs = 'init value {iv}={a} for attr {n!r} does not match test data ({iv}={b})'
					die(4,fs.format(iv=k,n=attrname,a=d[k],b=bits[k]))
				if opt.verbose and d[k] == True:
					msg_r(f' {k}={d[k]!r}')

		if opt.show_nonstandard_init:
			for k,v in (('typeconv',False),('set_none_ok',True)):
				if d[k] == v:
					msg_r(f' {k}={v}')

def test_object(test_data,objname):

	if '.' in objname:
		on1,on2 = objname.split('.')
		cls = getattr(globals()[on1],on2)
	else:
		cls = globals()[objname]

	fs = 'Testing attribute ' + ('{!r:<15}{dt:13}' if opt.show_descriptor_type else '{!r}')
	data = test_data[objname]
	obj = cls(*data.args,**data.kwargs)

	for attrname,adata in data.attrs.items():
		dobj = get_descriptor_obj(type(obj),attrname)
		if opt.verbose:
			msg_r(fs.format(attrname,dt=type(dobj).__name__.replace('MMGen','')))
		bits = parse_permbits(adata[0])
		test_attr(data,obj,attrname,dobj,bits,adata[1])
		for perm_name,perm_value in bits._asdict().items():
			test_attr_perm(obj,attrname,perm_name,perm_value,dobj,adata[1])
		vmsg('')

def do_loop():
	import importlib
	modname = f'test.objattrtest_py_d.oat_{proto.coin.lower()}_{proto.network}'
	test_data = importlib.import_module(modname).tests
	gmsg(f'Running immutable attribute tests for {proto.coin} {proto.network}')

	utests = cmd_args
	for obj in test_data:
		if utests and obj not in utests: continue
		msg((blue if opt.verbose else nocolor)(f'Testing {obj}'))
		test_object(test_data,obj)

from mmgen.protocol import init_proto_from_opts
proto = init_proto_from_opts(need_amt=True)
do_loop()
