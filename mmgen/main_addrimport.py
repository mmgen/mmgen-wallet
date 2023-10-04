#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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

from .cfg import gc,Config
from .util import msg,suf,die,fmt,async_run
from .addrlist import AddrList,KeyAddrList

opts_data = {
	'text': {
		'desc': f'Import addresses into an {gc.proj_name} tracking wallet',
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
		You must specify either an {gc.proj_name} address file, a single address with
		the ‘--address’ option, or a flat list of non-{gc.proj_name} addresses with
		the ‘--addrlist’ option.
	"""
}

def parse_cmd_args(rpc,cmd_args):

	def import_mmgen_list(infile):
		al = (AddrList,KeyAddrList)[bool(cfg.keyaddr_file)](cfg,proto,infile)
		if al.al_id.mmtype in ('S','B'):
			if not rpc.info('segwit_is_active'):
				die(2,'Segwit is not active on this chain. Cannot import Segwit addresses')
		return al

	if len(cmd_args) == 1:
		infile = cmd_args[0]
		from .fileutil import check_infile,get_lines_from_file
		check_infile(infile)
		if cfg.addrlist:
			al = AddrList(
				cfg      = cfg,
				proto    = proto,
				addrlist = get_lines_from_file(
					cfg,
					infile,
					f'non-{gc.proj_name} addresses',
					trim_comments = True ) )
		else:
			al = import_mmgen_list(infile)
	elif len(cmd_args) == 0 and cfg.address:
		al = AddrList( cfg, proto=proto, addrlist=[cfg.address] )
		infile = 'command line'
	else:
		die(1,addrimport_msgs['bad_args'])

	return al,infile

def check_opts(twctl):
	batch = bool(cfg.batch)
	rescan = bool(cfg.rescan)

	if rescan and not 'rescan' in twctl.caps:
		msg(f"‘--rescan’ ignored: not supported by {type(twctl).__name__}")
		rescan = False

	if rescan and not cfg.quiet:
		from .ui import keypress_confirm
		if not keypress_confirm(
				cfg,
				f'\n{addrimport_msgs["rescan"]}\n\nContinue?',
				default_yes = True ):
			die(1,'Exiting at user request')

	if batch and not 'batch' in twctl.caps:
		msg(f"‘--batch’ ignored: not supported by {type(twctl).__name__}")
		batch = False

	return batch,rescan

async def main():
	from .tw.ctl import TwCtl
	if cfg.token_addr:
		proto.tokensym = 'foo' # hack to trigger 'Token' in proto.base_proto_subclass()

	twctl = await TwCtl(
		cfg        = cfg,
		proto      = proto,
		token_addr = cfg.token_addr,
		mode       = 'i' )

	if cfg.token or cfg.token_addr:
		msg(f'Importing for token {twctl.token.hl()} ({twctl.token.hlc(proto.tokensym)})')

	from .rpc import rpc_init
	twctl.rpc = await rpc_init(cfg,proto)

	for k,v in addrimport_msgs.items():
		addrimport_msgs[k] = fmt(v,indent='  ',strip_char='\t').rstrip()

	al,infile = parse_cmd_args(twctl.rpc,cfg._args)

	cfg._util.qmsg(
		f'OK. {al.num_addrs} addresses'
		+ (f' from Seed ID {al.al_id.sid}' if hasattr(al.al_id,'sid') else '') )

	msg(
		f'Importing {len(al.data)} address{suf(al.data,"es")} from {infile}'
		+ (' (batch mode)' if cfg.batch else '') )

	batch,rescan = check_opts(twctl)

	def gen_args_list(al):
		_d = namedtuple('import_data',['addr','twmmid','comment'])
		for e in al.data:
			yield _d(
				addr    = e.addr,
				twmmid  = f'{al.al_id}:{e.idx}' if e.idx else f'{proto.base_coin.lower()}:{e.addr}',
				comment = e.comment )

	args_list = list(gen_args_list(al))

	await twctl.import_address_common( args_list, batch=batch )

	if rescan:
		await twctl.rescan_addresses({a.addr for a in args_list})

	del twctl

cfg = Config( opts_data=opts_data, need_amt=False )

proto = cfg._proto

async_run(main())
