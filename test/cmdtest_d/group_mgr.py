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
test.include.group_mgr: Command group manager for the MMGen Wallet cmdtest suite
"""

import sys, os, time

from mmgen.color import yellow, green, cyan
from mmgen.util import Msg, die

from .cfg import cfgs, cmd_groups_dfl, cmd_groups_extra

class CmdGroupMgr:

	dpy_data = None

	cmd_groups = cmd_groups_dfl.copy()
	cmd_groups.update(cmd_groups_extra)

	cfg_attrs = (
		'seed_len',
		'seed_id',
		'wpasswd',
		'kapasswd',
		'segwit',
		'hash_preset',
		'bw_filename',
		'bw_params',
		'ref_bw_seed_id',
		'addr_idx_list',
		'pass_idx_list')

	def __init__(self, cfg):
		self.cfg = cfg
		self.network_id = cfg._proto.coin.lower() + ('_tn' if cfg._proto.testnet else '')
		self.name = type(self).__name__

	def create_cmd_group(self, cls, sg_name=None):

		cmd_group_in = dict(cls.cmd_group_in)

		if sg_name and 'subgroup.' + sg_name not in cmd_group_in:
			die(1, f'{sg_name!r}: no such subgroup in test group {cls.__name__}')

		def add_entries(key, add_deps=True, added_subgroups=[]):

			if add_deps:
				for dep in cmd_group_in['subgroup.'+key]:
					yield from add_entries(dep)

			assert isinstance(cls.cmd_subgroups[key][0], str), f'header for subgroup {key!r} missing!'

			if not key in added_subgroups:
				yield from cls.cmd_subgroups[key][1:]
				added_subgroups.append(key)

		def gen():
			for name, data in cls.cmd_group_in:
				if name.startswith('subgroup.'):
					sg_key = name.removeprefix('subgroup.')
					if sg_name in (None, sg_key):
						yield from add_entries(
								sg_key,
								add_deps = sg_name and not self.cfg.skipping_deps,
								added_subgroups = [sg_name] if self.cfg.deps_only else [])
					if self.cfg.deps_only and sg_key == sg_name:
						return
				elif not self.cfg.skipping_deps:
					yield (name, data)

		return tuple(gen())

	def load_mod(self, gname, modname=None):
		clsname, kwargs = self.cmd_groups[gname]
		if modname is None and 'modname' in kwargs:
			modname = kwargs['modname']
		import importlib
		modpath = f'test.cmdtest_d.ct_{modname or gname}'
		return getattr(importlib.import_module(modpath), clsname)

	def create_group(self, gname, sg_name, full_data=False, modname=None, is3seed=False, add_dpy=False):
		"""
		Initializes the list 'cmd_list' and dict 'dpy_data' from module's cmd_group data.
		Alternatively, if called with 'add_dpy=True', updates 'dpy_data' from module data
		without touching 'cmd_list'
		"""

		cls = self.load_mod(gname, modname)
		cdata = []

		def get_shared_deps(cmdname, tmpdir_idx):
			"""
			shared_deps are "implied" dependencies for all cmds in cmd_group that don't appear in
			the cmd_group data or cmds' argument lists.  Supported only for 3seed tests at present.
			"""
			if not hasattr(cls, 'shared_deps'):
				return []

			return [k for k, v in cfgs[str(tmpdir_idx)]['dep_generators'].items()
						if k in cls.shared_deps and v != cmdname]

		if not hasattr(cls, 'cmd_group'):
			cls.cmd_group = self.create_cmd_group(cls, sg_name)

		for a, b in cls.cmd_group:
			if is3seed:
				for n, (i, j) in enumerate(zip(cls.tmpdir_nums, (128, 192, 256))):
					k = f'{a}_{n+1}'
					if hasattr(cls, 'skip_cmds') and k in cls.skip_cmds:
						continue
					sdeps = get_shared_deps(k, i)
					if isinstance(b, str):
						cdata.append((k, (i, f'{b} ({j}-bit)', [[[]+sdeps, i]])))
					else:
						cdata.append((k, (i, f'{b[1]} ({j}-bit)', [[b[0]+sdeps, i]])))
			elif full_data:
				cdata.append((a, b))
			else:
				cdata.append((a, (cls.tmpdir_nums[0], b, [[[], cls.tmpdir_nums[0]]])))

		if add_dpy:
			self.dpy_data.update(dict(cdata))
		else:
			self.cmd_list = tuple(e[0] for e in cdata)
			self.dpy_data = dict(cdata)

		cls.full_data = full_data or is3seed

		if not cls.full_data:
			cls.tmpdir_num = cls.tmpdir_nums[0]
			for k, v in cfgs[str(cls.tmpdir_num)].items():
				setattr(cls, k, v)

		return cls

	def gm_init_group(self, cfg, trunner, gname, sg_name, spawn_prog):
		kwargs = self.cmd_groups[gname][1]
		cls = self.create_group(gname, sg_name, **kwargs)
		cls.group_name = gname
		return cls(cfg, trunner, cfgs, spawn_prog)

	def get_cls_by_gname(self, gname):
		return self.load_mod(gname, self.cmd_groups[gname][1].get('modname'))

	def list_cmd_groups(self):
		ginfo = []
		for gname in self.cmd_groups:
			ginfo.append((gname, self.get_cls_by_gname(gname)))

		if self.cfg.list_current_cmd_groups:
			exclude = (self.cfg.exclude_groups or '').split(',')
			ginfo = [g for g in ginfo
						if self.network_id in g[1].networks
							and not g[0] in exclude
							and g[0] in tuple(self.cmd_groups_dfl) + tuple(self.cfg._args)]
			desc = 'CONFIGURED'
		else:
			desc = 'AVAILABLE'

		def gen_output():
			yield green(f'{desc} COMMAND GROUPS AND SUBGROUPS:')
			yield ''
			for name, cls in ginfo:
				yield '  {} - {}'.format(
					yellow(name.ljust(13)),
					(cls.__doc__.strip() if cls.__doc__ else cls.__name__))
				if 'cmd_subgroups' in cls.__dict__:
					subgroups = {k:v for k, v in cls.cmd_subgroups.items() if not k.startswith('_')}
					max_w = max(len(k) for k in subgroups)
					for k, v in subgroups.items():
						yield '    + {} · {}'.format(cyan(k.ljust(max_w+1)), v[0])

		from mmgen.ui import do_pager
		do_pager('\n'.join(gen_output()))

		Msg('\n' + ' '.join(e[0] for e in ginfo))

	def find_cmd_in_groups(self, cmd, group=None):
		"""
		Search for a test command in specified group or all configured command groups
		and return it as a string.  Loads modules but alters no global variables.
		"""
		if group:
			if not group in [e[0] for e in self.cmd_groups]:
				die(1, f'{group!r}: unrecognized group')
			groups = [self.cmd_groups[group]]
		else:
			groups = self.cmd_groups

		for gname in groups:
			cls = self.get_cls_by_gname(gname)

			if not hasattr(cls, 'cmd_group'):
				cls.cmd_group = self.create_cmd_group(cls)

			if cmd in cls.cmd_group:             # first search the class
				return gname

			if cmd in dir(cls(self.cfg, None, None, None)):  # then a throwaway instance
				return gname # cmd might exist in more than one group - we'll go with the first

		return None
