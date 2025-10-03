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
platform.darwin.util: utilities for the macOS platform
"""

from pathlib import Path
from subprocess import run, PIPE, DEVNULL

from ...obj import MMGenLabel
from ...util import oneshot_warning

def get_device_size(path_or_label):
	import re
	cp = run(['diskutil', 'info', path_or_label], text=True, stdout=PIPE, check=True)
	res = [e for e in cp.stdout.splitlines() if 'Disk Size' in e]
	errmsg = '‘diskutil info’ output could not be parsed for device size'
	assert len(res) == 1, f'{errmsg}:\n{cp.stdout}'
	m = re.search(r'\((\d+) Bytes\)', res[0])
	assert m, f'{errmsg}:\n{res[0]}'
	return int(m[1])

class warn_ramdisk_too_small(oneshot_warning):
	message = 'requested ramdisk size ({}MB) too small, using {}MB instead'
	color = 'yellow'
	def __init__(self, usr_size, min_size):
		oneshot_warning.__init__(self, div=usr_size, fmt_args=[usr_size, min_size])

class RamDiskLabel(MMGenLabel):
	max_len = 24
	desc = 'ramdisk label'

class MacOSRamDisk:

	desc = 'ramdisk'
	min_size = 10 # 10MB is the minimum supported by hdiutil

	def __init__(self, cfg, label, size, *, path=None):
		if size < self.min_size:
			warn_ramdisk_too_small(size, self.min_size)
			size = self.min_size
		self.cfg = cfg
		self.label = RamDiskLabel(label)
		self.size = size # size in MiB
		self.dfl_path = Path('/Volumes') / self.label
		self.path = Path(path) if path else self.dfl_path

	def exists(self):
		return self.path.is_mount()

	def get_diskutil_size(self):
		return get_device_size(self.label) // (2**20)

	def create(self, *, quiet=False):
		redir = DEVNULL if quiet else None
		if self.exists():
			diskutil_size = self.get_diskutil_size()
			if diskutil_size != self.size:
				self.cfg._util.qmsg(f'Existing ramdisk has incorrect size {diskutil_size}MB, deleting')
				self.destroy()
			else:
				self.cfg._util.qmsg(f'{self.desc.capitalize()} {self.label.hl()} at path {self.path} already exists')
				return
		self.cfg._util.qmsg(f'Creating {self.desc} {self.label.hl()} of size {self.size}MB')
		cp = run(
			['hdiutil', 'attach', '-nomount', f'ram://{2048 * self.size}'],
			stdout = PIPE,
			text = True,
			check = True)
		self.dev_name = cp.stdout.strip()
		self.cfg._util.qmsg(f'Created {self.desc} {self.label.hl()} [{self.dev_name}]')
		run(['diskutil', 'eraseVolume', 'APFS', self.label, self.dev_name], stdout=redir, check=True)
		diskutil_size = self.get_diskutil_size()
		assert diskutil_size == self.size, 'Reported ramdisk size {diskutil_size}MB is incorrect!'
		if self.path != self.dfl_path:
			run(['diskutil', 'umount', self.label], stdout=redir, check=True)
			self.path.mkdir(parents=True, exist_ok=True)
			run(['diskutil', 'mount', '-mountPoint', str(self.path.absolute()), self.label], stdout=redir, check=True)

	def destroy(self, *, quiet=False):
		if not self.exists():
			self.cfg._util.qmsg(f'{self.desc.capitalize()} {self.label.hl()} at path {self.path} not found')
			return
		redir = DEVNULL if quiet else None
		run(['diskutil', 'eject', self.label], stdout=redir, check=True)
		if not quiet:
			self.cfg._util.qmsg(f'Destroyed {self.desc} {self.label.hl()} at {self.path}')
