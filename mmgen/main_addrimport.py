#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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

from collections import namedtuple

from .common import *
from .addrlist import AddrList,KeyAddrList
from .tw.common import TwLabel

opts_data = {
	'text': {
		'desc': f'Import addresses into an {g.proj_name} tracking wallet',
		'usage':'[opts] [MMGen address file]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long options (common options)
-a, --address=a    Import the single coin address 'a'
-b, --batch        Import all addresses in one RPC call
-l, --addrlist     Address source is a flat list of non-MMGen coin addresses
-k, --keyaddr-file Address source is a key-address file
-q, --quiet        Suppress warnings
-r, --rescan       Update address balances by selectively rescanning the
                   blockchain for unspent outputs that include the imported
                   address(es).  Required if any of the imported addresses
                   are already in the blockchain and have a balance.
-t, --token-addr=A Import addresses for ERC20 token with address 'A'
""",
	'notes': """

This command can also be used to update the comment fields or balances of
addresses already in the tracking wallet.

Rescanning now uses the ‘scantxoutset’ RPC call and a selective scan of
blocks containing the relevant UTXOs for much faster performance than the
previous implementation.  The rescan operation typically takes around two
minutes total, independent of the number of addresses imported.

Bear in mind that the UTXO scan will not find historical transactions: to add
them to the tracking wallet, you must perform a full or partial rescan of the
blockchain with the ‘mmgen-tool rescan_blockchain’ utility.  A full rescan of
the blockchain may take up to several hours.

It’s recommended to use ‘--rpc-backend=aio’ with ‘--rescan’.
"""
	}
}

addrimport_msgs = {
	'rescan': """
		WARNING: You’ve chosen the ‘--rescan’ option.  Rescanning the blockchain is
		necessary only if an address you’re importing is already in an output or
		outputs in the blockchain but not all transactions involving the address
		are known to the tracking wallet.

		Rescanning is performed via the UTXO method, which is only minimally affected
		by the number of addresses imported and typically takes just a few minutes.
	""",
	'bad_args': f"""
		You must specify either an {g.proj_name} address file, a single address with
		the ‘--address’ option, or a flat list of non-{g.proj_name} addresses with
		the ‘--addrlist’ option.
	"""
}

def parse_cmd_args(rpc,cmd_args):

	def import_mmgen_list(infile):
		al = (AddrList,KeyAddrList)[bool(opt.keyaddr_file)](proto,infile)
		if al.al_id.mmtype in ('S','B'):
			if not rpc.info('segwit_is_active'):
				die(2,'Segwit is not active on this chain. Cannot import Segwit addresses')
		return al

	if len(cmd_args) == 1:
		infile = cmd_args[0]
		from .fileutil import check_infile,get_lines_from_file
		check_infile(infile)
		if opt.addrlist:
			al = AddrList(
				proto = proto,
				addrlist = get_lines_from_file(
					infile,
					f'non-{g.proj_name} addresses',
					trim_comments = True ) )
		else:
			al = import_mmgen_list(infile)
	elif len(cmd_args) == 0 and opt.address:
		al = AddrList(proto=proto,addrlist=[opt.address])
		infile = 'command line'
	else:
		die(1,addrimport_msgs['bad_args'])

	return al,infile

def check_opts(tw):
	batch = bool(opt.batch)
	rescan = bool(opt.rescan)

	if rescan and not 'rescan' in tw.caps:
		msg(f"‘--rescan’ ignored: not supported by {type(tw).__name__}")
		rescan = False

	if rescan and not opt.quiet:
		if not keypress_confirm(
				'\n{}\n\nContinue?'.format(addrimport_msgs['rescan']),
				default_yes = True ):
			die(1,'Exiting at user request')

	if batch and not 'batch' in tw.caps:
		msg(f"‘--batch’ ignored: not supported by {type(tw).__name__}")
		batch = False

	return batch,rescan

async def import_address(args):
	try:
		res = await args.tw.import_address( args.addr, args.lbl )
		qmsg(args.msg)
		return res
	except Exception as e:
		die(2,f'\nImport of address {args.addr!r} failed: {e.args[0]!r}')

def gen_args_list(tw,al,batch):

	fs = '{:%s} {:34} {:%s} - OK' % (
		len(str(al.num_addrs)) * 2 + 2,
		1 if opt.addrlist or opt.address else len(str(max(al.idxs()))) + 13 )

	ad = namedtuple('args_list_data',['addr','lbl','tw','msg'])

	for num,e in enumerate(al.data,1):
		if e.idx:
			label = f'{al.al_id}:{e.idx}' + (' ' + e.label if e.label else '')
			add_msg = label
		else:
			label = f'{proto.base_coin.lower()}:{e.addr}'
			add_msg = 'non-'+g.proj_name

		if batch:
			yield ad( e.addr, TwLabel(proto,label), None, None )
		else:
			yield ad(
				addr = e.addr,
				lbl  = TwLabel(proto,label),
				tw   = tw,
				msg  = fs.format(f'{num}/{al.num_addrs}:', e.addr, f'({add_msg})') )

async def main():
	from .tw.ctl import TrackingWallet
	if opt.token_addr:
		proto.tokensym = 'foo' # hack to trigger 'Token' in base_proto_subclass()

	tw = await TrackingWallet(
		proto      = proto,
		token_addr = opt.token_addr,
		mode       = 'i' )

	if opt.token or opt.token_addr:
		msg(f'Importing for token {tw.token.hl()} ({tw.token.hlc(proto.tokensym)})')

	from .rpc import rpc_init
	tw.rpc = await rpc_init(proto)

	for k,v in addrimport_msgs.items():
		addrimport_msgs[k] = fmt(v,indent='  ',strip_char='\t').rstrip()

	al,infile = parse_cmd_args(tw.rpc,cmd_args)

	qmsg(
		f'OK. {al.num_addrs} addresses'
		+ (f' from Seed ID {al.al_id.sid}' if hasattr(al.al_id,'sid') else '') )

	msg(
		f'Importing {len(al.data)} address{suf(al.data,"es")} from {infile}'
		+ (' (batch mode)' if opt.batch else '') )

	batch,rescan = check_opts(tw)

	args_list = list(gen_args_list(tw,al,batch))

	if batch:
		ret = await tw.batch_import_address([ (a.addr,a.lbl) for a in args_list ])
		msg(f'OK: {len(ret)} addresses imported')
	else:
		await asyncio.gather(*(import_address(a) for a in args_list))
		msg('Address import completed OK')

	if rescan:
		await tw.rescan_addresses({a.addr for a in args_list})

	del tw

cmd_args = opts.init(opts_data)
from .protocol import init_proto_from_opts
proto = init_proto_from_opts()
import asyncio
run_session(main())
