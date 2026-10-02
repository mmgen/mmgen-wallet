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
help.remote: command help for the ‘mmgen-remote’ utility
"""

from ..tool.help import gen_main_help
from ..cfg import gc
from ..color import yellow
from ..util import fmt_with_color

def help(proto, cfg):

	warning = """
		Communicating with a remote server can harm your privacy!
		To improve anonymity, proxy requests via Tor or I2P
		"""

	footer = f"""
		For individual command usage, invoke ‘{gc.prog_name} --coin={cfg.coin.lower()} help COMMAND’
		"""

	match cfg.coin:
		case 'RUNE':
			from ..proto.rune.rpc.remote import THORChainRemoteRPCClient as rpc
			clist = '\n  ' + '\n'.join(gen_main_help(
				mods_data        = rpc.mods,
				get_mod_cls_func = lambda x: rpc,
				indent           = '  '))
		case _:
			clist = f'No configured commands for coin {cfg.coin}\n  Supported coins: RUNE'
			warning = ''
			footer = ''

	return '{a}\nCOMMANDS:\n  {b}{c}\n'.format(
		a = '\n' + fmt_with_color(warning.strip(), yellow) if warning else '',
		b = clist,
		c = '\n' + footer.strip() if footer else '')
