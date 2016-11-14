#!/usr/bin/env python

from mmgen.common import *

opts_data = {
	'desc': 'Compute checksum for a MMGen data file',
	'usage':'[opts] infile',
	'options': """
-h, --help               Print this help message.
-i, --include-first-line Include the first line of the file (you probably don't want this)
""".strip()
}

cmd_args = opts.init(opts_data)

lines = get_lines_from_file(cmd_args[0])
start = (1,0)[bool(opt.include_first_line)]
a = make_chksum_6(' '.join(lines[start:]))
if start == 1:
	b = lines[0]
	m = ("Checksum in file (%s) doesn't match computed value!" % b,'Checksum in file OK')[a==b]
	msg(m)
Msg(a)
