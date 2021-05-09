#!/usr/bin/env python3

import sys
from include.tests_header import repo_root
from mmgen.common import *
from mmgen.daemon import CoinDaemon

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
-n, --no-daemonize   Don't fork daemon to background
-s, --get-state      Get the state of the daemon(s) and exit
-t, --testing        Testing mode.  Print commands but don't execute them
-v, --verbose        Produce more verbose output
-W, --no-wait        Don't wait for daemons to change state before exiting
""",
	'notes': """
Valid network IDs: {nid}, all, or no_xmr
"""
	},
	'code': {
		'options': lambda s: s.format(a=action.capitalize(),pn=g.prog_name),
		'notes': lambda s: s.format(nid=', '.join(CoinDaemon.network_ids))
	}
}

cmd_args = opts.init(opts_data)

if 'all' in cmd_args or 'no_xmr' in cmd_args:
	if len(cmd_args) != 1:
		die(1,"'all' or 'no_xmr' must be the sole argument")
	else:
		ids = list(CoinDaemon.network_ids)
		if cmd_args[0] == 'no_xmr':
			ids.remove('xmr')
else:
	ids = cmd_args
	if not ids:
		opts.usage()
	for i in ids:
		if i not in CoinDaemon.network_ids:
			die(1,f'{i!r}: invalid network ID')

if 'eth' in ids and 'etc' in ids:
	msg('Cannot run ETH and ETC simultaneously, so skipping ETC')
	ids.remove('etc')

for network_id in ids:
	network_id = network_id.lower()
	d = CoinDaemon(
		network_id,
		test_suite = True,
		opts       = ['no_daemonize'] if opt.no_daemonize else None )
	d.debug = opt.debug
	d.wait = not opt.no_wait
	if opt.get_state:
		print('{} {} (port {}) is {}'.format(d.net_desc,d.desc,d.rpc_port,d.state))
	elif opt.testing:
		print(' '.join(getattr(d,action+'_cmd')))
	else:
		d.cmd(action)
