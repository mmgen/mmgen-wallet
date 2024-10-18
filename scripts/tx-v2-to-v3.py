#!/usr/bin/env python3

"""
Convert an MMGen 'v2' transaction file (amounts as BTCAmt()) to 'v3' (amounts as
strings).  Version 3 TX files were introduced with MMGen version 0.9.7
"""

import sys, os, asyncio

from mmgen.cfg import Config
from mmgen.tx import CompletedTX

repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

opts_data = {
	'text': {
		'desc':    "Convert an MMGen transaction file from v2 format to v3 format",
		'usage':   "<TX file>",
		'options': """
-h, --help     Print this help message
-d, --outdir=d Output files to directory 'd' instead of working dir
-q, --quiet    Write (and overwrite) files without prompting
-S, --stdout   Write data to STDOUT instead of file
"""
	}
}

cfg = Config(opts_data=opts_data)

if len(cfg._args) != 1:
	cfg._usage()

tx = asyncio.run(CompletedTX(cfg._args[0], quiet_open=True))
tx.file.write(ask_tty=False, ask_overwrite=not cfg.quiet, ask_write=not cfg.quiet)
