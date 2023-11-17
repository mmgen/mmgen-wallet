#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.__init__: transaction class initializer
"""

from ..objmethods import MMGenObject

def _base_proto_subclass(clsname,modname,proto):
	if proto:
		clsname = ('Token' if proto.tokensym else '') + clsname
		modname = f'mmgen.proto.{proto.base_proto_coin.lower()}.tx.{modname}'
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
		from .file import MMGenTxFile
		proto = MMGenTxFile.get_proto( kwargs['cfg'], kwargs['filename'], quiet_open=True )
	elif clsname == 'Base':
		proto = None
	else:
		raise ValueError(
			f"{clsname} must be instantiated with 'proto','data' or 'filename' keyword" )

	if clsname == 'Completed':
		from ..util import get_extension,die
		from .completed import Completed
		ext = get_extension( kwargs['filename'] )
		cls = Completed.ext_to_cls( ext, proto )
		if not cls:
			die(1,f'{ext!r}: unrecognized file extension for CompletedTX')
		clsname = cls.__name__
		modname = cls.__module__.rsplit('.',maxsplit=1)[-1]

	kwargs['proto'] = proto

	return ( kwargs['cfg'], proto, clsname, modname, kwargs )


def _get_obj( _clsname, _modname, *args, **kwargs ):
	"""
	determine cls/mod/proto and pass them to _base_proto_subclass() to get a transaction instance
	"""
	cfg,proto,clsname,modname,kwargs = _get_cls_info(_clsname,_modname,args,kwargs)

	return _base_proto_subclass( clsname, modname, proto )(*args,**kwargs)

async def _get_obj_async( _clsname, _modname, *args, **kwargs ):

	cfg,proto,clsname,modname,kwargs = _get_cls_info(_clsname,_modname,args,kwargs)

	# NB: tracking wallet needed to retrieve the 'symbol' and 'decimals' parameters of token addr
	# (see twctl:import_token()).
	# No twctl required for the Unsigned and Signed(data=unsigned.__dict__) classes used during
	# signing.
	if proto and proto.tokensym and clsname in ('New','OnlineSigned'):
		from ..tw.ctl import TwCtl
		kwargs['twctl'] = await TwCtl(cfg,proto)

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
