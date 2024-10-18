#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
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
main_wallet: Entry point for MMGen wallet-related scripts
"""

import sys, os
from .cfg import gc, Config
from .color import green, yellow
from .util import msg, gmsg_r, ymsg, bmsg, die, capfirst
from .wallet import Wallet, get_wallet_cls

usage = '[opts] [infile]'
nargs = 1
iaction = 'convert'
oaction = 'convert'
do_bw_note = True
do_sw_note = False
do_ss_note = False

invoked_as = {
	'mmgen-walletgen':    'gen',
	'mmgen-walletconv':   'conv',
	'mmgen-walletchk':    'chk',
	'mmgen-passchg':      'passchg',
	'mmgen-subwalletgen': 'subgen',
	'mmgen-seedsplit':    'seedsplit',
}[gc.prog_name]

dsw = f'the default or specified {gc.proj_name} wallet'

# full: defhHiJkKlLmoOpPqrSvz-
if invoked_as == 'gen':
	desc = f'Generate an {gc.proj_name} wallet from a random seed'
	opt_filter = 'ehdoJlLpPqrSvz-'
	usage = '[opts]'
	oaction = 'output'
	nargs = 0
elif invoked_as == 'conv':
	desc = 'Convert ' + dsw + ' from one format to another'
	opt_filter = 'dehHiJkKlLmNoOpPqrSvz-'
elif invoked_as == 'chk':
	desc = 'Check validity of ' + dsw
	opt_filter = 'ehiHOlpPqrvz-'
	iaction = 'input'
elif invoked_as == 'passchg':
	desc = 'Change the passphrase, hash preset or label of ' + dsw
	opt_filter = 'efhdiHkKOlLmNpPqrSvz-'
	iaction = 'input'
	do_bw_note = False
elif invoked_as == 'subgen':
	desc = 'Generate a subwallet from ' + dsw
	opt_filter = 'dehHiJkKlLmNoOpPqrSvz-' # omitted: f
	usage = '[opts] [infile] <Subseed Index>'
	iaction = 'input'
	oaction = 'output'
	do_sw_note = True
elif invoked_as == 'seedsplit':
	desc = 'Generate a seed share from ' + dsw
	opt_filter = 'dehHiJlLMNIoOpPqrSvz-'
	usage = '[opts] [infile] [<Split ID String>:]<index>:<share count>'
	iaction = 'input'
	oaction = 'output'
	do_ss_note = True

opts_data = {
	'text': {
		'desc': desc,
		'usage': usage,
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long (global) options
-d, --outdir=      d  Output files to directory 'd' instead of working dir
-e, --echo-passphrase Echo passphrases and other user input to screen
-f, --force-update    Force update of wallet even if nothing has changed
-i, --in-fmt=      f  {iaction} from wallet format 'f' (see FMT CODES below)
-o, --out-fmt=     f  {oaction} to wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-J, --hidden-incog-output-params=f,o  Write hidden incognito data to file
                      'f' at offset 'o' (comma-separated). File 'f' will be
                      created if necessary and filled with random data.
-O, --old-incog-fmt   Specify old-format incognito input
-k, --keep-passphrase Reuse passphrase of input wallet for output wallet
-K, --keep-hash-preset Reuse hash preset of input wallet for output wallet
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {dsl}-bit) seed lengths.
-L, --label=       l  Specify a label 'l' for output wallet
-m, --keep-label      Reuse label of input wallet for output wallet
-M, --master-share=i  Use a master share with index 'i' (min:{ms_min}, max:{ms_max})
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{gc.dfl_hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-N, --passwd-file-new-only Use passwd file only for new, not existing, wallet
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={cfg.min_urandchars}, max={cfg.max_urandchars}, default={cfg.usr_randchars})
-S, --stdout          Write wallet data to stdout instead of file
-v, --verbose         Produce more verbose output
""",
	'notes': """

{n_ss}{n_sw}{n_pw}{n_bw}

FMT CODES:

  {f}
"""
	},
	'code': {
		'options': lambda cfg, help_notes, s: s.format(
			iaction = capfirst(iaction),
			oaction = capfirst(oaction),
			ms_min  = help_notes('MasterShareIdx').min_val,
			ms_max  = help_notes('MasterShareIdx').max_val,
			dsl     = help_notes('dfl_seed_len'),
			cfg     = cfg,
			gc      = gc,
		),
		'notes': lambda cfg, help_mod, help_notes, s: s.format(
			f       = help_notes('fmt_codes'),
			n_ss    = ('', help_mod('seedsplit')+'\n\n')[do_ss_note],
			n_sw    = ('', help_notes('subwallet')+'\n\n')[do_sw_note],
			n_pw    = help_notes('passwd'),
			n_bw    = ('', '\n\n'+help_notes('brainwallet'))[do_bw_note]
		)
	}
}

cfg = Config(opts_data=opts_data, opt_filter=opt_filter, need_proto=False)

cmd_args = cfg._args

if invoked_as == 'subgen':
	from .subseed import SubSeedIdx
	ss_idx = SubSeedIdx(cmd_args.pop())
elif invoked_as == 'seedsplit':
	from .obj import get_obj
	from .seedsplit import SeedSplitSpecifier, MasterShareIdx
	master_share = MasterShareIdx(cfg.master_share) if cfg.master_share else None
	if cmd_args:
		sss = get_obj(SeedSplitSpecifier, s=cmd_args.pop(), silent=True)
		if master_share:
			if not sss:
				sss = SeedSplitSpecifier('1:2')
			elif sss.idx == 1:
				m1 = 'Share index of 1 meaningless in master share context.'
				m2 = 'To generate a master share, omit the seed split specifier.'
				die(1, m1+'  '+m2)
		elif not sss:
			cfg._usage()
	elif master_share:
		sss = SeedSplitSpecifier('1:2')
	else:
		cfg._usage()

from .fileutil import check_infile, get_seed_file

if cmd_args:
	if invoked_as == 'gen' or len(cmd_args) > 1:
		cfg._usage()
	check_infile(cmd_args[0])

sf = get_seed_file(cfg, nargs, invoked_as=invoked_as)

if invoked_as != 'chk':
	from .ui import do_license_msg
	do_license_msg(cfg)

if invoked_as == 'gen':
	ss_in = None
else:
	ss_in = Wallet(
		cfg     = cfg,
		fn      = sf,
		passchg = invoked_as == 'passchg',
		passwd_file = False if cfg.passwd_file_new_only else None)
	m1 = green('Processing input wallet ')
	m2 = ss_in.seed.sid.hl()
	m3 = yellow(' (default wallet)') if sf and os.path.dirname(sf) == cfg.data_dir else ''
	msg(m1+m2+m3)

if invoked_as == 'chk':
	lbl = ss_in.ssdata.label.hl() if hasattr(ss_in.ssdata, 'label') else 'NONE'
	cfg._util.vmsg(f'Wallet label: {lbl}')
	# TODO: display creation date
	sys.exit(0)

if invoked_as != 'gen':
	gmsg_r('Processing output wallet' + ('\n', ' ')[invoked_as == 'seedsplit'])

if invoked_as == 'subgen':
	ss_out = Wallet(
		cfg      = cfg,
		seed_bin = ss_in.seed.subseed(ss_idx, print_msg=True).data)
elif invoked_as == 'seedsplit':
	shares = ss_in.seed.split(sss.count, sss.id, master_share)
	seed_out = shares.get_share_by_idx(sss.idx, base_seed=True)
	msg(seed_out.get_desc(ui=True))
	ss_out = Wallet(
		cfg  = cfg,
		seed = seed_out)
else:
	ss_out = Wallet(
		cfg     = cfg,
		ss      = ss_in,
		passchg = invoked_as == 'passchg')

if invoked_as == 'gen':
	cfg._util.qmsg(f"This wallet's Seed ID: {ss_out.seed.sid.hl()}")

if invoked_as == 'passchg':
	def data_changed(attrs):
		for attr in attrs:
			if getattr(ss_out.ssdata, attr) != getattr(ss_in.ssdata, attr):
				return True
		return False
	if not (cfg.force_update or data_changed(('passwd', 'hash_preset', 'label'))):
		die(1, 'Password, hash preset and label are unchanged.  Taking no action')

if invoked_as == 'passchg':

	def secure_delete(fn):
		bmsg('Securely deleting old wallet')
		from .fileutil import shred_file
		shred_file(fn, verbose = cfg.verbose)

	def rename_old_wallet_maybe(silent):
		# though very unlikely, old and new wallets could have same Key ID and thus same filename.
		# If so, rename old wallet file before deleting.
		old_fn = ss_in.infile.name
		if os.path.basename(old_fn) == ss_out._filename():
			if not silent:
				ymsg(
					'Warning: diverting old wallet {old_fn!r} due to Key ID collision.  ' +
					'Please securely delete or move the diverted file!')
			os.rename(old_fn, old_fn+'.divert')
			return old_fn+'.divert'
		else:
			return old_fn

	if ss_in.infile.dirname == cfg.data_dir:
		from .ui import confirm_or_raise
		confirm_or_raise(
			cfg      = cfg,
			message  = yellow('Confirmation of default wallet update'),
			action   = 'update the default wallet',
			exit_msg = 'Password not changed')
		old_wallet = rename_old_wallet_maybe(silent=True)
		ss_out.write_to_file(desc='New wallet', outdir=cfg.data_dir)
		secure_delete(old_wallet)
	else:
		old_wallet = rename_old_wallet_maybe(silent=False)
		ss_out.write_to_file()
		from .ui import keypress_confirm
		if keypress_confirm(cfg, f'Securely delete old wallet {old_wallet!r}?'):
			secure_delete(old_wallet)
elif invoked_as == 'gen' and not cfg.outdir and not cfg.stdout:
	from .filename import find_file_in_dir
	if find_file_in_dir(get_wallet_cls('mmgen'), cfg.data_dir):
		ss_out.write_to_file()
	else:
		from .ui import keypress_confirm
		if keypress_confirm(
				cfg,
				'Make this wallet your default and move it to the data directory?',
				default_yes = True):
			ss_out.write_to_file(outdir=cfg.data_dir)
		else:
			ss_out.write_to_file()
else:
	ss_out.write_to_file()

if invoked_as == 'passchg':
	if ss_out.ssdata.passwd == ss_in.ssdata.passwd:
		msg('New and old passphrases are the same')
	else:
		msg('Wallet passphrase has changed')
	if ss_out.ssdata.hash_preset != ss_in.ssdata.hash_preset:
		msg(f'Hash preset has been changed to {ss_out.ssdata.hash_preset!r}')
