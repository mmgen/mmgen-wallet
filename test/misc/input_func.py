#!/usr/bin/env python3
# this script is used both for interactive and automated testing

import sys,os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))))
sys.path[0] = os.curdir

from mmgen.common import *

cmd_args = opts.init({'text': { 'desc': '', 'usage':'', 'options':'-e, --echo-passphrase foo' }})

if cmd_args[0] == 'passphrase':
	from mmgen.ui import get_words_from_user
	pw = get_words_from_user(
		('Enter passphrase: ','Enter passphrase (echoed): ')[bool(opt.echo_passphrase)] )
	msg('Entered: {}'.format(' '.join(pw)))
elif cmd_args[0] in ('get_char','line_input'):
	from mmgen.term import get_char
	from mmgen.ui import line_input
	from ast import literal_eval
	func_args = literal_eval(cmd_args[1])
	Msg(f'\n  term: {get_char.__self__.__name__}')
	Msg(f'  g.hold_protect_disable: {g.hold_protect_disable}')
	Msg('  {name}( {args} )'.format(
		name = cmd_args[0],
		args = ', '.join(f'{k}={v!r}' for k,v in func_args.items())
		))
	ret = locals()[cmd_args[0]](**func_args)
	Msg('  ==> {!r}'.format(ret))
