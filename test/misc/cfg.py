#!/usr/bin/env python3

from mmgen.common import *

cfg = opts.init()

cmd_args = cfg._args

from mmgen.cfgfile import mmgen_cfg_file

cf_usr = mmgen_cfg_file(cfg,'usr')
cf_sys = mmgen_cfg_file(cfg,'sys')
cf_sample = mmgen_cfg_file(cfg,'sample')

msg(f'Usr cfg file:    {os.path.relpath(cf_usr.fn)}')
msg(f'Sys cfg file:    {os.path.relpath(cf_sys.fn)}')
msg(f'Sample cfg file: {os.path.relpath(cf_sample.fn)}')

if cmd_args:
	if cmd_args[0] == 'parse_test':
		ps = cf_sample.get_lines()
		msg(f'parsed chunks: {len(ps)}')
		pu = cf_usr.get_lines()
		msg('usr cfg: {}'.format( ' '.join(f'{i.name}={i.value}' for i in pu) ))
	elif cmd_args[0] == 'coin_specific_vars':
		for varname in cmd_args[1:]:
			msg('{}.{}: {}'.format(
				type(cfg._proto).__name__,
				varname,
				getattr(cfg._proto,varname)
			))
	elif cmd_args[0] == 'autoset_opts':
		assert cfg.rpc_backend == 'aiohttp', "cfg.rpc_backend != 'aiohttp'"
	elif cmd_args[0] == 'autoset_opts_cmdline':
		assert cfg.rpc_backend == 'curl', "cfg.rpc_backend != 'curl'"
	elif cmd_args[0] == 'mnemonic_entry_modes':
		from mmgen.mn_entry import mn_entry
		msg('mnemonic_entry_modes: {}\nmmgen: {}\nbip39: {}'.format(
			cfg.mnemonic_entry_modes,
			mn_entry(cfg,'mmgen').usr_dfl_entry_mode,
			mn_entry(cfg,'bip39').usr_dfl_entry_mode ))
