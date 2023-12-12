#!/usr/bin/env python3

"""
test/stop-coin-daemons.py: Stop daemons for the MMGen test suite
"""

try:
	from include.coin_daemon_control import main
except ImportError:
	from test.include.coin_daemon_control import main

from mmgen.main import launch
launch(func=main)
