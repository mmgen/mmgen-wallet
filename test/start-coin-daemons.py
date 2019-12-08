#!/usr/bin/env python3

import sys
from tests_header import repo_root
from mmgen.common import *
from mmgen.test_daemon import TestDaemon
from mmgen.regtest import MMGenRegtest

action = g.prog_name.split('-')[0]

opts_data = {
	'sets': [('debug',True,'verbose',True)],
	'text': {
		'desc': '{} coin daemons for the MMGen test suite'.format(action.capitalize()),
		'usage':'[opts] <network IDs>',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long options (common options)
-d, --debug          Produce debugging output (implies --verbose)
-r, --regtest-user=U {a} a regtest daemon for user 'U'
-s, --get-state      Get the state of the daemon(s) and exit
-t, --testing        Testing mode.  Print commands but don't execute them
-v, --verbose        Produce more verbose output
-W, --no-wait        Don't wait for daemons to change state before exiting
""",
	'notes': """
Valid network IDs: {nid}, all, or no_xmr
Valid Regtest network IDs: {rid}, or all
Valid Regtest users:       {ru}
"""
	},
	'code': {
		'options': lambda s: s.format(a=action.capitalize(),pn=g.prog_name),
		'notes': lambda s: s.format(
			nid=', '.join(TestDaemon.network_ids),
			rid=', '.join(MMGenRegtest.coins),
			ru=', '.join(MMGenRegtest.users),
		)
	}
}

cmd_args = opts.init(opts_data)

if 'all' in cmd_args or 'no_xmr' in cmd_args:
	if len(cmd_args) != 1:
		die(1,"'all' or 'no_xmr' must be the sole argument")
	if opt.regtest_user:
		ids = MMGenRegtest.coins
	else:
		ids = list(TestDaemon.network_ids)
		if cmd_args[0] == 'no_xmr':
			ids.remove('xmr')
else:
	ids = cmd_args
	if not ids:
		opts.usage()
	for i in ids:
		if i not in TestDaemon.network_ids:
			die(1,'{!r}: invalid network ID'.format(i))

if 'eth' in ids and 'etc' in ids:
	msg('Cannot run ETH and ETC simultaneously, so skipping ETC')
	ids.remove('etc')

for network_id in ids:
	network_id = network_id.lower()
	coin = network_id.replace('_tn','')
	if opt.regtest_user:
		datadir = '{}/test/data_dir/regtest/{}'.format(repo_root,coin)
		d = MMGenRegtest(network_id,datadir).test_daemon(opt.regtest_user)
	else:
		datadir = '{}/test/daemons/{}'.format(repo_root,coin)
		d = TestDaemon(network_id,datadir)
	d.debug = opt.debug
	d.wait = not opt.no_wait
	if opt.get_state:
		print('{} {} is {}'.format(d.net_desc,d.desc,d.state))
	elif opt.testing:
		print(' '.join(getattr(d,action+'_cmd')))
	else:
		d.cmd(action)
