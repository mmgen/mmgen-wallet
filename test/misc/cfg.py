#!/usr/bin/env python3

from mmgen.common import *

cmd_args = opts.init()

from mmgen.cfg import cfg_file

cf_usr = cfg_file('usr')
cf_sys = cfg_file('sys')
cf_sample = cfg_file('sample')

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
		from mmgen.protocol import init_proto_from_opts
		proto = init_proto_from_opts(need_amt=True)
		for varname in cmd_args[1:]:
			msg('{}.{}: {}'.format(
				type(proto).__name__,
				varname,
				getattr(proto,varname)
			))
	elif cmd_args[0] == 'autoset_opts':
		assert opt.rpc_backend == 'aiohttp', "opt.rpc_backend != 'aiohttp'"
	elif cmd_args[0] == 'autoset_opts_cmdline':
		assert opt.rpc_backend == 'curl', "opt.rpc_backend != 'curl'"
	elif cmd_args[0] == 'mnemonic_entry_modes':
		msg( 'mnemonic_entry_modes: {}'.format(g.mnemonic_entry_modes) )
