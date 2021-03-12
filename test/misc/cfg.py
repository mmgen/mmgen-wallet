#!/usr/bin/env python3

from mmgen.util import msg
from mmgen.common import *

cmd_args = opts.init()

from mmgen.cfg import cfg_file
cu = cfg_file('usr')
cS = cfg_file('sys')
cs = cfg_file('sample')
msg('usr cfg: {}'.format(cu.fn))
msg('sys cfg: {}'.format(cS.fn))
msg('sample cfg: {}'.format(cs.fn))

if cmd_args:
	if cmd_args[0] == 'parse_test':
		ps = cs.parse(parse_vars=True)
		msg('parsed chunks: {}'.format(len(ps)))
		pu = cu.parse()
		msg('usr cfg: {}'.format(' '.join(['{}={}'.format(i.name,i.value) for i in pu])))
	elif cmd_args[0] == 'coin_specific_vars':
		from mmgen.protocol import init_proto_from_opts
		proto = init_proto_from_opts()
		for varname in cmd_args[1:]:
			print(f'{type(proto).__name__}.{varname}:',getattr(proto,varname))
