#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
mmgen-remote: Retrieve data from a remote JSON-RPC server
"""

from .cfg import Config
from .util import Msg, die, fmt_list, async_run

opts_data = {
	'filter_codes': ['-'],
	'text': {
		'desc': 'Retrieve data from a remote JSON-RPC server',
		'usage': '[OPTS] COMMAND ARGS',
		'options': """
			-- -h, --help       Print this help message
			-- --, --longhelp   Print help message for long (global) options
			-- -d, --outdir=D   Output logfile to directory ‘D’ instead of working dir
			-- -l, --log        Log output to file
			X- -s, --swap-proto Swap protocol to use (Default: {x_dfl}, Choices: {x_all})
			X- -x, --proxy=P    Connect to remote server(s) via SOCKS5h proxy P (host:port)
			+                   Use special value ‘env’ to honor *_PROXY env vars instead.
		""",
		'notes': '{n_rc}',
	},
	'code': {
		'options': lambda cfg, proto, help_notes, s: s.format(
			x_all = fmt_list(cfg._autoset_opts['swap_proto'].choices, fmt='no_spc'),
			x_dfl = cfg._autoset_opts['swap_proto'].choices[0]),
		'notes': lambda cfg, help_mod, help_notes, s: s.format(
			n_rc = help_mod('remote'))
	}
}

cfg = Config(opts_data=opts_data)

def log(text, cmd, args, kwargs):
	args_disp = '-'.join(args) + '-'.join(f'{k}={v}' for k,v in kwargs.items())
	fn = 'mmgen-remote-{a}-{b}{c}.json'.format(
		a = cfg.coin,
		b = cmd.replace('_','-'),
		c = '-' + args_disp if args_disp else '')
	from .fileutil import write_data_to_file
	write_data_to_file(cfg, fn, text)

async def main():
	from .tool import get_cmds, process_args

	match cfg.coin:
		case 'RUNE':
			from .proto.rune.rpc.remote import THORChainRemoteRPCClient as cls
			cmds = get_cmds(cls.mods)
		case _:
			cmds = ()

	match cfg._args:
		case ['help']:
			from .help.remote import help
			Msg(help(cfg._proto, cfg))
		case ['help', cmd]:
			if cmd in cmds:
				from .tool.help import gen_tool_cmd_usage
				Msg('\n'.join(gen_tool_cmd_usage(None, cmd, lambda x: cls)))
			else:
				fs = '‘{}’: invalid command\n\nSupported commands:\n{}'
				die(1, fs.format(cmd, fmt_list(cmds, fmt='col', indent=' ' * 4)))
		case [cmd, *cmd_args] if cmd in cmds:
			args, kwargs = process_args(cmd, cmd_args, cls)
			res = getattr(cls(cfg, cfg._proto), cmd)(*args, **kwargs)
			import json
			from .ui import colorize_json
			text = json.dumps(res, indent=2)
			cfg._util.stdout_or_pager_nl(colorize_json(text) if cfg.color else text)
			if cfg.log:
				log(text, cmd, args, kwargs)
		case _:
			cfg._usage()

async_run(cfg, main)
