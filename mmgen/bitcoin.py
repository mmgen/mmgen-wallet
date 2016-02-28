#!/usr/bin/env python
#
# MMGen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
bitcoin.py:  Bitcoin address/key conversion functions
"""

import ecdsa
from binascii import hexlify, unhexlify
from hashlib import sha256
from hashlib import new as hashlib_new
import sys

# From electrum:
# secp256k1, http://www.oid-info.com/get/1.3.132.0.10
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
_b = 0x0000000000000000000000000000000000000000000000000000000000000007L
_a = 0x0000000000000000000000000000000000000000000000000000000000000000L
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L
curve_secp256k1 = ecdsa.ellipticcurve.CurveFp( _p, _a, _b )
generator_secp256k1 = ecdsa.ellipticcurve.Point( curve_secp256k1, _Gx, _Gy, _r )
oid_secp256k1 = (1,3,132,0,10)
secp256k1 = ecdsa.curves.Curve('secp256k1', curve_secp256k1, generator_secp256k1, oid_secp256k1)

b58a='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

#
# From en.bitcoin.it:
#   The Base58 encoding used is home made, and has some differences.
#   Especially, leading zeroes are kept as single zeroes when conversion
#   happens.
#
# Test: 5JbQQTs3cnoYN9vDYaGY6nhQ1DggVsY4FJNBUfEfpSQqrEp3srk
#
# The 'zero address':
# 1111111111111111111114oLvT2 (use step2 = ('0' * 40) to generate)
#

def pubhex2hexaddr(pubhex):
	step1 = sha256(unhexlify(pubhex)).digest()
	return hashlib_new('ripemd160',step1).hexdigest()

def hexaddr2addr(hexaddr, vers_num='00'):
	# See above:
	hexaddr2 = vers_num + hexaddr
	step1 = sha256(unhexlify(hexaddr2)).digest()
	step2 = sha256(step1).hexdigest()
	pubkey = hexaddr2 + step2[:8]
	lzeroes = (len(hexaddr2) - len(hexaddr2.lstrip('0'))) / 2
	return ('1' * lzeroes) + _numtob58(int(pubkey,16))

def verify_addr(addr,verbose=False,return_hex=False):

	for vers_num,ldigit in ('00','1'),('05','3'):
		if addr[0] != ldigit: continue
		num = _b58tonum(addr)
		if num == False: break
		addr_hex = '{:050x}'.format(num)
		if addr_hex[:2] != vers_num: continue
		step1 = sha256(unhexlify(addr_hex[:42])).digest()
		step2 = sha256(step1).hexdigest()
		if step2[:8] == addr_hex[42:]:
			return addr_hex[2:42] if return_hex else True
		else:
			if verbose: Msg("Invalid checksum in address '%s'" % addr)
			break

	if verbose: Msg("Invalid address '%s'" % addr)
	return False


# Reworked code from here:

def _numtob58(num):
	ret = []
	while num:
		ret.append(b58a[num % 58])
		num /= 58
	return ''.join(ret)[::-1]

def _b58tonum(b58num):
	for i in b58num:
		if not i in b58a: return False
	return sum([b58a.index(n) * (58**i) for i,n in enumerate(list(b58num[::-1]))])

def numtowif(numpriv):
	step1 = '80' + '{:064x}'.format(numpriv)
	step2 = sha256(unhexlify(step1)).digest()
	step3 = sha256(step2).hexdigest()
	key = step1 + step3[:8]
	return _numtob58(int(key,16))

# The following are MMGen internal (non-Bitcoin) b58 functions

# Drop-in replacements for b64encode() and b64decode():
# (well, not exactly: they yield numeric but not bytewise equivalence)

def b58encode(s):
	if s == '': return ''
	num = int(hexlify(s),16)
	return _numtob58(num)

def b58decode(b58num):
	if b58num == '': return ''
	# Zap all spaces:
	num = _b58tonum(b58num.translate(None,' \t\n\r'))
	if num == False: return False
	out = '{:x}'.format(num)
	return unhexlify('0'*(len(out)%2) + out)

# These yield bytewise equivalence in our special cases:

bin_lens = 16,24,32
b58_lens = 22,33,44

def _b58_pad(s,a,b,pad,f,w):
	try:
		outlen = b[a.index(len(s))]
	except:
		Msg('_b58_pad() accepts only %s %s bytes long '\
			'(input was %s bytes)' % (w,','.join([str(i) for i in a]),len(s)))
		return False

	out = f(s)
	if out == False: return False
	return '%s%s' % (pad * (outlen - len(out)), out)

def b58encode_pad(s):
	return _b58_pad(s,
		a=bin_lens,b=b58_lens,pad='1',f=b58encode,w='binary strings')

def b58decode_pad(s):
	return _b58_pad(s,
		a=b58_lens,b=bin_lens,pad='\0',f=b58decode,w='base 58 numbers')

# Compressed address support:

def wiftohex(wifpriv,compressed=False):
	idx = (66,68)[bool(compressed)]
	num = _b58tonum(wifpriv)
	if num == False: return False
	key = '{:x}'.format(num)
	if compressed and key[66:68] != '01': return False
	round1 = sha256(unhexlify(key[:idx])).digest()
	round2 = sha256(round1).hexdigest()
	return key[2:66] if (key[:2] == '80' and key[idx:] == round2[:8]) else False

def hextowif(hexpriv,compressed=False):
	step1 = '80' + hexpriv + ('','01')[bool(compressed)]
	step2 = sha256(unhexlify(step1)).digest()
	step3 = sha256(step2).hexdigest()
	key = step1 + step3[:8]
	return _numtob58(int(key,16))

def privnum2pubhex(numpriv,compressed=False):
	pko = ecdsa.SigningKey.from_secret_exponent(numpriv,secp256k1)
	pubkey = hexlify(pko.get_verifying_key().to_string())
	if compressed:
		p = ('03','02')[pubkey[-1] in '02468ace']
		return p+pubkey[:64]
	else:
		return '04'+pubkey

def privnum2addr(numpriv,compressed=False):
	return hexaddr2addr(pubhex2hexaddr(privnum2pubhex(numpriv,compressed)))
