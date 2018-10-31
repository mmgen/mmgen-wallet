# The reference Ed25519 software is in the public domain.
#     Source: https://ed25519.cr.yp.to/python/ed25519.py
#     Date accessed: 2 Nov. 2016

b = 256
q = 2**255 - 19
l = 2**252 + 27742317777372353535851937790883648493

def expmod(b, e, m):
	if e == 0: return 1
	t = expmod(b, e//2, m)**2 % m
	if e & 1: t = (t*b) % m
	return t

def inv(x):
	return expmod(x, q-2, q)

d = -121665 * inv(121666)
I = expmod(2, (q-1)//4, q)

def xrecover(y):
	xx = (y*y-1) * inv(d*y*y+1)
	x = expmod(xx, (q+3)//8, q)
	if (x*x - xx) % q != 0: x = (x*I) % q
	if x % 2 != 0: x = q-x
	return x

By = 4 * inv(5)
Bx = xrecover(By)
B = [Bx%q, By%q]

def edwards(P, Q):
	x1 = P[0]
	y1 = P[1]
	x2 = Q[0]
	y2 = Q[1]
	x3 = (x1*y2+x2*y1) * inv(1+d*x1*x2*y1*y2)
	y3 = (y1*y2+x1*x2) * inv(1-d*x1*x2*y1*y2)
	return [x3%q, y3%q]

def scalarmult(P, e):
	if e == 0: return [0, 1]
	Q = scalarmult(P, e//2)
	Q = edwards(Q, Q)
	if e & 1: Q = edwards(Q, P)
	return Q

def encodepoint(P):
	x = P[0]
	y = P[1]
	bits = [(y >> i) & 1 for i in range(b-1)] + [x & 1]
	return bytes([sum([bits[i * 8 + j] << j for j in range(8)]) for i in range(b//8)])
