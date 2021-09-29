#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
common.py: Shared routines and data for the test.py test suite
"""

import os
from mmgen.common import *
from ..include.common import *

log_file = 'test.py.log'

rt_pw = 'abc-α'
ref_wallet_brainpass = 'abc'
ref_wallet_hash_preset = '1'
ref_wallet_incog_offset = 123

dfl_seed_id = '98831F3A'
dfl_addr_idx_list = '1010,500-501,31-33,1,33,500,1011'
dfl_wpasswd = 'reference password'

pwfile = 'passwd_file'
hincog_fn = 'rand_data'
hincog_bytes = 1024*1024
hincog_offset = 98765
hincog_seedlen = 256

incog_id_fn = 'incog_id'
non_mmgen_fn = 'coinkey'

ref_dir = os.path.join('test','ref')
dfl_words_file = os.path.join(ref_dir,'98831F3A.mmwords')
dfl_bip39_file = os.path.join(ref_dir,'98831F3A.bip39')

from mmgen.obj import MMGenTxLabel,TwComment

tx_label_jp = text_jp
tx_label_zh = text_zh

lcg = ascii_cyr_gr if g.platform == 'win' else lat_cyr_gr # MSYS2 popen_spawn issue
tx_label_lat_cyr_gr = lcg[:MMGenTxLabel.max_len] # 72 chars

tw_label_zh         = text_zh[:TwComment.max_screen_width // 2]
tw_label_lat_cyr_gr = lcg[:TwComment.max_screen_width] # 80 chars

ref_bw_hash_preset = '1'
ref_bw_file = 'wallet.mmbrain'
ref_bw_file_spc = 'wallet-spaced.mmbrain'

ref_enc_fn = 'sample-text.mmenc'
tool_enc_passwd = "Scrypt it, don't hash it!"
chksum_pat = r'\b[A-F0-9]{4} [A-F0-9]{4} [A-F0-9]{4} [A-F0-9]{4}\b'

def ok_msg():
	if opt.profile: return
	sys.stderr.write(green('\nOK\n') if opt.exact_output or opt.verbose else ' OK\n')

def skip(name,reason=None):
	msg('Skipping {}{}'.format( name, f' ({reason})' if reason else '' ))
	return 'skip'

def confirm_continue():
	if keypress_confirm(blue('Continue? (Y/n): '),default_yes=True,complete_prompt=True):
		if opt.verbose or opt.exact_output: sys.stderr.write('\n')
	else:
		raise KeyboardInterrupt('Exiting at user request')

def randbool():
	return os.urandom(1).hex()[0] in '02468ace'

def disable_debug():
	global save_debug
	save_debug = {}
	for k in g.env_opts:
		if k[:11] == 'MMGEN_DEBUG':
			save_debug[k] = os.getenv(k)
			os.environ[k] = ''

def restore_debug():
	for k in save_debug:
		os.environ[k] = save_debug[k] or ''

def get_file_with_ext(tdir,ext,delete=True,no_dot=False,return_list=False,delete_all=False):

	dot = ('.','')[bool(no_dot)]
	flist = [os.path.join(tdir,f) for f in os.listdir(tdir) if f == ext or f[-len(dot+ext):] == dot+ext]

	if not flist: return False
	if return_list: return flist

	if len(flist) > 1 or delete_all:
		if delete or delete_all:
			if (opt.exact_output or opt.verbose) and not opt.quiet:
				if delete_all:
					msg(f'Deleting all *.{ext} files in {tdir!r}')
				else:
					msg(f'Multiple *.{ext} files in {tdir!r} - deleting')
			for f in flist:
				os.unlink(f)
		return False
	else:
		return flist[0]

def get_label(do_shuffle=False):
	labels = [
		"Automotive",
		"Travel expenses",
		"Healthcare",
		tx_label_jp[:40],
		tx_label_zh[:40],
		"Alice's allowance",
		"Bob's bequest",
		"House purchase",
		"Real estate fund",
		"Job 1",
		"XYZ Corp.",
		"Eddie's endowment",
		"Emergency fund",
		"Real estate fund",
		"Ian's inheritance",
		"",
		"Rainy day",
		"Fred's funds",
		"Job 2",
		"Carl's capital",
	]
	from random import shuffle
	global label_iter
	try:
		return next(label_iter)
	except:
		if do_shuffle:
			shuffle(labels)
		label_iter = iter(labels)
		return next(label_iter)
