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
mmgen-addrimport: Import addresses into a MMGen bitcoind watching wallet
"""

import sys
from mmgen.Opts   import *
from mmgen.license import *
from mmgen.util import *
from mmgen.tx import connect_to_bitcoind,parse_addrfile,parse_keyaddr_file

help_data = {
	'prog_name': g.prog_name,
	'desc': """Import addresses (both {pnm} and non-{pnm}) into a bitcoind
                     watching wallet""".format(pnm=g.proj_name),
	'usage':"[opts] [mmgen address file]",
	'options': """
-h, --help         Print this help message
-l, --addrlist     Address source is a flat list of addresses
-k, --keyaddr-file Address source is a key-address file
-q, --quiet        Suppress warnings
-r, --rescan       Rescan the blockchain.  Required if address to import is
                   on the blockchain and has a balance.  Rescanning is slow.
"""
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]
	check_infile(infile)
	if 'addrlist' in opts:
		lines = get_lines_from_file(infile,"non-{} addresses".format(g.proj_name),
				trim_comments=True)
		addr_list = [(None,l) for l in lines]
		seed_id = ""
	else:
		addr_data = {}
		pf = parse_keyaddr_file if 'keyaddr_file' in opts else parse_addrfile
		pf(infile,addr_data)
		seed_id = addr_data.keys()[0]
		e = addr_data[seed_id]
		addr_list = [(k,e[k][0],e[k][1]) for k in e.keys()]
else:
	msg_r("You must specify an mmgen address list (or a list of ")
	msg("non-%s addresses with\nthe '--addrlist' option)" % g.proj_name)
	sys.exit(1)

from mmgen.bitcoin import verify_addr
qmsg_r("Validating addresses...")
for n,i in enumerate(addr_list,1):
	if not verify_addr(i[1],verbose=True):
		msg("%s: invalid address" % i)
		sys.exit(2)
qmsg("OK. %s addresses%s" % (n," from seed ID "+seed_id if seed_id else ""))

import mmgen.config as g
g.http_timeout = 3600

c = connect_to_bitcoind()

m = """
WARNING: You've chosen the '--rescan' option.  Rescanning the block chain is
necessary only if an address you're importing is already on the block chain
and has a balance.  Note that the rescanning process is very slow (>30 min.
for each imported address on a low-powered computer).
	""".strip() if "rescan" in opts else """
WARNING: If any of the addresses you're importing is already on the block chain
and has a balance, you must exit the program now and rerun it using the
'--rescan' option.  Otherwise you may ignore this message and continue.
""".strip()

if g.quiet: m = ""
confirm_or_exit(m, "continue", expect="YES")

err_flag = False

def import_address(addr,label,rescan):
	try:
		c.importaddress(addr,label,rescan)
	except:
		global err_flag
		err_flag = True


w1 = len(str(len(addr_list))) * 2 + 2
w2 = "" if 'addrlist' in opts else \
		len(str(max([i[0] for i in addr_list if i[0]]))) + 12 \

if "rescan" in opts:
	import threading
	import time
	msg_fmt = "\r%s %-" + str(w1) + "s %-34s %-" + str(w2) + "s"
else:
	msg_fmt = "\r%-" + str(w1) + "s %-34s %-" + str(w2) + "s"

msg("Importing addresses")
for n,i in enumerate(addr_list):
	if i[0]:
		label = "%s:%s%s" % (seed_id,i[0], (" "+i[2] if i[2] else ""))
	else: label = "non-mmgen"

	if "rescan" in opts:
		t = threading.Thread(target=import_address, args=(i[1],label,True))
		t.daemon = True
		t.start()

		start = int(time.time())

		while True:
			if t.is_alive():
				elapsed = int(time.time() - start)
				msg_r(msg_fmt % (
						secs_to_hms(elapsed),
						("%s/%s:" % (n+1,len(addr_list))),
						i[1], "(" + label + ")"
					)
				)
				time.sleep(1)
			else:
				if err_flag: msg("\nImport failed"); sys.exit(2)
				msg("\nOK")
				break
	else:
		import_address(i[1],label,rescan=False)
		msg_r(msg_fmt % (("%s/%s:" % (n+1,len(addr_list))),
							i[1], "(" + label + ")"))
		if err_flag: msg("\nImport failed"); sys.exit(2)
		msg(" - OK")
