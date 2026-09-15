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
tx.__init__: transaction class initializer
"""

import importlib
from collections import namedtuple

cinfo = namedtuple('cls_info', 'clsname modname cfg proto')

def _base_proto_subclass(clsname, modname, cfg=None, proto=None):
	if proto:
		return getattr(
			importlib.import_module(f'mmgen.proto.{proto.base_proto_coin.lower()}.tx.{modname}'),
			('Token' if proto.tokensym else '') + clsname)
	else:
		return getattr(importlib.import_module('mmgen.tx.base'), clsname)

def _get_cls_info(
		clsname,
		modname,
		*,
		cfg,
		proto     = None,
		data      = None,
		filename  = None,
		automount = False,
		target    = None,
		**kwargs):
	"""
	determine cls/mod/proto and pass them to _base_proto_subclass() to get a TX instance
	"""
	if data:
		proto = data['proto']
	elif filename:
		from .file import MMGenTxFile
		proto = MMGenTxFile.get_proto(cfg, filename, quiet_open=True)
	elif not (proto or clsname == 'Base'):
		raise ValueError(
			f"{clsname} must be instantiated with 'proto', 'data' or 'filename' keyword")

	match clsname:
		case 'Completed':
			from ..util import get_extension, die
			from .completed import Completed
			if not (cls := Completed.ext_to_cls(get_extension(filename), proto)):
				die(1, f'{get_extension(filename)!r}: unrecognized file extension for CompletedTX')
			clsname = cls.__name__
			modname = cls.__module__.rsplit('.', maxsplit=1)[-1]
		case 'New' if target == 'swaptx':
			clsname = 'NewSwap'
			modname = 'new_swap'

	return cinfo(('Automount' + clsname if automount else clsname), modname, cfg, proto)

async def _get_twctl(d):
	# TwCtl instance required to retrieve the 'symbol' and 'decimals' parameters
	# of token contract (see twctl:import_token()).
	# No twctl required by the Unsigned and Signed classes used during signing,
	# or by the New and Bump classes, which already have a twctl.
	if d.proto and d.proto.tokensym and d.clsname in (
			'OnlineSigned',
			'AutomountOnlineSigned',
			'Sent',
			'AutomountSent'):
		from ..tw.ctl import TwCtl
		return await TwCtl(d.cfg, d.proto, no_rpc=True)
	else:
		return None

def _get(clsname, modname, kwargs):
	ret = _get_cls_info(clsname, modname, **kwargs)
	return _base_proto_subclass(*ret)(
		**(kwargs | {'proto': ret.proto}))

async def _get_async(clsname, modname, kwargs):
	ret = _get_cls_info(clsname, modname, **kwargs)
	return _base_proto_subclass(*ret)(
		**(kwargs | {'proto': ret.proto, 'twctl': await _get_twctl(ret)}))

BaseTX         = lambda **kwargs: _get('Base',     'base',     kwargs)
NewTX          = lambda **kwargs: _get('New',      'new',      kwargs)
NewSwapTX      = lambda **kwargs: _get('NewSwap',  'new_swap', kwargs)
BumpTX         = lambda **kwargs: _get('Bump',     'bump',     kwargs)
UnsignedTX     = lambda **kwargs: _get('Unsigned', 'unsigned', kwargs)
SignedTX       = lambda **kwargs: _get('Signed',   'signed',   kwargs)

CompletedTX    = lambda **kwargs: _get_async('Completed',    'completed', kwargs)
OnlineSignedTX = lambda **kwargs: _get_async('OnlineSigned', 'online',    kwargs)
SentTX         = lambda **kwargs: _get_async('Sent',         'online',    kwargs)
