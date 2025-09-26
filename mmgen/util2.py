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

def load_fake_cryptodome():
	import hashlib
	try:
		hashlib.new('keccak-256')
	except ValueError:
		return False

	class FakeHash:
		class keccak:
			def new(data=b'', digest_bits=256):
				assert digest_bits == 256
				return hashlib.new('keccak-256', data=data)

	sys.modules['Cryptodome.Hash'] = FakeHash
	sys.modules['Crypto.Hash'] = FakeHash
	return True

def cffi_override_fixup():
	from cffi import FFI
	class FFI_override:
		def cdef(self, csource, *, override=False, packed=False, pack=None):
			self._cdef(csource, override=True, packed=packed, pack=pack)
	FFI.cdef = FFI_override.cdef

# monkey-patch function: makes modules pycryptodome and pycryptodomex available to packages that
# expect them for the keccak256 function (monero-python, eth-keys), regardless of which one is
# installed on the system
#
# if the hashlib keccak256 function is available (>=OpenSSL 3.2, >=Python 3.13), it’s used instead
# and loaded as Crypto[dome].Hash via load_fake_cryptodome()
def load_cryptodome(called=[]):
	if not called:
		if not load_fake_cryptodome():
			cffi_override_fixup()
			try:
				import Crypto # Crypto == pycryptodome
			except ImportError:
				try:
					import Cryptodome # Crypto == pycryptodome
				except ImportError:
					die(2, 'Unable to import the ‘pycryptodome’ or ‘pycryptodomex’ package')
				else:
					sys.modules['Crypto'] = Cryptodome # Crypto == pycryptodome
			else:
				sys.modules['Cryptodome'] = Crypto # Cryptodome == pycryptodomex
		called.append(True)

def get_hashlib_keccak():
	import hashlib
	try:
		hashlib.new('keccak-256')
	except ValueError:
		return False
	return lambda data: hashlib.new('keccak-256', data)

# called with no arguments by proto.eth.tx.transaction:
def get_keccak(cfg=None, cached_ret=[]):

	if not cached_ret:
		if cfg and cfg.use_internal_keccak_module:
			cfg._util.qmsg('Using internal keccak module by user request')
			from .contrib.keccak import keccak_256
		elif not (keccak_256 := get_hashlib_keccak()):
			load_cryptodome()
			from Crypto.Hash import keccak
			keccak_256 = lambda data: keccak.new(data=data, digest_bytes=32)
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

def int2bytespec(n, spec, fmt, *, print_sym=True, strip=False, add_space=False):

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

	if m := re.match(r'([0123456789.]+)(.*)', nbytes):
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

def format_elapsed_days_hr(t, *, now=None, cached={}):
	e = int((now or time.time()) - t)
	if not e in cached:
		days = abs(e) // 86400
		cached[e] = f'{days} day{suf(days)} ' + ('ago' if e > 0 else 'in the future')
	return cached[e]

def format_elapsed_hr(
		t,
		*,
		now        = None,
		cached     = {},
		rel_now    = True,
		show_secs  = False,
		future_msg = 'in the future'):
	e = int((now or time.time()) - t)
	key = f'{e}:{rel_now}:{show_secs}'
	if not key in cached:
		def add_suffix():
			return (
				((' ago'           if rel_now else '') if e > 0 else
				(f' {future_msg}' if rel_now else ' (negative elapsed)'))
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

def pretty_format(s, *, width=80, pfx=''):
	out = []
	while s:
		if len(s) <= width:
			out.append(s)
			break
		i = s[:width].rfind(' ')
		out.append(s[:i])
		s = s[i+1:]
	return pfx + ('\n'+pfx).join(out)

def block_format(data, *, gw=2, cols=8, line_nums=None, data_is_hex=False):
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

def pretty_hexdump(data, *, gw=2, cols=8, line_nums=None):
	return block_format(data.hex(), gw=gw, cols=cols, line_nums=line_nums, data_is_hex=True)

def decode_pretty_hexdump(data):
	pat = re.compile(fr'^[{hexdigits}]+:\s+')
	lines = [pat.sub('', line) for line in data.splitlines()]
	try:
		return bytes.fromhex(''.join((''.join(lines).split())))
	except:
		msg('Data not in hexdump format')
		return False

def cliargs_convert(args):

	# return str instead of float for input into JSON-RPC
	def float_parser(n):
		return n

	import json
	def gen():
		for arg in args:
			try:
				yield json.loads(arg, parse_float=float_parser) # list, dict, bool, int, null, float
			except json.decoder.JSONDecodeError:
				yield arg # arbitrary string

	return tuple(gen())

def port_in_use(port):
	import socket
	try:
		socket.create_connection(('localhost', port)).close()
	except:
		return False
	else:
		return True

class ExpInt(int):
	'encode or parse an integer in exponential notation with specified precision'

	max_prec = 10

	def __new__(cls, spec, *, prec):
		assert 0 < prec < cls.max_prec
		cls.prec = prec

		from .util import is_int
		if is_int(spec):
			return int.__new__(cls, spec)
		else:
			assert isinstance(spec, str), f'ExpInt: {spec!r}: not a string!'
			assert len(spec) >= 3, f'ExpInt: {spec!r}: invalid specifier'
			val, exp = spec.split('e')
			assert is_int(val) and is_int(exp)
			return int.__new__(cls, val + '0' * int(exp))

	@property
	def trunc(self):
		s = str(self)
		return int(s[:self.prec] + '0' * (len(s) - self.prec))

	@property
	def enc(self):
		s = str(self)
		s_len = len(s)
		digits = s[:min(s_len, self.prec)].rstrip('0')
		ret = '{}e{}'.format(digits, s_len - len(digits))
		return ret if len(ret) < s_len else s
