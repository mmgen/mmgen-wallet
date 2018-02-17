#!/usr/bin/env python
# Convert MMGen 'v2' transaction file (amounts as BTCAmt())
# to MMGen 'v3' (amounts as strings)
# v3 tx files were introduced with MMGen version 0.9.7

import sys,os
repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

from mmgen.common import *

opts_data = lambda: {
	'desc':    "Convert MMGen transaction file from v2 format to v3 format",
	'usage':   "<tx file>",
	'options': """
-h, --help     Print this help message
-d, --outdir=d Output files to directory 'd' instead of working dir
-q, --quiet    Write (and overwrite) files without prompting
-S, --stdout   Write data to STDOUT instead of file
"""
}

cmd_args = opts.init(opts_data)

from mmgen.tx import *

if len(cmd_args) != 1: opts.usage()

tx = MMGenTX(cmd_args[0],silent_open=True)
tx.write_to_file(ask_tty=False,ask_overwrite=not opt.quiet,ask_write=not opt.quiet)
