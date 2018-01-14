#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
sha256.py: custom sha256 implementation for Zcash
"""

# Sha256 code ported from JavaScript, originally here:
#   CryptoJS v3.1.2 code.google.com/p/crypto-js
#   (c) 2009-2013 by Jeff Mott. All rights reserved.
#   code.google.com/p/crypto-js/wiki/License
# via here:
#   https://www.npmjs.com/package/sha256
# and here:
#   https://github.com/howardwu/zaddr

class Sha256(object):

	def initConstants():
		import math
		def isPrime(n):
			for factor in range(2,int(math.sqrt(n))+1):
				if not (n % factor): return False
			return True

		def getFractionalBits(n):
			return int((n - int(n)) * 0x100000000)

		k = [0] * 64
		n,nPrime = 2,0
		while nPrime < 64:
			if isPrime(n):
				k[nPrime] = getFractionalBits(math.pow(n, 1.0 / 3))
				nPrime += 1
			n += 1

		return k

	K = initConstants()

	# preprocess: True=Sha256(), False=Sha256Compress()
	def __init__(self,message,preprocess=True):
		self.H = [0x6A09E667,0xBB67AE85,0x3C6EF372,0xA54FF53A,0x510E527F,0x9B05688C,0x1F83D9AB,0x5BE0CD19]
		self.M = message
		self.W = [0] * 64
		(self.bytesToWords,self.preprocessBlock)[preprocess]()
#		self.initConstants()
		self.compute()

	def digest(self):
		self.M = self.H
		self.wordsToBytes()
		return self.M

	def hexdigest(self):
		return self.digest().encode('hex')

	def bytesToWords(self):
		assert type(self.M) in (str,list)
		words = [0] * (len(self.M) / 4 + len(self.M) % 4)
		b = 0
		for i in range(len(self.M)):
			words[b >> 5] |= ord(self.M[i]) << (24 - b % 32)
			b += 8
		self.M = words

	def wordsToBytes(self):
		assert type(self.M) == list and len(self.M) == 8
		self.M = ''.join([chr((self.M[b >> 5] >> (24 - b % 32)) & 0xff) for b in range(0,len(self.M)*32,8)])

	def preprocessBlock(self):
		def lshift(a,b): return (a << b) & 0xffffffff
		assert type(self.M) == str
		l = len(self.M) * 8
		self.bytesToWords()
		last_idx = lshift((l + 64 >> 9),4) + 15
		self.M.extend([0] * (last_idx - len(self.M) + 1))
		self.M[l >> 5] |= lshift(0x80, (24 - l % 32))
		self.M[last_idx] = l

	def compute(self):
		assert type(self.M) == list
		for i in range(0,len(self.M),16):
			self.processBlock(i)

	def processBlock(self,offset):
		def lshift(a,b): return (a << b) & 0xffffffff
		def sumr(a,b):   return (a + b) & 0xffffffff
		a,b,c,d,e,f,g,h = [self.H[i] for i in range(8)] # Working variables

		for i in range(64):
			if i < 16:
				self.W[i] = self.M[offset + i]
			else:
				gamma0x = self.W[i - 15]
				gamma0 = ( (lshift(gamma0x,25) | (gamma0x >> 7)) ^
							(lshift(gamma0x,14) | (gamma0x >> 18)) ^
							(gamma0x >> 3) )
				gamma1x = self.W[i - 2]
				gamma1 = ( (lshift(gamma1x,15) | (gamma1x >> 17)) ^
							(lshift(gamma1x,13) | (gamma1x >> 19)) ^
							(gamma1x >> 10) )
				self.W[i] = sumr(sumr(sumr(gamma0,self.W[i - 7]),gamma1),self.W[i - 16])

			ch = (e & f) ^ (~e & g)
			maj = (a & b) ^ (a & c) ^ (b & c)

			sigma0 = (lshift(a,30) | (a >> 2)) ^ (lshift(a,19) | (a >> 13)) ^ (lshift(a,10) | (a >> 22))
			sigma1 = (lshift(e,26) | (e >> 6)) ^ (lshift(e,21) | (e >> 11)) ^ (lshift(e,7) | (e >> 25))

			t1 = sumr(sumr(sumr(sumr(h,sigma1),ch),self.K[i]),self.W[i])
			t2 = sumr(sigma0,maj)

			h = g
			g = f
			f = e
			e = sumr(d,t1)
			d = c
			c = b
			b = a
			a = sumr(t1,t2)

		# Intermediate hash value
		for n,v in enumerate([a,b,c,d,e,f,g,h]):
			self.H[n] = sumr(self.H[n],v)
