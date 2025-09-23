#!/usr/bin/env python3
# this script is used both for interactive and automated testing

import sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))))
sys.path[0] = os.curdir

from mmgen.cfg import Config
from mmgen.util import msg

opts_data = {
	'text': {
		'desc': '',
		'usage':'',
		'options':'-e, --echo-passphrase foo',
	}
}

cfg = Config(opts_data=opts_data)

match cfg._args:
	case ['passphrase']:
		from mmgen.ui import get_words_from_user
		pw = get_words_from_user(
			cfg,
			('Enter passphrase: ', 'Enter passphrase (echoed): ')[bool(cfg.echo_passphrase)] )
		msg('Entered: {}'.format(' '.join(pw)))
	case 'get_char' | 'line_input' as cmd, args:
		from mmgen.term import get_char
		from mmgen.ui import line_input
		from ast import literal_eval
		func_args = literal_eval(args)
		msg(f'\n  term: {get_char.__self__.__name__}')
		msg(f'  cfg.hold_protect_disable: {cfg.hold_protect_disable}')
		if cmd == 'line_input':
			func_args.update({'cfg':cfg})
		msg('  Calling {name}({args})'.format(
			name = cmd,
			args = ', '.join(f'{k}={v!r}' for k, v in func_args.items())
			))
		ret = locals()[cmd](**func_args)
		msg(f'  ==> {ret!r}')
