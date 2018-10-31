#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
from mmgen.seed import SeedSource,Wallet
from mmgen.filename import find_file_in_dir
from mmgen.obj import MMGenWalletLabel

usage = '[opts] [infile]'
nargs = 1
iaction = 'convert'
oaction = 'convert'
invoked_as = 'passchg' if g.prog_name == 'mmgen-passchg' else g.prog_name.partition('-wallet')[2]
bw_note = True

# full: defhHiJkKlLmoOpPqrSvz-
if invoked_as == 'gen':
	desc = 'Generate an {pnm} wallet from a random seed'
	opt_filter = 'ehdoJlLpPqrSvz-'
	usage = '[opts]'
	oaction = 'output'
	nargs = 0
elif invoked_as == 'conv':
	desc = 'Convert an {pnm} wallet from one format to another'
	opt_filter = 'dehHiJkKlLmoOpPqrSvz-'
elif invoked_as == 'chk':
	desc = 'Check validity of an {pnm} wallet'
	opt_filter = 'ehiHOlpPqrvz-'
	iaction = 'input'
elif invoked_as == 'passchg':
	desc = 'Change the passphrase, hash preset or label of an {pnm} wallet'
	opt_filter = 'efhdiHkKOlLmpPqrSvz-'
	iaction = 'input'
	bw_note = False
else:
	die(1,"'{}': unrecognized invocation".format(g.prog_name))

opts_data = lambda: {
# Can't use: share/Opts doesn't know anything about fmt codes
#	'sets': [('hidden_incog_output_params',bool,'out_fmt','hi')],
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
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={g.min_urandchars}, max={g.max_urandchars}, default={g.usr_randchars})
-S, --stdout          Write wallet data to stdout instead of file
-v, --verbose         Produce more verbose output
""".format(
		g=g,
		iaction=capfirst(iaction),
		oaction=capfirst(oaction),
	),
	'notes': """

{n_pw}{n_bw}

FMT CODES:
  {f}
""".format(
	f='\n  '.join(SeedSource.format_fmt_codes().splitlines()),
	n_pw=help_notes('passwd'),
	n_bw=('','\n\n' + help_notes('brainwallet'))[bw_note]
	)
}

cmd_args = opts.init(opts_data,opt_filter=opt_filter)

if opt.label:
	opt.label = MMGenWalletLabel(opt.label,msg="Error in option '--label'")

sf = get_seed_file(cmd_args,nargs,invoked_as=invoked_as)

if not invoked_as == 'chk': do_license_msg()

if invoked_as in ('conv','passchg'):
	m1 = green('Processing input wallet')
	m2 = yellow(' (default wallet)') if sf and os.path.dirname(sf) == g.data_dir else ''
	msg(m1+m2)

ss_in = None if invoked_as == 'gen' else SeedSource(sf,passchg=(invoked_as=='passchg'))
if invoked_as == 'chk':
	lbl = ss_in.ssdata.label.hl() if hasattr(ss_in.ssdata,'label') else 'NONE'
	vmsg('Wallet label: {}'.format(lbl))
	# TODO: display creation date
	sys.exit(0)

if invoked_as in ('conv','passchg'):
	gmsg('Processing output wallet')

ss_out = SeedSource(ss=ss_in,passchg=invoked_as=='passchg')

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
	from subprocess import check_output,CalledProcessError
	sd_cmd = (['wipe','-sf'],['sdelete','-p','20'])[g.platform=='win']
	try:
		check_output(sd_cmd + [ss_in.infile.name])
	except:
		ymsg("WARNING: '{}' command failed, using regular file delete instead".format(sd_cmd[0]))
		os.unlink(ss_in.infile.name)
else:
	try:
		assert invoked_as == 'gen','dw'
		assert not opt.outdir,'dw'
		assert not opt.stdout,'dw'
		assert not find_file_in_dir(Wallet,g.data_dir),'dw'
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
