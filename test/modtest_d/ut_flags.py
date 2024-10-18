#!/usr/bin/env python3

"""
test.modtest_d.ut_flags: unit test for the MMGen suite's ClassFlags class
"""

from mmgen.flags import ClassOpts, ClassFlags

from ..include.common import qmsg, qmsg_r, vmsg

class unit_test:

	def run_test(self, name, ut):

		class MyClassOpts(ClassOpts):
			reserved_attrs = ('foo',)

		class cls1:
			avail_opts = ()
			avail_flags = ()
			def __init__(self, opts=None, flags=None):
				self.opt = ClassOpts(self, opts)
				self.flag = ClassFlags(self, flags)

		class cls2(cls1):
			avail_opts = ('foo', 'bar')
			avail_flags = ('baz',)

		class cls3(cls1):
			avail_opts = ('_foo',)

		class cls4(cls1):
			avail_opts = ('foo',)
			def __init__(self, opts=None, flags=None):
				self.opt = MyClassOpts(self, opts)

		def test_flags():
			def gen():
				for n, cls in enumerate((
						cls1(),
						cls2(),
						cls2(opts=['bar']),
						cls2(flags=['baz']),
					)):
					vmsg(f'Cfg {n+1}:')
					for k in ('opt', 'flag'):
						vmsg(f'  {k}s: {getattr(cls, k)}')
					yield cls
			return list(gen())

		def test_flags_err(d):

			def bad1(): d[1].flag.foo = False
			def bad2(): d[1].opt.baz = False
			def bad3(): cls3()
			def bad4(): cls4()
			def bad5(): cls1(opts='foo')
			def bad6(): cls2(opts=['qux'])
			def bad7(): d[1].flag.baz = False
			def bad8(): d[3].flag.baz = True
			def bad9(): d[1].flag.baz = 'x'

			ut.process_bad_data((
				('flag (1)',             'ClassFlagsError', 'unrecognized flag', bad1),
				('opt (1)',              'ClassFlagsError', 'unrecognized opt',  bad2),
				('avail_opts (1)',       'ClassFlagsError', 'underscore',        bad3),
				('avail_opts (2)',       'ClassFlagsError', 'reserved name',     bad4),
				('class invocation (1)', 'AssertionError',  'list or tuple',     bad5),
				('class invocation (2)', 'ClassFlagsError', 'unrecognized opt',  bad6),
				('flag (2)',             'ClassFlagsError', 'not set',           bad7),
				('flag (3)',             'ClassFlagsError', 'already set',       bad8),
				('flag (4)',             'AssertionError',  'not boolean',       bad9),
			))

		qmsg_r('Testing flags and opts...')
		vmsg('')
		classes = test_flags()
		qmsg('OK')

		qmsg_r('Testing error handling for flags and opts...')
		vmsg('')
		test_flags_err(classes)
		qmsg('OK')

		return True
