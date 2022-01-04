#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
uninstall-mmgen.py - Uninstall MMGen from a system
"""

import sys,os

def normalize_path(p):
	return os.path.normpath(os.path.realpath(os.path.abspath(p)))

curdir = normalize_path(os.curdir)

for n in reversed(range(len(sys.path))):
	if normalize_path(sys.path[n]) == curdir:
		del(sys.path[n])

try: import mmgen.main
except:
	sys.stderr.write('Failed to import mmgen.main module.  Is MMGen installed?\n')
	sys.exit(1)

modpath_save = sys.modules['mmgen.main'].__spec__.origin

from mmgen.common import *

opts_data = {
	'text': {
		'desc': 'Remove MMGen from your system',
		'usage': '[opts]',
		'options': """
-h, --help        Print this help message
-l, --list-paths  List the directories and files that would be deleted
-n, --no-prompt   Don't prompt before deleting
"""
	}
}

cmd_args = opts.init(opts_data)

if g.platform == 'linux' and os.getenv('USER') != 'root':
	die(1,'This program must be run as root')

if len(cmd_args):
	opts.usage()

mod_dir = os.path.split(normalize_path(modpath_save))[0]
mod_pardir = os.path.split(mod_dir)[0]
ull = '/usr/local/lib/'
ulb = '/usr/local/bin/'

if curdir == mod_dir[:len(curdir)] or mod_dir[:len(ull)] != ull:
	die(1,"Can't find system install directory! Aborting")

del_list = ['/usr/local/share/mmgen',mod_dir]

import stat
def is_reg(pn): return stat.S_ISREG(os.stat(pn).st_mode)
def is_dir(pn): return stat.S_ISDIR(os.stat(pn).st_mode)

for d in (ulb,mod_pardir):
	# add files only, not directories
	del_list += [os.path.join(d,e) for e in os.listdir(d) if is_reg(os.path.join(d,e)) and e[:6] == 'mmgen-']

if opt.list_paths:
	die(1,'\n'.join(del_list))

if not opt.no_prompt:
	m = 'Deleting the following paths and files:\n  {}\nProceed?'
	if not keypress_confirm(m.format('\n  '.join(del_list))):
		die(1,'Exiting at user request')

import shutil
for pn in del_list:
	if is_dir(pn): shutil.rmtree(pn)
	else:          os.unlink(pn)
	msg('Deleted: ' + pn)
