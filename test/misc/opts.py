#!/usr/bin/env python3

from mmgen.common import *

opts_data = {
	'sets': [('print_checksum',True,'quiet',True)],
	'text': {
		'desc': 'Opts test',
		'usage':'[args] [opts]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-i, --in-fmt=      f  Input is from wallet format 'f'
-d, --outdir=      d  Use outdir 'd'
-C, --print-checksum  Print a checksum
-E, --fee-estimate-mode=M Specify the network fee estimate mode.
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
-X, --cached-balances Use cached balances (Ethereum only)
-v, --verbose         Be more verbose
""",
	'notes': """

                           NOTES FOR THIS COMMAND
	{nn}
"""
	},
	'code': {
		'options': lambda help_notes,s: s.format(
			kgs=help_notes('keygen_backends'),
			coin_id=help_notes('coin_id'),
			g=g,
		),
		'notes': lambda s: s.format(nn='a note'),
	}
}

cmd_args = opts.init(opts_data)

if cmd_args == ['show_common_opts_diff']:
	from mmgen.opts import show_common_opts_diff
	show_common_opts_diff()
	sys.exit(0)

for k in (
	'foo',               # added opt
	'print_checksum',    # sets 'quiet'
	'quiet','verbose',   # required_opts, incompatible_opts
	'fee_estimate_mode', # autoset_opts
	'passwd_file',       # infile_opts - check_infile()
	'outdir',            # check_outdir()
	'cached_balances',   # opt_sets_global
	'minconf',           # global_sets_opt
	'hidden_incog_input_params',
	):
	msg('{:30} {}'.format( f'opt.{k}:', getattr(opt,k) ))

msg('')
for k in (
	'cached_balances',   # opt_sets_global
	'minconf',           # global_sets_opt
	):
	msg('{:30} {}'.format( f'g.{k}:', getattr(opt,k) ))
