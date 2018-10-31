#!/usr/bin/env python3


import sys,os,hashlib
from mmgen.sha256 import Sha256

random_rounds = int(sys.argv[1]) if len(sys.argv) == 2 else 500

def msg(s): sys.stderr.write(s)
def green(s): return '\033[32;1m' + s + '\033[0m'

def compare_hashes(dlen,data):
	sha2 = hashlib.sha256(data).hexdigest().encode()
#		msg('Dlen {:<5} {}\r'.format(dlen,sha2))
	my_sha2 = Sha256(data).hexdigest()
	assert my_sha2 == sha2,'Hashes do not match!'

def test_K():
	msg('Testing generated constants: ')
	K_ref = [1116352408,1899447441,-1245643825,-373957723,961987163,1508970993,-1841331548,-1424204075,-670586216,310598401,607225278,1426881987,1925078388,-2132889090,-1680079193,-1046744716,-459576895,-272742522,264347078,604807628,770255983,1249150122,1555081692,1996064986,-1740746414,-1473132947,-1341970488,-1084653625,-958395405,-710438585,113926993,338241895,666307205,773529912,1294757372,1396182291,1695183700,1986661051,-2117940946,-1838011259,-1564481375,-1474664885,-1035236496,-949202525,-778901479,-694614492,-200395387,275423344,430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,1955562222,2024104815,-2067236844,-1933114872,-1866530822,-1538233109,-1090935817,-965641998]
	def toSigned32(n): return ((n & 0xffffffff) ^ 0x80000000) - 0x80000000
	K_sig = [toSigned32(n) for n in Sha256.K]
	assert K_sig == K_ref,'Generated constants in K[] differ from reference value'
	msg('OK\n')

def test_ref():
	inputs = (
		'','x','xa','the','the quick','the quick brown fox',
		'\x00','\x00\x00','\x00'*256,'\x00'*512,'\x00'*511,'\x00'*513,
		'\x0f','\x0f\x0f','\x0f'*256,'\x0f'*512,'\x0f'*511,'\x0f'*513,
		'\x0f\x0d','\x0e\x0e'*256,'\x00\x0f'*512,'\x0e\x0f'*511,'\x0a\x0d'*513
	)
	for i,data in enumerate(inputs):
		msg('\rTesting reference input data: {:4}/{} '.format(i+1,len(inputs)))
		compare_hashes(len(data),data.encode())
	msg('OK\n')

def test_random(rounds):
	for i in range(rounds):
		if i+1 in (1,rounds) or not (i+1) % 10:
			msg('\rTesting random input data:    {:4}/{} '.format(i+1,rounds))
		dlen = int(os.urandom(4).encode('hex'),16) >> 18
		compare_hashes(dlen,os.urandom(dlen))
	msg('OK\n')

msg(green('Testing MMGen implementation of Sha256()\n'))
test_K()
test_ref()
test_random(random_rounds)
