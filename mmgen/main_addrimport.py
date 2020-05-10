#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
mmgen-addrimport: Import addresses into a MMGen coin daemon tracking wallet
"""

import time

from .common import *
from .addr import AddrList,KeyAddrList
from .obj import TwLabel,is_coin_addr

ai_msgs = lambda k: {
	'rescan': """
WARNING: You've chosen the '--rescan' option.  Rescanning the blockchain is
necessary only if an address you're importing is already in the blockchain,
has a balance and is not in your tracking wallet.  Note that the rescanning
process is very slow (>30 min. for each imported address on a low-powered
computer).
	""".strip() if opt.rescan else """
WARNING: If any of the addresses you're importing is already in the blockchain,
has a balance and is not in your tracking wallet, you must exit the program now
and rerun it using the '--rescan' option.
""".strip(),
	'bad_args': """
You must specify an {pnm} address file, a single address with the '--address'
option, or a list of non-{pnm} addresses with the '--addrlist' option
""".strip().format(pnm=g.proj_name)
}[k]

# In batch mode, daemon just rescans each address separately anyway, so make
# --batch and --rescan incompatible.

opts_data = {
	'text': {
		'desc': """Import addresses into an {} tracking wallet""".format(g.proj_name),
		'usage':'[opts] [mmgen address file]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long options (common options)
-a, --address=a    Import the single coin address 'a'
-b, --batch        Import all addresses in one RPC call
-l, --addrlist     Address source is a flat list of non-MMGen coin addresses
-k, --keyaddr-file Address source is a key-address file
-q, --quiet        Suppress warnings
-r, --rescan       Rescan the blockchain.  Required if address to import is
                   in the blockchain and has a balance.  Rescanning is slow.
""",
	'notes': """\n
This command can also be used to update the comment fields of addresses
already in the tracking wallet.

The --batch and --rescan options cannot be used together.
"""
	}
}

def parse_cmd_args(cmd_args):

	def import_mmgen_list(infile):
		al = (AddrList,KeyAddrList)[bool(opt.keyaddr_file)](infile)
		if al.al_id.mmtype in ('S','B'):
			from .tx import segwit_is_active
			if not segwit_is_active():
				rdie(2,'Segwit is not active on this chain. Cannot import Segwit addresses')
		return al

	if len(cmd_args) == 1:
		infile = cmd_args[0]
		check_infile(infile)
		if opt.addrlist:
			al = AddrList(addrlist=get_lines_from_file(
				infile,
				'non-{pnm} addresses'.format(pnm=g.proj_name),
				trim_comments=True))
		else:
			al = import_mmgen_list(infile)
	elif len(cmd_args) == 0 and opt.address:
		al = AddrList(addrlist=[opt.address])
		infile = 'command line'
	else:
		die(1,ai_msgs('bad_args'))

	return al,infile

def check_opts(tw):
	batch = bool(opt.batch)
	rescan = bool(opt.rescan)

	if rescan and not 'rescan' in tw.caps:
		msg("'--rescan' ignored: not supported by {}".format(type(tw).__name__))
		rescan = False

	if rescan and not opt.quiet:
		confirm_or_raise(ai_msgs('rescan'),'continue',expect='YES')

	if batch and not 'batch' in tw.caps:
		msg("'--batch' ignored: not supported by {}".format(type(tw).__name__))
		batch = False

	return batch,rescan

async def import_addr(tw,addr,label,rescan,msg_fmt,msg_args):
	try:
		task = asyncio.ensure_future(tw.import_address(addr,label,rescan)) # Python 3.7+: create_task()
		if rescan:
			start = time.time()
			while True:
				if task.done():
					break
				msg_r(('\r{} '+msg_fmt).format(secs_to_hms(int(time.time()-start)),*msg_args))
				await asyncio.sleep(0.5)
			await task
			msg('\nOK')
		else:
			await task
			qmsg(msg_fmt.format(*msg_args) + ' - OK')
	except Exception as e:
		die(2,'\nImport of address {!r} failed: {!r}'.format(addr,e.args[0]))

def make_args_list(tw,al,batch,rescan):

	fs = '{:%s} {:34} {:%s}' % (
		len(str(al.num_addrs)) * 2 + 2,
		1 if opt.addrlist or opt.address else len(str(max(al.idxs()))) + 13 )

	for num,e in enumerate(al.data,1):
		if e.idx:
			label = '{}:{}'.format(al.al_id,e.idx) + (' ' + e.label if e.label else '')
			add_msg = label
		else:
			label = '{}:{}'.format(g.proto.base_coin.lower(),e.addr)
			add_msg = 'non-'+g.proj_name

		if batch:
			yield (e.addr,TwLabel(label),False)
		else:
			msg_args = ( f'{num}/{al.num_addrs}:', e.addr, '('+add_msg+')' )
			yield (tw,e.addr,TwLabel(label),rescan,fs,msg_args)

async def main():
	al,infile = parse_cmd_args(cmd_args)

	qmsg(
		f'OK. {al.num_addrs} addresses'
		+ (f' from Seed ID {al.al_id.sid}' if hasattr(al.al_id,'sid') else '') )

	msg(
		f'Importing {len(al.data)} address{suf(al.data,"es")} from {infile}'
		+ (' (batch mode)' if opt.batch else '') )

	if not al.data[0].addr.is_for_chain(g.chain):
		die(2,f'Address{(" list","")[bool(opt.address)]} incompatible with {g.chain} chain!')

	from .tw import TrackingWallet
	tw = await TrackingWallet(mode='i')

	batch,rescan = check_opts(tw)

	if g.token:
		await tw.import_token()

	args_list = make_args_list(tw,al,batch,rescan)

	if batch:
		ret = await tw.batch_import_address(list(args_list))
		msg(f'OK: {len(ret)} addresses imported')
	elif rescan:
		for arg_list in args_list:
			await import_addr(*arg_list)
	else:
		tasks = [import_addr(*arg_list) for arg_list in args_list]
		await asyncio.gather(*tasks)
		msg('OK')

	del tw

cmd_args = opts.init(opts_data)
import asyncio
run_session(main())
