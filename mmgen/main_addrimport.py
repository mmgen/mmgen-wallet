#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
mmgen-addrimport: Import addresses into a MMGen bitcoind tracking wallet
"""

import sys, time
from mmgen.Opts   import *
from mmgen.license import *
from mmgen.util import *
from mmgen.tx import connect_to_bitcoind
from mmgen.addr import AddrInfo,AddrInfoEntry

help_data = {
	'prog_name': g.prog_name,
	'desc': """Import addresses (both {pnm} and non-{pnm}) into a bitcoind
                     tracking wallet""".format(pnm=g.proj_name),
	'usage':"[opts] [mmgen address file]",
	'options': """
-h, --help         Print this help message
-l, --addrlist     Address source is a flat list of addresses
-k, --keyaddr-file Address source is a key-address file
-q, --quiet        Suppress warnings
-r, --rescan       Rescan the blockchain.  Required if address to import is
                   on the blockchain and has a balance.  Rescanning is slow.
-t, --test         Simulate operation; don't actually import addresses
""",
	'notes': """\n
This command can also be used to update the comment fields of addresses already
in the tracking wallet.
"""
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]
	check_infile(infile)
	if 'addrlist' in opts:
		lines = get_lines_from_file(
			infile,"non-{} addresses".format(g.proj_name),trim_comments=True)
		ai,adata = AddrInfo(),[]
		for btcaddr in lines:
			a = AddrInfoEntry()
			a.idx,a.addr,a.comment = None,btcaddr,None
			adata.append(a)
		ai.initialize(None,adata)
	else:
		ai = AddrInfo(infile,has_keys='keyaddr_file' in opts)
else:
	msg("""
"You must specify an mmgen address file (or a list of non-%s addresses
with the '--addrlist' option)
""".strip() % g.proj_name)
	sys.exit(1)

from mmgen.bitcoin import verify_addr
qmsg_r("Validating addresses...")
for e in ai.addrdata:
	if not verify_addr(e.addr,verbose=True):
		msg("%s: invalid address" % e.addr)
		sys.exit(2)

m = (" from seed ID %s" % ai.seed_id) if ai.seed_id else ""
qmsg("OK. %s addresses%s" % (ai.num_addrs,m))

import mmgen.config as g
g.http_timeout = 3600

if not 'test' in opts:
	c = connect_to_bitcoind()

m = """
WARNING: You've chosen the '--rescan' option.  Rescanning the blockchain is
necessary only if an address you're importing is already on the blockchain,
has a balance and is not already in your tracking wallet.  Note that the
rescanning process is very slow (>30 min. for each imported address on a
low-powered computer).
	""".strip() if "rescan" in opts else """
WARNING: If any of the addresses you're importing is already on the blockchain,
has a balance and is not already in your tracking wallet, you must exit the
program now and rerun it using the '--rescan' option.  Otherwise you may ignore
this message and continue.
""".strip()

if g.quiet: m = ""
confirm_or_exit(m, "continue", expect="YES")

err_flag = False

def import_address(addr,label,rescan):
	try:
		if not 'test' in opts:
			c.importaddress(addr,label,rescan)
	except:
		global err_flag
		err_flag = True

w_n_of_m = len(str(ai.num_addrs)) * 2 + 2
w_mmid   = "" if 'addrlist' in opts else len(str(max(ai.idxs()))) + 12

if "rescan" in opts:
	import threading
	msg_fmt = "\r%s %-{}s %-34s %s".format(w_n_of_m)
else:
	msg_fmt = "\r%-{}s %-34s %s".format(w_n_of_m, w_mmid)

msg("Importing addresses")
for n,e in enumerate(ai.addrdata):
	if e.idx:
		label = "%s:%s" % (ai.seed_id,e.idx)
		if e.comment: label += " " + e.comment
	else: label = "non-%s" % g.proj_name

	if "rescan" in opts:
		t = threading.Thread(target=import_address, args=(e.addr,label,True))
		t.daemon = True
		t.start()

		start = int(time.time())

		while True:
			if t.is_alive():
				elapsed = int(time.time() - start)
				count = "%s/%s:" % (n+1, ai.num_addrs)
				msg_r(msg_fmt % (secs_to_hms(elapsed),count,e.addr,"(%s)"%label))
				time.sleep(1)
			else:
				if err_flag: msg("\nImport failed"); sys.exit(2)
				msg("\nOK")
				break
	else:
		import_address(e.addr,label,rescan=False)
		count = "%s/%s:" % (n+1, ai.num_addrs)
		msg_r(msg_fmt % (count, e.addr, "(%s)"%label))
		if err_flag:
			msg("\nImport failed")
			sys.exit(2)
		msg(" - OK")
