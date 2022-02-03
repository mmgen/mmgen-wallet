#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
tx.__init__: transaction class initializer
"""

from ..objmethods import MMGenObject

def _base_proto_subclass(clsname,modname,proto):
	if proto:
		clsname = ('Token' if proto.tokensym else '') + clsname
		modname = 'mmgen.base_proto.{}.tx.{}'.format( proto.base_proto.lower(), modname )
	else:
		modname = 'mmgen.tx.base'
	import importlib
	return getattr( importlib.import_module(modname), clsname )

def _get_cls_info(clsname,modname,args,kwargs):

	assert args == (), f'{clsname}.chk1: only keyword args allowed in {clsname} initializer'

	if 'proto' in kwargs:
		proto = kwargs['proto']
	elif 'data' in kwargs:
		proto = kwargs['data']['proto']
	elif 'filename' in kwargs:
		from ..txfile import MMGenTxFile
		proto = MMGenTxFile.get_proto( kwargs['filename'], quiet_open=True )
	elif clsname == 'Base':
		proto = None
	else:
		raise ValueError(
			f"{clsname} must be instantiated with 'proto','data' or 'filename' keyword" )

	if clsname == 'Completed':
		from ..util import get_extension,fmt_list
		from .unsigned import Unsigned
		from .signed import Signed

		ext = get_extension(kwargs['filename'])
		cls_data = {
			Unsigned.ext: ('Unsigned','unsigned'),
			Signed.ext:   ('OnlineSigned','online') if proto.tokensym else ('Signed','signed')
		}

		if ext not in cls_data:
			die(1,f'{ext!r}: unrecognized file extension for CompletedTX (not in {fmt_list(cls_data)})')

		clsname,modname = cls_data[ext]

	kwargs['proto'] = proto

	return ( proto, clsname, modname, kwargs )

def _get_obj( _clsname, _modname, *args, **kwargs ):
	"""
	determine cls/mod/proto and pass them to _base_proto_subclass() to get a transaction instance
	"""
	proto,clsname,modname,kwargs = _get_cls_info(_clsname,_modname,args,kwargs)

	return _base_proto_subclass( clsname, modname, proto )(*args,**kwargs)

async def _get_obj_async( _clsname, _modname, *args, **kwargs ):

	proto,clsname,modname,kwargs = _get_cls_info(_clsname,_modname,args,kwargs)

	# NB: tracking wallet needed to retrieve the 'symbol' and 'decimals' parameters of token addr
	# (see twctl:import_token()).
	# No tracking wallet required for the Unsigned and Signed(data=unsigned.__dict__) classes used
	# during signing.
	if proto and proto.tokensym and clsname in ('New','OnlineSigned'):
		from ..twctl import TrackingWallet
		kwargs['tw'] = await TrackingWallet(proto)

	return _base_proto_subclass( clsname, modname, proto )(*args,**kwargs)

def _get(clsname,modname):
	return lambda *args,**kwargs: _get_obj(clsname,modname,*args,**kwargs)

def _get_async(clsname,modname):
	return lambda *args,**kwargs: _get_obj_async(clsname,modname,*args,**kwargs)

BaseTX         = _get('Base',     'base')
UnsignedTX     = _get('Unsigned', 'unsigned')

NewTX          = _get_async('New',          'new')
CompletedTX    = _get_async('Completed',    'completed')
SignedTX       = _get_async('Signed',       'signed')
OnlineSignedTX = _get_async('OnlineSigned', 'online')
BumpTX         = _get_async('Bump',         'bump')
