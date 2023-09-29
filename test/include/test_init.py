#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
test.include.test_init: Initialization module for test scripts
"""

import sys,os
os.environ['MMGEN_TEST_SUITE'] = '1'
repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path[0] = repo_root

from test.overlay import overlay_setup
overlay_setup(repo_root)
os.environ['PYTHONPATH'] = repo_root

if 'TMUX' in os.environ:
	del os.environ['TMUX']
