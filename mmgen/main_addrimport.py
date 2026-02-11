#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
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

from .cfg import gc, Config
from .util import msg, suf, die, fmt, async_run
from .addrlist import AddrList, KeyAddrList

opts_data = {
	'filter_codes': ['-'],
	'text': {
		'desc': f'Import addresses into an {gc.proj_name} tracking wallet',
		'usage': '{u_args}',
		'options': """
			-- -h, --help         Print this help message
			-- --, --longhelp     Print help message for long (global) options
			m- -a, --autosign     Import addresses from pre-created key-address file on the
			+                     removable device.  The removable device is mounted and
			+                     unmounted automatically.  See notes below.
			R- -A, --address=ADDR Import the single coin address ADDR
			R- -b, --batch        Import all addresses in one RPC call (where applicable)
			R- -l, --addrlist     Address source is a flat list of non-MMGen coin addresses
			R- -k, --keyaddr-file Address source is a key-address file
			-- -q, --quiet        Suppress warnings
			b- -r, --rescan       Update address balances by selectively rescanning the
			+                     blockchain for unspent outputs that include the imported
			+                     address(es).  Required if any of the imported addresses
			+                     are already in the blockchain and have a balance.
			e- -t, --token-addr=ADDR Import addresses for ERC20 token with address ADDR
""",
	'notes': '{notes}',
	},
	'code': {
		'usage': lambda help_notes, s: s.format(
			u_args = help_notes('addrimport_args')),
		'notes': lambda help_mod, s: s.format(
			notes = help_mod('addrimport'))
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

def parse_cmd_args(cmd_args):

	def import_mmgen_list(infile):
		return (AddrList, KeyAddrList)[bool(cfg.keyaddr_file)](cfg, proto, infile=infile)

	match cmd_args:
		case [infile]:
			from .fileutil import check_infile, get_lines_from_file
			check_infile(infile)
			if cfg.addrlist:
				return (
					AddrList(
						cfg      = cfg,
						proto    = proto,
						addrlist = get_lines_from_file(
							cfg,
							infile,
							desc = f'non-{gc.proj_name} addresses',
							trim_comments = True)),
					infile)
			else:
				return (import_mmgen_list(infile), infile)
		case [] if cfg.address:
			return (AddrList(cfg, proto=proto, addrlist=[cfg.address]), 'command line')
		case _:
			die(1, addrimport_msgs['bad_args'])

def check_opts(twctl):
	batch = bool(cfg.batch)
	rescan = bool(cfg.rescan)

	if rescan and not 'rescan' in twctl.caps:
		msg(f"‘--rescan’ ignored: not supported by {type(twctl).__name__}")
		rescan = False

	if rescan and not cfg.quiet:
		from .ui import keypress_confirm
		keypress_confirm(
			cfg,
			f'\n{addrimport_msgs["rescan"]}\n\nContinue?',
			default_yes = True,
			do_exit = True)

	if batch and not 'batch' in twctl.caps:
		msg(f"‘--batch’ ignored: not supported by {type(twctl).__name__}")
		batch = False

	return batch, rescan

def check_xmr_args():
	if not cfg.autosign:
		die(1, 'For XMR address import, --autosign is required')
	if cfg._args:
		die(1, 'Address file arg not supported with --autosign')

async def main():

	if cfg._proto.base_coin == 'XMR':
		from .tx.util import mount_removable_device
		from .xmrwallet import op as xmrwallet_op
		check_xmr_args()
		mount_removable_device(cfg)
		op = xmrwallet_op('create', cfg, None, None, compat_call=True)
		if op.to_process:
			await op.restart_wallet_daemon()
			await op.main()
		return

	from .tw.ctl import TwCtl
	twctl = await TwCtl(
		cfg        = cfg,
		proto      = proto,
		token_addr = cfg.token_addr,
		mode       = 'i')

	if cfg.token or cfg.token_addr:
		msg(f'Importing for token {twctl.token.hl(0)} ({twctl.token.hlc(proto.tokensym)})')

	for k, v in addrimport_msgs.items():
		addrimport_msgs[k] = fmt(v, indent='  ', strip_char='\t').rstrip()

	al, infile = parse_cmd_args(cfg._args)

	cfg._util.qmsg(
		f'OK. {al.num_addrs} addresses'
		+ (f' from Seed ID {al.al_id.sid.hl()}' if hasattr(al.al_id, 'sid') else ''))

	msg(
		f'Importing {len(al.data)} address{suf(al.data, "es")} from {infile}'
		+ (' (batch mode)' if cfg.batch else ''))

	batch, rescan = check_opts(twctl)

	def gen_args_list(al):
		_d = namedtuple('import_data', ['addr', 'twmmid', 'comment'])
		for e in al.data:
			yield _d(
				addr    = e.addr,
				twmmid  = f'{al.al_id}:{e.idx}' if e.idx else f'{proto.base_coin.lower()}:{e.addr}',
				comment = e.comment)

	args_list = list(gen_args_list(al))

	await twctl.import_address_common(args_list, batch=batch)

	if rescan:
		await twctl.rescan_addresses({a.addr for a in args_list})

	del twctl

cfg = Config(opts_data=opts_data, need_amt=False)

proto = cfg._proto

async_run(cfg, main)
