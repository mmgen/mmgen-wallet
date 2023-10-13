#!/usr/bin/env python3

"""
test/start-coin-daemons.py: Start daemons for the MMGen test suite
"""

try:
	from include.coin_daemon_control import main
except ImportError:
	from test.include.coin_daemon_control import main

main()
