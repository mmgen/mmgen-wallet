#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.include.test_init: Initialization module for test scripts
"""

import sys, os
from pathlib import PurePath
os.environ['MMGEN_TEST_SUITE'] = '1'
repo_root = str(PurePath(*PurePath(__file__).parts[:-3]))
os.chdir(repo_root)
sys.path[0] = repo_root

from test.overlay import overlay_setup
overlay_root = overlay_setup(repo_root)
os.environ['PYTHONPATH'] = overlay_root

if 'TMUX' in os.environ:
	del os.environ['TMUX']

if os.getenv('MMGEN_DEVTOOLS'):
	from mmgen.devinit import init_dev
	init_dev()
