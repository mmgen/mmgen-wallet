#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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

import sys,os,re
import mmgen.globalvars as g
import mmgen.opt as opt
from mmgen.util import die,msg,green,do_license_msg,check_infile,mdie,mmsg,qmsg,capfirst
from mmgen.seed import SeedSource

bn = os.path.basename(sys.argv[0])
invoked_as = re.sub(r'^wallet','',bn.split("-")[-1])

usage = "[opts] [infile]"
nargs = 1
iaction = "convert"
oaction = "convert"
bw_note = opt.opts.bw_note
pw_note = opt.opts.pw_note

if invoked_as == "gen":
	desc = "Generate an {pnm} wallet from a random seed"
	opt_filter = "ehdoJlLpPqrSvz"
	usage = "[opts]"
	oaction = "output"
	nargs = 0
elif invoked_as == "conv":
	desc = "Convert an {pnm} wallet from one format to another"
	opt_filter = None
elif invoked_as == "chk":
	desc = "Check validity of an {pnm} wallet"
	opt_filter = "ehiHOlpPqrvz"
	iaction = "input"
elif invoked_as == "passchg":
	desc = "Change the password, hash preset or label of an {pnm} wallet"
	opt_filter = "ehdiHkKOlLmpPqrSvz"
	iaction = "input"
	bw_note = ""
else:
	die(1,"'%s': unrecognized invocation" % bn)

opts_data = {
# Can't use: share/Opts doesn't know anything about fmt codes
#	'sets': [('hidden_incog_output_params',bool,'out_fmt','hi')],
	'desc': desc.format(pnm=g.proj_name),
	'usage': usage,
	'options': """
-h, --help            Print this help message.
-d, --outdir=      d  Output files to directory 'd' instead of working dir.
-e, --echo-passphrase Echo passphrases and other user input to screen.
-i, --in-fmt=      f  {iaction} from wallet format 'f' (see FMT CODES below).
-o, --out-fmt=     f  {oaction} to wallet format 'f' (see FMT CODES below).
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated).
-J, --hidden-incog-output-params=f,o  Write hidden incognito data to file
                      'f' at offset 'o' (comma-separated).  If file 'f'
                      doesn't exist, it will be created and filled with
                      random data.
-O, --old-incog-fmt   Specify old-format incognito input.
-k, --keep-passphrase Reuse passphrase of input wallet for output wallet.
-K, --keep-hash-preset Reuse hash preset of input wallet for output wallet.
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {g.seed_len}-bit) seed lengths.
-L, --label=       l  Specify a label 'l' for output wallet.
-m, --keep-label      Reuse label of input wallet for output wallet.
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}').
-z, --show-hash-presets Show information on available hash presets.
-P, --passwd-file= f  Get wallet passphrase from file 'f'.
-q, --quiet           Produce quieter output; suppress some warnings.
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={g.min_urandchars}, max={g.max_urandchars}, default={g.usr_randchars}).
-S, --stdout          Write wallet data to stdout instead of file.
-v, --verbose         Produce more verbose output.
""".format(
		g=g,
		iaction=capfirst(iaction),
		oaction=capfirst(oaction),
	),
	'notes': """

{pw_note}{bw_note}

FMT CODES:
  {f}
""".format(
	f="\n  ".join(SeedSource.format_fmt_codes().splitlines()),
	pw_note=pw_note,
	bw_note=("","\n\n" + bw_note)[int(bool(bw_note))]
	)
}

cmd_args = opt.opts.init(opts_data,opt_filter=opt_filter)

if len(cmd_args) < nargs \
		and not opt.hidden_incog_input_params and not opt.in_fmt:
	die(1,"An input file or input format must be specified")
elif len(cmd_args) > nargs \
		or (len(cmd_args) == nargs and opt.hidden_incog_input_params):
	msg("No input files may be specified" if invoked_as == "gen"
			else "Too many input files specified")
	opt.opts.usage()

if cmd_args: check_infile(cmd_args[0])

if not invoked_as == "chk": do_license_msg()

if invoked_as in ("conv","passchg"): msg(green("Processing input wallet"))

ss_in = None if invoked_as == "gen" \
			else SeedSource(*cmd_args,passchg=invoked_as=="passchg")

if invoked_as == "chk":
	sys.exit()

if invoked_as in ("conv","passchg"): msg(green("Processing output wallet"))

ss_out = SeedSource(ss=ss_in,passchg=invoked_as=="passchg")
ss_out.write_to_file()
