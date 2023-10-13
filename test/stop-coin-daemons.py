#!/usr/bin/env python3

"""
test/stop-coin-daemons.py: Stop daemons for the MMGen test suite
"""

try:
	import include.coin_daemon_control
except ImportError:
	import test.include.coin_daemon_control
