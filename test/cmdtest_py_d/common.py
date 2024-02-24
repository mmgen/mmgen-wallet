#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
test.cmdtest_py_d.common: Shared routines and data for the cmdtest.py test suite
"""

import sys,os

from mmgen.color import green,blue
from mmgen.util import msg

from ..include.common import cfg,getrand,text_jp,text_zh,ascii_cyr_gr,lat_cyr_gr

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

from mmgen.obj import MMGenTxComment,TwComment

tx_comment_jp = text_jp
tx_comment_zh = text_zh

lcg = ascii_cyr_gr if sys.platform == 'win32' else lat_cyr_gr # MSYS2 popen_spawn issue
tx_comment_lat_cyr_gr = lcg[:MMGenTxComment.max_len] # 72 chars

tw_comment_zh         = text_zh[:TwComment.max_screen_width // 2]
tw_comment_lat_cyr_gr = lcg[:TwComment.max_screen_width] # 80 chars

ref_bw_hash_preset = '1'
ref_bw_file = 'wallet.mmbrain'
ref_bw_file_spc = 'wallet-spaced.mmbrain'

ref_enc_fn = 'sample-text.mmenc'
tool_enc_passwd = "Scrypt it, don't hash it!"
chksum_pat = r'\b[A-F0-9]{4} [A-F0-9]{4} [A-F0-9]{4} [A-F0-9]{4}\b'

Ctrl_U = '\x15'

def ok_msg():
	if cfg.profile:
		return
	sys.stderr.write(green('\nOK\n') if cfg.exact_output or cfg.verbose else ' OK\n')

def skip(name,reason=None):
	msg('Skipping {}{}'.format( name, f' ({reason})' if reason else '' ))
	return 'skip'

def confirm_continue():
	from mmgen.ui import keypress_confirm
	if keypress_confirm(
			cfg,
			blue('Continue? (Y/n): '),
			default_yes     = True,
			complete_prompt = True ):
		if cfg.verbose or cfg.exact_output:
			sys.stderr.write('\n')
	else:
		raise KeyboardInterrupt('Exiting at user request')

def randbool():
	return getrand(1).hex()[0] in '02468ace'

def get_env_without_debug_vars():
	ret = dict(os.environ)
	for k in cfg._env_opts:
		if k[:11] == 'MMGEN_DEBUG' and k in ret:
			del ret[k]
	return ret

def get_file_with_ext(tdir,ext,delete=True,no_dot=False,return_list=False,delete_all=False,substr=False):

	dot = '' if no_dot else '.'

	def have_match(fn):
		return (
			fn == ext
			or fn.endswith( dot + ext )
			or (substr and ext in fn) )

	# Don’t use os.scandir here - it returns broken paths under Windows/MSYS2
	flist = [os.path.join(tdir,name) for name in os.listdir(tdir) if have_match(name)]

	if not flist:
		return False

	if return_list:
		return flist

	if len(flist) > 1 or delete_all:
		if delete or delete_all:
			if (cfg.exact_output or cfg.verbose) and not cfg.quiet:
				if delete_all:
					msg(f'Deleting all *{dot}{ext} files in ‘{tdir}’')
				else:
					msg(f'Multiple *{dot}{ext} files in ‘{tdir}’ - deleting')
			for f in flist:
				os.unlink(f)
		return False
	else:
		return flist[0]

def get_comment(do_shuffle=False):
	labels = [
		"Automotive",
		"Travel expenses",
		"Healthcare",
		tx_comment_jp[:40],
		tx_comment_zh[:40],
		"Alice’s allowance",
		"Bob’s bequest",
		"House purchase",
		"Real estate fund",
		"Job 1",
		"XYZ Corp.",
		"Eddie’s endowment",
		"Emergency fund",
		"Real estate fund",
		"Ian’s inheritance",
		"",
		"Rainy day",
		"Fred’s funds",
		"Job 2",
		"Carl’s capital",
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
