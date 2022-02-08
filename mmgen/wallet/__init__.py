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
wallet.__init__: wallet class initializer
"""

import importlib
from collections import namedtuple

from ..globalvars import g
from ..opts import opt
from ..util import die,get_extension
from ..objmethods import MMGenObject
from ..seed import Seed

_wd = namedtuple('wallet_data', ['type','name','ext','base_type','enc','fmt_codes'])
_pd = namedtuple('partial_wallet_data',['name','ext','base_type','enc','fmt_codes'])

wallet_data = {
	'bip39':       _pd('BIP39Mnemonic',    'bip39',  'mnemonic',  False,('bip39',)),
	'brain':       _pd('Brainwallet',      'mmbrain',None,        True, ('mmbrain','brainwallet','brain','bw')),
	'dieroll':     _pd('DieRollWallet',    'b6d',    None,        False,('b6d','die','dieroll')),
	'incog':       _pd('IncogWallet',      'mmincog','incog_base',True, ('mmincog','incog','icg','i')),
	'incog_hex':   _pd('IncogWalletHex',   'mmincox','incog_base',True, ('mmincox','incox','incog_hex','ix','xi')),
	'incog_hidden':_pd('IncogWalletHidden',None,     'incog_base',True, ('incog_hidden','hincog','ih','hi')),
	'mmgen':       _pd('MMGenWallet',      'mmdat',  None,        True, ('wallet','w')),
	'mmhex':       _pd('MMGenHexSeedFile', 'mmhex',  None,        False,('seedhex','hexseed','mmhex')),
	'plainhex':    _pd('PlainHexSeedFile', 'hex',    None,        False,('hex','rawhex','plainhex')),
	'seed':        _pd('MMGenSeedFile',    'mmseed', None,        False,('mmseed','seed','s')),
	'words':       _pd('MMGenMnemonic',    'mmwords','mnemonic',  False,('mmwords','words','mnemonic','mn','m')),
}

def get_wallet_data(*args,**kwargs):

	if args:
		return _wd( args[0], *wallet_data[args[0]] )

	for key in ('fmt_code','ext'):
		if key in kwargs:
			val = kwargs[key]
			break
	else:
		die('{!r}: unrecognized argument'.format( list(kwargs.keys())[0] ))

	if key == 'fmt_code':
		for k,v in wallet_data.items():
			if val in v.fmt_codes:
				return _wd(k,*v)
	else:
		for k,v in wallet_data.items():
			if val == getattr(v,key):
				return _wd(k,*v)

	if 'die_on_fail' in kwargs:
		die( *{
			'ext':      ('BadFileExtension', f'{val!r}: unrecognized wallet file extension'),
			'fmt_code': (3, f'{val!r}: unrecognized wallet format code'),
			'type':     (3, f'{val!r}: unrecognized wallet type'),
		}[key] )

def get_wallet_cls(*args,**kwargs):
	return getattr(
		importlib.import_module( 'mmgen.wallet.{}'.format(
			args[0] if args else get_wallet_data(*args,**kwargs).type)
		),
		'wallet' )

def get_wallet_extensions(key):
	return {
		'enc':   [v.ext for v in wallet_data.values() if v.enc],
		'unenc': [v.ext for v in wallet_data.values() if not v.enc]
	}[key]

def format_fmt_codes():
	d = [(
			v.name,
			('.' + v.ext if v.ext else 'None'),
			','.join(v.fmt_codes)
		) for v in wallet_data.values()]
	w = max(len(i[0]) for i in d)
	ret = [f'{a:<{w}}  {b:<9} {c}' for a,b,c in [
		('Format','FileExt','Valid codes'),
		('------','-------','-----------')
		] + sorted(d) ]
	return '\n'.join(ret) + ('','-α')[g.debug_utf8] + '\n'

def _get_me(modname):
	return MMGenObject.__new__( getattr( importlib.import_module(f'mmgen.wallet.{modname}'), 'wallet' ) )

def Wallet(
	fn            = None,
	ss            = None,
	seed_bin      = None,
	seed          = None,
	passchg       = False,
	in_data       = None,
	ignore_in_fmt = False,
	in_fmt        = None,
	passwd_file   = None ):

	in_fmt = in_fmt or opt.in_fmt

	if opt.out_fmt:
		ss_out = get_wallet_data(fmt_code=opt.out_fmt)
		if not ss_out:
			die(1,f'{opt.out_fmt!r}: unrecognized output format')
	else:
		ss_out = None

	if seed or seed_bin:
		me = _get_me( ss_out.type if ss_out else 'mmgen' ) # default to native wallet format
		me.seed = seed or Seed(seed_bin=seed_bin)
		me.op = 'new'
	elif ss:
		me = _get_me( ss.type if passchg else ss_out.type if ss_out else 'mmgen' )
		me.seed = ss.seed
		me.ss_in = ss
		me.op = 'pwchg_new' if passchg else 'conv'
	elif fn or opt.hidden_incog_input_params:
		if fn:
			wd = get_wallet_data(ext=get_extension(fn),die_on_fail=True)
			if in_fmt and (not ignore_in_fmt) and in_fmt not in wd.fmt_codes:
				die(1,f'{in_fmt}: --in-fmt parameter does not match extension of input file')
			me = _get_me( wd.type )
		else:
			fn = ','.join(opt.hidden_incog_input_params.split(',')[:-1]) # permit comma in filename
			me = _get_me( 'incog_hidden' )
		from ..filename import Filename
		me.infile = Filename( fn, subclass=type(me) )
		me.op = 'pwchg_old' if passchg else 'old'
	elif in_fmt:
		me = _get_me( get_wallet_data(fmt_code=in_fmt).type )
		me.op = 'pwchg_old' if passchg else 'old'
	else: # called with no arguments: initialize with random seed
		me = _get_me( ss_out.type if ss_out else 'mmgen' ) # default to native wallet format
		me.seed = Seed()
		me.op = 'new'

	me.__init__(
		fn            = fn,
		ss            = ss,
		seed_bin      = seed_bin,
		seed          = seed,
		passchg       = passchg,
		in_data       = in_data,
		ignore_in_fmt = ignore_in_fmt,
		in_fmt        = in_fmt,
		passwd_file   = passwd_file )

	return me
