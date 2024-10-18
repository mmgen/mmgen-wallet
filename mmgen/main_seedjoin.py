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
mmgen-seedjoin: Regenerate an MMGen deterministic wallet from seed shares
                created by 'mmgen-seedsplit'
"""

from .cfg import gc, Config
from .util import msg, msg_r, die
from .color import yellow
from .seed import Seed
from .seedsplit import SeedSplitIDString, MasterShareIdx, SeedShareMasterJoining
from .wallet import Wallet

opts_data = {
	'text': {
		'desc': """Regenerate an MMGen deterministic wallet from seed shares
                  created by 'mmgen-seedsplit'""",
		'usage': '[options] share1 share2 [...shareN]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long (global) options
-d, --outdir=      d  Output file to directory 'd' instead of working dir
-e, --echo-passphrase Echo passphrases and other user input to screen
-i, --id-str=      s  ID String of split (required for master share join only)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated).  NOTE: only the
                      first share may be in hidden incognito format!
-J, --hidden-incog-output-params=f,o  Write hidden incognito data to file
                      'f' at offset 'o' (comma-separated). File 'f' will be
                      created if necessary and filled with random data.
-o, --out-fmt=     f  Output to wallet format 'f' (see FMT CODES below)
-O, --old-incog-fmt   Specify old-format incognito input
-L, --label=       l  Specify a label 'l' for output wallet
-M, --master-share=i  Use a master share with index 'i' (min:{ms_min}, max:{ms_max})
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{gc.dfl_hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={cfg.min_urandchars}, max={cfg.max_urandchars}, default={cfg.usr_randchars})
-S, --stdout          Write wallet data to stdout instead of file
-v, --verbose         Produce more verbose output
""",
	'notes': """

COMMAND NOTES:

When joining with a master share, the master share must be listed first.
The remaining shares may be listed in any order.

The --id-str option is required only for master share joins.  For ordinary
joins it will be ignored.

For usage examples, see the help screen for the 'mmgen-seedsplit' command.

{n_pw}

FMT CODES:

  {f}
"""
	},
	'code': {
		'options': lambda cfg, s: s.format(
			ms_min = MasterShareIdx.min_val,
			ms_max = MasterShareIdx.max_val,
			cfg    = cfg,
			gc     = gc,
		),
		'notes': lambda cfg, help_notes, s: s.format(
			f      = help_notes('fmt_codes'),
			n_pw   = help_notes('passwd'),
		)
	}
}

def print_shares_info():
	si = 0
	out = '\nComputed shares:\n'
	if cfg.master_share:
		fs = '{:3}: {}->{} ' + yellow('(master share #{}, split id ') + '{}' + yellow(', share count {})\n')
		out += fs.format(
				1,
				shares[0].sid,
				share1.sid,
				master_idx,
				id_str.hl2(encl='‘’'),
				len(shares))
		si = 1
	for n, s in enumerate(shares[si:], si+1):
		out += f'{n:3}: {s.sid}\n'
	cfg._util.qmsg(out)

cfg = Config(opts_data=opts_data)

if len(cfg._args) + bool(cfg.hidden_incog_input_params) < 2:
	cfg._usage()

if cfg.master_share:
	master_idx = MasterShareIdx(cfg.master_share)
	id_str = SeedSplitIDString(cfg.id_str or 'default')

if cfg.id_str and not cfg.master_share:
	die(1,'--id-str option meaningless in context of non-master-share join')

from .fileutil import check_infile
from .wallet import check_wallet_extension
for arg in cfg._args:
	check_wallet_extension(arg)
	check_infile(arg)

from .ui import do_license_msg
do_license_msg(cfg)

cfg._util.qmsg('Input files:\n  {}\n'.format('\n  '.join(cfg._args)))

shares = [Wallet(cfg).seed] if cfg.hidden_incog_input_params else []
shares += [Wallet(cfg,fn).seed for fn in cfg._args]

if cfg.master_share:
	share1 = SeedShareMasterJoining(cfg, master_idx, shares[0], id_str, len(shares)).derived_seed
else:
	share1 = shares[0]

print_shares_info()

msg_r('Joining {n}-of-{n} XOR split...'.format(n=len(shares)))

seed_out = Seed.join_shares(cfg, [share1] + shares[1:])

msg(f'OK\nJoined Seed ID: {seed_out.sid.hl()}')

Wallet(cfg,seed=seed_out).write_to_file()
