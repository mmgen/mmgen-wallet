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
tx.util: transaction utilities
"""

def get_autosign_obj(cfg, add_cfg={}):
	from ..cfg import Config
	from ..autosign import Autosign
	return Autosign(
		Config({
			'_clone': cfg,
			'mountpoint': cfg.autosign_mountpoint,
			'coins': cfg.coin,
			# used only in online environment (xmrwallet, txcreate, txsend, txbump):
			'online': not cfg.offline} | add_cfg))

def mount_removable_device(cfg, add_cfg={}):
	asi = get_autosign_obj(cfg, add_cfg=add_cfg)
	if not asi.device_inserted:
		from ..util import die
		die(1, 'Removable device not present!')
	import atexit
	atexit.register(lambda: asi.do_umount())
	asi.do_mount()
	return asi
