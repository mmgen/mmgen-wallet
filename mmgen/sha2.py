#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
sha2: A non-optimized but very compact implementation of the SHA2 hash
      algorithm for the MMGen suite.  Implements SHA256, SHA512 and
      SHA256Compress (unpadded SHA256, required for Zcash addresses)
"""

# IMPORTANT NOTE: Since GMP precision is platform-dependent, generated constants
# for SHA512 are not guaranteed to be correct!  Therefore, the SHA512
# implementation must not be used for anything but testing and study.  Test with
# the test/hashfunc.py script in the MMGen repository.

from struct import pack, unpack

class Sha2:
	'Implementation based on the pseudocode at https://en.wikipedia.org/wiki/SHA-2'
	K = ()

	@classmethod
	def initConstants(cls):

		from math import sqrt

		def nextPrime(n=2):
			while True:
				for factor in range(2, int(sqrt(n))+1):
					if n % factor == 0:
						break
				else:
					yield n
				n += 1

		# Find the first nRounds primes
		npgen = nextPrime()
		primes = [next(npgen) for x in range(cls.nRounds)]

		fb_mul = 2 ** cls.wordBits
		def getFractionalBits(n):
			return int((n - int(n)) * fb_mul)

		if cls.use_gmp:
			from gmpy2 import context, set_context, sqrt, cbrt
			# context() parameters are platform-dependent!
			set_context(context(precision=75, round=1)) # OK for gmp 6.1.2 / gmpy 2.1.0
		else:
			cbrt = lambda n: pow(n, 1 / 3)

		# First wordBits bits of the fractional parts of the square roots of the first 8 primes
		cls.H_init = tuple(getFractionalBits(sqrt(n)) for n in primes[:8])

		# First wordBits bits of the fractional parts of the cube roots of the first nRounds primes
		cls.K = tuple(getFractionalBits(cbrt(n)) for n in primes)

	def __init__(self, message, preprocess=True):
		'Use preprocess=False for Sha256Compress'
		assert isinstance(message, (bytes, bytearray, list)), 'message must be of type bytes, bytearray or list'
		if not self.K:
			type(self).initConstants()
		self.H = list(self.H_init)
		self.M = message
		self.W = [0] * self.nRounds
		if preprocess:
			self.padMessage()
		self.bytesToWords()
		self.compute()

	def padMessage(self):
		"""
		Pre-processing (padding) (adapted from the standard, translating bits to bytes)
		- Begin with the original message of length MSGLEN bytes
		- Create MLPACK := MSGLEN * 8 encoded as a blkSize-bit big-endian integer
		- Append 0x80 (0b10000000)
		- Append PADLEN null bytes, where PADLEN is the minimum number >= 0 such that
		  MSGLEN + 1 + PADLEN + len(MLPACK) is a multiple of blkSize
		- Append MLPACK
		"""
		mlpack = self.pack_msglen()
		padlen = self.blkSize - (len(self.M) % self.blkSize) - len(mlpack) - 1
		if padlen < 0:
			padlen += self.blkSize
		self.M = self.M + bytes([0x80] + [0] * padlen) + mlpack

	def bytesToWords(self):
		ws = self.wordSize
		assert len(self.M) % ws == 0
		self.M = tuple(unpack(self.word_fmt, self.M[i*ws:ws+(i*ws)])[0] for i in range(len(self.M) // ws))

	def digest(self):
		return b''.join((pack(self.word_fmt, w) for w in self.H))

	def hexdigest(self):
		return self.digest().hex()

	def compute(self):
		for i in range(0, len(self.M), 16):
			self.processBlock(i)

	def processBlock(self, offset):
		'Process a blkSize-byte chunk of the message'

		def rrotate(a, b):
			return ((a << self.wordBits-b) & self.wordMask) | (a >> b)

		def addm(a, b):
			return (a + b) & self.wordMask

		# Copy chunk into first 16 words of message schedule array
		for i in range(16):
			self.W[i] = self.M[offset + i]

		# Extend the first 16 words into the remaining nRounds words of message schedule array
		for i in range(16, self.nRounds):
			g0 = self.W[i-15]
			gamma0 = rrotate(g0, self.g0r1) ^ rrotate(g0, self.g0r2) ^ (g0 >> self.g0r3)
			g1 = self.W[i-2]
			gamma1 = rrotate(g1, self.g1r1) ^ rrotate(g1, self.g1r2) ^ (g1 >> self.g1r3)
			self.W[i] = addm(addm(addm(gamma0, self.W[i-7]), gamma1), self.W[i-16])

		# Initialize working variables from current hash state
		a, b, c, d, e, f, g, h = self.H

		# Compression function main loop
		for i in range(self.nRounds):
			ch = (e & f) ^ (~e & g)
			maj = (a & b) ^ (a & c) ^ (b & c)

			sigma0 = rrotate(a, self.s0r1) ^ rrotate(a, self.s0r2) ^ rrotate(a, self.s0r3)
			sigma1 = rrotate(e, self.s1r1) ^ rrotate(e, self.s1r2) ^ rrotate(e, self.s1r3)

			t1 = addm(addm(addm(addm(h, sigma1), ch), self.K[i]), self.W[i])
			t2 = addm(sigma0, maj)

			h = g
			g = f
			f = e
			e = addm(d, t1)
			d = c
			c = b
			b = a
			a = addm(t1, t2)

		# Save hash state
		for n, v in enumerate((a, b, c, d, e, f, g, h)):
			self.H[n] = addm(self.H[n], v)

class Sha256(Sha2):
	use_gmp = False
	g0r1, g0r2, g0r3 = (7, 18, 3)
	g1r1, g1r2, g1r3 = (17, 19, 10)
	s0r1, s0r2, s0r3 = (2, 13, 22)
	s1r1, s1r2, s1r3 = (6, 11, 25)
	blkSize = 64
	nRounds = 64
	wordSize = 4
	wordBits = 32
	wordMask = 0xffffffff
	word_fmt = '>I'

	def pack_msglen(self):
		return pack('>Q', len(self.M)*8)

class Sha512(Sha2):
	"""
	SHA-512 is identical in structure to SHA-256, but:
	- the message is broken into 1024-bit chunks,
	- the initial hash values and round constants are extended to 64 bits,
	- there are 80 rounds instead of 64,
	- the message schedule array W has 80 64-bit words instead of 64 32-bit words,
	- to extend the message schedule array W, the loop is from 16 to 79 instead of from 16 to 63,
	- the round constants are based on the first 80 primes 2..409,
	- the word size used for calculations is 64 bits long,
	- the appended length of the message (before pre-processing), in bits, is a 128-bit big-endian integer, and
	- the shift and rotate amounts used are different.
	"""
	use_gmp = True
	g0r1, g0r2, g0r3 = (1, 8, 7)
	g1r1, g1r2, g1r3 = (19, 61, 6)
	s0r1, s0r2, s0r3 = (28, 34, 39)
	s1r1, s1r2, s1r3 = (14, 18, 41)
	blkSize = 128
	nRounds = 80
	wordSize = 8
	wordBits = 64
	wordMask = 0xffffffffffffffff
	word_fmt = '>Q'

	def pack_msglen(self):
		return  pack('>Q', (len(self.M)*8) // (2**64)) + \
				pack('>Q', (len(self.M)*8) % (2**64))
