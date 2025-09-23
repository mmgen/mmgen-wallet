#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.__init__: transaction class initializer
"""

def _base_proto_subclass(clsname, modname, kwargs):
	proto = kwargs['proto']
	if proto:
		clsname = ('Token' if proto.tokensym else '') + clsname
		modname = f'mmgen.proto.{proto.base_proto_coin.lower()}.tx.{modname}'
	else:
		modname = 'mmgen.tx.base'
	import importlib
	return getattr(importlib.import_module(modname), clsname)

def _get_cls_info(clsname, modname, kwargs):
	"""
	determine cls/mod/proto and pass them to _base_proto_subclass() to get a TX instance
	"""
	if 'proto' in kwargs:
		proto = kwargs['proto']
	elif 'data' in kwargs:
		proto = kwargs['data']['proto']
	elif 'filename' in kwargs:
		from .file import MMGenTxFile
		proto = MMGenTxFile.get_proto(kwargs['cfg'], kwargs['filename'], quiet_open=True)
	elif clsname == 'Base':
		proto = None
	else:
		raise ValueError(
			f"{clsname} must be instantiated with 'proto', 'data' or 'filename' keyword")

	match clsname:
		case 'Completed':
			from ..util import get_extension, die
			from .completed import Completed
			ext = get_extension(kwargs['filename'])
			cls = Completed.ext_to_cls(ext, proto)
			if not cls:
				die(1, f'{ext!r}: unrecognized file extension for CompletedTX')
			clsname = cls.__name__
			modname = cls.__module__.rsplit('.', maxsplit=1)[-1]
		case 'New' if kwargs['target'] == 'swaptx':
			clsname = 'NewSwap'
			modname = 'new_swap'

	kwargs['proto'] = proto

	if 'automount' in kwargs:
		if kwargs['automount']:
			clsname = 'Automount' + clsname
		del kwargs['automount']

	return (clsname, modname, kwargs)

async def _add_twctl(clsname, modname, kwargs):
	proto = kwargs['proto']
	# TwCtl instance required to retrieve the 'symbol' and 'decimals' parameters
	# of token contract (see twctl:import_token()).
	# No twctl required by the Unsigned and Signed classes used during signing,
	# or by the New and Bump classes, which already have a twctl.
	if proto and proto.tokensym and clsname in (
			'OnlineSigned',
			'AutomountOnlineSigned',
			'Sent',
			'AutomountSent'):
		from ..tw.ctl import TwCtl
		kwargs['twctl'] = await TwCtl(kwargs['cfg'], proto, no_rpc=True)
	return (clsname, modname, kwargs)

def _get(clsname, modname, kwargs):
	return _base_proto_subclass(*_get_cls_info(clsname, modname, kwargs))(**kwargs)

async def _get_async(clsname, modname, kwargs):
	return _base_proto_subclass(*(await _add_twctl(*_get_cls_info(clsname, modname, kwargs))))(**kwargs)

BaseTX         = lambda **kwargs: _get('Base',     'base',     kwargs)
NewTX          = lambda **kwargs: _get('New',      'new',      kwargs)
NewSwapTX      = lambda **kwargs: _get('NewSwap',  'new_swap', kwargs)
BumpTX         = lambda **kwargs: _get('Bump',     'bump',     kwargs)
UnsignedTX     = lambda **kwargs: _get('Unsigned', 'unsigned', kwargs)
SignedTX       = lambda **kwargs: _get('Signed',   'signed',   kwargs)

CompletedTX    = lambda **kwargs: _get_async('Completed',    'completed', kwargs)
OnlineSignedTX = lambda **kwargs: _get_async('OnlineSigned', 'online',    kwargs)
SentTX         = lambda **kwargs: _get_async('Sent',         'online',    kwargs)
