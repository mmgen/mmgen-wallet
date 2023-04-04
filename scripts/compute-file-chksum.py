#!/usr/bin/env python3

import sys,os
repo_root = os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]
sys.path = [repo_root] + sys.path

from mmgen.common import *

opts_data = {
	'text': {
		'desc': 'Compute checksum for a MMGen data file',
		'usage':'[opts] infile',
		'options': """
-h, --help               Print this help message.
-i, --include-first-line Include the first line of the file (you probably don't want this)
"""
	}
}

cfg = Config(opts_data=opts_data)

from mmgen.fileutil import get_lines_from_file
lines = get_lines_from_file( cfg, cfg._args[0] )
start = (1,0)[bool(cfg.include_first_line)]
a = make_chksum_6(' '.join(lines[start:]).encode())
if start == 1:
	b = lines[0]
	msg(("Checksum in file ({}) doesn't match computed value!".format(b),'Checksum in file OK')[a==b])
Msg(a)
