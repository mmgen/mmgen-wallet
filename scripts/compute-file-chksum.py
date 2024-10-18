#!/usr/bin/env python3

import sys, os

import script_init
from mmgen.main import launch
from mmgen.cfg import Config
from mmgen.util import msg, Msg, make_chksum_6
from mmgen.fileutil import get_lines_from_file

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

def main():
	lines = get_lines_from_file(cfg, cfg._args[0])
	start = (1, 0)[bool(cfg.include_first_line)]
	a = make_chksum_6(' '.join(lines[start:]).encode())
	if start == 1:
		b = lines[0]
		msg(
			'Checksum in file OK' if a == b else
			f"Checksum in file ({b}) doesn't match computed value!")
	Msg(a)

launch(func=main)
