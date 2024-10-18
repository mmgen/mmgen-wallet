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
util2: Less frequently-used variables, classes and utility functions for the MMGen suite
"""

import sys, re, time
from .util import msg, suf, hexdigits, die

def die_wait(delay, ev=0, s=''):
	assert isinstance(delay, int)
	assert isinstance(ev, int)
	if s:
		msg(s)
	time.sleep(delay)
	sys.exit(ev)

def die_pause(ev=0, s=''):
	assert isinstance(ev, int)
	if s:
		msg(s)
	input('Press ENTER to exit')
	sys.exit(ev)

# monkey-patch function for monero-python: permits its use with pycryptodome (e.g. MSYS2)
# instead of the expected pycryptodomex
def load_cryptodomex():
	try:
		import Cryptodome # cryptodomex
	except ImportError:
		try:
			import Crypto # cryptodome
		except ImportError:
			die(2, 'Unable to import either the ‘pycryptodomex’ or ‘pycryptodome’ package')
		else:
			sys.modules['Cryptodome'] = Crypto

# called with no arguments by pyethereum.utils:
def get_keccak(cfg=None, cached_ret=[]):

	if not cached_ret:
		if cfg and cfg.use_internal_keccak_module:
			cfg._util.qmsg('Using internal keccak module by user request')
			from .contrib.keccak import keccak_256
		else:
			try:
				from Cryptodome.Hash import keccak
			except ImportError as e:
				try:
					from Crypto.Hash import keccak
				except ImportError as e2:
					msg(f'{e2} and {e}')
					die('MMGenImportError',
						'Please install the ‘pycryptodome’ or ‘pycryptodomex’ package on your system')
			def keccak_256(data):
				return keccak.new(data=data, digest_bytes=32)
		cached_ret.append(keccak_256)

	return cached_ret[0]

# From 'man dd':
# c=1, w=2, b=512, kB=1000, K=1024, MB=1000*1000, M=1024*1024,
# GB=1000*1000*1000, G=1024*1024*1024, and so on for T, P, E, Z, Y.
bytespec_map = (
	('c',  1),
	('w',  2),
	('b',  512),
	('kB', 1000),
	('K',  1024),
	('MB', 1000000),
	('M',  1048576),
	('GB', 1000000000),
	('G',  1073741824),
	('TB', 1000000000000),
	('T',  1099511627776),
	('PB', 1000000000000000),
	('P',  1125899906842624),
	('EB', 1000000000000000000),
	('E',  1152921504606846976),
)

def int2bytespec(n, spec, fmt, print_sym=True, strip=False, add_space=False):

	def spec2int(spec):
		for k, v in bytespec_map:
			if k == spec:
				return v
		die(1, f'{spec!r}: unrecognized bytespec')

	ret = f'{n/spec2int(spec):{fmt}f}'
	if strip:
		ret = ret.rstrip('0')
		return (
			ret
			+ ('0' if ret.endswith('.') else '')
			+ ((' ' if add_space else '') + spec if print_sym else ''))
	else:
		return (
			ret
			+ ((' ' if add_space else '') + spec if print_sym else ''))

def parse_bytespec(nbytes):
	m = re.match(r'([0123456789.]+)(.*)', nbytes)
	if m:
		if m.group(2):
			for k, v in bytespec_map:
				if k == m.group(2):
					from decimal import Decimal
					return int(Decimal(m.group(1)) * v)
			msg("Valid byte specifiers: '{}'".format("' '".join([i[0] for i in bytespec_map])))
		elif '.' in nbytes:
			raise ValueError('fractional bytes not allowed')
		else:
			return int(nbytes)

	die(1, f'{nbytes!r}: invalid byte specifier')

def format_elapsed_days_hr(t, now=None, cached={}):
	e = int((now or time.time()) - t)
	if not e in cached:
		days = abs(e) // 86400
		cached[e] = f'{days} day{suf(days)} ' + ('ago' if e > 0 else 'in the future')
	return cached[e]

def format_elapsed_hr(t, now=None, cached={}, rel_now=True, show_secs=False):
	e = int((now or time.time()) - t)
	key = f'{e}:{rel_now}:{show_secs}'
	if not key in cached:
		def add_suffix():
			return (
				((' ago'           if rel_now else '') if e > 0 else
				(' in the future' if rel_now else ' (negative elapsed)'))
					if (abs_e if show_secs else abs_e // 60) else
				('just now' if rel_now else ('0 ' + ('seconds' if show_secs else 'minutes')))
			)
		abs_e = abs(e)
		data = (
			('day',    abs_e // 86400),
			('hour',   abs_e // 3600 % 24),
			('minute', abs_e // 60 % 60),
			('second', abs_e % 60),
		) if show_secs else (
			('day',    abs_e // 86400),
			('hour',   abs_e // 3600 % 24),
			('minute', abs_e // 60 % 60),
		)
		cached[key] = ' '.join(f'{n} {desc}{suf(n)}' for desc, n in data if n) + add_suffix()
	return cached[key]

def pretty_format(s, width=80, pfx=''):
	out = []
	while s:
		if len(s) <= width:
			out.append(s)
			break
		i = s[:width].rfind(' ')
		out.append(s[:i])
		s = s[i+1:]
	return pfx + ('\n'+pfx).join(out)

def block_format(data, gw=2, cols=8, line_nums=None, data_is_hex=False):
	assert line_nums in (None, 'hex', 'dec'), "'line_nums' must be one of None, 'hex' or 'dec'"
	ln_fs = '{:06x}: ' if line_nums == 'hex' else '{:06}: '
	bytes_per_chunk = gw
	if data_is_hex:
		gw *= 2
	nchunks = len(data)//gw + bool(len(data)%gw)
	return ''.join(
		('' if (line_nums is None or i % cols) else ln_fs.format(i*bytes_per_chunk))
		+ data[i*gw:i*gw+gw]
		+ (' ' if (not cols or (i+1) % cols) else '\n')
			for i in range(nchunks)
	).rstrip() + '\n'

def pretty_hexdump(data, gw=2, cols=8, line_nums=None):
	return block_format(data.hex(), gw, cols, line_nums, data_is_hex=True)

def decode_pretty_hexdump(data):
	pat = re.compile(fr'^[{hexdigits}]+:\s+')
	lines = [pat.sub('', line) for line in data.splitlines()]
	try:
		return bytes.fromhex(''.join((''.join(lines).split())))
	except:
		msg('Data not in hexdump format')
		return False
