#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test/clean.py: Clean the test directory
"""

import sys, os

repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), os.pardir)))
os.chdir(repo_root)
sys.path[0] = repo_root

from mmgen.cfg import Config

opts_data = {
	'text': {
		'desc': 'Clean the test directory',
		'usage':'[options]',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long (global) options
""",
	},
}

cfg = Config(opts_data=opts_data)

from test.overlay import get_overlay_tree_dir
overlay_tree_dir = get_overlay_tree_dir(repo_root)
if os.path.exists(overlay_tree_dir):
	from shutil import rmtree
	rmtree(overlay_tree_dir, ignore_errors=True)
	print(f'Removed {os.path.relpath(overlay_tree_dir)!r}')

from test.include.common import clean, set_globals

set_globals(cfg)

from test.include.cfg import clean_cfgs

extra_dirs = [
	Config.test_datadir,
	os.path.join('test', 'trash'),
	os.path.join('test', 'trash2')
]

clean(clean_cfgs, extra_dirs=extra_dirs)
