#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013 by philemon <mmgen-py@yandex.com>
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
secp256k1 = ecdsa.curves.Curve("secp256k1", curve_secp256k1, generator_secp256k1, oid_secp256k1)

b58a='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

#
# From en.bitcoin.it:
#   The Base58 encoding used is home made, and has some differences.
#   Especially, leading zeroes are kept as single zeroes when conversion
#   happens.
#
# Test: 5JbQQTs3cnoYN9vDYaGY6nhQ1DggVsY4FJNBUfEfpSQqrEp3srk
#
# The "zero address":
# 1111111111111111111114oLvT2 (use step2 = ("0" * 40) to generate)
#
def pubhex2addr(pubhex):
	step1 = sha256(unhexlify(pubhex)).digest()
	step2 = hashlib_new('ripemd160',step1).hexdigest()
	# See above:
	extra_ones = (len(step2) - len(step2.lstrip("0"))) / 2
	step3 = sha256(unhexlify('00'+step2)).digest()
	step4 = sha256(step3).hexdigest()
	pubkey = int(step2 + step4[:8], 16)
	return "1" + ("1" * extra_ones) + _numtob58(pubkey)

def privnum2addr(numpriv):
	pko = ecdsa.SigningKey.from_secret_exponent(numpriv,secp256k1)
	pubkey = hexlify(pko.get_verifying_key().to_string())
	return pubhex2addr('04'+pubkey)

def verify_addr(addr):

	if addr[0] != "1":
		print "%s: Invalid address" % addr
		return False

  	num = _b58tonum(addr[1:])
	if num == False: return False
  	addr_hex = hex(num)[2:].rstrip("L").zfill(48)

	step1 = sha256(unhexlify('00'+addr_hex[:40])).digest()
	step2 = sha256(step1).hexdigest()

	if step2[:8] != addr_hex[40:]:
		print "Invalid checksum in address %s" % ("1" + addr)
		return False

	return True

# Reworked code from here:

def _numtob58(num):
	b58conv,i = [],0
	while True:
		n = num / (58**i); i += 1
		if not n: break
		b58conv.append(b58a[n % 58])
	return ''.join(b58conv)[::-1]

def _b58tonum(b58num):
	for i in b58num:
		if not i in b58a:
			print "Invalid symbol in b58 number: '%s'" % i
			return False

	b58deconv = []
	b58num_r = b58num[::-1]
	for i in range(len(b58num)):
		idx = b58a.index(b58num_r[i])
		b58deconv.append(idx * (58**i))
	return sum(b58deconv)

def numtowif(numpriv):
	step1 = '80'+hex(numpriv)[2:].rstrip('L').zfill(64)
	step2 = sha256(unhexlify(step1)).digest()
	step3 = sha256(step2).hexdigest()
	key = step1 + step3[:8]
	return _numtob58(int(key,16))


# The following are mmgen internal (non-bitcoin) b58 functions

# Drop-in replacements for b64encode() and b64decode():
# (well, not exactly: they yield numeric but not bytewise equivalence)

def b58encode(s):
	if s == "": return ""
	num = int(hexlify(s),16)
	return _numtob58(num)

def b58decode(b58num):
	if b58num == "": return ""
	# Zap all spaces:
	num = _b58tonum(b58num.translate(None,' \t\n\r'))
	if num == False: return False
	out = hex(num)[2:].rstrip('L')
	return unhexlify("0" + out if len(out) % 2 else out)

# These yield bytewise equivalence in our special cases:

bin_lens = 16,24,32
b58_lens = 22,33,44

def _b58_pad(s,a,b,pad,f,w):
	try:
		outlen = b[a.index(len(s))]
	except:
		print "_b58_pad() accepts only %s %s bytes long "\
			"(input was %s bytes)" % (w,",".join([str(i) for i in a]),len(s))
		return False

	out = f(s)
	if out == False: return False
	return "%s%s" % (pad * (outlen - len(out)), out)

def b58encode_pad(s):
	return _b58_pad(s,
		a=bin_lens,b=b58_lens,pad="1",f=b58encode,w="binary strings")

def b58decode_pad(s):
	return _b58_pad(s,
		a=b58_lens,b=bin_lens,pad='\0',f=b58decode,w="base 58 numbers")


################### FUNCTIONS UNUSED BY MMGEN: ###################

# To check validity, recode with numtowif()
def wiftonum(wifpriv):
	num = _b58tonum(wifpriv)
	if num == False: return False
	return (num % (1<<288)) >> 32

def wiftohex(wifpriv):
	num = _b58tonum(wifpriv)
	if num == False: return False
	key = hex(num)[2:].rstrip('L')
	round1 = sha256(unhexlify(key[:66])).digest()
	round2 = sha256(round1).hexdigest()
	return key[2:66] if (key[:2] == '80' and key[66:] == round2[:8]) else False
