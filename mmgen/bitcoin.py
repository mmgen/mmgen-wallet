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
_curve_secp256k1 = ecdsa.ellipticcurve.CurveFp(_p,_a,_b)
_generator_secp256k1 = ecdsa.ellipticcurve.Point(_curve_secp256k1,_Gx,_Gy,_r)
_oid_secp256k1 = (1,3,132,0,10)
_secp256k1 = ecdsa.curves.Curve('secp256k1',_curve_secp256k1,_generator_secp256k1,_oid_secp256k1)

b58a='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

# From en.bitcoin.it:
#   The Base58 encoding used is home made, and has some differences.
#   Especially, leading zeroes are kept as single zeroes when conversion
#   happens.
#
# Test: 5JbQQTs3cnoYN9vDYaGY6nhQ1DggVsY4FJNBUfEfpSQqrEp3srk
#
# The 'zero address':
# 1111111111111111111114oLvT2 (use step2 = ('0' * 40) to generate)

from mmgen.globalvars import g

def hash256(hexnum): # take hex, return hex - OP_HASH256
	return sha256(sha256(unhexlify(hexnum)).digest()).hexdigest()

def hash160(hexnum): # take hex, return hex - OP_HASH160
	return hashlib_new('ripemd160',sha256(unhexlify(hexnum)).digest()).hexdigest()

pubhex2hexaddr = hash160

def hexaddr2addr(hexaddr,p2sh=False):
	# devdoc/ref_transactions.md:
	s = ('00','6f','05','c4')[g.testnet+(2*p2sh)] + hexaddr.strip()
	lzeroes = (len(s) - len(s.lstrip('0'))) / 2
	return ('1' * lzeroes) + _numtob58(int(s+hash256(s)[:8],16))

def verify_addr(addr,verbose=False,return_hex=False):
	addr = addr.strip()
	for vers_num,ldigit in ('00','1'),('05','3'),('6f','mn'),('c4','2'):
		if addr[0] not in ldigit: continue
		num = _b58tonum(addr)
		if num == False: break
		addr_hex = '{:050x}'.format(num)
		if addr_hex[:2] != vers_num: continue
		if hash256(addr_hex[:42])[:8] == addr_hex[42:]:
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
	b58num = b58num.strip()
	for i in b58num:
		if not i in b58a: return False
	return sum([b58a.index(n) * (58**i) for i,n in enumerate(list(b58num[::-1]))])

# The following are MMGen internal (non-Bitcoin) b58 functions

# Drop-in replacements for b64encode() and b64decode():
# (well, not exactly: they yield numeric but not bytewise equivalence)

def b58encode(s):
	if s == '': return ''
	num = int(hexlify(s),16)
	return _numtob58(num)

def b58decode(b58num):
	b58num = b58num.strip()
	if b58num == '': return ''
	# Zap all spaces:
	# Use translate() only with str, not unicode
	num = _b58tonum(str(b58num).translate(None,' \t\n\r'))
	if num == False: return False
	out = u'{:x}'.format(num)
	return unhexlify(u'0'*(len(out)%2) + out)

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

def wif2hex(wif):
	wif = wif.strip()
	compressed = wif[0] != ('5','9')[g.testnet]
	num = _b58tonum(wif)
	if num == False: return False
	key = '{:x}'.format(num)
	klen = (66,68)[bool(compressed)]
	if compressed and key[66:68] != '01': return False
	if (key[:2] == ('80','ef')[g.testnet] and key[klen:] == hash256(key[:klen])[:8]):
		return key[2:66]
	else:
		return False

def hex2wif(hexpriv,compressed=False):
	s = ('80','ef')[g.testnet] + hexpriv.strip() + ('','01')[bool(compressed)]
	return _numtob58(int(s+hash256(s)[:8],16))

# devdoc/guide_wallets.md:
# Uncompressed public keys start with 0x04; compressed public keys begin with
# 0x03 or 0x02 depending on whether they're greater or less than the midpoint
# of the curve.
def privnum2pubhex(numpriv,compressed=False):
	pko = ecdsa.SigningKey.from_secret_exponent(numpriv,_secp256k1)
	# pubkey = 32-byte X coord + 32-byte Y coord (unsigned big-endian)
	pubkey = hexlify(pko.get_verifying_key().to_string())
	if compressed: # discard Y coord, replace with appropriate version byte
		# even Y: <0, odd Y: >0 -- https://bitcointalk.org/index.php?topic=129652.0
		p = ('03','02')[pubkey[-1] in '02468ace']
		return p+pubkey[:64]
	else:
		return '04'+pubkey

def privnum2addr(numpriv,compressed=False):
	return hexaddr2addr(pubhex2hexaddr(privnum2pubhex(numpriv,compressed)))
