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
test.overlay.__init__: Initialize the MMGen test suite overlay tree
"""

import sys, os, shutil

def get_overlay_tree_dir(repo_root):
	return os.path.join(repo_root, 'test', 'overlay', 'tree')

def overlay_setup(repo_root):

	def process_srcdir(pkgname, d):
		relpath = d.split('.')
		srcdir = os.path.join(repo_root, *relpath)
		destdir = os.path.join(overlay_tree_dir, *relpath)
		fakemod_dir = os.path.join(fakemod_root, pkgname, *(relpath[1:]))
		os.makedirs(destdir)
		for fn in os.listdir(srcdir):
			if (
				fn.endswith('.py') or
				d == f'{pkgname}.data' or
				(d == 'mmgen.proto.secp256k1' and fn.startswith('secp256k1'))
			):
				if fn.endswith('.py') and os.path.exists(os.path.join(fakemod_dir, fn)):
					make_link(
						os.path.join(fakemod_dir, fn),
						os.path.join(destdir, fn))
					link_fn = fn.removesuffix('.py') + '_orig.py'
				else:
					link_fn = fn
				make_link(
					os.path.join(srcdir, fn),
					os.path.join(destdir, link_fn))

	overlay_tree_dir = get_overlay_tree_dir(repo_root)
	fakemod_root = os.path.join(repo_root, 'test', 'overlay', 'fakemods')
	common_path = os.path.join(os.path.sep, 'test', 'overlay', 'fakemods')
	pkgdata = ((
			os.path.realpath(e.path).removesuffix(os.path.join(common_path, e.name)),
			e.name
		) for e in os.scandir(fakemod_root) if e.is_dir())

	for repodir, pkgname in pkgdata:
		if not os.path.exists(os.path.join(overlay_tree_dir, pkgname)):

			sys.stderr.write(f'Setting up overlay tree: {pkgname}\n')

			make_link = os.symlink if sys.platform in ('linux', 'darwin') else shutil.copy2
			shutil.rmtree(os.path.join(overlay_tree_dir, pkgname), ignore_errors=True)

			import configparser
			cfg = configparser.ConfigParser()
			cfg.read(os.path.join(repodir, 'setup.cfg'))

			for d in cfg.get('options', 'packages').split():
				process_srcdir(pkgname, d)

	sys.path.insert(0, overlay_tree_dir)

	return overlay_tree_dir
