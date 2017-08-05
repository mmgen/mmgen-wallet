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
mmgen-addrimport: Import addresses into a MMGen bitcoind tracking wallet
"""

import time

from mmgen.common import *
from mmgen.addr import AddrList,KeyAddrList
from mmgen.obj import TwLabel

# In batch mode, bitcoind just rescans each address separately anyway, so make
# --batch and --rescan incompatible.

def opts_data(): return {
	'desc': """Import addresses (both {pnm} and non-{pnm}) into an {pnm}
                     tracking wallet""".format(pnm=g.proj_name),
	'usage':'[opts] [mmgen address file]',
	'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long options (common options)
-a, --address=a    Import the single Bitcoin address 'a'
-b, --batch        Import all addresses in one RPC call.
-l, --addrlist     Address source is a flat list of (non-MMGen) Bitcoin addresses
-k, --keyaddr-file Address source is a key-address file
-q, --quiet        Suppress warnings
-r, --rescan       Rescan the blockchain.  Required if address to import is
                   on the blockchain and has a balance.  Rescanning is slow.
-t, --test         Simulate operation; don't actually import addresses
""",
	'notes': """\n
This command can also be used to update the comment fields of addresses already
in the tracking wallet.

The --batch and --rescan options cannot be used together.
"""
}

cmd_args = opts.init(opts_data)

def import_mmgen_list(infile):
	al = (AddrList,KeyAddrList)[bool(opt.keyaddr_file)](infile)
	if al.al_id.mmtype == 'S':
		from mmgen.tx import segwit_is_active
		if not segwit_is_active():
			rdie(2,'Segwit is not active on this chain. Cannot import Segwit addresses')
	return al

def import_flat_list(lines):
	al = AddrList(addrlist=lines)
	from mmgen.bitcoin import verify_addr
	qmsg_r('Validating addresses...')
	for e in al.data:
		if not verify_addr(e.addr,verbose=True):
			die(2,'\n%s: invalid address' % e.addr)
		if e.addr.addr_fmt == 'p2sh':
			fs = "\n'{}':\n  Non-{} P2SH addresses may not be imported into the tracking wallet"
			rdie(2,fs.format(e.addr,g.proj_name))
	return al

if len(cmd_args) == 1:
	infile = cmd_args[0]
	check_infile(infile)
	if opt.addrlist:
		lines = get_lines_from_file(
			infile,'non-{pnm} addresses'.format(pnm=g.proj_name),trim_comments=True)
		al = import_flat_list(lines)
	else:
		al = import_mmgen_list(infile)
elif len(cmd_args) == 0 and opt.address:
	al = import_flat_list([opt.address])
	infile = 'command line'
else:
	die(1,"""
You must specify an {pnm} address file, a single address, or a list of
non-{pnm} addresses with the '--addrlist' option)
""".strip().format(pnm=g.proj_name))

m = ' from Seed ID {}'.format(al.al_id.sid) if hasattr(al.al_id,'sid') else ''
qmsg('OK. {} addresses{}'.format(al.num_addrs,m))

if not opt.test:
	c = bitcoin_connection()

m = """
WARNING: You've chosen the '--rescan' option.  Rescanning the blockchain is
necessary only if an address you're importing is already on the blockchain,
has a balance and is not in your tracking wallet.  Note that the rescanning
process is very slow (>30 min. for each imported address on a low-powered
computer).
	""".strip() if opt.rescan else """
WARNING: If any of the addresses you're importing is already on the blockchain,
has a balance and is not in your tracking wallet, you must exit the program now
and rerun it using the '--rescan' option.
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

w_n_of_m = len(str(al.num_addrs)) * 2 + 2
w_mmid   = '' if opt.addrlist else len(str(max(al.idxs()))) + 12

if opt.rescan:
	import threading
	msg_fmt = '\r%s %-{}s %-34s %s'.format(w_n_of_m)
else:
	msg_fmt = '\r%-{}s %-34s %s'.format(w_n_of_m, w_mmid)

msg("Importing {} address{} from {}{}".format(
		len(al.data), suf(al.data,'es'), infile,
		('',' (batch mode)')[bool(opt.batch)]
	))

if not al.is_for_current_chain():
	die(2,"Address{} not compatible with {} chain!".format((' list','')[bool(opt.address)],g.chain))

arg_list = []
for n,e in enumerate(al.data):
	if e.idx:
		label = '{}:{}'.format(al.al_id,e.idx)
		if e.label: label += ' ' + e.label
		m = label
	else:
		label = 'btc:{}'.format(e.addr)
		m = 'non-'+g.proj_name

	label = TwLabel(label)

	if opt.batch:
		arg_list.append((e.addr,label,False))
	elif opt.rescan:
		t = threading.Thread(target=import_address,args=[e.addr,label,True])
		t.daemon = True
		t.start()

		start = int(time.time())

		while True:
			if t.is_alive():
				elapsed = int(time.time() - start)
				count = '%s/%s:' % (n+1, al.num_addrs)
				msg_r(msg_fmt % (secs_to_hms(elapsed),count,e.addr,'(%s)' % m))
				time.sleep(1)
			else:
				if err_flag: die(2,'\nImport failed')
				msg('\nOK')
				break
	else:
		import_address(e.addr,label,False)
		count = '%s/%s:' % (n+1, al.num_addrs)
		msg_r(msg_fmt % (count, e.addr, '(%s)' % m))
		if err_flag: die(2,'\nImport failed')
		msg(' - OK')

if opt.batch:
	ret = c.importaddress(arg_list,batch=True)
	msg('OK: %s addresses imported' % len(ret))
