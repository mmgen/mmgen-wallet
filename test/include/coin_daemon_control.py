#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
test.include.coin_daemon_control: Start and stop daemons for the MMGen test suite
"""

from .tests_header import repo_root
from mmgen.common import *
from mmgen.protocol import init_proto

action = gc.prog_name.split('-')[0]

opts_data = {
	'sets': [('debug',True,'verbose',True)],
	'text': {
		'desc': f'{action.capitalize()} coin daemons for the MMGen test suite',
		'usage':'[opts] <network IDs>',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long options (common options)
-D, --debug          Produce debugging output (implies --verbose)
-d, --datadir=       Override the default datadir
-i, --daemon-ids     Print all known daemon IDs
-m, --mainnet-only   Perform operations for mainnet daemons only
-n, --no-daemonize   Don't fork daemon to background
-p, --port-shift=    Shift the RPC port by this number
-s, --get-state      Get the state of the daemon(s) and exit
-t, --testing        Testing mode.  Print commands but don't execute them
-q, --quiet          Produce quieter output
-u, --usermode       Run the daemon in user (non test-suite) mode
-v, --verbose        Produce more verbose output
-V, --print-version  Print version strings from exec’ed daemons (not RPC)
-W, --no-wait        Don't wait for daemons to change state before exiting
""",
	'notes': """
Valid network IDs: {nid}, all, or no_xmr
"""
	},
	'code': {
		'options': lambda s: s.format(a=action.capitalize(),pn=gc.prog_name),
		'notes': lambda s,help_notes: s.format(nid=help_notes('coin_daemon_network_ids'))
	}
}

cfg = Config(opts_data=opts_data)

from mmgen.daemon import CoinDaemon

class warn_missing_exec(oneshot_warning):
	color = 'nocolor'
	message = 'daemon executable {!r} not found on this system!'

def run(network_id=None,proto=None,daemon_id=None,missing_exec_ok=False):

	d = CoinDaemon(
		cfg,
		network_id = network_id,
		proto      = proto,
		test_suite = not cfg.usermode,
		opts       = ['no_daemonize'] if cfg.no_daemonize else None,
		port_shift = int(cfg.port_shift or 0),
		datadir    = cfg.datadir,
		daemon_id  = daemon_id )

	if cfg.mainnet_only and d.network != 'mainnet':
		return

	d.debug = d.debug or cfg.debug
	d.wait = not cfg.no_wait

	if missing_exec_ok:
		try:
			d.get_exec_version_str()
		except Exception as e:
			if not cfg.quiet:
				msg(str(e))
				warn_missing_exec( div=d.exec_fn, fmt_args=(d.exec_fn,) )
			return
	if cfg.print_version:
		msg('{:16} {}'.format( d.exec_fn+':', d.get_exec_version_str() ))
	elif cfg.get_state:
		print(d.state_msg())
	elif cfg.testing:
		for cmd in d.start_cmds if action == 'start' else [d.stop_cmd]:
			print(' '.join(cmd))
	else:
		if action == 'stop' and hasattr(d,'rpc'):
			async_run(d.rpc.stop_daemon(quiet=cfg.quiet))
		else:
			d.cmd(action,quiet=cfg.quiet)

if cfg.daemon_ids:
	print('\n'.join(CoinDaemon.all_daemon_ids()))
elif 'all' in cfg._args or 'no_xmr' in cfg._args:
	if len(cfg._args) != 1:
		die(1,"'all' or 'no_xmr' must be the sole argument")
	for coin in CoinDaemon.coins:
		if coin == 'XMR' and cfg._args[0] == 'no_xmr':
			continue
		for daemon_id in CoinDaemon.get_daemon_ids(cfg,coin):
			for network in CoinDaemon.get_daemon(cfg,coin,daemon_id).networks:
				run(
					proto           = init_proto( cfg, coin=coin, network=network ),
					daemon_id       = daemon_id,
					missing_exec_ok = True )
else:
	ids = cfg._args
	network_ids = CoinDaemon.get_network_ids(cfg)
	if not ids:
		cfg._opts.usage()
	for i in ids:
		if i not in network_ids:
			die(1,f'{i!r}: invalid network ID')
	for network_id in ids:
		run(network_id=network_id.lower())
