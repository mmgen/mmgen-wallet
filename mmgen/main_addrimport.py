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
mmgen-addrimport: Import addresses into a MMGen bitcoind tracking wallet
"""

import time

from mmgen.common import *
from mmgen.tx import connect_to_bitcoind
from mmgen.addr import AddrInfo,AddrInfoEntry

opts_data = {
	'desc': """Import addresses (both {pnm} and non-{pnm}) into a bitcoind
                     tracking wallet""".format(pnm=g.proj_name),
	'usage':'[opts] [mmgen address file]',
	'options': """
-h, --help         Print this help message
-b, --batch        Batch mode.  Import all addresses in one RPC call
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

cmd_args = opts.init(opts_data)

if len(cmd_args) == 1:
	infile = cmd_args[0]
	check_infile(infile)
	if opt.addrlist:
		lines = get_lines_from_file(
			infile,'non-{pnm} addresses'.format(pnm=g.proj_name),trim_comments=True)
		ai,adata = AddrInfo(),[]
		for btcaddr in lines:
			a = AddrInfoEntry()
			a.idx,a.addr,a.comment = None,btcaddr,None
			adata.append(a)
		ai.initialize(None,adata)
	else:
		ai = AddrInfo(infile,has_keys=opt.keyaddr_file)
else:
	die(1,"""
You must specify an {pnm} address file (or a list of non-{pnm} addresses
with the '--addrlist' option)
""".strip().format(pnm=g.proj_name))

from mmgen.bitcoin import verify_addr
qmsg_r('Validating addresses...')
for e in ai.addrdata:
	if not verify_addr(e.addr,verbose=True):
		die(2,'%s: invalid address' % e.addr)

m = (' from Seed ID %s' % ai.seed_id) if ai.seed_id else ''
qmsg('OK. %s addresses%s' % (ai.num_addrs,m))

if not opt.test:
	c = connect_to_bitcoind()

m = """
WARNING: You've chosen the '--rescan' option.  Rescanning the blockchain is
necessary only if an address you're importing is already on the blockchain,
has a balance and is not already in your tracking wallet.  Note that the
rescanning process is very slow (>30 min. for each imported address on a
low-powered computer).
	""".strip() if opt.rescan else """
WARNING: If any of the addresses you're importing is already on the blockchain,
has a balance and is not already in your tracking wallet, you must exit the
program now and rerun it using the '--rescan' option.  Otherwise you may ignore
this message and continue.
""".strip()

if not opt.quiet: confirm_or_exit(m, 'continue', expect='YES')

err_flag = False

def import_address(addr,label,rescan):
	try:
		if not opt.test:
			c.importaddress(addr,label,rescan,timeout=(False,3600)[rescan])
	except:
		global err_flag
		err_flag = True

w_n_of_m = len(str(ai.num_addrs)) * 2 + 2
w_mmid   = '' if opt.addrlist else len(str(max(ai.idxs()))) + 12

if opt.rescan:
	import threading
	msg_fmt = '\r%s %-{}s %-34s %s'.format(w_n_of_m)
else:
	msg_fmt = '\r%-{}s %-34s %s'.format(w_n_of_m, w_mmid)

msg("Importing %s addresses from '%s'%s" %
		(len(ai.addrdata),infile,('',' (batch mode)')[bool(opt.batch)]))

arg_list = []
for n,e in enumerate(ai.addrdata):
	if e.idx:
		label = '%s:%s' % (ai.seed_id,e.idx)
		if e.comment: label += ' ' + e.comment
	else: label = 'non-{pnm}'.format(pnm=g.proj_name)

	if opt.batch:
		arg_list.append((e.addr,label,False))
	elif opt.rescan:
		t = threading.Thread(target=import_address, args=(e.addr,label,True))
		t.daemon = True
		t.start()

		start = int(time.time())

		while True:
			if t.is_alive():
				elapsed = int(time.time() - start)
				count = '%s/%s:' % (n+1, ai.num_addrs)
				msg_r(msg_fmt % (secs_to_hms(elapsed),count,e.addr,'(%s)'%label))
				time.sleep(1)
			else:
				if err_flag: die(2,'\nImport failed')
				msg('\nOK')
				break
	else:
		import_address(e.addr,label,False)
		count = '%s/%s:' % (n+1, ai.num_addrs)
		msg_r(msg_fmt % (count, e.addr, '(%s)'%label))
		if err_flag: die(2,'\nImport failed')
		msg(' - OK')

if opt.batch:
	if opt.rescan:
		msg('Warning: this command may take a long time to complete!')
	ret = c.importaddress(arg_list,batch=True,timeout=(False,3600)[bool(opt.rescan)])
	msg('OK: %s addresses imported' % len(ret))
