#!/usr/bin/env python3

from mmgen.util import msg
from mmgen.common import *

cmd_args = opts.init()

from mmgen.cfg import cfg_file

cf_usr = cfg_file('usr')
cf_sys = cfg_file('sys')
cf_sample = cfg_file('sample')

msg('Usr cfg file:    {}'.format(cf_usr.fn))
msg('Sys cfg file:    {}'.format(cf_sys.fn))
msg('Sample cfg file: {}'.format(cf_sample.fn))

if cmd_args:
	if cmd_args[0] == 'parse_test':
		ps = cf_sample.parse(parse_vars=True)
		msg('parsed chunks: {}'.format(len(ps)))
		pu = cf_usr.parse()
		msg('usr cfg: {}'.format(' '.join(['{}={}'.format(i.name,i.value) for i in pu])))
	elif cmd_args[0] == 'coin_specific_vars':
		from mmgen.protocol import init_proto_from_opts
		proto = init_proto_from_opts()
		for varname in cmd_args[1:]:
			print('{}.{}: {}'.format(
				type(proto).__name__,
				varname,
				getattr(proto,varname)
			))
