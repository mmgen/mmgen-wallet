#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013-2014 by philemon <mmgen-py@yandex.com>
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
addr.py:  Address generation/display routines for mmgen suite
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
# Everything following a hash symbol '#' is a comment and ignored by {}.
# A text label of {} characters or less may be added to the right of each
# address, and it will be appended to the bitcoind wallet label upon import.
# The label may contain any printable ASCII symbol.
""".strip().format(g.proj_name,g.max_addr_label_len)
}

def test_for_keyconv():
	"""
	Test for the presence of 'keyconv' utility on system
	"""

	from subprocess import Popen, PIPE
	try:
		p = Popen([g.keyconv_exec, '-h'], stdout=PIPE, stderr=PIPE)
	except:
		sys.stderr.write("""
Executable '%s' unavailable. Falling back on (slow) internal ECDSA library.
Please install '%s' from the %s package on your system for much
faster address generation.

""" % (g.keyconv_exec, g.keyconv_exec, "vanitygen"))
		return False
	else:
		return True


def generate_addrs(seed, addrnums, opts):

	if not 'no_addresses' in opts:
		if 'no_keyconv' in opts or test_for_keyconv() == False:
			msg("Using (slow) internal ECDSA library for address generation")
			from mmgen.bitcoin import privnum2addr
			keyconv = False
		else:
			from subprocess import Popen, PIPE
			keyconv = "keyconv"

	a,t_addrs,i,out = sorted(addrnums),len(addrnums),0,[]

	while a:
		seed = sha512(seed).digest()
		i += 1 # round /i/

		if g.debug: print "Seed round %s: %s" % (i, hexlify(seed))

		if i < a[0]: continue

		a.pop(0)

		qmsg_r("\rGenerating %s %s (%s of %s)" %
			(opts['gen_what'], i, t_addrs-len(a), t_addrs))

		# Secret key is double sha256 of seed hash round /i/
		sec = sha256(sha256(seed).digest()).hexdigest()
		wif = numtowif(int(sec,16))

		if g.debug:
			print "Privkey round %s:\n  hex: %s\n  wif: %s" % (i, sec, wif)

		el = { 'num': i }

		if not 'print_addresses_only' in opts:
			el['sec'] = sec
			el['wif'] = wif

		if not 'no_addresses' in opts:
			if keyconv:
				p = Popen([keyconv, wif], stdout=PIPE)
				addr = dict([j.split() for j in \
						p.stdout.readlines()])['Address:']
			else:
				addr = privnum2addr(int(sec,16))

			el['addr'] = addr

		out.append(el)

	w = opts['gen_what']
	if t_addrs == 1:
		import re
		w = re.sub('e*s$','',w)

	qmsg("\rGenerated %s %s%s"%(t_addrs, w, " "*15))

	return out

def generate_keys(seed, addrnums):
	o = {'no_addresses': True, 'gen_what': "keys"}
	return generate_addrs(seed, addrnums, o)


def format_addr_data(addr_data, addr_data_chksum, seed_id, addr_list, opts):

	start = addr_data[0]['num']
	end   = addr_data[-1]['num']

	wif_msg = ""
	if ('b16' in opts and 'print_secret' in opts) \
		or 'no_addresses' in opts:
			wif_msg = " (wif)"

	fa = "%s%%-%ss %%-%ss %%s" % (
			" "*2, len(str(end)) + (0 if 'no_addresses' in opts else 1),
			(5 if 'print_secret' in opts else 1) + len(wif_msg)
		)

	data = []
	if not 'stdout' in opts: data.append(addrmsgs['addrfile_header'] + "\n")
	data.append("# Address data checksum for {}[{}]: {}".format(
				seed_id, fmt_addr_list(addr_list), addr_data_chksum))
	data.append("# Record this value to a secure location\n")
	data.append("%s {" % seed_id.upper())

	for el in addr_data:
		col1 = el['num']
		if 'no_addresses' in opts:
			if 'b16' in opts:
				data.append(fa % (col1, " (hex):", el['sec']))
				col1 = ""
			data.append(fa % (col1, " (wif):", el['wif']))
			if 'b16' in opts: data.append("")
		elif 'print_secret' in opts:
			if 'b16' in opts:
				data.append(fa % (col1, "sec (hex):", el['sec']))
				col1 = ""
			data.append(fa % (col1, "sec"+wif_msg+":", el['wif']))
			data.append(fa % ("",   "addr:", el['addr']))
			data.append("")
		else:
			data.append(fa % (col1, "", el['addr']))

	if not data[-1]: data.pop()
	data.append("}")

	return "\n".join(data) + "\n"


def fmt_addr_list(addr_list):

	addr_list = list(set(sorted(addr_list)))

	prev = addr_list[0]
	ret = prev,

	for i in addr_list[1:]:
		if i == prev + 1:
			if i == addr_list[-1]: ret += "-", i
		else:
			if prev != ret[-1]: ret += "-", prev
			ret += ",", i
		prev = i

	return "".join([str(i) for i in ret])


def write_addr_data_to_file(seed, addr_data_str, addr_list, opts):

	if 'print_addresses_only' in opts: ext = g.addrfile_ext
	elif 'no_addresses' in opts:       ext = g.keyfile_ext
	else:                              ext = "akeys"

	if 'b16' in opts: ext = ext.replace("keys","xkeys")
	from mmgen.util import write_to_file, make_chksum_8
	outfile = "{}[{}].{}".format(
			make_chksum_8(seed),
			fmt_addr_list(addr_list),
			ext
		)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)

	write_to_file(outfile,addr_data_str)

	dtype = "Address" if 'print_addresses_only' in opts else "Key"
	msg("%s data saved to file '%s'" % (dtype,outfile))
