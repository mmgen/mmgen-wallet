#!/usr/bin/env python3

from mmgen.common import *

cmd_args = opts.init()

class foo(oneshot_warning):

	color = 'purple'
	message = 'foo variant {} selected'

class bar(oneshot_warning):

	color = 'yellow'
	message = 'bar is experimental software'

class wg(oneshot_warning_group):

	class foo:
		color = 'yellow'
		message = 'foo is experimental software.  Proceed at your own risk'

	class bar:
		color = 'red'
		message = 'The bar command is {} and can break your {}!!!'

	class baz:
		color = 'orange'
		message = 'baz variant {} selected'

for i in (1,2,3):
	wg('foo')
	wg('bar',fmt_args=['dangerous','computer'])
	wg('baz',div='alpha',fmt_args=['alpha'])
	wg('baz',div='beta',fmt_args=['beta'])
	foo(div='alpha',fmt_args=['alpha'])
	foo(div='beta',fmt_args=['beta'])
	bar()
	msg('loop')
