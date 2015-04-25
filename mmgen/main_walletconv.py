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
mmgen-walletconv: Convert an MMGen deterministic wallet from one format
                  to another
"""

import sys
import mmgen.globalvars as g
import mmgen.opt as opt
from mmgen.util import die,msg,green,do_license_msg,check_infile
from mmgen.seed import SeedSource

opts_data = {
	'sets_disabled': (
		('hidden_incog_input_params',  bool, 'in_fmt',  'hi'),
		('hidden_incog_output_params', bool, 'out_fmt', 'hi')
	),
	'desc': "Convert an {pnm} wallet from one format to another".format(
				pnm=g.proj_name),
	'usage':"[opts] [infile]",
	'options': """
-h, --help            Print this help message.
-d, --outdir=      d  Output files to directory 'd' instead of working dir.
-i, --in-fmt=      f  Convert from wallet format 'f' (see FMT CODES below).
-o, --out-fmt=     f  Convert to wallet format 'f' (see FMT CODES below).
-H, --hidden-incog-input-params=f,o  Use filename 'f' and offset 'o' (comma
                      separated) for hidden incognito input.
-J, --hidden-incog-output-params=f,o  Same above, but for output.  If file
                      'f' doesn't exist, it will be created and filled with
                      random data.
-O, --old-incog-fmt   Specify old-format incognito input.
-k, --keep-passphrase Reuse input wallet passphrase for output wallet.
-K, --keep-hash-preset Reuse input wallet hash preset for output wallet.
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {g.seed_len}-bit) seed lengths.
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}').
-q, --quiet           Produce quieter output; suppress some warnings.
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={g.min_urandchars}, max={g.max_urandchars}, default={g.usr_randchars}).
-S, --stdout          Write wallet data to stdout instead of file.
-v, --verbose         Produce more verbose output.

FMT CODES:
  {f}
""".format(g=g,f="\n  ".join(SeedSource.format_fmt_codes().split("\n")))
}

cmd_args = opt.opts.init(opts_data)

if len(cmd_args) == 0 \
	and not opt.hidden_incog_input_params \
		and not opt.in_fmt:
	die(1,"An input file or input format must be specified")

if len(cmd_args) > 1 or (len(cmd_args) == 1 and opt.hidden_incog_input_params):
	die(1,"Only one input file may be specified")

if len(cmd_args) == 1:
	check_infile(cmd_args[0])

do_license_msg()

msg(green("Processing input wallet"))

ss_in = SeedSource(*cmd_args)

msg(green("Processing output wallet"))

ss_out = SeedSource(ss=ss_in)
ss_out.write_to_file()
