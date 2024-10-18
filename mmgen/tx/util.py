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
tx.util: transaction utilities
"""

def get_autosign_obj(cfg):
	from ..cfg import Config
	from ..autosign import Autosign
	return Autosign(
		Config({
			'mountpoint': cfg.autosign_mountpoint,
			'test_suite': cfg.test_suite,
			'test_suite_root_pfx': cfg.test_suite_root_pfx,
			'coins': cfg.coin,
			'online': not cfg.offline, # used only in online environment (xmrwallet, txcreate, txsend, txbump)
		})
	)

def mount_removable_device(cfg):
	asi = get_autosign_obj(cfg)
	if not asi.device_inserted:
		from ..util import die
		die(1, 'Removable device not present!')
	import atexit
	atexit.register(lambda: asi.do_umount())
	asi.do_mount()
	return asi
