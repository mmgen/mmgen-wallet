#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
#
# Ported to Python 3 (added floor division) from ed25519ll package:
#   https://pypi.org/project/ed25519ll/
# This module is adapted from that package's pure-Python fallback
# implementation.  All functions and vars not required by MMGen have
# been removed.
#
# ed25519ll, a low-level ctypes wrapper for Ed25519 digital signatures by
# Daniel Holth <dholth@fastmail.fm> - http://bitbucket.org/dholth/ed25519ll/
#   This wrapper also contains a reasonably performant pure-Python fallback.
#   Unlike the reference implementation, the Python implementation does not
#   contain protection against timing attacks.
#
# Ed25519 digital signatures
# Based on http://ed25519.cr.yp.to/python/ed25519.py
# See also http://ed25519.cr.yp.to/software.html
# Adapted by Ron Garret
# Sped up considerably using coordinate transforms found on:
# http://www.hyperelliptic.org/EFD/g1p/auto-twisted-extended-1.html
# Specifically add-2008-hwcd-4 and dbl-2008-hwcd

q = 2**255 - 19

def expmod(b,e,m):
	if e == 0:
		return 1
	t = expmod(b,e//2,m)**2 % m
	if e & 1:
		t = (t*b) % m
	return t

# Can probably get some extra speedup here by replacing this with
# an extended-euclidean, but performance seems OK without that
def inv(x):
	return expmod(x,q-2,q)

# Faster (!) version based on:
# http://www.hyperelliptic.org/EFD/g1p/auto-twisted-extended-1.html

def xpt_add(pt1, pt2):
	(X1, Y1, Z1, T1) = pt1
	(X2, Y2, Z2, T2) = pt2
	A = ((Y1-X1)*(Y2+X2)) % q
	B = ((Y1+X1)*(Y2-X2)) % q
	C = (Z1*2*T2) % q
	D = (T1*2*Z2) % q
	E = (D+C) % q
	F = (B-A) % q
	G = (B+A) % q
	H = (D-C) % q
	X3 = (E*F) % q
	Y3 = (G*H) % q
	Z3 = (F*G) % q
	T3 = (E*H) % q
	return (X3, Y3, Z3, T3)

def xpt_double (pt):
	(X1, Y1, Z1, _) = pt
	A = (X1*X1)
	B = (Y1*Y1)
	C = (2*Z1*Z1)
	D = (-A) % q
	J = (X1+Y1) % q
	E = (J*J-A-B) % q
	G = (D+B) % q
	F = (G-C) % q
	H = (D-B) % q
	X3 = (E*F) % q
	Y3 = (G*H) % q
	Z3 = (F*G) % q
	T3 = (E*H) % q
	return (X3, Y3, Z3, T3)

def pt_xform (pt):
	(x, y) = pt
	return (x, y, 1, (x*y)%q)

def pt_unxform (pt):
	(x, y, z, _) = pt
	return ((x*inv(z))%q, (y*inv(z))%q)

def xpt_mult (pt, n):
	if n==0:
		return pt_xform((0,1))
	_ = xpt_double(xpt_mult(pt, n>>1))
	return xpt_add(_, pt) if n&1 else _

def scalarmult(pt, e):
	return pt_unxform(xpt_mult(pt_xform(pt), e))
