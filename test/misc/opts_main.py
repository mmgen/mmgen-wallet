#!/usr/bin/env python3

import os

from mmgen.cfg import Config
from mmgen.util import msg

opts_data = {
	'sets': [('print_checksum', True, 'quiet', True)],
	'text': {
		'desc': 'Opts test',
		'usage':'[args] [opts]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long (global) options
-i, --in-fmt=      f  Input is from wallet format 'f'
-d, --outdir=      d  Use outdir 'd'
-C, --print-checksum  Print a checksum
-E, --fee-estimate-mode=M Specify the network fee estimate mode.
-F, --no-foobleize    Do not foobleize the output, even on user request
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-k, --keep-label      Reuse label of input wallet for output wallet
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.
-L, --label=       l  Specify a label 'l' for output wallet
-m, --minconf=     n  Minimum number of confirmations required to spend
                      outputs (default: 1)
-o, --show-opts=   L  List of cfg opts to display
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Be quieter
-t, --min-temp=    t  Minimum temperature (in degrees Celsius)
-T, --max-temp=    t  Maximum temperature (in degrees Celsius)
-x, --point=       P  Point in Euclidean space
-X, --cached-balances Use cached balances (Ethereum only)
-v, --verbose         Be more verbose
                      sample help_note: {kgs}
                      sample help_note: {coin_id}
""",
	'notes': """

                           NOTES FOR THIS COMMAND

sample note: {nn}
"""
	},
	'code': {
		'options': lambda cfg, help_notes, s: s.format(
			kgs     = help_notes('keygen_backends'),
			coin_id = help_notes('coin_id'),
		),
		'notes': lambda s: s.format(nn='a note'),
	}
}

cfg = Config(opts_data=opts_data, need_proto=os.getenv('TEST_MISC_OPTS_NEEDS_PROTO'))

if cfg.show_opts:
	opts = cfg.show_opts.split(',')
	col1_w = max(len(s) for s in opts) + 5
	for opt in opts:
		msg('{:{w}} {}'.format(f'cfg.{opt}:', getattr(cfg, opt), w=col1_w))
		if cfg._proto:
			coin, *rem = opt.split('_')
			network = rem[0] if rem[0] in cfg._proto.network_names else None
			opt_name = '_'.join(rem[bool(network):])
			msg('{:{w}} {}'.format(f'proto.{opt_name}:', getattr(cfg._proto, opt_name), w=col1_w))

msg('')
for n, arg in enumerate(cfg._args, 1):
	msg(f'arg{n}: {arg}')
