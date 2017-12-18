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
test/gentest.py:  Cryptocoin key/address generation tests for the MMGen suite
"""

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

from binascii import hexlify

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.obj import MMGenAddrType

rounds = 100
opts_data = lambda: {
	'desc': "Test address generation in various ways",
	'usage':'[options] [spec] [rounds | dump file]',
	'options': """
-h, --help       Print this help message
--, --longhelp   Print help message for long options (common options)
-q, --quiet      Produce quieter output
-t, --type=t     Specify address type (valid options: 'compressed','segwit','zcash_z')
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
  {prog} 2:ext 100
    (compare output of secp256k1 library with external library (see below), 100 rounds)
  {prog} 2 1000
    (test speed of secp256k1 library address generation, 1000 rounds)
  {prog} 2 my.dump
    (compare addrs generated with secp256k1 library to {dn} wallet dump)

  External libraries required for the 'ext' generator:
    + pyethereum (for ETH,ETC)          https://github.com/ethereum/pyethereum
    + pycoin     (for all other coins)  https://github.com/richardkiss/pycoin
""".format(prog='gentest.py',pnm=g.proj_name,snum=rounds,dn=g.proto.daemon_name)
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]

cmd_args = opts.init(opts_data,add_opts=['exact_output'])

if not 1 <= len(cmd_args) <= 2: opts.usage()

addr_type = MMGenAddrType(opt.type or g.proto.dfl_mmtype)

def pyethereum_sec2addr(sec):
	return sec,eth.privtoaddr(sec).encode('hex')

def zcash_mini_sec2addr(sec):
	p = sp.Popen(['zcash-mini','-key','-simple'],stderr=sp.PIPE,stdin=sp.PIPE,stdout=sp.PIPE)
	p.stdin.write(sec.wif+'\n')
	o = p.stdout.read().split()
	return sec.wif,o[0],o[-1]

def pycoin_sec2addr(sec):
	if g.testnet: # pycoin/networks/all.py pycoin/networks/legacy_networks.py
		coin = { 'BTC':'XTN', 'LTC':'XLT', 'DASH':'tDASH' }[g.coin]
	else:
		coin = g.coin
	key = pcku.parse_key(sec,PREFIX_TRANSFORMS,coin)
	if key is None: die(1,"can't parse {}".format(sec))
	o = pcku.create_output(sec,key)[0]
#	pmsg(o)
	suf = ('_uncompressed','')[addr_type.compressed]
	wif = o['wif{}'.format(suf)]
	addr = o['p2sh_segwit' if addr_type.name == 'segwit' else '{}_address{}'.format(coin,suf)]
	return wif,addr

def init_external_prog():
	global b_desc,ext_lib,ext_sec2addr,sp,eth,pcku,PREFIX_TRANSFORMS
	if addr_type.name == 'zcash_z':
		import subprocess as sp
		ext_sec2addr = zcash_mini_sec2addr
		ext_lib = 'zcash_mini'
	elif addr_type.name == 'ethereum':
		try:
			import ethereum.utils as eth
		except:
			die(1,"Unable to import 'pyethereum' module. Is pyethereum installed?")
		ext_sec2addr = pyethereum_sec2addr
		ext_lib = 'pyethereum'
	else:
		try:
			import pycoin.cmds.ku as pcku
		except:
			die(1,"Unable to import module 'ku'. Is pycoin installed?")
		PREFIX_TRANSFORMS = pcku.prefix_transforms_for_network(g.coin)
		ext_sec2addr = pycoin_sec2addr
		ext_lib = 'pycoin'
	b_desc = ext_lib

def match_error(sec,wif,a_addr,b_addr,a,b):
	qmsg_r(red('\nERROR: Values do not match!'))
	die(3,"""
  sec key   : {}
  WIF key   : {}
  {a:10}: {}
  {b:10}: {}
""".format(sec,wif,a_addr,b_addr,pnm=g.proj_name,a=kg_a.desc,b=b_desc).rstrip())

def compare_test():
	m = "Comparing address generators '{}' and '{}' for coin {}"
	last_t = time.time()
	qmsg(green(m.format(kg_a.desc,(ext_lib if b == 'ext' else kg_b.desc),g.coin)))

	for i in range(rounds):
		if opt.verbose or time.time() - last_t >= 0.1:
			qmsg_r('\rRound %s/%s ' % (i+1,rounds))
			last_t = time.time()
		sec = PrivKey(os.urandom(32),compressed=addr_type.compressed,pubkey_type=addr_type.pubkey_type)
		ph = kg_a.to_pubhex(sec)
		a_addr = ag.to_addr(ph)
		if opt.type == 'zcash_z':
			a_vk = ag.to_viewkey(ph)
		if b == 'ext':
			if opt.type == 'zcash_z':
				b_wif,b_addr,b_vk = ext_sec2addr(sec)
				if b_vk != a_vk:
					match_error(sec,sec.wif,a_vk,b_vk,a,b)
			else:
				b_wif,b_addr = ext_sec2addr(sec)
			if b_wif != sec.wif:
				match_error(sec,sec.wif,sec.wif,b_wif,a,b)
		else:
			b_addr = ag.to_addr(kg_b.to_pubhex(sec))
		vmsg('\nkey:  %s\naddr: %s\n' % (sec.wif,a_addr))
		if a_addr != b_addr:
			match_error(sec,sec.wif,a_addr,b_addr,a,ext_lib if b == 'ext' else b)
	qmsg_r('\rRound %s/%s ' % (i+1,rounds))
	qmsg(green(('\n','')[bool(opt.verbose)] + 'OK'))

def speed_test():
	m = "Testing speed of address generator '{}' for coin {}"
	qmsg(green(m.format(kg_a.desc,g.coin)))
	from struct import pack,unpack
	seed = os.urandom(28)
	print 'Incrementing key with each round'
	print 'Starting key:', hexlify(seed+pack('I',0))
	import time
	start = last_t = time.time()

	for i in range(rounds):
		if time.time() - last_t >= 0.1:
			qmsg_r('\rRound %s/%s ' % (i+1,rounds))
			last_t = time.time()
		sec = PrivKey(seed+pack('I',i),compressed=addr_type.compressed,pubkey_type=addr_type.pubkey_type)
		a_addr = ag.to_addr(kg_a.to_pubhex(sec))
		vmsg('\nkey:  %s\naddr: %s\n' % (sec.wif,a_addr))
	qmsg_r('\rRound %s/%s ' % (i+1,rounds))
	qmsg('\n{} addresses generated in {:.2f} seconds'.format(rounds,time.time()-start))

def dump_test():
	m = "Comparing output of address generator '{}' against wallet dump '{}'"
	qmsg(green(m.format(kg_a.desc,cmd_args[1])))
	for n,[wif,a_addr] in enumerate(dump,1):
		qmsg_r('\rKey %s/%s ' % (n,len(dump)))
		try:
			sec = PrivKey(wif=wif)
		except:
			die(2,'\nInvalid {}net WIF address in dump file: {}'.format(('main','test')[g.testnet],wif))
		b_addr = ag.to_addr(kg_a.to_pubhex(sec))
		if a_addr != b_addr:
			match_error(sec,wif,a_addr,b_addr,3,a)
	qmsg(green(('\n','')[bool(opt.verbose)] + 'OK'))

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
b_desc = 'unknown'
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
		a = int(a)
		assert 1 <= a <= len(g.key_generators)
		if b == 'ext':
			init_external_prog()
		else:
			b = int(b)
			assert 1 <= b <= len(g.key_generators)
		assert a != b
	except:
		die(1,"%s: invalid generator IDs" % cmd_args[0])

from mmgen.addr import KeyGenerator,AddrGenerator
from mmgen.obj import PrivKey

kg_a = KeyGenerator(addr_type.pubkey_type,a)
ag = AddrGenerator(addr_type.gen_method)

if a and b:
	if b != 'ext':
		kg_b = KeyGenerator(addr_type.pubkey_type,b)
		b_desc = kg_b.desc
	compare_test()
elif a and not fh:
	speed_test()
elif a and dump:
	b_desc = 'dump'
	dump_test()
else:
	die(2,'Illegal invocation')
