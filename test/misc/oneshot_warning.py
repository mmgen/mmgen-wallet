#!/usr/bin/env python3

from mmgen.cfg import Config
from mmgen.util import msg, oneshot_warning, oneshot_warning_group

cfg = Config()

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

for i in (1, 2, 3):

	from mmgen.crypto import Crypto

	msg('\npw')
	for k in ('A', 'B'):
		ret = Crypto.pwfile_reuse_warning(k).warning_shown
		assert ret == (i != 1), 'warning_shown incorrect'

	msg('wg1')
	wg('foo')
	msg('wg2')
	wg('bar', fmt_args=['dangerous', 'computer'])
	msg('wg3')
	wg('baz', div='alpha', fmt_args=['alpha'])
	msg('wg4')
	wg('baz', div='beta', fmt_args=['beta'])

	msg('w1')
	foo(div='alpha', fmt_args=['alpha'])
	msg('w2')
	foo(div='beta', fmt_args=['beta'])
	msg('w3')
	bar()

	msg('bottom')
