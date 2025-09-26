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
wallet.__init__: wallet class initializer
"""

import importlib
from collections import namedtuple

from ..util import die, get_extension
from ..objmethods import MMGenObject
from ..seed import Seed

_wd = namedtuple('wallet_data', ['type', 'name', 'ext', 'base_type', 'enc', 'fmt_codes'])

wallet_data = {
	'bip39':
_wd('bip39',        'BIP39Mnemonic',     'bip39',   'mnemonic',   False, ('bip39',)),
	'brain':
_wd('brain',        'Brainwallet',       'mmbrain', None,         True,  ('mmbrain','brainwallet','brain','bw')),
	'dieroll':
_wd('dieroll',      'DieRollWallet',     'b6d',     None,         False, ('b6d','die','dieroll')),
	'incog':
_wd('incog',        'IncogWallet',       'mmincog', 'incog_base', True,  ('mmincog','incog','icg','i')),
	'incog_hex':
_wd('incog_hex',    'IncogWalletHex',    'mmincox', 'incog_base', True,  ('mmincox','incox','incog_hex','ix','xi')),
	'incog_hidden':
_wd('incog_hidden', 'IncogWalletHidden', None,      'incog_base', True,  ('incog_hidden','hincog','ih','hi')),
	'mmgen':
_wd('mmgen',        'MMGenWallet',       'mmdat',   None,         True,  ('wallet','w')),
	'mmhex':
_wd('mmhex',        'MMGenHexSeedFile',  'mmhex',   None,         False, ('seedhex','hexseed','mmhex')),
	'plainhex':
_wd('plainhex',     'PlainHexSeedFile',  'hex',     None,         False, ('hex','rawhex','plainhex')),
	'seed':
_wd('seed',         'MMGenSeedFile',     'mmseed',  None,         False, ('mmseed','seed','s')),
	'words':
_wd('words',        'MMGenMnemonic',     'mmwords', 'mnemonic',   False, ('mmwords','words','mnemonic','mn','m')),
}

def get_wallet_data(
		*,
		wtype       = None,
		fmt_code    = None,
		ext         = None,
		die_on_fail = False):

	if wtype:
		return wallet_data[wtype]
	elif fmt_code:
		for v in wallet_data.values():
			if fmt_code in v.fmt_codes:
				return v
	elif ext is not None: # ext could be the empty string
		for v in wallet_data.values():
			if ext == v.ext:
				return v
	else:
		die(4, 'no argument supplied!')

	if die_on_fail:
		if fmt_code:
			die(3, f'{fmt_code!r}: unrecognized wallet format code')
		else:
			die('BadFileExtension', f'{ext!r}: unrecognized wallet file extension')

def get_wallet_cls(
		wtype       = None,
		*,
		fmt_code    = None,
		ext         = None,
		die_on_fail = False):

	return getattr(
		importlib.import_module('mmgen.wallet.{}'.format(
			wtype or
			get_wallet_data(
				fmt_code    = fmt_code,
				ext         = ext,
				die_on_fail = die_on_fail).type
		)),
		'wallet')

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
	ret = [f'{a:<{w}}  {b:<9} {c}' for a, b, c in [
		('Format', 'FileExt', 'Valid codes'),
		('------', '-------', '-----------')
		] + sorted(d)]
	return '\n'.join(ret) + '\n'

def _get_me(modname):
	return MMGenObject.__new__(getattr(importlib.import_module(f'mmgen.wallet.{modname}'), 'wallet'))

def Wallet(
	cfg,
	*,
	fn            = None,
	ss            = None,
	seed_bin      = None,
	seed          = None,
	passchg       = False,
	in_data       = None,
	ignore_in_fmt = False,
	in_fmt        = None,
	passwd_file   = None):

	in_fmt = in_fmt or cfg.in_fmt

	ss_out = (
		get_wallet_data(
			fmt_code    = cfg.out_fmt,
			die_on_fail = True).type
		if cfg.out_fmt else None)

	if seed or seed_bin:
		me = _get_me(ss_out or 'mmgen') # default to native wallet format
		me.seed = seed or Seed(cfg, seed_bin=seed_bin)
		me.op = 'new'
	elif ss:
		me = _get_me(ss.type if passchg else (ss_out or 'mmgen'))
		me.seed = ss.seed
		me.ss_in = ss
		me.op = 'pwchg_new' if passchg else 'conv'
	elif fn or cfg.hidden_incog_input_params:
		if fn:
			wd = get_wallet_data(ext=get_extension(fn), die_on_fail=True)
			if in_fmt and (not ignore_in_fmt) and in_fmt not in wd.fmt_codes:
				die(1, f'{in_fmt}: --in-fmt parameter does not match extension of input file')
			me = _get_me(wd.type)
		else:
			fn = cfg.hidden_incog_input_params.rsplit(',', 1)[0] # permit comma in filename
			me = _get_me('incog_hidden')
		from ..filename import MMGenFile
		me.infile = MMGenFile(fn, subclass=type(me))
		me.op = 'pwchg_old' if passchg else 'old'
	elif in_fmt:
		me = _get_me(get_wallet_data(fmt_code=in_fmt).type)
		me.op = 'pwchg_old' if passchg else 'old'
	else: # called with no arguments: initialize with random seed
		me = _get_me(ss_out or 'mmgen') # default to native wallet format
		me.seed = Seed(cfg)
		me.op = 'new'

	me.cfg = cfg

	me.__init__(
		in_data     = in_data,
		passwd_file = passwd_file)

	return me

def check_wallet_extension(fn):
	get_wallet_data(ext=get_extension(fn), die_on_fail=True) # raises exception on failure
