#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
mmgen/main_wallet:  Entry point for MMGen wallet-related scripts
"""

import os
from mmgen.common import *
from mmgen.seed import Wallet,MMGenWallet
from mmgen.filename import find_file_in_dir
from mmgen.obj import MMGenWalletLabel,MasterShareIdx

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
}[g.prog_name]

dsw = 'the default or specified {pnm} wallet'

# full: defhHiJkKlLmoOpPqrSvz-
if invoked_as == 'gen':
	desc = 'Generate an {pnm} wallet from a random seed'
	opt_filter = 'ehdoJlLpPqrSvz-'
	usage = '[opts]'
	oaction = 'output'
	nargs = 0
elif invoked_as == 'conv':
	desc = 'Convert ' + dsw + ' from one format to another'
	opt_filter = 'dehHiJkKlLmoOpPqrSvz-'
elif invoked_as == 'chk':
	desc = 'Check validity of ' + dsw
	opt_filter = 'ehiHOlpPqrvz-'
	iaction = 'input'
elif invoked_as == 'passchg':
	desc = 'Change the passphrase, hash preset or label of ' + dsw
	opt_filter = 'efhdiHkKOlLmpPqrSvz-'
	iaction = 'input'
	do_bw_note = False
elif invoked_as == 'subgen':
	desc = 'Generate a subwallet from ' + dsw
	opt_filter = 'dehHiJkKlLmoOpPqrSvz-' # omitted: f
	usage = '[opts] [infile] <Subseed Index>'
	iaction = 'input'
	oaction = 'output'
	do_sw_note = True
elif invoked_as == 'seedsplit':
	desc = 'Generate a seed share from ' + dsw
	opt_filter = 'dehHiJlLMIoOpPqrSvz-'
	usage = '[opts] [infile] [<Split ID String>:]<index>:<share count>'
	iaction = 'input'
	oaction = 'output'
	do_ss_note = True

opts_data = {
	'text': {
		'desc': desc.format(pnm=g.proj_name),
		'usage': usage,
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
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
                      with non-standard (< {g.seed_len}-bit) seed lengths.
-L, --label=       l  Specify a label 'l' for output wallet
-m, --keep-label      Reuse label of input wallet for output wallet
-M, --master-share=i  Use a master share with index 'i' (min:{ms_min}, max:{ms_max})
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={g.min_urandchars}, max={g.max_urandchars}, default={g.usr_randchars})
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
		'options': lambda s: s.format(
			iaction=capfirst(iaction),
			oaction=capfirst(oaction),
			ms_min=MasterShareIdx.min_val,
			ms_max=MasterShareIdx.max_val,
			g=g,
		),
		'notes': lambda s: s.format(
			f='\n  '.join(Wallet.format_fmt_codes().splitlines()),
			n_ss=('',help_notes('seedsplit')+'\n\n')[do_ss_note],
			n_sw=('',help_notes('subwallet')+'\n\n')[do_sw_note],
			n_pw=help_notes('passwd'),
			n_bw=('','\n\n'+help_notes('brainwallet'))[do_bw_note]
		)
	}
}

cmd_args = opts.init(opts_data,opt_filter=opt_filter)

if opt.label:
	opt.label = MMGenWalletLabel(opt.label,msg="Error in option '--label'")

if invoked_as == 'subgen':
	from mmgen.obj import SubSeedIdx
	ss_idx = SubSeedIdx(cmd_args.pop())
elif invoked_as == 'seedsplit':
	from mmgen.obj import SeedSplitSpecifier
	master_share = MasterShareIdx(opt.master_share) if opt.master_share else None
	if cmd_args:
		sss = SeedSplitSpecifier(cmd_args.pop(),on_fail='silent')
		if master_share:
			if not sss:
				sss = SeedSplitSpecifier('1:2')
			elif sss.idx == 1:
				m1 = 'Share index of 1 meaningless in master share context.'
				m2 = 'To generate a master share, omit the seed split specifier.'
				die(1,m1+'  '+m2)
		elif not sss:
			opts.usage()
	elif master_share:
		sss = SeedSplitSpecifier('1:2')
	else:
		opts.usage()

if cmd_args:
	if invoked_as == 'gen' or len(cmd_args) > 1:
		opts.usage()
	check_infile(cmd_args[0])

sf = get_seed_file(cmd_args,nargs,invoked_as=invoked_as)

if invoked_as != 'chk':
	do_license_msg()

if invoked_as == 'gen':
	ss_in = None
else:
	ss_in = Wallet(sf,passchg=(invoked_as=='passchg'))
	m1 = green('Processing input wallet ')
	m2 = ss_in.seed.sid.hl()
	m3 = yellow(' (default wallet)') if sf and os.path.dirname(sf) == g.data_dir else ''
	msg(m1+m2+m3)

if invoked_as == 'chk':
	lbl = ss_in.ssdata.label.hl() if hasattr(ss_in.ssdata,'label') else 'NONE'
	vmsg('Wallet label: {}'.format(lbl))
	# TODO: display creation date
	sys.exit(0)

if invoked_as != 'gen':
	gmsg_r('Processing output wallet' + ('\n',' ')[invoked_as == 'seedsplit'])

if invoked_as == 'subgen':
	ss_out = Wallet(seed_bin=ss_in.seed.subseed(ss_idx,print_msg=True).data)
elif invoked_as == 'seedsplit':
	shares = ss_in.seed.split(sss.count,sss.id,master_share)
	seed_out = shares.get_share_by_idx(sss.idx,base_seed=True)
	msg(seed_out.get_desc(ui=True))
	ss_out = Wallet(seed=seed_out)
else:
	ss_out = Wallet(ss=ss_in,passchg=invoked_as=='passchg')

if invoked_as == 'gen':
	qmsg("This wallet's Seed ID: {}".format(ss_out.seed.sid.hl()))

if invoked_as == 'passchg':
	if not (opt.force_update or [k for k in ('passwd','hash_preset','label')
		if getattr(ss_out.ssdata,k) != getattr(ss_in.ssdata,k)]):
		die(1,'Password, hash preset and label are unchanged.  Taking no action')

if invoked_as == 'passchg' and ss_in.infile.dirname == g.data_dir:
	m1 = yellow('Confirmation of default wallet update')
	m2 = 'update the default wallet'
	confirm_or_raise(m1,m2,exit_msg='Password not changed')
	ss_out.write_to_file(desc='New wallet',outdir=g.data_dir)
	msg('Securely deleting old wallet')
	from subprocess import run
	wipe_cmd = ['sdelete','-p','20'] if g.platform=='win' else ['wipe','-sf']
	try:
		run(wipe_cmd + [ss_in.infile.name],check=True)
	except:
		ymsg("WARNING: '{}' command failed, using regular file delete instead".format(wipe_cmd[0]))
		os.unlink(ss_in.infile.name)
else:
	try:
		assert invoked_as == 'gen','dw'
		assert not opt.outdir,'dw'
		assert not opt.stdout,'dw'
		assert not find_file_in_dir(MMGenWallet,g.data_dir),'dw'
		m = 'Make this wallet your default and move it to the data directory?'
		assert keypress_confirm(m,default_yes=True),'dw'
	except Exception as e:
		if e.args[0] != 'dw': raise
		ss_out.write_to_file()
	else:
		ss_out.write_to_file(outdir=g.data_dir)

if invoked_as == 'passchg':
	if ss_out.ssdata.passwd == ss_in.ssdata.passwd:
		msg('New and old passphrases are the same')
	else:
		msg('Wallet passphrase has changed')
	if ss_out.ssdata.hash_preset != ss_in.ssdata.hash_preset:
		msg("Hash preset has been changed to '{}'".format(ss_out.ssdata.hash_preset))
