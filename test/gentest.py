#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
test/gentest.py:  Bitcoin key/address generation tests for the MMGen suite
"""

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

from binascii import hexlify

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.bitcoin import hex2wif

rounds = 100
opts_data = lambda: {
	'desc': "Test address generation in various ways",
	'usage':'[options] [spec] [rounds | dump file]',
	'options': """
-h, --help       Print this help message
--, --longhelp   Print help message for long options (common options)
-q, --quiet      Produce quieter output
-s, --segwit     Generate Segwit (P2SH-P2WPKH) addresses
-v, --verbose    Produce more verbose output
""",
	'notes': """
    Tests:
       A/B:     {prog} a:b [rounds]  (compare output of two key generators)
       Speed:   {prog} a [rounds]    (test speed of one key generator)
       Compare: {prog} a <dump file> (compare output of a key generator against wallet dump)
          where a and b are one of:
             '1' - native Python ecdsa library (very slow)
             '2' - bitcoincore.org's secp256k1 library (default from v0.8.6)

EXAMPLES:
  {prog} 1:2 100
    (compare output of native Python ECDSA with secp256k1 library, 100 rounds)
  {prog} 2 1000
    (test speed of secp256k1 library address generation, 1000 rounds)
  {prog} 2 my.dump
    (compare addrs generated with secp256k1 library to bitcoind wallet dump)
""".format(prog='gentest.py',pnm=g.proj_name,snum=rounds)
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cmd_args = opts.init(opts_data,add_opts=['exact_output'])

if not 1 <= len(cmd_args) <= 2: opts.usage()

urounds,fh = None,None
dump = []
if len(cmd_args) == 2:
	try:
		urounds = int(cmd_args[1])
		assert urounds > 0
	except:
		try:
			fh = open(cmd_args[1])
		except:
			die(1,"Second argument must be filename or positive integer")
		else:
			for line in fh.readlines():
				if 'addr=' in line:
					x,addr = line.split('addr=')
					dump.append([x.split()[0],addr.split()[0]])

if urounds: rounds = urounds

a,b = None,None
try:
	a,b = cmd_args[0].split(':')
except:
	try:
		a = cmd_args[0]
		a = int(a)
		assert 1 <= a <= len(g.key_generators)
	except:
		die(1,"First argument must be one or two generator IDs, colon separated")
else:
	try:
		a,b = int(a),int(b)
		for i in (a,b): assert 1 <= i <= len(g.key_generators)
		assert a != b
	except:
		die(1,"%s: invalid generator IDs" % cmd_args[0])

def match_error(sec,wif,a_addr,b_addr,a,b):
	m = ['','py-ecdsa','secp256k1','dump']
	qmsg_r(red('\nERROR: Addresses do not match!'))
	die(3,"""
  sec key   : {}
  WIF key   : {}
  {a:10}: {}
  {b:10}: {}
""".format(sec,wif,a_addr,b_addr,pnm=g.proj_name,a=m[a],b=m[b]).rstrip())

# Begin execution
mmtype = ('L','S')[bool(opt.segwit)]
compressed = True

from mmgen.addr import KeyGenerator,AddrGenerator
from mmgen.obj import PrivKey
ag = AddrGenerator(('p2pkh','segwit')[bool(opt.segwit)])

if a and b:
	m = "Comparing address generators '{}' and '{}'"
	qmsg(green(m.format(g.key_generators[a-1],g.key_generators[b-1])))
	last_t = time.time()
	kg_a = KeyGenerator(a)
	kg_b = KeyGenerator(b)

	for i in range(rounds):
		if time.time() - last_t >= 0.1:
			qmsg_r('\rRound %s/%s ' % (i+1,rounds))
			last_t = time.time()
		sec = PrivKey(os.urandom(32),compressed)
		a_addr = ag.to_addr(kg_a.to_pubhex(sec))
		b_addr = ag.to_addr(kg_b.to_pubhex(sec))
		vmsg('\nkey:  %s\naddr: %s\n' % (sec.wif,a_addr))
		if a_addr != b_addr:
			match_error(sec,sec.wif,a_addr,b_addr,a,b)
		if not opt.segwit:
			compressed = not compressed
	qmsg_r('\rRound %s/%s ' % (i+1,rounds))

	qmsg(green(('\n','')[bool(opt.verbose)] + 'OK'))
elif a and not fh:
	m = "Testing speed of address generator '{}'"
	qmsg(green(m.format(g.key_generators[a-1])))
	from struct import pack,unpack
	seed = os.urandom(28)
	print 'Incrementing key with each round'
	print 'Starting key:', hexlify(seed+pack('I',0))
	import time
	start = last_t = time.time()
	kg = KeyGenerator(a)

	for i in range(rounds):
		if time.time() - last_t >= 0.1:
			qmsg_r('\rRound %s/%s ' % (i+1,rounds))
			last_t = time.time()
		sec = PrivKey(seed+pack('I',i),compressed)
		a_addr = ag.to_addr(kg.to_pubhex(sec))
		vmsg('\nkey:  %s\naddr: %s\n' % (sec.wif,a_addr))
		if not opt.segwit:
			compressed = not compressed
	qmsg_r('\rRound %s/%s ' % (i+1,rounds))

	qmsg('\n{} addresses generated in {:.2f} seconds'.format(rounds,time.time()-start))
elif a and dump:
	m = "Comparing output of address generator '{}' against wallet dump '{}'"
	qmsg(green(m.format(g.key_generators[a-1],cmd_args[1])))
	kg = KeyGenerator(a)
	for n,[wif,a_addr] in enumerate(dump,1):
		qmsg_r('\rKey %s/%s ' % (n,len(dump)))
		try:
			sec = PrivKey(wif=wif)
		except:
			die(2,'\nInvalid {}net WIF address in dump file: {}'.format(('main','test')[g.testnet],wif))
		compressed = wif[0] != ('5','9')[g.testnet]
		b_addr = ag.to_addr(kg.to_pubhex(sec))
		if a_addr != b_addr:
			match_error(sec,wif,a_addr,b_addr,3,a)
	qmsg(green(('\n','')[bool(opt.verbose)] + 'OK'))
