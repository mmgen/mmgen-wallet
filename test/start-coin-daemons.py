#!/usr/bin/env python3

import sys
from include.tests_header import repo_root
from mmgen.common import *
from mmgen.daemon import *

network_ids = CoinDaemon.get_network_ids()

action = g.prog_name.split('-')[0]

opts_data = {
	'sets': [('debug',True,'verbose',True)],
	'text': {
		'desc': '{} coin daemons for the MMGen test suite'.format(action.capitalize()),
		'usage':'[opts] <network IDs>',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long options (common options)
-D, --debug          Produce debugging output (implies --verbose)
-d, --datadir=       Override the default datadir
-n, --no-daemonize   Don't fork daemon to background
-p, --port-shift=    Shift the RPC port by this number
-s, --get-state      Get the state of the daemon(s) and exit
-t, --testing        Testing mode.  Print commands but don't execute them
-q, --quiet          Produce quieter output
-v, --verbose        Produce more verbose output
-W, --no-wait        Don't wait for daemons to change state before exiting
""",
	'notes': """
Valid network IDs: {nid}, all, or no_xmr
"""
	},
	'code': {
		'options': lambda s: s.format(a=action.capitalize(),pn=g.prog_name),
		'notes': lambda s: s.format(nid=', '.join(network_ids))
	}
}

cmd_args = opts.init(opts_data)

def run(network_id=None,proto=None,daemon_id=None):
	d = CoinDaemon(
		network_id = network_id,
		proto      = proto,
		test_suite = True,
		opts       = ['no_daemonize'] if opt.no_daemonize else None,
		port_shift = int(opt.port_shift or 0),
		datadir    = opt.datadir,
		daemon_id  = daemon_id )
	d.debug = d.debug or opt.debug
	d.wait = not opt.no_wait
	if opt.get_state:
		print(d.state_msg())
	elif opt.testing:
		print(' '.join(getattr(d,action+'_cmd')))
	else:
		d.cmd(action,quiet=opt.quiet)

if 'all' in cmd_args or 'no_xmr' in cmd_args:
	if len(cmd_args) != 1:
		die(1,"'all' or 'no_xmr' must be the sole argument")
	from mmgen.protocol import init_proto
	for coin,data in CoinDaemon.coins.items():
		if coin == 'XMR' and cmd_args[0] == 'no_xmr':
			continue
		for daemon_id in data.daemon_ids:
			for network in globals()[daemon_id+'_daemon'].networks:
				run(proto=init_proto(coin=coin,network=network),daemon_id=daemon_id)
else:
	ids = cmd_args
	if not ids:
		opts.usage()
	for i in ids:
		if i not in network_ids:
			die(1,f'{i!r}: invalid network ID')
	for network_id in ids:
		run(network_id=network_id.lower())
