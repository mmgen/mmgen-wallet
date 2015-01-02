#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
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
addr.py:  Address generation/display routines for the MMGen suite
"""

import sys
from hashlib import sha256, sha512
from hashlib import new as hashlib_new
from binascii import hexlify, unhexlify

from mmgen.bitcoin import numtowif
from mmgen.util import msg,qmsg,qmsg_r
import mmgen.config as g

addrmsgs = {
	'addrfile_header': """
# MMGen address file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {} characters or less may be added to the right of each
# address, and it will be appended to the bitcoind wallet label upon import.
# The label may contain any printable ASCII symbol.
""".strip().format(g.max_addr_label_len,pnm=g.proj_name),
	'no_keyconv_msg': """
Executable '{kcexe}' unavailable. Falling back on (slow) internal ECDSA library.
Please install '{kcexe}' from the {vanityg} package on your system for much
faster address generation.
""".format(kcexe=g.keyconv_exec, vanityg="vanitygen")
}

def test_for_keyconv():

	from subprocess import check_output,STDOUT
	try:
		check_output([g.keyconv_exec, '-G'],stderr=STDOUT)
	except:
		msg(addrmsgs['no_keyconv_msg'])
		return False

	return True


def generate_addrs(seed, addrnums, opts, seed_id=""):

	if 'a' in opts['gen_what']:
		if g.no_keyconv or test_for_keyconv() == False:
			msg("Using (slow) internal ECDSA library for address generation")
			from mmgen.bitcoin import privnum2addr
			keyconv = False
		else:
			from subprocess import check_output
			keyconv = "keyconv"

	ai_attrs = ("num,sec,wif,addr") if 'ka' in opts['gen_what'] else (
		("num,sec,wif") if 'k' in opts['gen_what'] else ("num,addr"))

	from collections import namedtuple
	addrinfo = namedtuple("addrinfo",ai_attrs.split(","))

	addrnums = sorted(set(addrnums)) # don't trust the calling function
	t_addrs,num,pos,out = len(addrnums),0,0,[]

	w = {
		'ka': ('key/address pair','s'),
		'k':  ('key','s'),
		'a':  ('address','es')
	}[opts['gen_what']]

	while pos != t_addrs:
		seed = sha512(seed).digest()
		num += 1 # round

		if g.debug: print "Seed round %s: %s" % (num, hexlify(seed))
		if num != addrnums[pos]: continue

		pos += 1

		qmsg_r("\rGenerating %s #%s (%s of %s)" % (w[0],num,pos,t_addrs))

		# Secret key is double sha256 of seed hash round /num/
		sec = sha256(sha256(seed).digest()).hexdigest()
		wif = numtowif(int(sec,16))

		if 'a' in opts['gen_what']:
			if keyconv:
				addr = check_output([keyconv, wif]).split()[1]
			else:
				addr = privnum2addr(int(sec,16))

		out.append(addrinfo(*eval(ai_attrs)))

	m = w[0] if t_addrs == 1 else w[0]+w[1]
	if seed_id:
		qmsg("\r%s: %s %s generated%s" % (seed_id,t_addrs,m," "*15))
	else:
		qmsg("\rGenerated %s %s%s" % (t_addrs,m," "*15))

	return out


def format_addr_data(addr_data, addr_data_chksum, seed_id, addr_idxs, opts):

	fs = "  {:<%s}  {}" % len(str(addr_data[-1].num))

	if 'a' in opts['gen_what']:
		out = [] if 'stdout' in opts else [addrmsgs['addrfile_header']+"\n"]
		w = "Key-address" if 'k' in opts['gen_what'] else "Address"
		out.append("# {} data checksum for {}[{}]: {}".format(
					w, seed_id, fmt_addr_idxs(addr_idxs), addr_data_chksum))
		out.append("# Record this value to a secure location\n")
	else: out = []

	out.append("%s {" % seed_id.upper())

	for d in addr_data:
		if 'a' in opts['gen_what']:  # First line with number
			out.append(fs.format(d.num, d.addr))
		else:
			out.append(fs.format(d.num, "wif: "+d.wif))

		if 'k' in opts['gen_what']:   # Subsequent lines
			if 'b16' in opts:
				out.append(fs.format("", "hex: "+d.sec))
			if 'a' in opts['gen_what']:
				out.append(fs.format("", "wif: "+d.wif))

	out.append("}")

	return "\n".join(out) + "\n"


def fmt_addr_idxs(addr_idxs):

	addr_idxs = list(sorted(set(addr_idxs)))

	prev = addr_idxs[0]
	ret = prev,

	for i in addr_idxs[1:]:
		if i == prev + 1:
			if i == addr_idxs[-1]: ret += "-", i
		else:
			if prev != ret[-1]: ret += "-", prev
			ret += ",", i
		prev = i

	return "".join([str(i) for i in ret])
