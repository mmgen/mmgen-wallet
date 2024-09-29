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
opts: MMGen-specific command-line options processing after generic processing by share.Opts
"""
import sys,os

from .share import Opts
from .cfg import gc

def opt_preproc_debug(po):
	d = (
		('Cmdline',            ' '.join(sys.argv), False),
		('Filtered opts',      po.filtered_opts,   False),
		('User-selected opts', po.user_opts,       False),
		('Cmd args',           po.cmd_args,        False),
		('Opts',               po.opts,            True),
	)
	from .util import Msg,fmt_list
	Msg('\n=== opts.py debug ===')
	for label,data,pretty in d:
		Msg('    {:<20}: {}'.format(label,'\n' + fmt_list(data,fmt='col',indent=' '*8) if pretty else data))

long_opts_data = {
	'text': """
--, --accept-defaults      Accept defaults at all prompts
--, --coin=c               Choose coin unit. Default: BTC. Current choice: {cu_dfl}
--, --token=t              Specify an ERC20 token by address or symbol
--, --color=0|1            Disable or enable color output (default: 1)
--, --columns=N            Force N columns of output with certain commands
--, --scroll               Use the curses-like scrolling interface for
                         tracking wallet views
--, --force-256-color      Force 256-color output when color is enabled
--, --pager                Pipe output of certain commands to pager (WIP)
--, --data-dir=path        Specify {pnm} data directory location
--, --daemon-data-dir=path Specify coin daemon data directory location
--, --daemon-id=ID         Specify the coin daemon ID
--, --ignore-daemon-version Ignore coin daemon version check
--, --http-timeout=t       Set HTTP timeout in seconds for JSON-RPC connections
--, --no-license           Suppress the GPL license prompt
--, --rpc-host=HOST        Communicate with coin daemon running on host HOST
--, --rpc-port=PORT        Communicate with coin daemon listening on port PORT
--, --rpc-user=USER        Authenticate to coin daemon using username USER
--, --rpc-password=PASS    Authenticate to coin daemon using password PASS
--, --rpc-backend=backend  Use backend 'backend' for JSON-RPC communications
--, --aiohttp-rpc-queue-len=N Use N simultaneous RPC connections with aiohttp
--, --regtest=0|1          Disable or enable regtest mode
--, --testnet=0|1          Disable or enable testnet
--, --tw-name=NAME         Specify alternate name for the BTC/LTC/BCH tracking
                         wallet (default: ‘{tw_name}’)
--, --skip-cfg-file        Skip reading the configuration file
--, --version              Print version information and exit
--, --bob                  Specify user “Bob” in MMGen regtest mode
--, --alice                Specify user “Alice” in MMGen regtest mode
--, --carol                Specify user “Carol” in MMGen regtest mode
	""",
	'code': lambda proto,help_notes,s: s.format(
			pnm    = gc.proj_name,
			cu_dfl = proto.coin,
			tw_name = help_notes('dfl_twname')
		)
}

opts_data_dfl = {
	'text': {
		'desc': '',
		'usage':'[options]',
		'options': """
-h, --help         Print this help message
--, --longhelp     Print help message for long (common) options
"""
	}
}

class UserOpts:

	def __init__(
			self,
			cfg,
			opts_data,
			init_opts,    # dict containing opts to pre-initialize
			opt_filter,   # whitelist of opt letters; all others are skipped
			parse_only,
			parsed_opts):

		self.opts_data = od = opts_data or opts_data_dfl
		self.opt_filter = opt_filter

		od['text']['long_options'] = long_opts_data['text']

		# Make this available to usage()
		self.usage_data = od['text'].get('usage2') or od['text']['usage']

		# po: (user_opts,cmd_args,opts,filtered_opts)
		po = parsed_opts or Opts.parse_opts(od,opt_filter=opt_filter)

		cfg._args = po.cmd_args
		cfg._uopts = uopts = po.user_opts

		if init_opts: # initialize user opts to given value
			for uopt,val in init_opts.items():
				if uopt not in uopts:
					uopts[uopt] = val

		cfg._opts = self
		cfg._parsed_opts = po
		cfg._use_env = True
		cfg._use_cfg_file = not 'skip_cfg_file' in uopts

		if os.getenv('MMGEN_DEBUG_OPTS'):
			opt_preproc_debug(po)

		if 'version' in uopts:
			self.version() # exits

		if 'show_hash_presets' in uopts:
			self.show_hash_presets() # exits

		if parse_only:
			return

	def init_bottom(self,cfg):

		# print help screen only after globals initialized and locked:
		if cfg.help or cfg.longhelp:
			self.print_help(cfg) # exits

		# delete unneeded data:
		for k in ('text','notes','code'):
			if k in self.opts_data:
				del self.opts_data[k]
		del Opts.make_help
		del Opts.process_uopts
		del Opts.parse_opts

	def usage(self):
		from .util import Die
		Die(1,Opts.make_usage_str(gc.prog_name,'user',self.usage_data))

	def version(self):
		from .util import Die,fmt
		Die(0,fmt(f"""
			{gc.prog_name.upper()} version {gc.version}
			Part of {gc.proj_name} Wallet, an online/offline cryptocurrency wallet for the
			command line. Copyright (C){gc.Cdates} {gc.author} {gc.email}
		""",indent='  ').rstrip())

	def print_help(self,cfg):

		if not 'code' in self.opts_data:
			self.opts_data['code'] = {}

		from .protocol import init_proto_from_cfg
		proto = init_proto_from_cfg(cfg,need_amt=True)

		if getattr(cfg,'longhelp',None):
			self.opts_data['code']['long_options'] = long_opts_data['code']
			def remove_unneeded_long_opts():
				d = self.opts_data['text']['long_options']
				if proto.base_proto != 'Ethereum':
					d = '\n'.join(''+i for i in d.split('\n') if not '--token' in i)
				self.opts_data['text']['long_options'] = d
			remove_unneeded_long_opts()

		from .ui import do_pager
		do_pager(Opts.make_help( cfg, proto, self.opts_data, self.opt_filter ))

		sys.exit(0)

	def show_hash_presets(self):
		fs = '      {:<6} {:<3} {:<2} {}'
		from .util import msg
		from .crypto import Crypto
		msg('  Available parameters for scrypt.hash():')
		msg(fs.format('Preset','N','r','p'))
		for i in sorted(Crypto.hash_presets.keys()):
			msg(fs.format(i,*Crypto.hash_presets[i]))
		msg('  N = memory usage (power of two)\n  p = iterations (rounds)')
		sys.exit(0)
