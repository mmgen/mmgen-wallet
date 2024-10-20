#!/usr/bin/env python3

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
			kgs=help_notes('keygen_backends'),
			coin_id=help_notes('coin_id'),
		),
		'notes': lambda s: s.format(nn='a note'),
	}
}

cfg = Config(opts_data=opts_data)

for k in (
		'foo',               # added opt
		'print_checksum',    # sets 'quiet'
		'quiet', 'verbose',  # _incompatible_opts
		'passwd_file',       # _infile_opts - check_infile()
		'outdir',            # check_outdir()
		'cached_balances',   # opt_sets_global
		'minconf',           # global_sets_opt
		'hidden_incog_input_params',
		'keep_label',
		'seed_len',
		'hash_preset',
		'label',
		'min_temp',
		'max_temp',
		'coin',
		'pager',
		'point',
		'no_foobleize'):
	msg('{:30} {}'.format(f'cfg.{k}:', getattr(cfg, k)))

msg('')
for k in (
		'cached_balances',   # opt_sets_global
		'minconf'):          # global_sets_opt
	msg('{:30} {}'.format(f'cfg.{k}:', getattr(cfg, k)))

msg('')
for k in ('fee_estimate_mode',): # _autoset_opts
	msg('{:30} {}'.format(f'cfg.{k}:', getattr(cfg, k)))

msg('')
for n, k in enumerate(cfg._args, 1):
	msg(f'arg{n}: {k}')
