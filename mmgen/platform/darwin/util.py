#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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

from ...color import cyan
from ...obj import MMGenLabel

def get_device_size(fn):
	import re
	cp = run(['diskutil', 'info', fn], text=True, stdout=PIPE, check=True)
	res = [e for e in cp.stdout.splitlines() if 'Disk Size' in e]
	errmsg = '‘diskutil info’ output could not be parsed for device size'
	assert len(res) == 1, f'{errmsg}:\n{cp.stdout}'
	m = re.search(r'\((\d+) Bytes\)', res[0])
	assert m, f'{errmsg}:\n{res[0]}'
	return int(m[1])

class RamDiskLabel(MMGenLabel):
	max_len = 24
	desc = 'ramdisk label'

class MacOSRamDisk:

	desc = 'macOS ramdisk'

	def __init__(self, cfg, label, size_in_MB, path=None):
		self.cfg = cfg
		self.label = RamDiskLabel(label)
		self.size_in_MB  = size_in_MB
		self.dfl_path = Path('/Volumes') / self.label
		self.path = Path(path) if path else self.dfl_path

	def create(self, quiet=False):
		redir = DEVNULL if quiet else None
		if self.path.exists():
			self.cfg._util.qmsg('{} {} [{}] already exists'.format(self.desc, self.label.hl(), self.path))
			return
		cp = run(['hdiutil', 'attach', '-nomount', f'ram://{2048 * self.size_in_MB}'], stdout=PIPE, check=True)
		self.dev_name = cp.stdout.decode().strip()
		self.cfg._util.qmsg('{} {} [{}]'.format(cyan(f'Created {self.desc}'), self.label.hl(), self.dev_name))
		run(['diskutil', 'eraseVolume', 'APFS', self.label, self.dev_name], stdout=redir, check=True)
		if self.path != self.dfl_path:
			run(['diskutil', 'umount', self.label], stdout=redir, check=True)
			self.path.mkdir(parents=True, exist_ok=True)
			run(['diskutil', 'mount', '-mountPoint', str(self.path.absolute()), self.label], stdout=redir, check=True)

	def destroy(self, quiet=False):
		redir = DEVNULL if quiet else None
		run(['diskutil', 'eject', self.label], stdout=redir, check=True)
		if not quiet:
			self.cfg._util.qmsg('{} {} [{}]'.format(cyan(f'Destroyed {self.desc}'), self.label.hl(), self.path))
