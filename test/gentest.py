#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
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
test/gentest.py:  Bitcoin key/address generation tests for the MMGen suite
"""

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

from binascii import hexlify

# Import these _after_ local path's been added to sys.path
from mmgen.common import *
from mmgen.bitcoin import hex2wif,privnum2addr

start_mscolor()

rounds = 100
opts_data = {
	'desc': "Test address generation using various methods",
	'usage':'[options] a:b [rounds]',
	'options': """
-h, --help         Print this help message
-s, --system       Test scripts and modules installed on system rather than
                   those in the repo root
-v, --verbose      Produce more verbose output
""",
	'notes': """
{pnm} can generate addresses from secret keys using one of three methods,
as specified by the user:

    1) with the native Python ecdsa library (very slow)
    2) with the 'keyconv' utility from the 'vanitygen' package (old default)
    3) using bitcoincore.org's secp256k1 library (default from v0.8.6)

This test suite compares the output of these different methods against each
other over set of randomly generated secret keys ({snum} by default).

EXAMPLE:
  gentest.py 2:3 1000
  (compare output of 'keyconv' with secp256k1 library, 1000 rounds)
""".format(pnm=g.proj_name,snum=rounds)
}
cmd_args = opts.init(opts_data,add_opts=['exact_output'])

if not 1 <= len(cmd_args) <= 2: opts.usage()

if len(cmd_args) == 2:
	try:
		rounds = int(cmd_args[1])
		assert rounds > 0
	except:
		die(1,"'rounds' must be a positive integer")

try:
	a,b = cmd_args[0].split(':')
	a,b = int(a),int(b)
	for i in a,b: assert 1 <= i <= len(g.key_generators)
	assert a != b
except:
	die(1,"%s: incorrect 'a:b' specifier" % cmd_args[0])

if opt.system: sys.path.pop(0)

m = "Comparing address generators '{}' and '{}'"
msg(green(m.format(g.key_generators[a-1],g.key_generators[b-1])))
from mmgen.addr import get_privhex2addr_f
gen_a = get_privhex2addr_f(selector=a)
gen_b = get_privhex2addr_f(selector=b)
compressed = False
for i in range(1,rounds+1):
	msg_r('\rRound %s/%s ' % (i,rounds))
	sec = hexlify(os.urandom(32))
	wif = hex2wif(sec,compressed=compressed)
	a_addr = gen_a(sec,compressed)
	b_addr = gen_b(sec,compressed)
	vmsg('\nkey:  %s\naddr: %s\n' % (wif,a_addr))
	if a_addr != b_addr:
		msg_r(red('\nERROR: Addresses do not match!'))
		die(3,"""
  sec key: {}
  WIF key: {}
  {pnm}:   {}
  keyconv: {}
""".format(sec,wif,a_addr,b_addr,pnm=g.proj_name).rstrip())
	if a != 2 and b != 2:
		compressed = not compressed

msg(green(('\n','')[bool(opt.verbose)] + 'OK'))
